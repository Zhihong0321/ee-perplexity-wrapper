from fastapi import FastAPI, Query, HTTPException, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import sys
import os

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from lib import perplexity
from lib.cookie_manager import CookieManager
from typing import List, Optional
from datetime import datetime
from api.utils import extract_answer, save_resp, create_api_response, handle_api_error
from api.config import get_storage_file_path
import asyncio
import time

# Initialize cookie manager with persistent storage path
storage_file = get_storage_file_path("accounts.json")
cookie_manager = CookieManager(storage_file)

# Templates
try:
    # Use absolute path from current working directory
    template_dir = "api/templates"
    print(f"Looking for templates in: {template_dir}")
    templates = Jinja2Templates(directory=template_dir)
except Exception as e:
    print(f"Failed to load templates: {e}")
    templates = None

app = FastAPI(
    title="Perplexity Multi-Account API", 
    description="""
# Perplexity AI Wrapper API

This API provides a programmatic interface to Perplexity AI, supporting multiple accounts, cookie management, and persistent conversations.

## Features

*   **Multi-Account Support**: Manage multiple Perplexity accounts with automatic cookie handling.
*   **Persistent Conversations**: Maintain visual and logical threads using `frontend_context_uuid` and `backend_uuid`.
*   **Perplexity Spaces**: Access and manage Collections (Spaces).
*   **Streaming Support**: Real-time SSE (Server-Sent Events) responses.
*   **Flexible Query Modes**: Support for various search modes (pro, reasoning, writing, etc.) and models.
*   **Source Selection**: Filter by web, scholar, or social sources.

## Usage Guide

1.  **Authentication**: Add your Perplexity cookies via the `/api/account/add` endpoint or the dashboard.
2.  **Querying**: Use `/api/query_sync` for JSON responses or `/api/query_async` for streaming.
3.  **Threads**: To continue a conversation, pass the `backend_uuid` from the previous response and keep the same `frontend_context_uuid`.

## Important Notes

*   This is an unofficial wrapper.
*   Ensure you comply with Perplexity's terms of service.
"""
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include queue router
try:
    from api.queue_endpoints import router as queue_router
    app.include_router(queue_router)
    print("[OK] Queue management endpoints loaded")
except Exception as e:
    print(f"[WARN] Failed to load queue endpoints: {e}")

# Import and include TNB extractor router
try:
    from api.tnb_extractor_endpoints import router as tnb_router
    app.include_router(tnb_router)
    print("[OK] TNB Bill Extractor endpoints loaded")
except Exception as e:
    print(f"[WARN] Failed to load TNB extractor endpoints: {e}")

# Import and include MYKAD extractor router
try:
    from api.mykad_extractor_endpoints import router as mykad_router
    app.include_router(mykad_router)
    print("[OK] MYKAD & Namecard Extractor endpoints loaded")
except Exception as e:
    print(f"[WARN] Failed to load MYKAD extractor endpoints: {e}")

# Global queue manager
async_queue_manager = None

async def get_queue_manager(cookie_mgr):
    """Get or initialize the global queue manager"""
    global async_queue_manager
    if async_queue_manager is None:
        from lib.queue_manager import QueueManager
        async_queue_manager = QueueManager(cookie_mgr)
        await async_queue_manager.start()
    return async_queue_manager

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "message": "Perplexity Multi-Account API is running"}


async def get_perplexity_client(account_name: str) -> perplexity.Client:
    """Get a Perplexity client for the specified account."""
    try:
        cookies = cookie_manager.get_account_cookies(account_name)
        client = perplexity.Client(cookies)
        await client.init()  # Initialize the async session
        return client
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


