# Perplexity AI Wrapper API

A powerful, unofficial Python wrapper and API for Perplexity AI. This project provides a FastAPI-based server that enables programmatic access to Perplexity's search capabilities, featuring multi-account support, persistent conversations, intelligent request queuing, and access to Perplexity Spaces (Collections).

## 🚀 Features

### Core Features
*   **Full Perplexity AI Access**: Query using various modes (auto, pro, reasoning, deep research) and models (GPT-4o, GPT-4.5, Claude 3.7 Sonnet, Gemini 2.0 Flash, Grok-2, o3-mini, R1, etc.).
*   **Multi-Account Management**: Seamlessly manage and rotate between multiple Perplexity accounts with persistent cookie storage.
*   **Persistent Conversations**:
    *   Maintain visual threads in your Perplexity history using `frontend_context_uuid`.
    *   Continue logical conversation context using `backend_uuid`.
*   **Streaming Support**: Real-time server-sent events (SSE) for token-by-token responses.
*   **Perplexity Collections (Spaces)**: List, access, and query within your Collections with full threading support.
*   **Source Filtering**: Restrict searches to Web, Scholar, or Social sources.

### Advanced Queue System
*   **Human-Like Behavior Simulation**: Configurable delays, peak hours detection, weekend patterns, burst behavior, and idle periods.
*   **Priority-Based Queuing**: Four priority levels (LOW, NORMAL, HIGH, URGENT) with intelligent processing.
*   **Automatic Account Rotation**: Load balancing and intelligent account selection based on usage patterns.
*   **Concurrent Request Management**: Configurable limits per account with semaphore-based control.
*   **Real-Time Monitoring**: Queue statistics, request tracking, and performance metrics.

### Developer Experience
*   **Web Dashboard**: Interactive HTML interface for account management and queue monitoring.
*   **RESTful API**: Comprehensive endpoints with OpenAPI documentation at `/docs`.
*   **Robust Error Handling**: Detailed error reporting with account context.
*   **Flexible Deployment**: Railway, Heroku, and self-hosted support with environment configuration.

## 🛠️ Installation

### Using pip (Recommended)

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/perplexity-wrapper.git
    cd perplexity-wrapper
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the server**:
    ```bash
    python run_server.py
    ```

### Using uv (Faster)

```bash
uv pip install -r requirements.txt
python run_server.py
```

### Access the API
*   **Dashboard**: `http://localhost:8000/`
*   **API Documentation**: `http://localhost:8000/docs`
*   **Health Check**: `http://localhost:8000/health`

## 📖 API Usage

### Document Extractor APIs

#### TNB Bill Extractor
Extract TNB electricity bill information from PDF files.

**Endpoint**: `POST /api/extract-tnb`

**Parameters**:
*   `file`: PDF file (required)
*   `account_name`: Account to use (optional, default: first available)
*   `model`: Model to use (optional, default: gemini-3-flash)

**Response**:
```json
{
  "status": "success",
  "data": {
    "customer_name": "Mak Kian Keong",
    "address": "3, Jalan Flora 3F/5, Bandar Rimbayu, 42500 Telok Panglima Garang, Selangor",
    "tnb_account": "220012905808",
    "bill_date": "25.06.2025"
  }
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/extract-tnb" \
  -F "file=@TNB1.pdf" \
  -F "account_name=my_account"
```

**Python Example**:
```python
import requests

with open('TNB1.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/extract-tnb',
        files={'file': f},
        data={'account_name': 'my_account'}
    )

result = response.json()
print(result['data'])
```

#### MYKAD & Namecard Extractor
Extract personal information from MYKAD cards or customer namecards.

**Endpoint**: `POST /api/extract-mykad`

**Parameters**:
*   `file`: Image (JPG, JPEG, PNG) or PDF file (required)
*   `account_name`: Account to use (optional, default: first available)
*   `model`: Model to use (optional, default: gemini-3-flash)

**Response**:
```json
{
  "status": "success",
  "data": {
    "name": "John Doe",
    "mykad_id": "123456-01-5678",
    "address": "123 Street Name, City, Postal Code",
    "contact_number": "+60 12-34567890"
  }
}
```

**Example**:
```bash
curl -X POST "http://localhost:8000/api/extract-mykad" \
  -F "file=@mykad_front.jpg" \
  -F "account_name=my_account"
```

**Health Check**: `GET /api/tnb-health` or `GET /api/mykad-health`

---

### 1. Authentication (Adding Accounts)

Extract cookies from a logged-in Perplexity session using a browser extension like [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/).

**Method**: `POST /api/account/add`

