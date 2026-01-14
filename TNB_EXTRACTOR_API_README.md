# TNB Bill Extractor API

Extract TNB (Tenaga Nasional Berhad) electricity bill information from PDF files with minimal JSON output.

## Features

- **Minimal Payload**: ~250 bytes response
- **Strict JSON Parsing**: Consistent structure, no fallback parsing
- **Fast Response**: ~5-8 seconds extraction time
- **Auto Thread Deletion**: Cleans up Perplexity threads after extraction
- **Multi-Account Support**: Rotate between multiple accounts
- **Error Handling**: Graceful fallback with detailed error messages

## Quick Start

### Using curl

```bash
curl -X POST "http://localhost:8000/api/extract-tnb" \
  -F "file=@TNB1.pdf" \
  -F "account_name=my_account"
```

### Using Python

```python
import requests

with open('TNB1.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/extract-tnb',
        files={'file': f},
        data={'account_name': 'my_account'}
    )

result = response.json()

if result['status'] == 'success':
    data = result['data']
    print(f"Customer Name: {data['customer_name']}")
    print(f"TNB Account: {data['tnb_account']}")
    print(f"Address: {data['address']}")
    print(f"Bill Date: {data['bill_date']}")
    print(f"State: {data['state']}")
    print(f"Post Code: {data['post_code']}")
else:
    print(f"Error: {result.get('error')}")
```

### Using JavaScript/Fetch

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('account_name', 'my_account');

const response = await fetch('http://localhost:8000/api/extract-tnb', {
    method: 'POST',
    body: formData
});

const result = await response.json();
console.log(result.data);
```

## API Reference

### POST /api/extract-tnb

Extract TNB bill information from a PDF file.

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | TNB bill PDF file |
| `account_name` | String | No | Perplexity account to use (default: first available) |
| `model` | String | No | AI model (default: gemini-3-flash) |

**Success Response** (200 OK):

```json
{
  "status": "success",
  "data": {
    "customer_name": "Mak Kian Keong",
    "address": "3, Jalan Flora 3F/5, Bandar Rimbayu, 42500 Telok Panglima Garang, Selangor",
    "tnb_account": "220012905808",
    "bill_date": "25.06.2025",
    "state": "Selangor",
    "post_code": "42500"
  }
}
```

**Error Response** (500):

```json
{
  "status": "error",
  "error": "Extraction failed: File upload rate limit reached"
}
```

**Error Response** (400):

```json
{
  "detail": "Invalid file format. Only PDF files are supported."
}
```

### GET /api/extract-tnb

Retrieve extraction results (when called with query parameters) or API documentation (default).

**Query Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `customer_name` | String | Extracted customer name |
| `address` | String | Extracted address |
| `tnb_account` | String | Extracted TNB account number |
| `bill_date` | String | Extracted bill date |
| `state` | String | Extracted state/region |
| `post_code` | String | Extracted postal code |

**Response with Parameters**:

```json
{
  "status": "success",
  "data": {
    "customer_name": "Mak Kian Keong",
    "address": "3, Jalan Flora 3F/5, Bandar Rimbayu, 42500 Telok Panglima Garang, Selangor",
    "tnb_account": "220012905808",
    "bill_date": "25.06.2025",
    "state": "Selangor",
    "post_code": "42500"
  }
}
```

**Response without Parameters**: Returns API documentation (JSON format with endpoint details)

### GET /api/tnb-health

Health check endpoint for TNB extractor.

**Response**:

```json
{
  "status": "healthy",
  "service": "tnb-extractor-api",
  "version": "1.0.0"
}
```

## Extracted Fields

| Field | Description | Example |
|-------|-------------|---------|
| `customer_name` | Customer name from bill | "Mak Kian Keong" |
| `tnb_account` | TNB account number | "220012905808" |
| `address` | Complete address from bill | "3, Jalan Flora 3F/5, Bandar Rimbayu, 42500 Telok Panglima Garang, Selangor" |
| `bill_date` | Bill date in DD.MM.YYYY format | "25.06.2025" |
| `state` | State/region extracted from address | "Selangor" |
| `post_code` | Postal/ZIP code extracted from address | "42500" |

## Error Handling

### Common Errors

**1. Invalid File Format**
- Status: 400
- Message: "Invalid file format. Only PDF files are supported."
- Solution: Ensure you're uploading a PDF file

**2. Account Not Found**
- Status: 500
- Message: "Account not found: Account 'xxx' not found"
- Solution: Check account name in `/api/account/list`

**3. File Upload Rate Limit**
- Status: 500
- Message: "File upload rate limit reached for account"
- Solution: Wait a few minutes and try again, or use a different account

**4. Extraction Failed**
- Status: 500
- Message: "Extraction failed: [error details]"
- Solution: Check if PDF is a valid TNB bill, ensure it's not corrupted

## Implementation Details

### How It Works

1. **File Upload**: PDF is uploaded to Perplexity AI
2. **Extraction**: AI extracts 6 specific fields using strict JSON prompt
3. **Parsing**: JSON is cleaned (markdown removal) and parsed
4. **Response**: Minimal JSON response (~250 bytes) is returned
5. **Cleanup**: Perplexity thread is automatically deleted

### Prompt Engineering

The system uses an optimized prompt for strict JSON output:

```
Extract only these 6 fields from TNB electricity bill. Return ONLY raw JSON with no markdown formatting, no code blocks, no explanations:

