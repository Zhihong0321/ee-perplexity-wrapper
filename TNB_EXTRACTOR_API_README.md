# TNB Bill Extractor API - REST API Endpoint

## Overview

Flask-based REST API for extracting TNB electricity bill information from PDF files.

**Key Feature**: Returns extracted data as **query parameters** in redirect URL:
```
/api/extract-tnb?customer_name=xxx&address=xxx&tnb-account=xxx&bill-date=xxx
```

---

## 📦 Installation

The API is already included in your project at `api/tnb_extractor_api.py`.

### Start API Server

```bash
cd E:\perplexity-wrapper
python api/tnb_extractor_api.py
```

Server will start on: `http://localhost:5000`

---

## 🌐 API Endpoints

### 1. POST /api/extract-tnb

**Purpose**: Upload PDF and extract TNB bill information

**Method**: `POST`

**Content-Type**: `multipart/form-data`

**Request Parameters**:

| Parameter | Type | Required | Description | Default |
|-----------|---------|------------|-------------|
| file | File | Yes | PDF file to extract from | - |
| account_name | String | No | Account name from cookies.json | yamal |
| model | String | No | Model to use | gemini-3-flash |

**Request Example**:

```bash
curl -X POST "http://localhost:5000/api/extract-tnb" \
  -F "file=@TNB1.pdf" \
  -F "account_name=yamal" \
  -F "model=gemini-3-flash"
```

```python
import requests

with open('TNB1.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/extract-tnb',
        files={'file': f},
        data={'account_name': 'yamal', 'model': 'gemini-3-flash'}
    )
```

**Response**:

| Field | Type | Description |
|--------|---------|-------------|
| status | String | "success" or "error" |
| data | Object | Extracted TNB bill information |
| redirect_url | String | Redirect URL with query parameters |
| response_time | Float | Extraction time in seconds |

**Success Response (JSON Body)**:
```json
{
  "status": "success",
  "data": {
    "customer_name": "Mak Kian Keong",
    "address": "3, Jalan Flora 3F/5, Bandar Rimbayu, 42500 Telok Panglima Garang, Selangor",
    "tnb_account": "220012905808",
    "bill_date": "25.06.2025",
    "response_time": 7.76
  },
  "redirect_url": "/api/extract-tnb?customer_name=Mak%20Kian%20Keong&address=...&tnb-account=220012905808&bill-date=25.06.2025"
}
```

**HTTP Response**:

| Header | Value |
|---------|--------|
| Status | 302 (Redirect) |
| Location | /api/extract-tnb?customer_name=xxx&address=xxx&tnb-account=xxx&bill-date=xxx |

---

### 2. GET /api/extract-tnb (Without Query Parameters)

**Purpose**: Get API documentation

**Method**: `GET`

**Response**: Complete API documentation in JSON format

**Request Example**:
```bash
curl "http://localhost:5000/api/extract-tnb"
```

**Response Example**:
```json
{
  "name": "TNB Bill Extractor API",
  "version": "1.0.0",
  "description": "Extract TNB electricity bill information and return as query parameters",
  "endpoints": {
    "POST /api/extract-tnb": { ... },
    "GET /api/extract-tnb": { ... }
  },
  "usage_examples": [ ... ]
}
```

---

### 3. GET /api/extract-tnb (With Query Parameters)

**Purpose**: Access extraction results via redirect URL

**Method**: `GET`

**Query Parameters**:

| Parameter | Type | Description |
|-----------|---------|-------------|
| customer_name | String | Extracted customer name |
| address | String | Extracted address |
| tnb-account | String | Extracted TNB account number |
| bill-date | String | Extracted bill date |

**Request Example**:
```bash
curl "http://localhost:5000/api/extract-tnb?customer_name=Mak%20Kian%20Keong&address=3%2C%20Jalan%20Flora...&tnb-account=220012905808&bill-date=25.06.2025"
```

**Response Example**:
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

---

### 4. GET /health

**Purpose**: Health check endpoint

**Method**: `GET`

**Response**:
```json
{
  "status": "healthy",
  "service": "tnb-extractor-api"
}
```

---

## 📋 Extracted Data Fields

| Field Name | JSON Key | Example Value | Description |
|------------|-----------|---------------|-------------|
| Customer Name | `customer_name` | "Mak Kian Keong" | Customer's full name |
| TNB Account | `tnb_account` | "220012905808" | 12-digit TNB account number |
| Address | `address` | "3, Jalan Flora 3F/5, Bandar Rimbayu, 42500 Telok Panglima Garang, Selangor" | Complete billing address |
| Bill Date | `bill_date` | "25.06.2025" | Bill date in DD.MM.YYYY format |

---

## 🔍 Complete Usage Examples

### Example 1: Basic Extraction (curl)

```bash
# Upload PDF and get redirect URL
curl -X POST "http://localhost:5000/api/extract-tnb" \
  -F "file=@TNB1.pdf" \
  -w "\nRedirect: %{redirect_url}\n"

# Output:
# Status: 302
# Redirect: /api/extract-tnb?customer_name=Mak%20Kian%20Keong&address=3%2C%20Jalan%20Flora...&tnb-account=220012905808&bill-date=25.06.2025
```

### Example 2: Basic Extraction (Python)

