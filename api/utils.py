import os
import json
from fastapi.responses import JSONResponse
from typing import Any, Dict

# Determine storage path
STORAGE_DIR = os.getenv("STORAGE_ROOT", "/app/storage")
if os.path.exists(STORAGE_DIR) and os.path.isdir(STORAGE_DIR):
    logs_dir = os.path.join(STORAGE_DIR, "logs")
else:
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../logs")

if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)


def extract_answer(res, file_name):
    """Extract answer from Perplexity API response."""
    backend_uuid = res.get("backend_uuid", None)
    blocks = res.get("blocks", [])
    if not isinstance(blocks, list):
        print(f"Unexpected blocks format in {file_name}: {blocks}")
        return {"answer": None, "backend_uuid": backend_uuid}

    for block in blocks:
        intended_usage = block.get("intended_usage", "")
        if not intended_usage == "ask_text":
            continue

        mardown_block = block.get("markdown_block", {})
        if not isinstance(mardown_block, dict):
            print(f"Unexpected markdown_block format in {file_name}: {mardown_block}")
            continue

        progress = mardown_block.get("progress")
        if progress == "IN_PROGRESS":
            chunks = mardown_block.get("chunks", [])
            if not isinstance(chunks, list):
                print(f"Unexpected chunks format in {file_name}: {chunks}")
                continue

            answer = "".join(chunks)
            return {
                "progress": progress,
                "answer": answer,
                "backend_uuid": backend_uuid,
            }

        if progress == "DONE":
            answer = mardown_block.get("answer")

            return {
                "progress": progress,
                "answer": answer,
                "backend_uuid": backend_uuid,
            }

        else:
            print(
                f"Unexpected progress state in {file_name}: {progress} for block {block}"
            )
            return {"answer": None, "backend_uuid": backend_uuid}

    return {"answer": None, "backend_uuid": backend_uuid}


def save_resp(res, file_name):
    """Save response to file for logging/debugging."""
    try:
        with open(os.path.join(logs_dir, file_name), "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
    except Exception:
        # Silently fail if we can't save
        pass

def create_api_response(content: Any, account_used: str = None, status_code: int = 200) -> JSONResponse:
    """
    Create a standardized JSON response.
    Wraps content in a consistent structure and handles errors.
    """
    response_content = content if isinstance(content, dict) else {"data": content}
    
    if account_used:
        response_content["account_used"] = account_used
        
    return JSONResponse(content=response_content, status_code=status_code)

def handle_api_error(e: Exception, account_used: str = None) -> JSONResponse:
    """Handle API errors consistently."""
    return JSONResponse(
        content={"error": str(e), "account_used": account_used},
        status_code=500
    )