async def generate_sse_stream(
    query: str,
    answer_only: bool,
    mode: str,
    model: Optional[str],
    sources: List[str],
    language: str,
    follow_up: Optional[dict],
    incognito: bool,
    account_name: str,
    collection_uuid: Optional[str] = None,
    frontend_uuid: Optional[str] = None,
    frontend_context_uuid: Optional[str] = None,
):
    """Generate SSE stream from Perplexity responses."""
    response_count = 0

    try:
        # Get the specific account client
        client = await get_perplexity_client(account_name)
    
        # Start the streaming search
        async for stream in await client.search(
            query,
            mode=mode,
            model=model,
            sources=sources,
            files={},
            stream=True,
            language=language,
            follow_up=follow_up,
            incognito=incognito,
            collection_uuid=collection_uuid,
            frontend_uuid=frontend_uuid,
            frontend_context_uuid=frontend_context_uuid,
        ):
            response_count += 1
            file_name = (
                f"API-{account_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{response_count}"
            )
            save_resp(stream, file_name)
            if answer_only:
                ans_data = extract_answer(stream, file_name)
                if "answer" in ans_data and ans_data["answer"] is not None:
                    event_data = json.dumps(
                        {
                            "type": "content",
                            "content": ans_data,
                            "done": False,
                            "account_used": account_name
                        }
                    )
                    yield f"data: {event_data}\n\n"

            # If not answer_only, send the full stream content
            else:
                event_data = json.dumps(
                    {"type": "content", "content": stream, "done": False, "account_used": account_name}
                )
                yield f"data: {event_data}\n\n"

        # Send completion event
        event_data = json.dumps({"type": "content", "content": "", "done": True, "account_used": account_name})
        yield f"data: {event_data}\n\n"

    except Exception as e:
        error_data = json.dumps({"type": "error", "error": str(e), "account_used": account_name})
        yield f"data: {error_data}\n\n"

    finally:
        # Mark account as used
        await cookie_manager.mark_account_used(account_name)


@app.get("/api/query_async")
async def query_async(
    q: str = Query(..., description="Query string to search"),
    account_name: str = Query(..., description="Account name to use"),
    backend_uuid: str = Query(
        None, description="UUID of the previous response", alias="backend_uuid"
    ),
    answer_only: bool = Query(False, description="Return only the answer text"),
    mode: str = Query(
        "auto",
        description="Search mode",
        enum=["auto", "writing", "coding", "research"],
    ),
    model: Optional[str] = Query(None, description="Model to use"),
    sources: str = Query(
        "web",
        description="Sources (comma-separated: web, scholar, social)",
    ),
    language: str = Query("en-US", description="Language"),
    incognito: bool = Query(False, description="Use incognito mode"),
    collection_uuid: Optional[str] = Query(None, description="Collection UUID to search within"),
    frontend_uuid: Optional[str] = Query(None, description="Frontend UUID"),
    frontend_context_uuid: Optional[str] = Query(None, description="Frontend Context UUID (Thread ID)"),
):
    """Stream Perplexity AI responses as Server-Sent Events (SSE). Handles both new and follow-up queries."""
    sources_list = [s.strip() for s in sources.split(",")]
    follow_up = (
        {"backend_uuid": backend_uuid, "attachments": []} if backend_uuid else None
    )
    return StreamingResponse(
        generate_sse_stream(
            query=q,
            answer_only=answer_only,
            mode=mode,
            model=model,
            sources=sources_list,
            language=language,
            follow_up=follow_up,
            incognito=incognito,
            account_name=account_name,
            collection_uuid=collection_uuid,
            frontend_uuid=frontend_uuid,
            frontend_context_uuid=frontend_context_uuid,
        ),
        media_type="text/event-stream",
    )


