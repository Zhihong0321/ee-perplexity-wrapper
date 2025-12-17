import asyncio
import random
import time
import threading
import json
import os
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import aiofiles
from lib import perplexity
from lib.cookie_manager import CookieManager

logger = logging.getLogger(__name__)

def get_results_storage_path() -> str:
    """Get path for queue results storage using Railway storage"""
    env_storage = os.getenv("STORAGE_ROOT")
    possible_paths = []
    if env_storage:
        possible_paths.append(env_storage)
    possible_paths.extend(["/storage", "/app/storage"])
    
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            return os.path.join(path, "queue_results.json")
    return "queue_results.json"

class RequestPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class QueueRequest:
    id: str
    account_name: str
    query_params: Dict[str, Any]
    priority: RequestPriority = RequestPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    callback: Optional[Callable] = None
    future: Optional[asyncio.Future] = field(default=None)

@dataclass
class HumanBehaviorSettings:
    """Settings to mimic human usage patterns"""
    min_delay_seconds: float = 5.0  # Minimum delay between requests
    max_delay_seconds: float = 20.0  # Maximum delay between requests
    peak_hours_start: int = 9  # Start of peak usage hours (24h format)
    peak_hours_end: int = 17  # End of peak usage hours (24h format)
    weekend_factor: float = 0.3  # Activity reduction factor for weekends
    burst_probability: float = 0.1  # Probability of burst behavior
    burst_size: int = 3  # Maximum size of burst requests
    idle_probability: float = 0.05  # Probability of idle periods
    
