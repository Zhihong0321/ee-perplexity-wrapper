#!/usr/bin/env python3
"""
Example script demonstrating queue manager usage
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.queue_manager import QueueManager, HumanBehaviorSettings, RequestPriority
from lib.cookie_manager import CookieManager

async def demo_queue_manager():
    """Demonstrate queue manager functionality"""
    
    # Initialize cookie manager
    cookie_manager = CookieManager("accounts.json")
    
    # Create queue manager with custom human behavior settings
    settings = HumanBehaviorSettings(
        min_delay_seconds=2.0,  # Faster for demo
        max_delay_seconds=5.0,
        peak_hours_start=9,
        peak_hours_end=17,
        weekend_factor=0.5,
        burst_probability=0.2,
        burst_size=2,
        idle_probability=0.1
    )
    
    queue_mgr = QueueManager(cookie_manager, settings, max_concurrent_requests=2)
    
    print("Starting Queue Manager Demo")
    print("=" * 50)
    
    # Start the queue manager
    await queue_mgr.start()
    
    try:
        # Show initial status
        status = queue_mgr.get_queue_status()
        print(f"Queue Status: {status['is_running']}")
        print(f"Active Requests: {status['active_requests']}")
        print(f"Queue Sizes: {status['queue_sizes']}")
        
        # Submit some example queries (will fail without valid accounts, but demonstrates queue)
        print("\nSubmitting demo queries...")
        
        query_examples = [
            ("What is artificial intelligence?", "demo_1"),
            ("How does machine learning work?", "demo_2"),
            ("Python best practices", "demo_3"),
            ("FastAPI tutorial", "demo_4")
        ]
        
        for query, account_name in query_examples:
            query_params = {
                "query": query,
                "mode": "auto",
                "sources": ["web"],
                "files": {},
                "stream": False,
                "language": "en-US",
                "follow_up": None,
                "incognito": False,
                "collection_uuid": None,
                "frontend_uuid": None,
                "frontend_context_uuid": None
            }
            
            # Determine priority based on query content
            priority = RequestPriority.NORMAL
            if "urgent" in query.lower():
                priority = RequestPriority.HIGH
            elif "demo" in account_name:
                priority = RequestPriority.LOW
            
            request_id = await queue_mgr.submit_request(
                account_name=account_name,
                query_params=query_params,
                priority=priority
            )
            
            print(f"Submitted request {request_id} with priority {priority.name}")
        
        # Wait a bit and check status
        print("\nWaiting 5 seconds to process...")
        await asyncio.sleep(5)
        
        # Check final status
        final_status = queue_mgr.get_queue_status()
        print(f"\nFinal Queue Status:")
        print(f"  Total Requests: {final_status['statistics']['total_requests']}")
        print(f"  Completed: {final_status['statistics']['completed_requests']}")
        print(f"  Failed: {final_status['statistics']['failed_requests']}")
        print(f"  Active: {final_status['active_requests']}")
        print(f"  Queue Sizes: {final_status['queue_sizes']}")
        
        # Show account usage
        if final_status['account_semaphores']:
            print(f"  Account Usage: {final_status['account_semaphores']}")
        
    except Exception as e:
        print(f"Demo error: {e}")
    
    finally:
        # Stop the queue manager
        print("\nStopping queue manager...")
        await queue_mgr.stop()
        print("Demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_queue_manager())