@app.get("/api/query_sync")
async def query_sync(
    q: str = Query(..., description="Query string to search"),
    account_name: str = Query(..., description="Account name to use"),
    backend_uuid: str = Query(
        None, description="UUID of the previous response", alias="backend_uuid"
    ),
    answer_only: bool = Query(False, description="Return only the answer text"),
    mode: str = Query(
        "auto",
        description="Search mode",
        enum=["auto", "writing", "coding", "research"],
    ),
    model: Optional[str] = Query(None, description="Model to use"),
    sources: str = Query(
        "web",
        description="Sources (comma-separated: web, scholar, social)",
    ),
    language: str = Query("en-US", description="Language"),
    incognito: bool = Query(False, description="Use incognito mode"),
    collection_uuid: Optional[str] = Query(None, description="Collection UUID to search within"),
    frontend_uuid: Optional[str] = Query(None, description="Frontend UUID"),
    frontend_context_uuid: Optional[str] = Query(None, description="Frontend Context UUID (Thread ID)"),
):
    """Query Perplexity AI and return the full response as JSON (no streaming)."""
    sources_list = [s.strip() for s in sources.split(",")]
    follow_up = (
        {"backend_uuid": backend_uuid, "attachments": []} if backend_uuid else None
    )
    try:
        # Get the specific account client
        client = await get_perplexity_client(account_name)
        
        result = await client.search(
            q,
            mode=mode,
            model=model,
            sources=sources_list,
            files={},
            stream=False,
            language=language,
            follow_up=follow_up,
            incognito=incognito,
            collection_uuid=collection_uuid,
            frontend_uuid=frontend_uuid,
            frontend_context_uuid=frontend_context_uuid,
        )
        file_name = f"API-{account_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}-sync"
        save_resp(result, file_name)
        
        # Mark account as used
        await cookie_manager.mark_account_used(account_name)
        
        if answer_only:
            ans_data = extract_answer(result, file_name)
            return create_api_response(ans_data, account_name)
        
        return create_api_response(result, account_name)
    except Exception as e:
        return handle_api_error(e, account_name)


# Queue-based query endpoints
@app.get("/api/query_queue_sync")
async def query_queue_sync(
    q: str = Query(..., description="Query string to search"),
    account_name: str = Query(None, description="Account name to use (optional, queue will select if not provided)"),
    backend_uuid: str = Query(
        None, description="UUID of the previous response", alias="backend_uuid"
    ),
    answer_only: bool = Query(False, description="Return only the answer text"),
    mode: str = Query(
        "auto",
        description="Search mode",
        enum=["auto", "writing", "coding", "research"],
    ),
    model: Optional[str] = Query(None, description="Model to use"),
    sources: str = Query(
        "web",
        description="Sources (comma-separated: web, scholar, social)",
    ),
    language: str = Query("en-US", description="Language"),
    incognito: bool = Query(False, description="Use incognito mode"),
    collection_uuid: Optional[str] = Query(None, description="Collection UUID to search within"),
    frontend_uuid: Optional[str] = Query(None, description="Frontend UUID"),
    frontend_context_uuid: Optional[str] = Query(None, description="Frontend Context UUID (Thread ID)"),
    priority: str = Query("normal", description="Request priority (low, normal, high, urgent)"),
    timeout: int = Query(300, description="Timeout in seconds"),
):
    """Query Perplexity AI through the queue manager with human-like timing."""
    global async_queue_manager
    
    try:
        # Initialize queue manager if needed
        if async_queue_manager is None:
            async_queue_manager = await get_queue_manager(cookie_manager)
        
        # Prepare query parameters
        sources_list = [s.strip() for s in sources.split(",")]
        follow_up = (
            {"backend_uuid": backend_uuid, "attachments": []} if backend_uuid else None
        )
        
        query_params = {
            "query": q,
            "mode": mode,
            "model": model,
            "sources": sources_list,
            "files": {},
            "stream": False,
            "language": language,
            "follow_up": follow_up,
            "incognito": incognito,
            "collection_uuid": collection_uuid,
            "frontend_uuid": frontend_uuid,
            "frontend_context_uuid": frontend_context_uuid,
        }
        
        # If no account specified, queue manager will select one
        if not account_name:
            # Get first available account
            accounts = cookie_manager.get_all_accounts()
            if not accounts:
                return handle_api_error(Exception("No accounts available"), "none")
            account_name = list(accounts.keys())[0]
        
        # Submit to queue and wait for result with future
        from lib.queue_manager import RequestPriority
        priority_map = {
            "low": RequestPriority.LOW,
            "normal": RequestPriority.NORMAL,
            "high": RequestPriority.HIGH,
            "urgent": RequestPriority.URGENT
        }
        priority_obj = priority_map.get(priority.lower(), RequestPriority.NORMAL)
        
        # Create future for result
        result_future = asyncio.Future()
        
        # Create request with future
        from lib.queue_manager import QueueRequest
        request_id = f"req_{int(time.time())}_{async_queue_manager.request_counter}"
        async_queue_manager.request_counter += 1
        
        queue_request = QueueRequest(
            id=request_id,
            account_name=account_name,
            query_params=query_params,
            priority=priority_obj,
            future=result_future
        )
        
        # Submit to queue
        await async_queue_manager.queues[priority_obj].put(queue_request)
        async_queue_manager.stats['total_requests'] += 1
        
        # Wait for result with timeout
        try:
            import time
            result = await asyncio.wait_for(result_future, timeout=timeout)
            
            # Process the result
            file_name = f"API-QUEUE-{account_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}-sync"
            save_resp(result, file_name)
            
            if answer_only:
                ans_data = extract_answer(result, file_name)
                return create_api_response(ans_data, account_name)
            
            return create_api_response(result, account_name)
            
        except asyncio.TimeoutError:
            return handle_api_error(Exception("Request timed out"), account_name)
        
    except Exception as e:
        return handle_api_error(e, account_name or "unknown")