**Parameters**:
*   `account_name`: Unique identifier (e.g., "personal", "work")
*   `cookie_data`: Raw JSON cookie array from browser extension
*   `display_name`: (Optional) Friendly display name

**Example**:
```bash
curl -X POST "http://localhost:8000/api/account/add" \
  -F "account_name=my_account" \
  -F "cookie_data=@cookies.json" \
  -F "display_name=My Account"
```

### 2. Standard Search Queries

#### Synchronous Query (Wait for Complete Response)
**Endpoint**: `GET /api/query_sync`

**Key Parameters**:
*   `q`: Search query string
*   `account_name`: Account to use for the query
*   `mode`: Search mode (`auto`, `pro`, `reasoning`, `deep research`)
*   `model`: AI model (e.g., `gpt-4o`, `claude 3.7 sonnet`, `r1`, `o3-mini`)
*   `sources`: Comma-separated sources (`web`, `scholar`, `social`)
*   `frontend_context_uuid`: UUID for thread persistence (keeps queries in same conversation)
*   `backend_uuid`: Backend UUID from previous response (maintains conversation context)
*   `collection_uuid`: (Optional) Search within a specific Collection/Space

**Example**:
```bash
curl "http://localhost:8000/api/query_sync?q=What+is+quantum+computing&account_name=my_account&mode=pro&model=gpt-4o"
```

#### Asynchronous Query (Streaming Response)
**Endpoint**: `GET /api/query_async`

**Response**: Server-Sent Events (SSE) stream with token-by-token output

**Parameters**: Same as `query_sync`

**Example**:
```bash
curl -N "http://localhost:8000/api/query_async?q=Explain+AI&account_name=my_account&mode=auto"
```

### 3. Queue-Based Queries (Advanced)

Use the queue system for human-like behavior patterns and automatic rate limiting.

#### Queue Sync Query
**Endpoint**: `GET /api/query_queue_sync`

**Additional Parameters**:
*   `priority`: Request priority (`low`, `normal`, `high`, `urgent`)
*   `timeout`: Maximum wait time in seconds (default: 300)

**Example**:
```bash
curl "http://localhost:8000/api/query_queue_sync?q=Research+topic&priority=high&timeout=120"
```

#### Queue Async Query
**Endpoint**: `GET /api/query_queue_async`

**Returns**: Request ID for tracking

### 4. Thread Management

*   **List Recent Threads**: `GET /api/threads?account_name={account}`
*   **Get Thread Details**: `GET /api/threads/{slug}?account_name={account}`
*   **Delete Thread**: `DELETE /api/threads/{thread_uuid}?account_name={account}`

### 5. Collection Management (Spaces)

*   **List Collections**: `GET /api/collections?account_name={account}`
*   **Get Collection Details**: `GET /api/collections/{collection_slug}?account_name={account}`
*   **List Collection Threads**: `GET /api/collections/{collection_slug}/threads?account_name={account}`

### 6. Queue Management

*   **Queue Status**: `GET /api/queue/status`
*   **Start Queue**: `POST /api/queue/start`
*   **Stop Queue**: `POST /api/queue/stop`
*   **Get Behavior Settings**: `GET /api/queue/settings/behavior`
*   **Update Behavior Settings**: `POST /api/queue/settings/behavior`

**Example - Update Queue Settings**:
```bash
curl -X POST "http://localhost:8000/api/queue/settings/behavior" \
  -H "Content-Type: application/json" \
  -d '{
    "min_delay_seconds": 10.0,
    "max_delay_seconds": 30.0,
    "peak_hours_start": 9,
    "peak_hours_end": 17,
    "weekend_factor": 0.3,
    "burst_probability": 0.1,
    "burst_size": 3,
    "idle_probability": 0.05
  }'
```

## 🧩 Persistent Conversations

Maintain coherent multi-turn conversations using two UUID systems:

### UUID System
*   **`frontend_context_uuid`**: Visual thread ID - keeps all queries in the same conversation thread in Perplexity UI
*   **`backend_uuid`**: Logical context ID - maintains conversation memory between queries

### Example Flow

**1. Start a new conversation:**
```bash
# Generate a UUID for your thread (e.g., using uuidgen or online generator)
THREAD_ID="550e8400-e29b-41d4-a716-446655440000"

curl "http://localhost:8000/api/query_sync?q=What+is+Python&account_name=my_account&frontend_context_uuid=${THREAD_ID}" > response1.json

# Extract backend_uuid from response
BACKEND_UUID=$(jq -r '.backend_uuid' response1.json)
```

**2. Continue the conversation:**
```bash
curl "http://localhost:8000/api/query_sync?q=Show+me+an+example&account_name=my_account&frontend_context_uuid=${THREAD_ID}&backend_uuid=${BACKEND_UUID}" > response2.json
```

