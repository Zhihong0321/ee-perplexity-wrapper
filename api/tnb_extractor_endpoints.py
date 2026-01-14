#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TNB Bill Extractor API - FastAPI Endpoints

Provides REST API endpoints for extracting TNB bill information
from PDF files using FastAPI (compatible with main app).
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import json
from typing import Optional

# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.tnb_extractor import extract_tnb_bill

# Create router
router = APIRouter(prefix="/api", tags=["TNB Extractor"])


@router.post("/extract-tnb")
async def extract_tnb_bill_endpoint(
    file: UploadFile = File(...),
    account_name: str = Form(default="yamal"),
    model: str = Form(default="gemini-3-flash")
):
    """
    TNB Bill Extraction API Endpoint

    Uploads PDF and extracts TNB bill information.

    **Request Parameters:**
      - file: PDF file (required)
      - account_name: Account name (optional, default: yamal)
      - model: Model name (optional, default: gemini-3-flash)

    **Response:**
      - HTTP 302 redirect to: /api/extract-tnb?customer_name=xxx&address=xxx&tnb-account=xxx&bill-date=xxx
      - JSON body with extracted data

    **Example Request:**
      curl -X POST "http://localhost:5000/api/extract-tnb" \
        -F "file=@TNB1.pdf" \
        -F "account_name=yamal" \
        -F "model=gemini-3-flash"
    """

    # Check file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only PDF files are supported."
        )

    # Read file content
    file_content = await file.read()

    # Sanitize filename to prevent regex errors in mimetypes.guess_type()
    import re
    safe_filename = re.sub(r'[^\w\-. ]', '_', file.filename)

    # Extract TNB bill information
    result = await extract_tnb_bill(safe_filename, file_content, account_name, model)

    if not result['success']:
        # Extraction failed
        return JSONResponse(
            status_code=500,
            content={
                'status': 'error',
                'error': result.get('error', 'Extraction failed'),
                'response_time': result.get('response_time', 0)
            }
        )

    # Build redirect URL with query parameters
    redirect_url = f"/api/extract-tnb?customer_name={result.get('customer_name', '')}&address={result.get('address', '')}&tnb-account={result.get('tnb_account', '')}&bill-date={result.get('bill_date', '')}"

    # Return both redirect and JSON
    response_content = {
        'status': 'success',
        'data': {
            'customer_name': result.get('customer_name'),
            'address': result.get('address'),
            'tnb_account': result.get('tnb_account'),
            'bill_date': result.get('bill_date'),
            'response_time': result.get('response_time')
        },
        'redirect_url': redirect_url
    }

    return JSONResponse(
        status_code=200,
        content=response_content,
        headers={'Location': redirect_url}
    )


@router.get("/extract-tnb")
async def get_extraction_results(
    customer_name: Optional[str] = None,
    address: Optional[str] = None,
    tnb_account: Optional[str] = None,
    bill_date: Optional[str] = None
):
    """
    TNB Extraction Results Endpoint

    Returns extraction results (accessed via redirect URL).

    **Query Parameters:**
      - customer_name: Extracted customer name
      - address: Extracted address
      - tnb-account: Extracted TNB account number
      - bill-date: Extracted bill date

    **Example Request:**
      curl "http://localhost:5000/api/extract-tnb?customer_name=Mak%20Kian%20Keong&address=...&tnb-account=220012905808&bill-date=25.06.2025"
    """

    # Check if this is a result redirect (has query parameters)
    if customer_name or address or tnb_account or bill_date:
        # This is a result redirect, return data in JSON format
        return {
            'status': 'success',
            'data': {
                'customer_name': customer_name,
                'address': address,
                'tnb_account': tnb_account,
                'bill_date': bill_date
            }
        }

    # No query params: Return API documentation
    return {
        'name': 'TNB Bill Extractor API',
        'version': '1.0.0',
        'description': 'Extract TNB electricity bill information and return as query parameters',
        'endpoints': {
            'POST /api/extract-tnb': {
                'description': 'Extract TNB bill from uploaded PDF',
                'parameters': {
                    'file (form-data)': 'PDF file (required)',
                    'account_name (form-data)': 'Account name (optional, default: yamal)',
                    'model (form-data)': 'Model name (optional, default: gemini-3-flash)'
                },
                'response': {
                    'status': 'HTTP 200 with JSON',
                    'headers': {'Location': '/api/extract-tnb?customer_name=xxx&address=xxx&tnb-account=xxx&bill-date=xxx'},
                    'body': 'JSON with extracted data'
                },
                'example': {
                    'command': 'curl -X POST "http://localhost:5000/api/extract-tnb" -F "file=@TNB1.pdf"',
                    'response': '200 OK + JSON'
                }
            },
            'GET /api/extract-tnb': {
                'description': 'API documentation (default) or extraction results (with query params)',
                'parameters': {
                    'customer_name': 'Extracted customer name',
                    'address': 'Extracted address',
                    'tnb-account': 'Extracted TNB account number',
                    'bill-date': 'Extracted bill date'
                },
                'response': 'JSON with extracted data'
            }
        },
        'usage_examples': [
            {
                'title': 'Basic Extraction',
                'curl': 'curl -X POST "http://localhost:5000/api/extract-tnb" -F "file=@TNB1.pdf"',
                'python': '''
import requests

with open('TNB1.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/extract-tnb',
        files={'file': f}
    )

# Access results
result = response.json()
print(result['data']['customer_name'])
                '''
            },
            {
                'title': 'Custom Account and Model',
                'curl': 'curl -X POST "http://localhost:5000/api/extract-tnb" -F "file=@TNB1.pdf" -F "account_name=test_user" -F "model=gemini-3-pro"',
                'python': '''
import requests

files = {'file': open('TNB1.pdf', 'rb')}
data = {
    'account_name': 'test_user',
    'model': 'gemini-3-pro'
}

response = requests.post(
    'http://localhost:5000/api/extract-tnb',
    files=files,
    data=data
)

result = response.json()
print(result['data'])
                '''
            }
        ]
    }


@router.get("/tnb-health")
async def tnb_health_check():
    """TNB Extractor health check endpoint."""
    return {
        'status': 'healthy',
        'service': 'tnb-extractor-api',
        'version': '1.0.0'
    }