@app.get("/api/query_queue_async")
async def query_queue_async(
    q: str = Query(..., description="Query string to search"),
    account_name: str = Query(None, description="Account name to use (optional)"),
    backend_uuid: str = Query(
        None, description="UUID of the previous response", alias="backend_uuid"
    ),
    answer_only: bool = Query(False, description="Return only the answer text"),
    mode: str = Query(
        "auto",
        description="Search mode",
        enum=["auto", "writing", "coding", "research"],
    ),
    model: Optional[str] = Query(None, description="Model to use"),
    sources: str = Query(
        "web",
        description="Sources (comma-separated: web, scholar, social)",
    ),
    language: str = Query("en-US", description="Language"),
    incognito: bool = Query(False, description="Use incognito mode"),
    collection_uuid: Optional[str] = Query(None, description="Collection UUID to search within"),
    frontend_uuid: Optional[str] = Query(None, description="Frontend UUID"),
    frontend_context_uuid: Optional[str] = Query(None, description="Frontend Context UUID (Thread ID)"),
    priority: str = Query("normal", description="Request priority (low, normal, high, urgent)"),
):
    """Submit a query to the queue and return immediately with request ID."""
    global async_queue_manager
    
    try:
        # Initialize queue manager if needed
        if async_queue_manager is None:
            async_queue_manager = await get_queue_manager(cookie_manager)
        
        # Prepare query parameters
        sources_list = [s.strip() for s in sources.split(",")]
        follow_up = (
            {"backend_uuid": backend_uuid, "attachments": []} if backend_uuid else None
        )
        
        query_params = {
            "query": q,
            "mode": mode,
            "model": model,
            "sources": sources_list,
            "files": {},
            "stream": False,
            "language": language,
            "follow_up": follow_up,
            "incognito": incognito,
            "collection_uuid": collection_uuid,
            "frontend_uuid": frontend_uuid,
            "frontend_context_uuid": frontend_context_uuid,
        }
        
        # If no account specified, queue manager will select one
        if not account_name:
            accounts = cookie_manager.get_all_accounts()
            if not accounts:
                raise Exception("No accounts available")
            account_name = list(accounts.keys())[0]
        
        # Submit to queue
        from lib.queue_manager import RequestPriority
        priority_map = {
            "low": RequestPriority.LOW,
            "normal": RequestPriority.NORMAL,
            "high": RequestPriority.HIGH,
            "urgent": RequestPriority.URGENT
        }
        priority_obj = priority_map.get(priority.lower(), RequestPriority.NORMAL)
        
        request_id = await async_queue_manager.submit_request(
            account_name=account_name,
            query_params=query_params,
            priority=priority_obj
        )
        
        return {
            "status": "submitted",
            "message": "Query submitted to queue. Poll /api/queue/result/{request_id} for results.",
            "request_id": request_id,
            "priority": priority,
            "account_name": account_name,
            "result_url": f"/api/queue/result/{request_id}"
        }
        
    except Exception as e:
        return handle_api_error(e, account_name or "unknown")


@app.get("/api/threads")
async def get_threads(
    account_name: str = Query(..., description="Account name to use"),
    limit: int = 20, 
    offset: int = 0, 
    search_term: str = ""
):
    """Fetch a list of threads from Perplexity AI."""
    try:
        # Get the specific account client
        client = await get_perplexity_client(account_name)
        
        threads = await client.get_threads(
            limit=limit, offset=offset, search_term=search_term
        )
        
        # Mark account as used
        await cookie_manager.mark_account_used(account_name)
        
        return create_api_response(threads, account_name)
    except Exception as e:
        return handle_api_error(e, account_name)


