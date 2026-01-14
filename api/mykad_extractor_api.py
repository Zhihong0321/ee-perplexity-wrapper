#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MYKAD & Namecard Extractor API - Flask Endpoint

Provides REST API endpoint for extracting MYKAD/namecard information
from image/PDF files.

Usage:
  POST /api/extract-mykad
  Body: multipart/form-data with 'file' field

Returns:
  JSON with extracted data
"""

import asyncio
import json
import sys
import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.mykad_extractor import extract_mykad_info
from api.config import get_storage_file_path
from lib.cookie_manager import CookieManager

app = Flask(__name__)


@app.route('/api/extract-mykad', methods=['GET', 'POST'])
def extract_mykad_api():
    """
    MYKAD/Namecard Extraction API Endpoint

    GET: Returns API documentation
    POST: Extracts MYKAD/namecard information

    Request Body (for POST):
      - file: Image or PDF file (required)
      - account_name: Account name (optional, default: "yamal")
      - model: Model name (optional, default: "gemini-3-flash")

    Returns (POST):
      JSON with extracted data

    Example POST:
      curl -X POST http://localhost:5001/api/extract-mykad \
           -F "file=@mykad.jpg" \
           -F "account_name=yamal"
    """

    # GET request: Return API documentation
    if request.method == 'GET':
        return jsonify({
            'name': 'MYKAD & Namecard Extractor API',
            'version': '1.0.0',
            'description': 'Extract Name, MYKAD ID, Address, and Contact Number from MYKAD cards or namecards',
            'supported_file_types': ['JPG', 'JPEG', 'PNG', 'PDF'],
            'endpoints': {
                'POST /api/extract-mykad': {
                    'description': 'Extract information from uploaded MYKAD card or namecard',
                    'parameters': {
                        'file (form-data)': 'Image or PDF file (required)',
                        'account_name (form-data)': 'Account name (optional, default: yamal)',
                        'model (form-data)': 'Model name (optional, default: gemini-3-flash)'
                    },
                    'response': 'JSON with extracted data',
                    'example': {
                        'command': 'curl -X POST http://localhost:5001/api/extract-mykad -F "file=@mykad.jpg"',
                        'response': '200 OK + JSON'
                    }
                },
                'GET /api/extract-mykad': {
                    'description': 'API documentation',
                    'response': 'JSON documentation'
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
                    'title': 'MYKAD Card Extraction',
                    'curl': 'curl -X POST http://localhost:5001/api/extract-mykad -F "file=@mykad_front.jpg"',
                    'python': '''
import requests

with open('mykad_front.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5001/api/extract-mykad',
        files={'file': f}
    )

result = response.json()
print(result['data'])
                    '''
                },
                {
                    'title': 'Namecard Extraction',
                    'curl': 'curl -X POST http://localhost:5001/api/extract-mykad -F "file=@namecard.jpg" -F "account_name=test_user"',
                    'python': '''
import requests

files = {'file': open('namecard.jpg', 'rb')}
data = {'account_name': 'test_user'}

response = requests.post(
    'http://localhost:5001/api/extract-mykad',
    files=files,
    data=data
)

result = response.json()
print(result['data'])
                    '''
                }
            ]
        })

    # POST request: Process file upload
    if request.method == 'POST':
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'error': 'No file uploaded. Please upload an image or PDF file.'
            }), 400

        file = request.files['file']

        # Check if file has a filename
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'error': 'No file selected. Please select a file to upload.'
            }), 400

        # Secure the filename
        filename = secure_filename(file.filename)

        # Check file extension (images and PDF)
        allowed_extensions = ('.jpg', '.jpeg', '.png', '.pdf')
        if not filename.lower().endswith(allowed_extensions):
            return jsonify({
                'status': 'error',
                'error': 'Invalid file format. Only images (JPG, PNG) and PDF files are supported.'
            }), 400

        # Get optional parameters
        account_name = request.form.get('account_name', 'yamal')
        model = request.form.get('model', 'gemini-3-flash')

        # Read file content
        file_content = file.read()

        # Extract MYKAD/namecard information
        result = asyncio.run(extract_mykad_info(filename, file_content, account_name, model))

        if not result['success']:
            # Extraction failed
            return jsonify({
                'status': 'error',
                'error': result.get('error', 'Extraction failed'),
                'response_time': result.get('response_time', 0)
            }), 500

        # Return success response
        return jsonify({
            'status': 'success',
            'data': {
                'name': result.get('name'),
                'mykad_id': result.get('mykad_id'),
                'address': result.get('address'),
                'contact_number': result.get('contact_number'),
                'response_time': result.get('response_time')
            }
        })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'mykad-extractor-api'})


if __name__ == '__main__':
    print("="*80)
    print("🚀 MYKAD & Namecard Extractor API Starting")
    print("="*80)
    print("\n📌 API Endpoints:")
    print("  - POST /api/extract-mykad  - Upload image/PDF and extract info")
    print("  - GET  /api/extract-mykad  - View API documentation")
    print("  - GET  /health             - Health check")
    print("\n📋 Extracted Fields:")
    print("  - name           : Full name")
    print("  - mykad_id       : MYKAD identification number")
    print("  - address        : Complete address")
    print("  - contact_number : Phone number")
    print("\n📁 Supported File Types:")
    print("  - Images: JPG, JPEG, PNG")
    print("  - Documents: PDF")
    print("\n💡 Example Usage:")
    print('  curl -X POST http://localhost:5001/api/extract-mykad -F "file=@mykad.jpg"')
    print("="*80)

    app.run(debug=True, host='0.0.0.0', port=5001)
