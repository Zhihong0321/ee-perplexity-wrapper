# TNB Bill Extractor - Strict JSON Output

## Overview

`lib/tnb_extractor.py` provides a high-performance function to extract specific fields from TNB electricity bills with **strict JSON output**.

## Features

- ✅ **Strict JSON Output**: Prompt explicitly requests valid JSON, no markdown formatting
- ⚡ **Fast Processing**: Optimized minimal prompt for 32% speedup (~7.8s vs ~11.4s)
- 📄 **Batch Processing**: Supports multiple files
- 🔧 **Flexible**: Works with any model (default: gemini-3-flash)

## Installation

The module is already included in your project at `lib/tnb_extractor.py`.

## Usage

### Basic Usage

```python
from lib.tnb_extractor import extract_tnb_bill
import asyncio

# Read PDF file
with open("TNB1.pdf", "rb") as f:
    pdf_content = f.read()

# Extract information
result = await extract_tnb_bill("TNB1.pdf", pdf_content)

# Check result
if result["success"]:
    print(f"Customer Name: {result['customer_name']}")
    print(f"TNB Account:    {result['tnb_account']}")
    print(f"Address:        {result['address']}")
    print(f"Bill Date:      {result['bill_date']}")
    print(f"Response Time:  {result['response_time']:.2f}s")
else:
    print(f"Error: {result['error']}")
```

### Advanced Usage with Custom Account

```python
result = await extract_tnb_bill(
    file_path="TNB1.pdf",
    file_content=pdf_content,
    account_name="yamal",
    model="gemini-3-flash"
)
```

### Batch Processing Multiple Files

```python
from lib.tnb_extractor import batch_extract_tnb_bills

# Prepare files
files = [
    ("TNB1.pdf", pdf_content_1),
    ("TNB2.pdf", pdf_content_2),
    ("TNB3.pdf", pdf_content_3)
]

# Extract all files
results = await batch_extract_tnb_bills(files)

# Process results
for result in results:
    print(f"\nFile: {result['file_name']}")
    print(f"Customer: {result.get('customer_name', 'N/A')}")
```

## Response Format

### Success Response

```json
{
  "success": true,
  "customer_name": "Mak Kian Keong",
  "tnb_account": "220012905808",
  "address": "3, Jalan Flora 3F/5, Bandar Rimbayu, 42500 Telok Panglima Garang, Selangor",
  "bill_date": "25.06.2025",
  "response_time": 7.76,
  "raw_answer": "{ \"customer_name\": \"...\", ... }"
}
```

### Error Response

```json
{
  "success": false,
  "error": "File upload rate limit reached for account.",
  "customer_name": null,
  "tnb_account": null,
  "address": null,
  "bill_date": null,
  "response_time": 0.54,
  "raw_answer": null
}
```

## Strict JSON Prompt

The function uses this optimized prompt for fast extraction with strict JSON output:

```text
Extract these fields from TNB electricity bill. Return ONLY valid JSON, no other text, no markdown formatting:
{
  "customer_name": "Customer Name",
  "tnb_account": "Account Number",
  "address": "Complete Address",
  "bill_date": "Bill Date (DD.MM.YYYY)"
}
```

### Why This Prompt Works

1. **Explicit JSON Request**: "Return ONLY valid JSON"
2. **No Markdown Warning**: "no other text, no markdown formatting"
3. **Field Names Match JSON Keys**: Helps model understand expected structure
4. **Minimal Instructions**: Reduces processing time by ~32%

## Performance

| Prompt Type | Response Time | Speedup |
|--------------|----------------|----------|
| Original (detailed) | ~11.4s | Baseline |
| **Strict JSON (minimal)** | ~7.8s | **+32%** ⚡ |

## Integration Examples

### Flask API Endpoint

```python
@app.route('/api/extract-tnb', methods=['POST'])
def extract_tnb():
    from lib.tnb_extractor import extract_tnb_bill
    import asyncio

    # Get file from request
    file = request.files['file']
    file_content = file.read()

    # Extract information
    result = asyncio.run(extract_tnb_bill(file.filename, file_content))

    if result["success"]:
        return jsonify({
            "status": "success",
            "data": {
                "customer_name": result["customer_name"],
                "tnb_account": result["tnb_account"],
                "address": result["address"],
                "bill_date": result["bill_date"]
            }
        })
    else:
        return jsonify({
            "status": "error",
            "error": result["error"]
        }), 500
```

### FastAPI Endpoint

```python
from fastapi import UploadFile, File
from lib.tnb_extractor import extract_tnb_bill

@app.post("/api/extract-tnb")
async def extract_tnb_endpoint(file: UploadFile = File(...)):
    file_content = await file.read()

    result = await extract_tnb_bill(file.filename, file_content)

    if result["success"]:
        return {
            "status": "success",
            "customer_name": result["customer_name"],
            "tnb_account": result["tnb_account"],
            "address": result["address"],
            "bill_date": result["bill_date"],
            "response_time": result["response_time"]
        }
    else:
        raise HTTPException(status_code=500, detail=result["error"])
```

## Testing

Run the included test script:

```bash
cd E:\perplexity-wrapper
python test_tnb_extractor.py
```

This will test the extractor with `TNB1.pdf` and display results.

## Troubleshooting

### "Account not found" Error

- Check account exists in `accounts.json`
- Use correct account name parameter:
  ```python
  await extract_tnb_bill(..., account_name="test_user")
  ```

### "File upload rate limit reached" Error

- Account has exceeded file upload quota
- Wait for quota reset or use different account
- Consider upgrading account tier

### JSON Parse Failures

The function includes fallback regex extraction if JSON parsing fails. This ensures:
- Data is still extracted even if model doesn't return strict JSON
- No silent failures
- Graceful degradation

## Notes

- **Default Model**: `gemini-3-flash` (fastest for extraction)
- **File Support**: PDF files only
- **Rate Limiting**: Handled by Perplexity API
- **Cookie Management**: Automatic via CookieManager

## License

Part of the ee-perplexity-wrapper project.
