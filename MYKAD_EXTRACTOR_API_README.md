# MYKAD & Namecard Extractor API - REST API Endpoint

## Overview

FastAPI-based REST API for extracting personal information from MYKAD cards or customer namecards.

**Extracted Fields:**
- Name
- MYKAD ID (format: XXXXXX-XX-XXXX)
- Address
- Contact Number

**Supported File Types:**
- Images: JPG, JPEG, PNG
- Documents: PDF

---

## 📦 Installation

The API is already included in your project at `api/mykad_extractor_api.py`.

### Start API Server

```bash
cd E:\perplexity-wrapper
python api/mykad_extractor_api.py
```

Server will start on: `http://localhost:5001`

**Note:** If you're using the main FastAPI app, the endpoints are already included at `http://localhost:8000/api/extract-mykad`

---

## 🌐 API Endpoints

### 1. POST /api/extract-mykad

**Purpose**: Upload image/PDF and extract MYKAD/namecard information

**Method**: `POST`

**Content-Type**: `multipart/form-data`

**Request Parameters**:

| Parameter | Type | Required | Description | Default |
|-----------|---------|------------|-------------|
| file | File | Yes | Image or PDF file | - |
| account_name | String | No | Account name from cookies.json | yamal |
| model | String | No | Model to use | gemini-3-flash |

**Request Example**:

```bash
curl -X POST "http://localhost:5001/api/extract-mykad" \
  -F "file=@mykad_front.jpg" \
  -F "account_name=yamal" \
  -F "model=gemini-3-flash"
```

```python
import requests

with open('mykad_front.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5001/api/extract-mykad',
        files={'file': f},
        data={'account_name': 'yamal', 'model': 'gemini-3-flash'}
    )
```

**Response**:

| Field | Type | Description |
|--------|---------|-------------|
| status | String | "success" or "error" |
| data | Object | Extracted MYKAD/namecard information |
| data.name | String | Full name |
| data.mykad_id | String | MYKAD identification number |
| data.address | String | Complete address |
| data.contact_number | String | Phone number |
| data.response_time | Float | Extraction time in seconds |

**Success Response Example**:
```json
{
  "status": "success",
  "data": {
    "name": "Ahmad bin Ali",
    "mykad_id": "123456-01-1234",
    "address": "No. 123, Jalan Merdeka, 50000 Kuala Lumpur",
    "contact_number": "012-3456789",
    "response_time": 7.76
  }
}
```

---

### 2. GET /api/extract-mykad

**Purpose**: Get API documentation

**Method**: `GET`

**Response**: Complete API documentation in JSON format

**Request Example**:
```bash
curl "http://localhost:5001/api/extract-mykad"
```

---

### 3. GET /health

**Purpose**: Health check endpoint

**Method**: `GET`

**Response**:
```json
{
  "status": "healthy",
  "service": "mykad-extractor-api"
}
```

---

## 📋 Extracted Data Fields

| Field Name | JSON Key | Example Value | Description |
|------------|-----------|---------------|-------------|
| Full Name | `name` | "Ahmad bin Ali" | Person's full name |
| MYKAD ID | `mykad_id` | "123456-01-1234" | 12-digit MYKAD identification number |
| Address | `address` | "No. 123, Jalan Merdeka, 50000 Kuala Lumpur" | Complete address |
| Contact Number | `contact_number` | "012-3456789" | Phone number |

---

## 🧪 Testing

Run included test script:

```bash
cd E:\perplexity-wrapper
python test_mykad_api.py
```

Or test the extractor module directly:

```bash
python test_mykad_extractor.py
```

---

## 🔍 Complete Usage Examples

### Example 1: MYKAD Card Extraction

```bash
curl -X POST "http://localhost:5001/api/extract-mykad" \
  -F "file=@mykad_front.jpg"
```

```python
import requests

with open('mykad_front.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5001/api/extract-mykad',
        files={'file': f}
    )

result = response.json()
print(f"Name: {result['data']['name']}")
print(f"MYKAD ID: {result['data']['mykad_id']}")
```

