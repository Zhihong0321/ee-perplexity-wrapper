#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MYKAD & Namecard Extractor API - FastAPI Endpoints

Provides REST API endpoints for extracting MYKAD or namecard information
from image/PDF files using FastAPI (compatible with main app).
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

from lib.mykad_extractor import extract_mykad_info

# Create router
router = APIRouter(prefix="/api", tags=["MYKAD Extractor"])


@router.post("/extract-mykad")
async def extract_mykad_endpoint(
    file: UploadFile = File(...),
    account_name: str = Form(default="yamal"),
    model: str = Form(default="gemini-3-flash")
):
    """
    MYKAD/Namecard Extraction API Endpoint

    Uploads image/PDF and extracts personal information.

    **Request Parameters:**
      - file: Image or PDF file (required)
      - account_name: Account name (optional, default: yamal)
      - model: Model name (optional, default: gemini-3-flash)

    **Response:**
      - HTTP 200 with JSON containing extracted data

    **Example Request:**
      curl -X POST "http://localhost:5000/api/extract-mykad" \
        -F "file=@mykad.jpg" \
        -F "account_name=yamal" \
        -F "model=gemini-3-flash"
    """

    # Check file type (accept images and PDFs)
    allowed_extensions = ('.jpg', '.jpeg', '.png', '.pdf')
    if not file.filename or not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only images (JPG, PNG) and PDF files are supported."
        )

    # Read file content
    file_content = await file.read()

    # Sanitize filename to prevent regex errors in mimetypes.guess_type()
    import re
    safe_filename = re.sub(r'[^\w\-. ]', '_', file.filename)

    # Extract MYKAD/namecard information
    result = await extract_mykad_info(safe_filename, file_content, account_name, model)

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

    # Return success response
    response_content = {
        'status': 'success',
        'data': {
            'name': result.get('name'),
            'mykad_id': result.get('mykad_id'),
            'address': result.get('address'),
            'contact_number': result.get('contact_number'),
            'response_time': result.get('response_time')
        }
    }

    return JSONResponse(
        status_code=200,
        content=response_content
    )


@router.get("/extract-mykad")
async def get_mykad_documentation():
    """
    MYKAD Extractor API Documentation

    Returns API documentation.
    """

    return {
        'name': 'MYKAD & Namecard Extractor API',
        'version': '1.0.0',
        'description': 'Extract Name, MYKAD ID, Address, and Contact Number from MYKAD cards or namecards (images/PDFs)',
        'supported_file_types': ['JPG', 'JPEG', 'PNG', 'PDF'],
        'endpoints': {
            'POST /api/extract-mykad': {
                'description': 'Extract information from uploaded MYKAD card or namecard',
                'parameters': {
                    'file (form-data)': 'Image or PDF file (required)',
                    'account_name (form-data)': 'Account name (optional, default: yamal)',
                    'model (form-data)': 'Model name (optional, default: gemini-3-flash)'
                },
                'response': {
                    'status': 'HTTP 200 with JSON',
                    'body': 'JSON with extracted data'
                },
                'example': {
                    'command': 'curl -X POST "http://localhost:5000/api/extract-mykad" -F "file=@mykad.jpg"',
                    'response': '200 OK + JSON'
                }
            }
        },
        'extracted_fields': {
            'name': 'Full name of the person',
            'mykad_id': 'MYKAD identification number (format: XXXXXX-XX-XXXX)',
            'address': 'Complete address',
            'contact_number': 'Phone number'
        },
        'usage_examples': [
            {
                'title': 'Basic Extraction (MYKAD Card)',
                'curl': 'curl -X POST "http://localhost:5000/api/extract-mykad" -F "file=@mykad_front.jpg"',
                'python': '''
import requests

with open('mykad_front.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/extract-mykad',
        files={'file': f}
    )

result = response.json()
print(result['data']['name'])
print(result['data']['mykad_id'])
                '''
            },
            {
                'title': 'Namecard Extraction',
                'curl': 'curl -X POST "http://localhost:5000/api/extract-mykad" -F "file=@namecard.jpg"',
                'python': '''
import requests

with open('namecard.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/extract-mykad',
        files={'file': f}
    )

result = response.json()
print(result['data'])
                '''
            }
        ]
    }


@router.get("/mykad-health")
async def mykad_health_check():
    """MYKAD Extractor health check endpoint."""
    return {
        'status': 'healthy',
        'service': 'mykad-extractor-api',
        'version': '1.0.0'
    }
