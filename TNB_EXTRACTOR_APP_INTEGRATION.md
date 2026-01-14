# TNB Bill Extractor API - App Homepage Integration

## ✅ Integration Complete

TNB Bill Extractor API documentation has been successfully added to the app homepage at `http://localhost:5000` (or your production URL).

---

## 🌐 What's New on Homepage?

When you visit the Perplexity Account Manager homepage, you'll now see a **TNB Bill Extractor API** section at the top of the page:

### Section Features:

1. **🎨 Highlighted Card**: Blue gradient background with "New Feature" badge
2. **📄 Feature List**: Shows key features (file upload, JSON output, query parameters, ~7.8s response)
3. **🔗 Endpoint Display**: Shows `POST /api/extract-tnb`
4. **📋 Extracted Fields**: Lists all 4 fields (customer_name, tnb_account, address, bill_date)
5. **🚀 Quick Start (curl)**: Ready-to-use curl command
6. **🐍 Python Example**: Complete Python code example
7. **🔗 Action Buttons**:
   - "Try API" - Opens API endpoint in new tab
   - "Full Documentation" - Links to FastAPI docs

---

## 📍 Location in Dashboard

The TNB Extractor section appears **immediately after the header** and **before all other cards**:

```
┌─────────────────────────────────────────────────────────────┐
│ Perplexity Account Manager                            │
│ Manage multiple Perplexity accounts for API usage     │
├─────────────────────────────────────────────────────────────┤
│ [Manage Chats]                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ⚡ TNB Bill Extractor API        [New Feature]      │
│ Extract TNB electricity bill information from PDF files   │
│ with strict JSON output and query parameters.            │
│                                                      │
│ ┌─────┬──────┬──────────┐                       │
│ │📄   │🔗   │📋        │                       │
│ │Features│Endpoint│Fields    │                       │
│ │       │       │          │                       │
│ │- File │POST   │customer   │                       │
│ │  upload│/api/  │_name    │                       │
│ │       │extract │tnb_     │                       │
│ │- JSON │-tnb   │_account  │                       │
│ │  output│       │          │                       │
│ │- Query│       │address   │                       │
│ │  params│       │          │                       │
│ │- ~7.8s│       │bill_date │                       │
│ └─────┴──────┴──────────┘                       │
│                                                      │
│ 🚀 Quick Start (curl)                             │
│ ┌────────────────────────────────────────────────────┐   │
│ │ curl -X POST "http://localhost:5000/... │   │
│ │   -F "file=@TNB1.pdf" \                      │   │
│ │   -F "account_name=yamal"                    │   │
│ └────────────────────────────────────────────────────┘   │
│                                                      │
│ 🐍 Python Example                                  │
│ ┌────────────────────────────────────────────────────┐   │
│ │ import requests                                 │   │
│ │ with open('TNB1.pdf', 'rb') as f:            │   │
│ │   response = requests.post(...)                 │   │
│ └────────────────────────────────────────────────────┘   │
│                                                      │
│ [Try API]      [Full Documentation]                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔗 Quick Access to Documentation

### Option 1: Dashboard Homepage

1. **Visit**: `http://localhost:5000` (or your production URL)
2. **Scroll**: TNB Extractor section is at the top
3. **Click**: "Full Documentation" button

### Option 2: Direct API Docs

1. **Visit**: `http://localhost:5000/docs`
2. **Find**: "TNB Extractor" section in the sidebar
3. **Expand**: `POST /api/extract-tnb` endpoint

### Option 3: Direct API Endpoint

1. **Try API**: Opens `http://localhost:5000/api/extract-tnb`
2. **View Docs**: Returns API documentation JSON

---

## 📋 API Documentation Structure

When you click "Full Documentation" or visit `/docs`, you'll see:

### Endpoint Documentation:

```json
{
  "name": "TNB Bill Extractor API",
  "version": "1.0.0",
  "endpoints": {
    "POST /api/extract-tnb": {
      "description": "Upload PDF and extract TNB bill information",
      "parameters": { ... },
      "response": { ... },
      "example": { ... }
    },
    "GET /api/extract-tnb": {
      "description": "API documentation (default) or extraction results",
      "parameters": { ... }
    }
  },
  "extracted_fields": {
    "customer_name": "Customer's full name",
    "tnb_account": "12-digit TNB account number",
    "address": "Complete billing address",
    "bill_date": "Bill date in DD.MM.YYYY format"
  },
  "usage_examples": [ ... ],
  "response_format": { ... }
}
```

---

## 🚀 Using the API from Dashboard

### Step 1: Copy curl Command