```python
import requests

# Upload PDF
with open('TNB1.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/extract-tnb',
        files={'file': f}
    )

# Get redirect URL
redirect_url = response.headers.get('Location')
print(f"Redirect URL: {redirect_url}")

# Get JSON data
result = response.json()
print(f"Customer: {result['data']['customer_name']}")
print(f"Account: {result['data']['tnb_account']}")
```

### Example 3: Custom Account and Model

```bash
curl -X POST "http://localhost:5000/api/extract-tnb" \
  -F "file=@TNB1.pdf" \
  -F "account_name=test_user" \
  -F "model=gemini-3-pro"
```

```python
response = requests.post(
    'http://localhost:5000/api/extract-tnb',
    files={'file': open('TNB1.pdf', 'rb')},
    data={
        'account_name': 'test_user',
        'model': 'gemini-3-pro'
    }
)
```

### Example 4: Access Results via Redirect URL

```python
import requests
from urllib.parse import urlparse, parse_qs

# Upload PDF
response = requests.post(
    'http://localhost:5000/api/extract-tnb',
    files={'file': open('TNB1.pdf', 'rb')},
    allow_redirects=False  # Don't follow redirect
)

# Get redirect URL
redirect_url = response.headers.get('Location')

# Parse query parameters
parsed = urlparse(redirect_url)
params = parse_qs(parsed.query)

# Access extracted data
customer_name = params.get('customer_name', [''])[0]
address = params.get('address', [''])[0]
tnb_account = params.get('tnb-account', [''])[0]
bill_date = params.get('bill-date', [''])[0]

print(f"Customer Name: {customer_name}")
print(f"TNB Account: {tnb_account}")
print(f"Address: {address}")
print(f"Bill Date: {bill_date}")
```

### Example 5: Batch Processing Multiple Files

```python
import requests
import os

api_url = "http://localhost:5000/api/extract-tnb"
pdf_files = ["TNB1.pdf", "TNB2.pdf", "TNB3.pdf"]

results = []

for pdf_file in pdf_files:
    with open(pdf_file, 'rb') as f:
        response = requests.post(
            api_url,
            files={'file': f}
        )
        result = response.json()
        result['file'] = pdf_file
        results.append(result)

# Print all results
for r in results:
    if r['status'] == 'success':
        print(f"\n{r['file']}:")
        print(f"  Customer: {r['data']['customer_name']}")
        print(f"  Account: {r['data']['tnb_account']}")
```

---

## 📥 Response Codes

| Code | Meaning |
|-------|---------|
| 200 | Success (GET requests) |
| 302 | Redirect (POST requests - extraction successful) |
| 400 | Bad Request (missing file or invalid format) |
| 500 | Server Error (extraction failed or rate limit) |

### Error Response Example

```json
{
  "status": "error",
  "error": "File upload rate limit reached for account.",
  "response_time": 0.54
}
```

---

## 🧪 Testing

Run included test script:

```bash
cd E:\perplexity-wrapper
python test_tnb_api.py
```

This will:
1. Show curl command example
2. Test API with Python requests
3. Demonstrate redirect URL parsing
4. Display API documentation

---

## 🔒 Security Features

- **Filename Sanitization**: Uses `secure_filename()` to prevent directory traversal
- **File Extension Validation**: Only accepts `.pdf` files
- **Input Validation**: Checks for file presence and valid format

---

## 📊 Performance

| Metric | Value |
|---------|--------|
| **Average Response Time** | ~7.8 seconds |
| **Model** | gemini-3-flash (default) |
| **File Size Support** | Up to 10 MB PDF |
| **Rate Limiting** | Handled by Perplexity API |

---

## 🌐 Production Deployment

### Start Server in Background

```bash
# Windows
start /B python api/tnb_extractor_api.py

# Linux/Mac
nohup python api/tnb_extractor_api.py > api.log 2>&1 &
```

### Railway Deployment

Update `Procfile`:
```
web: python api/tnb_extractor_api.py
```

API will be accessible at: `https://your-app.railway.app/api/extract-tnb`

---

## 🐛 Troubleshooting

### "No file uploaded" Error

**Cause**: Request missing `file` field

**Solution**:
```bash
# Wrong:
curl -X POST "http://localhost:5000/api/extract-tnb"

# Right:
curl -X POST "http://localhost:5000/api/extract-tnb" -F "file=@TNB1.pdf"
```

### "Invalid file format" Error

**Cause**: Uploaded file is not PDF

**Solution**: Ensure file has `.pdf` extension:
```bash
# Wrong:
curl -X POST "http://localhost:5000/api/extract-tnb" -F "file=@TNB1.txt"

# Right:
curl -X POST "http://localhost:5000/api/extract-tnb" -F "file=@TNB1.pdf"
```

### "File upload rate limit reached" Error

**Cause**: Account exceeded file upload quota

**Solution**:
1. Wait for quota reset
2. Use different account: `-F "account_name=test_user"`
3. Consider upgrading account tier

---

## 📝 Notes

- **Default Port**: 5000 (configurable in `app.run()`)
- **Host**: 0.0.0.0 (all interfaces)
- **Debug Mode**: Enabled by default for development
- **Query Parameters**: URL-encoded in redirect URL

---

## 📚 Related Files

- `api/tnb_extractor_api.py` - Main Flask API
- `test_tnb_api.py` - Test script
- `lib/tnb_extractor.py` - Extraction logic
- `TNB_EXTRACTOR_README.md` - Function documentation

---

## 📜 License

Part of ee-perplexity-wrapper project.
