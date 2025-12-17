# AGENTS.md

## Project Overview

This is a **Perplexity AI Multi-Account Wrapper API** - a Python-based FastAPI server that provides a programmatic interface to Perplexity AI's web interface. The project supports multiple accounts, persistent conversations, and access to Perplexity Spaces (Collections).

## Development Commands

### Running the Server
```bash
# Primary method
python run_server.py

# Alternative with environment setup
./start.sh
```

### Testing Imports
```bash
python test_imports.py
```

### Dependencies
- Primary: Uses `uv` for dependency management (`uv.lock` present)
- Legacy: `requirements.txt` for backward compatibility
- Config: `pyproject.toml` for modern Python packaging

### Environment Variables
- `PORT`: Server port (default: 8000)
- `HOST`: Server host (default: 0.0.0.0)
- `STORAGE_ROOT`: Custom path for storing data/logs (default: `/app/storage` or local `logs/`)

## Architecture

### Directory Structure
```
api/
├── main.py          # FastAPI app with all endpoints
├── config.py        # Configuration utilities
├── utils.py         # Response processing utilities
└── templates/
    └── dashboard.html  # Web dashboard

lib/
├── perplexity.py    # Core Perplexity AI client
└── cookie_manager.py # Multi-account cookie management
```

### Key Components

1. **FastAPI Application** (`api/main.py`):
   - All HTTP endpoints
   - CORS middleware
   - SSE streaming support
   - Template rendering for dashboard

2. **Perplexity Client** (`lib/perplexity.py`):
   - Async HTTP client using curl-cffi
   - Impersonates Chrome browser
   - Handles search queries and conversations

3. **Cookie Manager** (`lib/cookie_manager.py`):
   - Multi-account support
   - Chrome cookie format conversion
   - Persistent storage in `accounts.json`

## API Design Patterns

### Endpoint Structure
- Health check: `/health`
- Account management: `/api/account/*`
- Query endpoints: `/api/query_sync`, `/api/query_async`
- Queue-based queries: `/api/query_queue_sync`, `/api/query_queue_async`
- Queue management: `/api/queue/*` (status, settings, control)
- Thread management: `/api/threads/*`
- Collection management: `/api/collections/*`

### Response Format
All API responses follow this structure:
```python
{
    "status": "success|error",
    "data": {...},
    "account_used": "account_name"
}
```

### Streaming Support
- Uses Server-Sent Events (SSE)
- `generate_sse_stream()` handles real-time responses
- JSON-encoded events with `type` field (`content`, `error`)

### Queue Processing
- Priority-based request queuing with `RequestPriority` enum
- Human-like timing with configurable `HumanBehaviorSettings`
- Account rotation and load balancing via `asyncio.Semaphore`
- Burst behavior and idle period simulation
- Automatic retry logic for failed requests

### Authentication Pattern
- Chrome extension cookie format required
- Multi-account support via cookie_manager
- Account validation through thread fetching

## Database & Storage

### Cookie Storage
- File: `accounts.json`
- Format: JSON with metadata
- Async file operations using aiofiles

### Logging
- Responses saved with timestamp format: `API-{account}-{timestamp}-{count}`
- Storage location configurable via `STORAGE_ROOT`

## Key Gotchas & Implementation Details

### Model Validation
- When `mode="auto"` and specific `model` is provided, mode gets converted to `"pro"`
- This matches current Perplexity web behavior

### Persistent Conversations
- Two UUID system:
  - `frontend_context_uuid`: Maintains visual thread in Perplexity history
  - `backend_uuid`: Maintains logical conversation context
- Critical to pass both for continued conversations

### Account Management
- Chrome extension cookie format required for import
- Automatic cookie validation
- Account usage tracking for monitoring

### Queue Management (NEW)
- **Queue Manager**: `lib/queue_manager.py` handles request queuing with human-like timing
- **Priority System**: LOW, NORMAL, HIGH, URGENT priority levels
- **Human Behavior**: Configurable delays, peak hours, weekend activity, burst behavior
- **Account Selection**: Automatic account rotation with load balancing
- **New Endpoints**: `/api/query_queue_sync`, `/api/query_queue_async`, `/api/queue/*`
- **Rate Limiting**: Built-in semaphores prevent concurrent request overloads
- **Dashboard UI**: Web interface for queue monitoring and settings control

### Error Handling
- `handle_api_error()` in `api/utils.py` standardizes error responses
- Always includes account name in error context
- Graceful fallback when templates fail to load

### Async Patterns
- All Perplexity client operations are async
- Use `await client.init()` after client creation
- Proper session cleanup required
- Queue manager uses asyncio for concurrent request handling

## Deployment

### Railway
- Uses NIXPACKS builder
- Health check at `/health` with 60s timeout
- Python 3.11 specified in railway.toml

### Heroku
- Procfile specifies `python run_server.py`
- Web dyno configuration

## Code Conventions

### Style
- Python 3.11+ (per pyproject.toml)
- Type hints used throughout
- Async/await patterns for HTTP operations
- FastAPI dependency injection patterns

### Imports
- lib directory added to Python path dynamically
- Relative imports within api/ package
- Standard library imports first, third-party second

### Error Messages
- Always include account context
- User-friendly HTTP status codes
- Detailed error logging for debugging

## Testing Approach

- `test_imports.py` for dependency validation
- No formal test suite currently implemented
- Manual testing via dashboard at `/`
- Account validation endpoint at `/api/account/test/{account_name}`

## Security Considerations

- CORS currently allows all origins (restrict in production)
- Cookie storage in plain text JSON
- No rate limiting implemented
- SSL/TLS handled by deployment platform