From the "Quick Start (curl)" section:
```bash
curl -X POST "http://localhost:5000/api/extract-tnb" \
  -F "file=@TNB1.pdf" \
  -F "account_name=yamal"
```

### Step 2: Copy Python Code

From the "Python Example" section:
```python
import requests

with open('TNB1.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/extract-tnb',
        files={'file': f},
        data={'account_name': 'yamal', 'model': 'gemini-3-flash'}
    )

# Get JSON response
result = response.json()
print(f"Customer Name: {result['data']['customer_name']}")
print(f"TNB Account: {result['data']['tnb_account']}")
```

### Step 3: Click "Try API"

Opens the API endpoint in a new tab where you can:
- Upload PDF file
- View API documentation
- Test extraction

---

## 📱 Responsive Design

The TNB Extractor section is fully responsive:

- **Desktop** (lg: 3 columns): Features, Endpoint, Fields side by side
- **Tablet** (md: 2 columns): Stacked layout
- **Mobile** (sm: 1 column): Single column, fully accessible

---

## 🎨 Visual Highlights

- **Gradient Background**: Blue to indigo gradient for visibility
- **New Feature Badge**: Highlights recent addition
- **Icon Usage**: ⚡ 📄 🔗 📋 🚀 🐍 for visual clarity
- **Code Blocks**: Dark background with green syntax highlighting
- **Action Buttons**: Primary (blue) and secondary (gray) for clear hierarchy

---

## 🔗 Links in Dashboard

| Button | Action | Target |
|---------|---------|----------|
| **Try API** | Opens extraction endpoint | `/api/extract-tnb` (new tab) |
| **Full Documentation** | Opens API docs | `/docs#tnb--extractor` (new tab) |
| **Manage Chats** (header) | Opens chat manager | `/chats` |

---

## 📊 Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER                                              │
│ Perplexity Account Manager                            │
│ [Manage Chats]                                       │
├─────────────────────────────────────────────────────────────┤
│ TNB BILL EXTRACTOR API (NEW!) ⭐                      │
│ - Feature overview                                     │
│ - Quick start examples                                  │
│ - Action buttons                                      │
├─────────────────────────────────────────────────────────────┤
│ ADD NEW ACCOUNT FORM                                   │
│ - Account name input                                   │
│ - Cookie data textarea                                 │
├─────────────────────────────────────────────────────────────┤
│ EXISTING ACCOUNTS LIST                               │
│ - Account cards with status                             │
├─────────────────────────────────────────────────────────────┤
│ QUEUE MANAGEMENT                                     │
│ - Queue status                                      │
│ - Behavior settings                                   │
├─────────────────────────────────────────────────────────────┤
│ API USAGE                                            │
│ - Query examples                                     │
│ - Available accounts                                 │
├─────────────────────────────────────────────────────────────┤
│ SERVER STATUS                                        │
│ - API status                                        │
│ - Account count                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Getting Started Checklist

- [ ] Visit dashboard: `http://localhost:5000`
- [ ] Scroll to TNB Extractor section (top of page)
- [ ] Review curl example
- [ ] Copy Python example
- [ ] Click "Try API" to test
- [ ] Click "Full Documentation" for complete docs
- [ ] Upload a TNB PDF file
- [ ] View extracted results

---

## 🔍 Finding Documentation on Homepage

1. **Look for**: Blue gradient card at the top
2. **Read title**: "⚡ TNB Bill Extractor API"
3. **Locate buttons**: "Try API" and "Full Documentation"
4. **Click**: "Full Documentation" for complete API reference

---

## 📞 Support

If documentation doesn't appear on homepage:

1. **Check file**: `api/templates/dashboard.html` exists
2. **Restart server**: Stop and start FastAPI app
3. **Clear cache**: Refresh browser (Ctrl+F5)
4. **Check logs**: Look for `[OK] TNB Bill Extractor endpoints loaded`

---

## ✅ Summary

**Dashboard Integration**: ✅ Complete

**Files Modified**:
- `api/templates/dashboard.html` - Added TNB Extractor section
- `api/main.py` - Added `/tnb-api-docs` endpoint
- `api/tnb_extractor_endpoints.py` - FastAPI router

**New Features**:
- Visible TNB Extractor section on homepage
- Quick start examples (curl & Python)
- Direct links to API documentation
- Responsive design for all devices

**Access Points**:
- Homepage: `http://localhost:5000/` (dashboard)
- API Docs: `http://localhost:5000/docs`
- TNB Endpoint: `http://localhost:5000/api/extract-tnb`
- API Info: `http://localhost:5000/api/extract-tnb` (GET)

---

The TNB Bill Extractor API is now **fully integrated** into your app homepage with complete documentation and examples! 🎉
