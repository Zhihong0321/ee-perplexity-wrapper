from fastapi import APIRouter, HTTPException, Query, Form, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json
import asyncio

from lib.queue_manager import QueueManager, HumanBehaviorSettings, RequestPriority, get_queue_manager
from lib.cookie_manager import CookieManager

# Dependency for cookie manager
async def get_cookie_manager():
    """Dependency to get cookie manager"""
    from api.main import cookie_manager
    return cookie_manager

router = APIRouter(prefix="/api/queue", tags=["queue"])

class BehaviorSettingsModel(BaseModel):
    min_delay_seconds: float = Field(5.0, ge=1.0, le=60.0, description="Minimum delay between requests")
    max_delay_seconds: float = Field(20.0, ge=1.0, le=300.0, description="Maximum delay between requests")
    peak_hours_start: int = Field(9, ge=0, le=23, description="Start of peak usage hours (24h format)")
    peak_hours_end: int = Field(17, ge=0, le=23, description="End of peak usage hours (24h format)")
    weekend_factor: float = Field(0.3, ge=0.1, le=1.0, description="Activity reduction factor for weekends")
    burst_probability: float = Field(0.1, ge=0.0, le=1.0, description="Probability of burst behavior")
    burst_size: int = Field(3, ge=1, le=10, description="Maximum size of burst requests")
    idle_probability: float = Field(0.05, ge=0.0, le=1.0, description="Probability of idle periods")

class QueryRequestModel(BaseModel):
    account_name: str = Field(..., description="Account name to use")
    query: str = Field(..., description="Query string to search")
    mode: str = Field("auto", description="Search mode")
    model: Optional[str] = Field(None, description="Model to use")
    sources: str = Field("web", description="Sources (comma-separated)")
    language: str = Field("en-US", description="Language")
    incognito: bool = Field(False, description="Use incognito mode")
    collection_uuid: Optional[str] = Field(None, description="Collection UUID")
    frontend_uuid: Optional[str] = Field(None, description="Frontend UUID")
    frontend_context_uuid: Optional[str] = Field(None, description="Frontend Context UUID")
    priority: str = Field("normal", description="Request priority")

# Global queue manager reference
_queue_manager: Optional[QueueManager] = None