@app.get("/api/threads/{slug}")
async def get_thread(
    slug: str,
    account_name: str = Query(..., description="Account name to use")
):
    """Fetch a specific thread by slug."""
    try:
        # Get the specific account client
        client = await get_perplexity_client(account_name)
        
        thread = await client.get_thread_details_by_slug(slug)
        
        # Mark account as used
        await cookie_manager.mark_account_used(account_name)
        
        return create_api_response(thread, account_name)
    except Exception as e:
        return handle_api_error(e, account_name)


@app.delete("/api/threads/{thread_uuid}")
async def delete_thread(
    thread_uuid: str,
    account_name: str = Query(..., description="Account name to use")
):
    """Delete a thread by UUID."""
    try:
        # Get the specific account client
        client = await get_perplexity_client(account_name)
        
        result = await client.delete_thread(thread_uuid)
        
        # Mark account as used
        await cookie_manager.mark_account_used(account_name)
        
        return create_api_response(result, account_name)
    except Exception as e:
        return handle_api_error(e, account_name)


@app.delete("/api/threads/clear_all")
async def clear_all_threads(account_name: str = Query(..., description="Account name to use")):
    """Clear all threads for an account."""
    try:
        # Get the specific account client
        client = await get_perplexity_client(account_name)
        
        result = await client.delete_all_threads()
        
        # Mark account as used
        await cookie_manager.mark_account_used(account_name)
        
        return create_api_response(result, account_name)
    except Exception as e:
        return handle_api_error(e, account_name)


@app.get("/api/collections")
async def list_collections(
    account_name: str = Query(..., description="Account name to use"),
    limit: int = 20, 
    offset: int = 0
):
    """List collections for account"""
    try:
        client = await get_perplexity_client(account_name)
        collections = await client.list_collections(limit=limit, offset=offset)
        await cookie_manager.mark_account_used(account_name)
        return create_api_response(collections, account_name)
    except Exception as e:
        return handle_api_error(e, account_name)


@app.get("/api/collections/{collection_slug}")
async def get_collection_details(
    collection_slug: str, 
    account_name: str = Query(..., description="Account name to use")
):
    """Get collection details"""
    try:
        client = await get_perplexity_client(account_name)
        details = await client.get_collection(collection_slug=collection_slug)
        await cookie_manager.mark_account_used(account_name)
        return create_api_response(details, account_name)
    except Exception as e:
        return handle_api_error(e, account_name)


@app.get("/api/collections/{collection_slug}/threads")
async def get_collection_threads(
    collection_slug: str, 
    account_name: str = Query(..., description="Account name to use"),
    limit: int = 20, 
    offset: int = 0
):
    """Get threads from collection"""
    try:
        client = await get_perplexity_client(account_name)
        threads = await client.list_collection_threads(collection_slug, limit=limit, offset=offset)
        await cookie_manager.mark_account_used(account_name)
        return create_api_response(threads, account_name)
    except Exception as e:
        return handle_api_error(e, account_name)


@app.post("/api/query_with_file")
async def query_with_file(
    account_name: str = Form(..., description="Account name to use"),
    query: str = Form(..., description="Query to ask about the uploaded file"),
    file: UploadFile = File(..., description="PDF or other file to analyze"),
    model: Optional[str] = Form(None, description="Model to use (default: gemini-3-flash for files)"),
    mode: str = Form("auto", description="Search mode"),
):
    """Query Perplexity AI with a file upload."""
    try:
        # Default to gemini-3-flash for file uploads if no model specified
        if not model:
            model = "gemini-3-flash"

        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required"
            )

        # Read file content
        file_content = await file.read()

        # Sanitize filename to prevent regex errors in mimetypes.guess_type()
        import re
        safe_filename = re.sub(r'[^\w\-. ]', '_', file.filename)

        # Prepare files dictionary for Perplexity client
        files_dict = {safe_filename: file_content}

        # Get the specific account client
        client = await get_perplexity_client(account_name)

        # Execute search with file
        result = await client.search(
            query,
            mode=mode,
            model=model,
            sources=["web"],
            files=files_dict,
            stream=False,
            language="en-US",
            follow_up=None,
            incognito=False,
            collection_uuid=None,
            frontend_uuid=None,
            frontend_context_uuid=None,
        )

        file_name = f"API-FILE-{account_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{file.filename}"
        save_resp(result, file_name)

        # Mark account as used
        await cookie_manager.mark_account_used(account_name)

        return create_api_response(result, account_name)
    except Exception as e:
        return handle_api_error(e, account_name)