class QueueManager:
    def __init__(
        self, 
        cookie_manager: CookieManager,
        behavior_settings: Optional[HumanBehaviorSettings] = None,
        max_concurrent_requests: int = 3
    ):
        self.cookie_manager = cookie_manager
        self.behavior_settings = behavior_settings or HumanBehaviorSettings()
        self.max_concurrent_requests = max_concurrent_requests
        
        # Request queues
        self.queues: Dict[RequestPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in RequestPriority
        }
        
        # Account management
        self.account_semaphores: Dict[str, asyncio.Semaphore] = {}
        self.account_last_used: Dict[str, datetime] = {}
        self.active_requests: Dict[str, asyncio.Task] = {}
        
        # Queue management
        self.queue_task: Optional[asyncio.Task] = None
        self.is_running = False
        self.request_counter = 0
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'completed_requests': 0,
            'failed_requests': 0,
            'average_wait_time': 0.0,
            'requests_per_hour': {}
        }
        
        # Result storage (non-blocking pattern)
        self.results_storage_path = get_results_storage_path()
        self.results: Dict[str, Dict[str, Any]] = {}  # request_id -> {status, result, error, timestamp}
        self._load_results()
    
    def _load_results(self):
        """Load results from persistent storage"""
        try:
            if os.path.exists(self.results_storage_path):
                with open(self.results_storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.results = data.get('results', {})
                    # Clean up old results (older than 1 hour)
                    cutoff = (datetime.now() - timedelta(hours=1)).isoformat()
                    self.results = {
                        k: v for k, v in self.results.items() 
                        if v.get('timestamp', '') > cutoff
                    }
                    logger.info(f"Loaded {len(self.results)} pending results from storage")
        except Exception as e:
            logger.warning(f"Failed to load results: {e}")
            self.results = {}
    
    async def _save_results(self):
        """Save results to persistent storage"""
        try:
            data = {
                'results': self.results,
                'last_updated': datetime.now().isoformat()
            }
            async with aiofiles.open(self.results_storage_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, default=str))
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
    
    async def store_result(self, request_id: str, result: Any = None, error: str = None):
        """Store a completed result"""
        self.results[request_id] = {
            'status': 'completed' if error is None else 'failed',
            'result': result,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        await self._save_results()
    
    def get_result(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get result by request_id. Returns None if not found."""
        return self.results.get(request_id)
    
    async def delete_result(self, request_id: str) -> bool:
        """Delete a result after it's been retrieved"""
        if request_id in self.results:
            del self.results[request_id]
            await self._save_results()
            return True
        return False
    
    async def start(self):
        """Start the queue manager"""
        if self.is_running:
            return
        
        self.is_running = True
        self.queue_task = asyncio.create_task(self._process_queue())
        logger.info("Queue manager started")
    
    async def stop(self):
        """Stop the queue manager"""
        self.is_running = False
        if self.queue_task:
            self.queue_task.cancel()
            try:
                await self.queue_task
            except asyncio.CancelledError:
                pass
        logger.info("Queue manager stopped")
    
    def _calculate_human_delay(self) -> float:
        """Calculate delay based on human behavior patterns"""
        now = datetime.now()
        hour = now.hour
        is_weekend = now.weekday() >= 5
        
        # Base delay
        base_delay = random.uniform(
            self.behavior_settings.min_delay_seconds,
            self.behavior_settings.max_delay_seconds
        )
        
        # Time-based adjustments
        if is_weekend:
            base_delay *= (1.0 / self.behavior_settings.weekend_factor)  # Slower on weekends
        
        if hour < self.behavior_settings.peak_hours_start or hour > self.behavior_settings.peak_hours_end:
            base_delay *= 2.0  # Slower outside peak hours
        
        # Random behaviors
        if random.random() < self.behavior_settings.idle_probability:
            # Add extra idle time
            base_delay *= random.uniform(2.0, 5.0)
        
        return base_delay
    
    def _get_next_priority_queue(self) -> RequestPriority:
        """Get the next request based on priority"""
        # Check queues in order of priority
        for priority in sorted(RequestPriority, key=lambda x: x.value, reverse=True):
            if not self.queues[priority].empty():
                return priority
        return RequestPriority.NORMAL  # Default
    
    async def _get_available_account(self) -> Optional[str]:
        """Get an account that's not currently overloaded"""
        accounts = self.cookie_manager.get_all_accounts()
        available_accounts = []
        
        for account_name in accounts:
            # Initialize account semaphore if needed
            if account_name not in self.account_semaphores:
                self.account_semaphores[account_name] = asyncio.Semaphore(self.max_concurrent_requests)
            
            semaphore = self.account_semaphores[account_name]
            # Use _value correctly for semaphore count
            if hasattr(semaphore, '_value') and semaphore._value > 0:  # Has available slots
                # Check if enough time has passed since last use
                last_used = self.account_last_used.get(account_name)
                if not last_used or (datetime.now() - last_used).total_seconds() > self.behavior_settings.min_delay_seconds:
                    available_accounts.append(account_name)
        
        # Return account with longest time since last use
        if available_accounts:
            return min(available_accounts, key=lambda x: self.account_last_used.get(x, datetime.min))
        
        return None
    
    def _cleanup_task(self, request_id: str):
        """Clean up completed task"""
        # Use thread-safe removal
        if request_id in self.active_requests:
            try:
                del self.active_requests[request_id]
            except KeyError:
                pass  # Already removed by another thread
    
    async def _process_request(self, request: QueueRequest):
        """Process a single request"""
        try:
            # Update status to processing
            if request.id in self.results:
                self.results[request.id]['status'] = 'processing'
                await self._save_results()
            
            # Get available account (with retry logic)
            account_name = None
            max_wait_time = 60  # Maximum wait time for available account
            
            for _ in range(max_wait_time):
                account_name = await self._get_available_account()
                if account_name:
                    break
                await asyncio.sleep(1)
            
            if not account_name:
                raise Exception("No available accounts after waiting")
            
            # Override account name with the selected one
            request.account_name = account_name
            
            # Initialize semaphore if not exists
            if account_name not in self.account_semaphores:
                self.account_semaphores[account_name] = asyncio.Semaphore(self.max_concurrent_requests)
            
            # Acquire account semaphore
            async with self.account_semaphores[account_name]:
                self.account_last_used[account_name] = datetime.now()
                
                # Create Perplexity client
                cookies = self.cookie_manager.get_account_cookies(account_name)
                client = perplexity.Client(cookies)
                await client.init()
                
                try:
                    # Execute the request
                    query_params = request.query_params
                    result = await client.search(**query_params)
                    
                    # Update account usage
                    await self.cookie_manager.mark_account_used(account_name)
                finally:
                    # Clean up client session if it has a close method
                    if hasattr(client, 'session') and hasattr(client.session, 'close'):
                        await client.session.close()
                
                # Store result for later retrieval (non-blocking pattern)
                await self.store_result(request.id, result=result)
                logger.info(f"Request {request.id} completed, result stored")
                
                # Also set future if provided (for sync callers)
                if request.future and not request.future.done():
                    request.future.set_result(result)
                
                if request.callback:
                    await request.callback(result, request)
                
                self.stats['completed_requests'] += 1
                
        except Exception as e:
            logger.error(f"Request {request.id} failed: {str(e)}")
            
            # Store error for later retrieval
            await self.store_result(request.id, error=str(e))
            
            if request.future and not request.future.done():
                request.future.set_exception(e)
            
            self.stats['failed_requests'] += 1
        
        finally:
            # Clean up
            if request.id in self.active_requests:
                del self.active_requests[request.id]
    
    async def _process_queue(self):
        """Main queue processing loop"""
        while self.is_running:
            try:
                # Get next request based on priority
                priority = self._get_next_priority_queue()
                queue = self.queues[priority]
                
                try:
                    # Wait for request with timeout
                    request = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Calculate human-like delay
                delay = self._calculate_human_delay()
                
                # Handle burst behavior
                if random.random() < self.behavior_settings.burst_probability:
                    burst_size = random.randint(1, self.behavior_settings.burst_size)
                    logger.info(f"Burst mode: processing {burst_size} requests rapidly")
                    
                    # Process burst of requests
                    burst_tasks = []
                    for i in range(burst_size):
                        if queue.empty():
                            break
                        
                        burst_request = await queue.get()
                        task = asyncio.create_task(self._process_request(burst_request))
                        self.active_requests[burst_request.id] = task
                        burst_tasks.append(task)
                        
                        # Add task done callback to clean up
                        task.add_done_callback(lambda t, req_id=burst_request.id: self._cleanup_task(req_id))
                        
                        if i < burst_size - 1:  # Small delay between burst requests
                            await asyncio.sleep(0.5)
                    
                    # Wait for all burst tasks to complete before processing next burst
                    if burst_tasks:
                        await asyncio.gather(*burst_tasks, return_exceptions=True)
                    
                    # Longer delay after burst
                    delay *= 2.0
                else:
                    # Normal single request processing
                    task = asyncio.create_task(self._process_request(request))
                    self.active_requests[request.id] = task
                    
                    # Add task done callback to clean up
                    task.add_done_callback(lambda t, req_id=request.id: self._cleanup_task(req_id))
                
                # Wait before next request
                await asyncio.sleep(delay)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processing error: {str(e)}")
                await asyncio.sleep(5)  # Brief pause on error
    
    async def submit_request(
        self, 
        account_name: str,
        query_params: Dict[str, Any],
        priority: RequestPriority = RequestPriority.NORMAL
    ) -> str:
        """Submit a request to the queue"""
        request_id = f"req_{int(time.time())}_{self.request_counter}"
        self.request_counter += 1
        
        request = QueueRequest(
            id=request_id,
            account_name=account_name,
            query_params=query_params,
            priority=priority
        )
        
        # Store request immediately with "queued" status so it can be tracked
        self.results[request_id] = {
            'status': 'queued',
            'result': None,
            'error': None,
            'timestamp': datetime.now().isoformat(),
            'priority': priority.name,
            'account_name': account_name
        }
        await self._save_results()
        
        # Add to appropriate queue
        await self.queues[priority].put(request)
        
        self.stats['total_requests'] += 1
        
        # Update hourly statistics (thread-safe)
        current_hour = datetime.now().strftime("%Y-%m-%d %H:00")
        with threading.Lock():
            if current_hour not in self.stats['requests_per_hour']:
                self.stats['requests_per_hour'][current_hour] = 0
            self.stats['requests_per_hour'][current_hour] += 1
        
        logger.info(f"Request {request_id} submitted to queue with priority {priority.name}")
        return request_id
    
    async def submit_request_with_result(
        self,
        account_name: str,
        query_params: Dict[str, Any],
        priority: RequestPriority = RequestPriority.NORMAL,
        timeout: Optional[float] = None
    ) -> Any:
        """Submit request and wait for result"""
        request_id = await self.submit_request(account_name, query_params, priority)
        
        # Create future and set it in the request
        future = asyncio.Future()
        
        # Find the request in the queue and set its future
        # This is a bit tricky since we can't easily modify queued items
        # For simplicity, we'll wait for completion via polling
        
        start_time = time.time()
        while True:
            if timeout and (time.time() - start_time) > timeout:
                raise asyncio.TimeoutError(f"Request {request_id} timed out")
            
            # Check if request is completed
            if request_id not in self.active_requests and request_id in self.stats:
                break
            
            await asyncio.sleep(0.1)
        
        return None  # This would need to be improved to return actual result
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            'is_running': self.is_running,
            'queue_sizes': {priority.name: queue.qsize() for priority, queue in self.queues.items()},
            'active_requests': len(self.active_requests),
            'account_semaphores': {name: str(sem._value) + '/' + str(self.max_concurrent_requests) 
                                 for name, sem in self.account_semaphores.items()},
            'statistics': self.stats.copy()
        }
    
    def update_behavior_settings(self, settings: HumanBehaviorSettings):
        """Update human behavior settings"""
        self.behavior_settings = settings
        logger.info("Behavior settings updated")

# Global queue manager instance
queue_manager: Optional[QueueManager] = None

async def get_queue_manager(cookie_manager: CookieManager) -> QueueManager:
    """Get or create the global queue manager"""
    global queue_manager
    if queue_manager is None:
        queue_manager = QueueManager(cookie_manager)
        await queue_manager.start()
    return queue_manager

def get_priority_from_string(priority_str: str) -> RequestPriority:
    """Convert string to RequestPriority enum"""
    priority_map = {
        "low": RequestPriority.LOW,
        "normal": RequestPriority.NORMAL,
        "high": RequestPriority.HIGH,
        "urgent": RequestPriority.URGENT
    }
    return priority_map.get(priority_str.lower(), RequestPriority.NORMAL)