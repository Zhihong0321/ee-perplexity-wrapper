#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for MYKAD & Namecard Extractor API
"""

import requests
import os

API_URL = "http://localhost:5001"


def test_get_documentation():
    """Test GET endpoint for API documentation"""
    print("\n" + "="*80)
    print("📋 Testing GET /api/extract-mykad (Documentation)")
    print("="*80)

    response = requests.get(f"{API_URL}/api/extract-mykad")

    print(f"Status Code: {response.status_code}")
    print(f"\nAPI Name: {response.json()['name']}")
    print(f"Version: {response.json()['version']}")
    print(f"Description: {response.json()['description']}")


def test_health_check():
    """Test health check endpoint"""
    print("\n" + "="*80)
    print("🏥 Testing GET /health")
    print("="*80)

    response = requests.get(f"{API_URL}/health")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")


def test_post_extraction(file_path, account_name="yamal", model="gemini-3-flash"):
    """Test POST endpoint for extraction"""
    print("\n" + "="*80)
    print(f"📤 Testing POST /api/extract-mykad")
    print(f"File: {file_path}")
    print("="*80)

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        print("Skipping test...")
        return

    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'account_name': account_name,
            'model': model
        }

        response = requests.post(f"{API_URL}/api/extract-mykad", files=files, data=data)

    print(f"Status Code: {response.status_code}")

    result = response.json()

    if result['status'] == 'success':
        print(f"\n✅ Extraction Successful!")
        print(f"⏱️  Response Time: {result['data']['response_time']:.2f} seconds")
        print(f"\n📋 Extracted Data:")
        print("-"*80)
        print(f"Name:           {result['data'].get('name', 'N/A')}")
        print(f"MYKAD ID:       {result['data'].get('mykad_id', 'N/A')}")
        print(f"Address:        {result['data'].get('address', 'N/A')}")
        print(f"Contact Number: {result['data'].get('contact_number', 'N/A')}")
        print("-"*80)
    else:
        print(f"\n❌ Extraction Failed!")
        print(f"Error: {result['error']}")


def main():
    """Run all tests"""
    print("="*80)
    print("🧪 MYKAD & NAMECARD EXTRACTOR API TEST")
    print("="*80)
    print(f"\nAPI URL: {API_URL}")

    # Test 1: Get API documentation
    test_get_documentation()

    # Test 2: Health check
    test_health_check()

    # Test 3: POST extraction with MYKAD image (if exists)
    mykad_files = [
        "mykad_front.jpg",
        "mykad_back.jpg",
        "test_mykad.jpg",
        "mykad.jpg",
        "test.jpg"
    ]

    for file in mykad_files:
        if os.path.exists(file):
            test_post_extraction(file, account_name="yamal")
            break
    else:
        print("\n" + "="*80)
        print("⚠️  No MYKAD test files found")
        print("Please provide a MYKAD image file (mykad_front.jpg, mykad.jpg, etc.)")
        print("="*80)

    # Test 4: POST extraction with namecard image (if exists)
    namecard_files = [
        "namecard.jpg",
        "namecard.png",
        "test_namecard.jpg",
        "card.jpg"
    ]

    for file in namecard_files:
        if os.path.exists(file):
            test_post_extraction(file, account_name="yamal")
            break
    else:
        print("\n" + "="*80)
        print("⚠️  No namecard test files found")
        print("Please provide a namecard image file (namecard.jpg, card.jpg, etc.)")
        print("="*80)

    print("\n" + "="*80)
    print("📚 API Usage Examples")
    print("="*80)

    print("\n1. Basic Extraction (curl):")
    print('   curl -X POST http://localhost:5001/api/extract-mykad \\')
    print('        -F "file=@mykad.jpg"')

    print("\n2. Custom Account and Model:")
    print('   curl -X POST http://localhost:5001/api/extract-mykad \\')
    print('        -F "file=@namecard.jpg" \\')
    print('        -F "account_name=test_user" \\')
    print('        -F "model=gemini-3-pro"')

    print("\n3. Python:")
    print('''   import requests

   with open('mykad.jpg', 'rb') as f:
       response = requests.post(
           'http://localhost:5001/api/extract-mykad',
           files={'file': f}
       )

   result = response.json()
   print(result['data'])''')

    print("\n" + "="*80)
    print("✅ All tests completed!")
    print("="*80)


if __name__ == "__main__":
    main()
