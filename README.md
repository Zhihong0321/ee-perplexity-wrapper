# Perplexity AI Wrapper API

A powerful, unofficial Python wrapper and API for Perplexity AI. This project provides a FastAPI-based server that enables programmatic access to Perplexity's search capabilities, including multi-account support, persistent conversations, and access to Perplexity Spaces (Collections).

## 🚀 Features

*   **Full Perplexity AI Access**: Query using various modes (Copilot/Pro, Reasoning, Writing, etc.) and models (GPT-4o, Claude 3, Sonar).
*   **Multi-Account Management**: seamless switching between multiple accounts with persistent cookie management.
*   **Persistent Conversations**:
    *   Maintain visual threads in your Perplexity history using `frontend_context_uuid`.
    *   Continue logical conversation context using `backend_uuid`.
*   **Streaming Support**: Real-time server-sent events (SSE) for token-by-token responses.
*   **Perplexity Spaces**: List and query within your Collections (Spaces).
*   **Robust Error Handling**: Automatic retries and detailed error reporting.
*   **Source Filtering**: Restrict searches to Web, Scholar, or Social sources.

## 🛠️ Installation

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
    The API will be available at `http://localhost:8000`.

## 📖 API Usage

### 1. Authentication (Adding Accounts)

You need to extract your cookies from a logged-in Perplexity session.
*   **Method**: `POST /api/account/add`
*   **Parameters**:
    *   `account_name`: A unique alias for this account (e.g., "personal", "work").
    *   `cookie_data`: The raw JSON cookie array (e.g., exported via a browser extension like "EditThisCookie").
    *   `display_name`: (Optional) A friendly name.

### 2. Search Queries

#### Synchronous (JSON Response)
*   **Endpoint**: `GET /api/query_sync`
*   **Parameters**:
    *   `q`: Your search query.
    *   `account_name`: The account alias to use.
    *   `mode`: Search mode (`auto`, `pro`, `reasoning`, etc.).
    *   `model`: Specific model (e.g., `gpt-4o`, `claude 3.7 sonnet`).
    *   `frontend_context_uuid`: (Optional) **Crucial for persistent threads**. Pass a stable UUID to keep this chat in one thread.
    *   `backend_uuid`: (Optional) Pass the `backend_uuid` from the *previous* response to continue the conversation context.

#### Asynchronous (Streaming)
*   **Endpoint**: `GET /api/query_async`
*   **Response**: Server-Sent Events (SSE) stream.
*   **Parameters**: Same as synchronous endpoint.

### 3. Managing Threads & Collections

*   **List Recent Threads**: `GET /api/threads`
*   **Get Specific Thread**: `GET /api/threads/{slug}`
*   **List Collections**: `GET /api/collections`
*   **Get Collection Threads**: `GET /api/collections/{collection_slug}/threads`

## 🧩 Persistent Conversations (How-To)

To create a chat experience like the official website:

1.  **Start a new thread**:
    *   Generate a random UUID (e.g., `my-thread-001`).
    *   Call `/api/query_sync?q=Hello&frontend_context_uuid=my-thread-001`.
    *   Save the `backend_uuid` from the response.

2.  **Continue the thread**:
    *   Call `/api/query_sync?q=FollowUp&frontend_context_uuid=my-thread-001&backend_uuid={PREVIOUS_BACKEND_UUID}`.
    *   The chat will visually appear in the same thread in your Perplexity history.

## ⚙️ Configuration

*   **Storage**: Cookies are stored in `accounts.json`.
*   **Environment Variables**:
    *   `STORAGE_ROOT`: Custom path for storing data/logs (default: `/app/storage` or local `logs/`).

## ⚠️ Disclaimer

This is an unofficial API wrapper and is not affiliated with Perplexity AI. Use it responsibly and in accordance with Perplexity's Terms of Service.