### Example 2: Namecard Extraction

```bash
curl -X POST "http://localhost:5001/api/extract-mykad" \
  -F "file=@namecard.jpg" \
  -F "account_name=test_user"
```

### Example 3: Custom Account and Model

```bash
curl -X POST "http://localhost:5001/api/extract-mykad" \
  -F "file=@mykad.jpg" \
  -F "account_name=test_user" \
  -F "model=gemini-3-pro"
```

### Example 4: Batch Processing Multiple Files

```python
import requests
import os

api_url = "http://localhost:5001/api/extract-mykad"
image_files = ["mykad_front.jpg", "mykad_back.jpg", "namecard.jpg"]

results = []

for image_file in image_files:
    with open(image_file, 'rb') as f:
        response = requests.post(
            api_url,
            files={'file': f}
        )
        result = response.json()
        result['file'] = image_file
        results.append(result)

# Print all results
for r in results:
    if r['status'] == 'success':
        print(f"\n{r['file']}:")
        print(f"  Name: {r['data']['name']}")
        print(f"  MYKAD ID: {r['data']['mykad_id']}")
```

---

## 📥 Response Codes

| Code | Meaning |
|-------|---------|
| 200 | Success (GET requests) |
| 200 | Success (POST requests - extraction successful) |
| 400 | Bad Request (missing file or invalid format) |
| 500 | Server Error (extraction failed or rate limit) |

**Error Response Example**:
```json
{
  "status": "error",
  "error": "Invalid file format. Only images (JPG, PNG) and PDF files are supported."
}
```

---

## 🔒 Security Features

- **Filename Sanitization**: Uses `secure_filename()` to prevent directory traversal
- **File Extension Validation**: Only accepts `.jpg`, `.jpeg`, `.png`, `.pdf` files
- **Input Validation**: Checks for file presence and valid format

---

## 📊 Performance

| Metric | Value |
|---------|--------|
| **Average Response Time** | ~7.8 seconds |
| **Model** | gemini-3-flash (default) |
| **File Size Support** | Up to 10 MB images/PDF |
| **Rate Limiting** | Handled by Perplexity API |

---

## 🌐 Production Deployment

### Start Server in Background

```bash
# Windows
start /B python api/mykad_extractor_api.py

# Linux/Mac
nohup python api/mykad_extractor_api.py > api.log 2>&1 &
```

### Railway Deployment

Update `Procfile`:
```
web: python api/mykad_extractor_api.py
```

API will be accessible at: `https://your-app.railway.app/api/extract-mykad`

---

## 🐛 Troubleshooting

### "No file uploaded" Error

**Cause**: Request missing `file` field

**Solution**:
```bash
# Wrong:
curl -X POST "http://localhost:5001/api/extract-mykad"

# Right:
curl -X POST "http://localhost:5001/api/extract-mykad" -F "file=@mykad.jpg"
```

### "Invalid file format" Error

**Cause**: Uploaded file is not supported

**Solution**:
- Use JPG, JPEG, PNG, or PDF files
- Ensure file has correct extension

### "File upload rate limit reached" Error

**Cause**: Account exceeded file upload quota

**Solution**:
1. Wait for quota reset
2. Use different account: `-F "account_name=test_user"`
3. Consider upgrading account tier

---

## 📝 Notes

- **Default Port**: 5001 (configurable in `app.run()`)
- **Host**: 0.0.0.0 (all interfaces)
- **Debug Mode**: Enabled by default for development
- **Thread Deletion**: Threads are automatically deleted after successful extraction

---

## 📚 Related Files

- `api/mykad_extractor_api.py` - Main Flask API
- `api/mykad_extractor_endpoints.py` - FastAPI router (integrated in main app)
- `lib/mykad_extractor.py` - Extraction logic
- `test_mykad_api.py` - API test script
- `test_mykad_extractor.py` - Module test script

---

## 📜 License

Part of ee-perplexity-wrapper project.