# Account Management Endpoints
@app.get("/")
async def dashboard(request: Request):
    """Main dashboard for account management."""
    accounts = cookie_manager.get_all_accounts()
    
    if templates is None:
        return JSONResponse(content={
            "message": "Template loading failed, using JSON response",
            "accounts": accounts,
            "html_available": False,
            "api_endpoints": {
                "account_list": "/api/account/list",
                "add_account": "/api/account/add",
                "test_account": "/api/account/test/{account_name}",
                "chat_list": "/chats",
                "api_docs": "/docs",
                "health": "/health"
            }
        })
    
    return templates.TemplateResponse("dashboard.html", {"request": request, "accounts": accounts})


@app.get("/chats")
async def chat_list_page(request: Request):
    """Chat list page with delete functionality."""
    if templates is None:
        return JSONResponse(content={
            "message": "Template loading failed, using JSON response",
            "html_available": False
        })
    
    return templates.TemplateResponse("chat_list.html", {"request": request})

# Simple API info endpoint 
@app.get("/info")
async def api_info():
    """API information endpoint."""
    return JSONResponse(content={
        "name": "Perplexity Multi-Account API",
        "status": "running",
        "endpoints": {
            "dashboard": "/",
            "api_docs": "/docs",
            "health": "/health",
            "account_list": "/api/account/list",
            "query_async": "/api/query_async",
            "query_sync": "/api/query_sync"
        }
    })


@app.post("/api/account/add")
async def add_account(
    account_name: str = Form(...),
    cookie_data: str = Form(...),
    display_name: str = Form("")
):
    """Add a new account from Chrome extension cookie data."""
    try:
        chrome_cookies = json.loads(cookie_data)
        account = await cookie_manager.add_account(account_name, chrome_cookies, display_name or account_name)
        return JSONResponse(content={"status": "success", "message": f"Account '{account_name}' added successfully", "account": account})
    except json.JSONDecodeError:
        return JSONResponse(content={"status": "error", "message": "Invalid JSON in cookie data"}, status_code=400)
    except ValueError as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Failed to add account: {str(e)}"}, status_code=500)


@app.post("/api/account/update/{account_name}")
async def update_account(
    account_name: str,
    cookie_data: str = Form(...),
    display_name: str = Form("")
):
    """Update an existing account with new cookies."""
    try:
        chrome_cookies = json.loads(cookie_data)
        account = await cookie_manager.update_account(account_name, chrome_cookies)
        if display_name:
            account['name'] = display_name
        return JSONResponse(content={"status": "success", "message": f"Account '{account_name}' updated successfully", "account": account})
    except json.JSONDecodeError:
        return JSONResponse(content={"status": "error", "message": "Invalid JSON in cookie data"}, status_code=400)
    except ValueError as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Failed to update account: {str(e)}"}, status_code=500)


@app.get("/api/account/list")
async def list_accounts():
    """List all accounts (without cookies)."""
    accounts = cookie_manager.get_all_accounts()
    return JSONResponse(content={"status": "success", "accounts": accounts})


@app.post("/api/account/test/{account_name}")
async def test_account(account_name: str):
    """Test if an account's cookies are valid."""
    try:
        client = await get_perplexity_client(account_name)
        # Simple test - try to get threads (this validates the session)
        threads = await client.get_threads(limit=1, offset=0, search_term="")
        await cookie_manager.mark_account_validated(account_name, True)
        return JSONResponse(content={"status": "success", "message": f"Account '{account_name}' is valid", "valid": True})
    except Exception as e:
        await cookie_manager.mark_account_validated(account_name, False)
        return JSONResponse(content={"status": "error", "message": f"Account '{account_name}' is invalid: {str(e)}", "valid": False})


