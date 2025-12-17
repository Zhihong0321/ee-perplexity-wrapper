# Adding Perplexity Spaces (Collections) Support

## Overview

Current wrapper does NOT support Perplexity Spaces/Custom instructions. After HAR analysis, discovered this is **LOW-MEDIUM complexity** (3/10) to implement.

## Key Findings

### Perplexity Uses "Collections" Not "Spaces"
- Perplexity's implementation uses "Collections" as the backend term
- Spaces in UI = Collections in API
- Same authentication and endpoints as regular queries

### Collection API Endpoints Discovered
```
GET /rest/collections/list_recent?version=2.18&source=default
GET /rest/collections/get_collection?collection_slug=news-rewriter-a4gprUwXSkWsZ9s7AXwr5g&version=2.18&source=default
GET /rest/collections/list_collection_threads?collection_slug=news-rewriter-a4gprUwXSkWsZ9s7AXwr5g&limit=20&filter_by_user=false&filter_by_shared_threads=true&offset=0&version=2.18&source=default
GET /rest/collections/list_collection_articles?collection_slug=a4gprUwXSkWsZ9s7AXwr5g&limit=20&offset=0&version=2.18&source=default
GET /rest/collections/list_user_collections?limit=30&offset=0&version=2.18&source=default
```

### Space Query Structure
The actual query uses the same `/rest/sse/perplexity_ask` endpoint but adds:
```json
{
  "params": {
    "target_collection_uuid": "6b8829ad-4c17-4a45-ac67-db3b017c2be6",
    "query_source": "collection",
    "mode": "copilot",
    "model_preference": "pplx_pro"
  },
  "query_str": "news about malaysia pm's aide corruption"
}
```

## Required Implementation Changes

### 1. Library Changes (`lib/perplexity.py`)

#### New Methods Needed
```python
def list_collections(self, limit=30, offset=0):
    """Get list of user's collections"""
    # Note: list_user_collections is deprecated/empty. Use list_recent.
    url = "https://www.perplexity.ai/rest/collections/list_recent"
    params = {"version": "2.18", "source": "default"}
    resp = self.session.get(url, params=params)
    # ... processing logic needed to map response ...
    return {"data": mapped_collections}

def get_collection(self, collection_slug=None, collection_uuid=None):
    """Get collection details by slug or UUID"""
    if collection_slug:
        url = f"https://www.perplexity.ai/rest/collections/get_collection?collection_slug={collection_slug}&version=2.18&source=default"
    elif collection_uuid:
        # May need reverse-lookup or different endpoint for UUID
        pass
    resp = self.session.get(url)
    return resp.json()

def list_collection_threads(self, collection_slug, limit=20, offset=0, filter_by_user=True, filter_by_shared_threads=False):
    """Get threads from specific collection"""
    url = f"https://www.perplexity.ai/rest/collections/list_collection_threads"
    params = {
        "collection_slug": collection_slug,
        "limit": limit,
        "offset": offset,
        "filter_by_user": filter_by_user,
        "filter_by_shared_threads": filter_by_shared_threads,
        "version": "2.18",
        "source": "default"
    }
    resp = self.session.post(url, json=params)
    return resp.json()
```

#### Modify Existing search() Method
```python
def search(self, query, collection_uuid=None, **kwargs):
    # ... existing validation code ...
    
    # Add collection context if provided
    json_data = {
        "query_str": query,
        "params": {
            # ... existing params ...
            "target_collection_uuid": collection_uuid,
            "query_source": "collection" if collection_uuid else "default"
            # ... rest of params ...
        }
    }
    
    # Same endpoint: "https://www.perplexity.ai/rest/sse/perplexity_ask"
    resp = self.session.post("https://www.perplexity.ai/rest/sse/perplexity_ask", json=json_data, stream=True)
    # ... existing response handling ...
```

### 2. API Changes (`api/main.py`)

#### New Endpoints
```python
@app.get("/api/collections")
async def list_collections(account_name: str, limit=20, offset=0):
    """List collections for account"""
    
@app.get("/api/collections/{collection_slug}")
async def get_collection_details(collection_slug: str, account_name: str):
    """Get collection details"""

@app.get("/api/collections/{collection_slug}/threads")
async def get_collection_threads(collection_slug: str, account_name: str, limit=20, offset=0):
    """Get threads from collection"""
```

#### Update Query Endpoints
Add `collection_uuid` parameter to:
- `/api/query_async`
- `/api/query_sync`

### 3. Frontend Updates

#### Dashboard UI Changes
- Add collection selector to query interface
- Show available collections per account
- Display collection context in results

## Implementation Complexity: LOW-MEDIUM (3/10)

### Why It's Simple:
- Same authentication/cookies work
- Same SSE endpoint `/rest/sse/perplexity_ask`
- Just add `target_collection_uuid` to payload
- Collection endpoints are simple REST APIs
- No special handling required

### Estimated Development Time:
- **Core functionality**: 1-2 hours
- **API endpoints**: 30 minutes
- **Frontend integration**: 1-2 hours
- **Testing**: 1 hour

**Total: 4-6 hours** (vs original estimate of 2 days)

## Update Log

### [2025-11-27] Fix for Collection Listing
- **Issue**: `list_user_collections` endpoint returned empty results.
- **Fix**: Switched to `list_recent` endpoint which returns the correct list of collections.
- **Implementation Details**: Added response mapping to convert the `list_recent` format (which provides `title`, `link`, `emoji`) into a standardized format with `slug` and `uuid`.

### [2025-12-05] Revert to list_user_collections
- **Issue**: `list_recent` only returned recently used collections (incomplete list).
- **Fix**: Switched back to `list_user_collections` endpoint which provides the full list of user collections including UUIDs.
- **Implementation Details**: Simplified mapping logic as `list_user_collections` returns full details directly.

## Next Steps for Implementation

1. **Add collection management methods** to `lib/perplexity.py`
2. **Modify search() method** to accept `collection_uuid`
3. **Add collection endpoints** to `api/main.py`
4. **Test with existing collections** using HAR-derived parameters
5. **Update frontend** for collection selection

## Key Advantages
- Minimal code changes required
- Leverages existing authentication and streaming logic
- Same error handling and response processing
- Backwards compatible (collection_uuid is optional)

## Testing Strategy
1. Test collection listing with authenticated cookies
2. Verify collection details retrieval
3. Test search within collection using UUID from HAR
4. Validate streaming responses work same as regular queries

This implementation will enable the wrapper to support Perplexity Spaces through their Collections API with minimal complexity.