**3. Keep going:**
```bash
BACKEND_UUID=$(jq -r '.backend_uuid' response2.json)
curl "http://localhost:8000/api/query_sync?q=Explain+decorators&account_name=my_account&frontend_context_uuid=${THREAD_ID}&backend_uuid=${BACKEND_UUID}"
```

All queries will appear in a single thread in your Perplexity history, maintaining full conversation context.

## ⚙️ Configuration

### Environment Variables

*   **`STORAGE_ROOT`**: Custom storage path for accounts and logs
    *   Default: `/app/storage` (production) or local directory
    *   Example: `export STORAGE_ROOT=/path/to/storage`

*   **`PORT`**: Server port (default: 8000)
*   **`HOST`**: Server host (default: 0.0.0.0)

### Storage Locations

*   **Accounts**: `accounts.json` - Cookie storage with metadata
*   **Logs**: `logs/` directory - API response logs with timestamps
*   **Format**: `API-{account}-{timestamp}-{count}` or `API-QUEUE-{account}-{timestamp}`

### Queue Behavior Settings

Configure human-like timing patterns via API or directly in code:

```python
from lib.queue_manager import HumanBehaviorSettings

settings = HumanBehaviorSettings(
    min_delay_seconds=5.0,      # Minimum delay between requests
    max_delay_seconds=20.0,     # Maximum delay between requests
    peak_hours_start=9,          # Peak activity start (9 AM)
    peak_hours_end=17,           # Peak activity end (5 PM)
    weekend_factor=0.3,          # 30% activity on weekends
    burst_probability=0.1,       # 10% chance of burst behavior
    burst_size=3,                # Up to 3 requests in a burst
    idle_probability=0.05        # 5% chance of idle periods
)
```

### Deployment Configurations

**Railway**: Uses `railway.toml` with NIXPACKS builder
**Heroku**: Uses `Procfile` with Python 3.11+
**Docker**: Standard Python 3.11+ with `requirements.txt` or `uv.lock`

## 🏗️ Architecture

### Project Structure
```
perplexity-wrapper/
├── api/
│   ├── main.py              # FastAPI app with all core endpoints
│   ├── queue_endpoints.py   # Queue management endpoints
│   ├── config.py            # Storage configuration
│   ├── utils.py             # Response processing utilities
│   └── templates/           # HTML dashboard templates
├── lib/
│   ├── perplexity.py        # Perplexity AI client (async)
│   ├── cookie_manager.py    # Multi-account cookie management
│   └── queue_manager.py     # Human-like request queuing
├── run_server.py            # Server entry point
├── requirements.txt         # Pip dependencies
├── pyproject.toml           # Modern Python packaging
└── uv.lock                  # UV dependency lock file
```

### Key Components

**FastAPI Application** (`api/main.py`)
*   All HTTP endpoints with OpenAPI schema
*   CORS middleware for cross-origin requests
*   SSE streaming support for real-time responses
*   Template rendering for web dashboard

**Perplexity Client** (`lib/perplexity.py`)
*   Async HTTP client using `curl-cffi` for browser impersonation
*   Chrome 128 user agent spoofing
*   Full support for all Perplexity modes and models
*   File upload handling with S3 integration

**Cookie Manager** (`lib/cookie_manager.py`)
*   Chrome extension cookie format conversion
*   Persistent JSON storage with metadata
*   Account validation and usage tracking
*   Async file operations with `aiofiles`

**Queue Manager** (`lib/queue_manager.py`)
*   Priority-based asyncio queues (4 levels)
*   Human behavior simulation with configurable patterns
*   Account rotation with semaphore-based concurrency control
*   Request statistics and monitoring

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is provided as-is for educational and research purposes.

## ⚠️ Disclaimer

This is an **unofficial** API wrapper and is **not affiliated** with Perplexity AI. 

**Important Usage Notes**:
*   Use responsibly and in accordance with Perplexity's Terms of Service
*   Respect rate limits and avoid aggressive querying
*   The queue system helps mimic human behavior patterns
*   Account cookies are stored locally - ensure proper security
*   This tool is for personal/educational use; commercial use may violate ToS

## 🔗 Resources

*   **API Documentation**: Access `/docs` when server is running
*   **TNB Extractor**: See [TNB_FIX_SUMMARY.md](TNB_FIX_SUMMARY.md) for detailed fix information
*   **Queue Features**: See [QUEUE_FEATURES.md](QUEUE_FEATURES.md)
*   **Development Guide**: See [AGENTS.md](AGENTS.md)
*   **Collections Support**: See [add-custom-space.md](add-custom-space.md)