@app.delete("/api/account/{account_name}")
async def delete_account(account_name: str):
    """Delete an account."""
    try:
        deleted = await cookie_manager.delete_account(account_name)
        if deleted:
            return JSONResponse(content={"status": "success", "message": f"Account '{account_name}' deleted successfully"})
        else:
            return JSONResponse(content={"status": "error", "message": f"Account '{account_name}' not found"}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Failed to delete account: {str(e)}"}, status_code=500)


# Thread Management Endpoints
@app.get("/api/threads/manage/list")
async def list_threads_manage(
    account_name: str = Query(..., description="Account name to use"),
    limit: int = 50
):
    """List threads for management purposes."""
    try:
        client = await get_perplexity_client(account_name)
        result = await client.get_threads(limit=limit, offset=0, search_term="")
        await cookie_manager.mark_account_used(account_name)

        threads = result.get('threads', [])
        return JSONResponse(content={
            "status": "success",
            "account_name": account_name,
            "total": len(threads),
            "threads": threads
        })
    except Exception as e:
        return JSONResponse(content={"status": "error", "error": str(e)}, status_code=500)


@app.delete("/api/threads/manage/delete-old")
async def delete_old_threads(
    account_name: str = Query(..., description="Account name to use"),
    keep_count: int = Query(10, description="Number of recent threads to keep")
):
    """Delete old threads, keeping the most recent N threads."""
    try:
        client = await get_perplexity_client(account_name)

        result = await client.get_threads(limit=1000, offset=0)
        threads = result.get('threads', [])

        if len(threads) <= keep_count:
            await cookie_manager.mark_account_used(account_name)
            return JSONResponse(content={
                "status": "success",
                "message": f"Only {len(threads)} threads found. Keeping all.",
                "deleted": 0,
                "remaining": len(threads)
            })

        # Delete older threads (keep the most recent)
        threads_to_delete = threads[keep_count:]

        deleted = 0
        failed = 0
        failed_threads = []

        for thread in threads_to_delete:
            thread_uuid = thread.get('uuid') or thread.get('id')
            if not thread_uuid:
                continue

            try:
                await client.delete_thread(thread_uuid)
                deleted += 1
            except Exception as e:
                failed += 1
                failed_threads.append({
                    "title": thread.get('title', 'Untitled'),
                    "uuid": thread_uuid,
                    "error": str(e)
                })

        await cookie_manager.mark_account_used(account_name)

        return JSONResponse(content={
            "status": "success",
            "message": f"Deleted {deleted} old threads, kept {keep_count} most recent",
            "deleted": deleted,
            "failed": failed,
            "remaining": keep_count,
            "failed_threads": failed_threads[:10]  # Only return first 10 failures
        })
    except Exception as e:
        return JSONResponse(content={"status": "error", "error": str(e)}, status_code=500)


@app.get("/api/threads/manage/check-quota")
async def check_upload_quota(
    account_name: str = Query(..., description="Account name to use")
):
    """Check if the account can upload files (quota status)."""
    try:
        client = await get_perplexity_client(account_name)

        # Try to get upload URL for a small test file
        import mimetypes
        test_file_info = await client.session.post(
            "https://www.perplexity.ai/rest/uploads/create_upload_url?version=2.18&source=default",
            json={
                "content_type": "application/pdf",
                "file_size": 1000,
                "filename": "test.pdf",
                "force_image": False,
                "source": "default",
            },
        )

        info = test_file_info.json()
        await cookie_manager.mark_account_used(account_name)

        if info.get("rate_limited"):
            return JSONResponse(content={
                "status": "rate_limited",
                "message": "File upload rate limit reached",
                "account_name": account_name,
                "quota_available": False,
                "details": info
            })
        else:
            return JSONResponse(content={
                "status": "success",
                "message": "Upload quota available",
                "account_name": account_name,
                "quota_available": True,
                "s3_bucket_url": info.get('s3_bucket_url'),
                "file_uuid": info.get('file_uuid')
            })
    except Exception as e:
        return JSONResponse(content={"status": "error", "error": str(e)}, status_code=500)