{"customer_name":"","tnb_account":"","address":"","bill_date":"","state":"","post_code":""}

Rules:
- Return ONLY the JSON object above with values filled in
- No markdown, no code blocks (```json), no introductory or concluding text
- If a field is not found, return empty string "" for that field
- bill_date format: DD.MM.YYYY
- state: Extract the state/region from the address (e.g., "Selangor")
- post_code: Extract the postal/ZIP code from the address (e.g., "42500")
```

### JSON Parsing

The parsing logic:
1. Remove markdown code blocks (```json, ```)
2. Extract JSON object from response
3. Parse JSON using Python's `json.loads()`
4. Validate and extract required fields
5. Return None for any missing fields

No regex fallback - ensures consistent structure.

### Auto Thread Deletion

After successful extraction, Perplexity thread is automatically deleted to:
- Clean up conversation history
- Prevent accumulation of test threads
- Maintain account hygiene

## Performance

| Metric | Value |
|---------|-------|
| Response Time | 5-8 seconds |
| Payload Size | ~250 bytes |
| Success Rate | ~95% (with clear TNB bills) |
| Concurrent Requests | Limited by Perplexity rate limits |

## Migration from v1.0

### Breaking Changes

If you were using old version:

**Removed**:
- `raw_answer` field (was 50-100KB+)
- `redirect_url` field
- `Location` header
- `response_time` from API response
- 302 redirect behavior

**No Action Needed**:
If you only use `result['data']` for the 6 extracted fields, your code will work without changes.

**Migration Example**:

```python
# OLD (v1.0)
result = response.json()
customer_name = result['data']['customer_name']

# NEW (v2.0) - Same usage!
result = response.json()
customer_name = result['data']['customer_name']

# NEW FIELDS - Also available:
state = result['data']['state']
post_code = result['data']['post_code']
```

Only remove any code that references:
- `result['data']['response_time']`
- `result['data']['raw_answer']`
- `result['redirect_url']`
- `response.headers['Location']`

## Troubleshooting

### Q: Why is extraction failing?
- Check that PDF is a valid TNB bill
- Ensure account cookies are valid (test via dashboard)
- Verify Perplexity is not rate-limited
- Check server logs for detailed errors

### Q: Why are some fields null?
- The AI couldn't find that field in the bill
- Try with a clearer/better quality PDF
- The field might be missing from that specific bill format

### Q: How can I improve accuracy?
- Use high-resolution PDF scans
- Ensure the bill is not rotated
- Use the latest model (`gemini-3-flash` or `gemini-3-pro`)
- Test multiple accounts if one consistently fails

### Q: What's the difference between address, state, and post_code?
- `address`: Complete address as shown on the bill
- `state`: Only the state/region extracted from the address
- `post_code`: Only the postal/ZIP code extracted from the address

### Q: Can I extract additional fields?
- Currently, only 6 fields are supported
- To add more fields, modify the prompt in `lib/tnb_extractor.py`
- Update the response structure accordingly

## Related Documentation

- [AGENTS.md](AGENTS.md) - Development guide
- [README.md](README.md) - Main project documentation