async def get_global_queue_manager(cookie_manager: CookieManager) -> QueueManager:
    """Get or create the global queue manager"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = await get_queue_manager(cookie_manager)
    return _queue_manager

def get_priority_from_string(priority_str: str) -> RequestPriority:
    """Convert string to RequestPriority enum"""
    priority_map = {
        "low": RequestPriority.LOW,
        "normal": RequestPriority.NORMAL,
        "high": RequestPriority.HIGH,
        "urgent": RequestPriority.URGENT
    }
    return priority_map.get(priority_str.lower(), RequestPriority.NORMAL)

@router.get("/status")
async def get_queue_status(cookie_manager: CookieManager = Depends(get_cookie_manager)):
    """Get current queue status and statistics"""
    queue_mgr = await get_global_queue_manager(cookie_manager)
    status = queue_mgr.get_queue_status()
    
    return {
        "status": "success",
        "queue_status": status,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/settings/behavior")
async def update_behavior_settings(
    settings: BehaviorSettingsModel,
    cookie_manager: CookieManager = Depends(get_cookie_manager)
):
    """Update human behavior settings"""
    queue_mgr = await get_global_queue_manager(cookie_manager)
    
    behavior_settings = HumanBehaviorSettings(
        min_delay_seconds=settings.min_delay_seconds,
        max_delay_seconds=settings.max_delay_seconds,
        peak_hours_start=settings.peak_hours_start,
        peak_hours_end=settings.peak_hours_end,
        weekend_factor=settings.weekend_factor,
        burst_probability=settings.burst_probability,
        burst_size=settings.burst_size,
        idle_probability=settings.idle_probability
    )
    
    queue_mgr.update_behavior_settings(behavior_settings)
    
    return {
        "status": "success",
        "message": "Behavior settings updated",
        "settings": {
            "min_delay_seconds": behavior_settings.min_delay_seconds,
            "max_delay_seconds": behavior_settings.max_delay_seconds,
            "peak_hours_start": behavior_settings.peak_hours_start,
            "peak_hours_end": behavior_settings.peak_hours_end,
            "weekend_factor": behavior_settings.weekend_factor,
            "burst_probability": behavior_settings.burst_probability,
            "burst_size": behavior_settings.burst_size,
            "idle_probability": behavior_settings.idle_probability
        }
    }

@router.get("/settings/behavior")
async def get_behavior_settings(cookie_manager: CookieManager = Depends(get_cookie_manager)):
    """Get current human behavior settings"""
    queue_mgr = await get_global_queue_manager(cookie_manager)
    
    return {
        "status": "success",
        "settings": {
            "min_delay_seconds": queue_mgr.behavior_settings.min_delay_seconds,
            "max_delay_seconds": queue_mgr.behavior_settings.max_delay_seconds,
            "peak_hours_start": queue_mgr.behavior_settings.peak_hours_start,
            "peak_hours_end": queue_mgr.behavior_settings.peak_hours_end,
            "weekend_factor": queue_mgr.behavior_settings.weekend_factor,
            "burst_probability": queue_mgr.behavior_settings.burst_probability,
            "burst_size": queue_mgr.behavior_settings.burst_size,
            "idle_probability": queue_mgr.behavior_settings.idle_probability
        }
    }

@router.post("/query")
async def submit_query_request(
    request: QueryRequestModel,
    cookie_manager: CookieManager = Depends(get_cookie_manager)
):
    """Submit a query request to the queue"""
    queue_mgr = await get_global_queue_manager(cookie_manager)
    
    # Prepare query parameters
    sources_list = [s.strip() for s in request.sources.split(",")]
    query_params = {
        "query": request.query,
        "mode": request.mode,
        "model": request.model,
        "sources": sources_list,
        "files": {},
        "stream": False,
        "language": request.language,
        "follow_up": None,
        "incognito": request.incognito,
        "collection_uuid": request.collection_uuid,
        "frontend_uuid": request.frontend_uuid,
        "frontend_context_uuid": request.frontend_context_uuid
    }
    
    # Submit to queue
    priority = get_priority_from_string(request.priority)
    request_id = await queue_mgr.submit_request(
        account_name=request.account_name,
        query_params=query_params,
        priority=priority
    )
    
    return {
        "status": "success",
        "message": "Query submitted to queue",
        "request_id": request_id,
        "priority": priority.name,
        "queue_position": queue_mgr.get_queue_status()['queue_sizes'][priority.name]
    }

@router.get("/query/{request_id}")
async def get_request_status(
    request_id: str,
    cookie_manager: CookieManager = Depends(get_cookie_manager)
):
    """Get status of a specific request"""
    queue_mgr = await get_global_queue_manager(cookie_manager)
    status = queue_mgr.get_queue_status()
    
    # Check if request is active
    is_active = request_id in status.get('active_requests', {})
    
    return {
        "status": "success",
        "request_id": request_id,
        "is_active": is_active,
        "queue_status": status
    }

@router.get("/result/{request_id}")
async def get_request_result(
    request_id: str,
    delete_after: bool = Query(False, description="Delete result after retrieval"),
    cookie_manager: CookieManager = Depends(get_cookie_manager)
):
    """
    Get the result of a completed request by request_id.
    
    Returns:
    - status: "queued" | "processing" | "completed" | "failed" | "not_found"
    - result: The query result (if completed)
    - error: Error message (if failed)
    """
    queue_mgr = await get_global_queue_manager(cookie_manager)
    
    # Check if result is stored (all requests are now tracked from submission)
    result_data = queue_mgr.get_result(request_id)
    
    if result_data:
        response = {
            "status": result_data['status'],
            "request_id": request_id,
            "timestamp": result_data.get('timestamp')
        }
        
        # Include result/error based on status
        if result_data['status'] == 'completed':
            response["result"] = result_data.get('result')
        elif result_data['status'] == 'failed':
            response["error"] = result_data.get('error')
        elif result_data['status'] in ('queued', 'processing'):
            response["message"] = f"Request is {result_data['status']}"
        
        # Optionally delete after retrieval (only for completed/failed)
        if delete_after and result_data['status'] in ('completed', 'failed'):
            await queue_mgr.delete_result(request_id)
            response["deleted"] = True
        
        return response
    else:
        return {
            "status": "not_found",
            "request_id": request_id,
            "message": "Request not found - may have expired or never existed"
        }

@router.delete("/result/{request_id}")
async def delete_request_result(
    request_id: str,
    cookie_manager: CookieManager = Depends(get_cookie_manager)
):
    """Delete a stored result"""
    queue_mgr = await get_global_queue_manager(cookie_manager)
    deleted = await queue_mgr.delete_result(request_id)
    
    return {
        "status": "success" if deleted else "not_found",
        "request_id": request_id,
        "deleted": deleted
    }

@router.get("/results")
async def list_all_results(
    cookie_manager: CookieManager = Depends(get_cookie_manager)
):
    """List all stored results (for debugging)"""
    queue_mgr = await get_global_queue_manager(cookie_manager)
    
    return {
        "status": "success",
        "count": len(queue_mgr.results),
        "results": {
            req_id: {
                "status": data.get("status"),
                "timestamp": data.get("timestamp"),
                "has_result": data.get("result") is not None,
                "has_error": data.get("error") is not None
            }
            for req_id, data in queue_mgr.results.items()
        }
    }

@router.post("/stop")
async def stop_queue_manager(cookie_manager: CookieManager = Depends(get_cookie_manager)):
    """Stop the queue manager"""
    queue_mgr = await get_global_queue_manager(cookie_manager)
    await queue_mgr.stop()
    
    return {
        "status": "success",
        "message": "Queue manager stopped"
    }

@router.post("/start")
async def start_queue_manager(cookie_manager: CookieManager = Depends(get_cookie_manager)):
    """Start the queue manager"""
    queue_mgr = await get_global_queue_manager(cookie_manager)
    await queue_mgr.start()
    
    return {
        "status": "success",
        "message": "Queue manager started"
    }

@router.delete("/active_requests")
async def cancel_active_requests(cookie_manager: CookieManager = Depends(get_cookie_manager)):
    """Cancel all active requests"""
    queue_mgr = await get_global_queue_manager(cookie_manager)
    
    # Cancel all active tasks
    for task_id, task in queue_mgr.active_requests.items():
        task.cancel()
    
    queue_mgr.active_requests.clear()
    
    return {
        "status": "success",
        "message": "All active requests cancelled"
    }

@router.get("/health")
async def queue_health_check(cookie_manager: CookieManager = Depends(get_cookie_manager)):
    """Queue manager health check"""
    queue_mgr = await get_global_queue_manager(cookie_manager)
    status = queue_mgr.get_queue_status()
    
    return {
        "status": "healthy" if status["is_running"] else "stopped",
        "queue_manager": status["is_running"],
        "active_requests": len(status["active_requests"]),
        "total_queue_size": sum(status["queue_sizes"].values())
    }