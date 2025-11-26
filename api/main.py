from fastapi import FastAPI, Query, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
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
from api.utils import extract_answer, save_resp

# Initialize cookie manager
cookie_manager = CookieManager()

# Templates
try:
    templates = Jinja2Templates(directory="templates")
except Exception as e:
    print(f"Failed to load templates: {e}")
    templates = None

app = FastAPI(
    title="Perplexity Multi-Account API", description="Multi-account Perplexity AI API with cookie management"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "message": "Perplexity Multi-Account API is running"}


def get_perplexity_client(account_name: str) -> perplexity.Client:
    """Get a Perplexity client for the specified account."""
    try:
        cookies = cookie_manager.get_account_cookies(account_name)
        return perplexity.Client(cookies)
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
):
    """Generate SSE stream from Perplexity responses."""
    response_count = 0

    # Get the specific account client
    client = get_perplexity_client(account_name)
    
    # Start the streaming search in a sync function
    try:
        for stream in client.search(
            query,
            mode=mode,
            model=model,
            sources=sources,
            files={},
            stream=True,
            language=language,
            follow_up=follow_up,
            incognito=incognito,
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
    sources: str = Query("web", description="Sources (comma-separated)"),
    language: str = Query("en-US", description="Language"),
    incognito: bool = Query(False, description="Use incognito mode"),
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
    sources: str = Query("web", description="Sources (comma-separated)"),
    language: str = Query("en-US", description="Language"),
    incognito: bool = Query(False, description="Use incognito mode"),
):
    """Query Perplexity AI and return the full response as JSON (no streaming)."""
    sources_list = [s.strip() for s in sources.split(",")]
    follow_up = (
        {"backend_uuid": backend_uuid, "attachments": []} if backend_uuid else None
    )
    try:
        # Get the specific account client
        client = get_perplexity_client(account_name)
        
        result = client.search(
            q,
            mode=mode,
            model=model,
            sources=sources_list,
            files={},
            stream=False,
            language=language,
            follow_up=follow_up,
            incognito=incognito,
        )
        file_name = f"API-{account_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}-sync"
        save_resp(result, file_name)
        
        # Mark account as used
        await cookie_manager.mark_account_used(account_name)
        
        if answer_only:
            ans_data = extract_answer(result, file_name)
            ans_data["account_used"] = account_name
            return JSONResponse(content=ans_data)
        
        result["account_used"] = account_name
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e), "account_used": account_name}, status_code=500)


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
        client = get_perplexity_client(account_name)
        
        threads = client.get_threads(
            limit=limit, offset=offset, search_term=search_term
        )
        threads["account_used"] = account_name
        
        # Mark account as used
        await cookie_manager.mark_account_used(account_name)
        
        return JSONResponse(content=threads)
    except Exception as e:
        return JSONResponse(content={"error": str(e), "account_used": account_name}, status_code=500)


@app.get("/api/threads/{slug}")
async def get_thread(
    slug: str,
    account_name: str = Query(..., description="Account name to use")
):
    """Fetch a specific thread by slug."""
    try:
        # Get the specific account client
        client = get_perplexity_client(account_name)
        
        thread = client.get_thread_details_by_slug(slug)
        thread["account_used"] = account_name
        
        # Mark account as used
        await cookie_manager.mark_account_used(account_name)
        
        return JSONResponse(content=thread)
    except Exception as e:
        return JSONResponse(content={"error": str(e), "account_used": account_name}, status_code=500)


# Account Management Endpoints
@app.get("/")
async def dashboard(request: Request):
    """Main dashboard for account management."""
    accounts = cookie_manager.get_all_accounts()
    
    if templates is None:
        return JSONResponse(content({
            "message": "Template loading failed, using JSON response",
            "accounts": accounts,
            "html_available": False
        }))
    
    return templates.TemplateResponse("dashboard.html", {"request": request, "accounts": accounts})


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
        client = get_perplexity_client(account_name)
        # Simple test - try to get threads (this validates the session)
        threads = client.get_threads(limit=1, offset=0, search_term="")
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
