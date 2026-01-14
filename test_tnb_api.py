#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test TNB Bill Extractor API

Demonstrates how to use the TNB extractor API endpoint
with both curl and Python requests.
"""

import requests
import time


def test_api_with_curl():
    """Test API using curl command"""

    print("="*80)
    print("🧪 TEST 1: Using curl")
    print("="*80)

    curl_command = '''curl.exe -X POST "http://localhost:5000/api/extract-tnb" \
  -F "file=@TNB1.pdf" \
  -F "account_name=yamal" \
  -w "\\n\\nSTATUS: %{http_code}\\nREDIRECT: %{redirect_url}\\nTIME: %{time_total}s\\n"'''

    print("\n💡 Command:")
    print("-"*80)
    print(curl_command)
    print("-"*80)
    print("\n📝 Copy and run this command in your terminal")
    print("="*80)


def test_api_with_python():
    """Test API using Python requests"""

    print("\n" + "="*80)
    print("🧪 TEST 2: Using Python requests")
    print("="*80)

    # API endpoint
    url = "http://localhost:5000/api/extract-tnb"

    # Prepare file upload
    with open("TNB1.pdf", "rb") as f:
        files = {"file": f}

        # Optional parameters
        data = {
            "account_name": "yamal",
            "model": "gemini-3-flash"
        }

        print("\n📤 Request:")
        print("-"*80)
        print(f"URL: {url}")
        print(f"File: TNB1.pdf")
        print(f"Account: yamal")
        print(f"Model: gemini-3-flash")
        print("-"*80)

        # Send POST request
        print("\n⏳ Sending request...")
        start_time = time.time()

        try:
            response = requests.post(url, files=files, data=data, allow_redirects=False)

            end_time = time.time()
            total_time = end_time - start_time

            print(f"\n📥 Response:")
            print("-"*80)
            print(f"Status: {response.status_code}")
            print(f"Time: {total_time:.2f}s")

            # Check redirect URL
            if 'Location' in response.headers:
                redirect_url = response.headers['Location']
                print(f"\n🔀 Redirect URL:")
                print("-"*80)
                print(redirect_url)

                # Parse query parameters
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(redirect_url)
                params = parse_qs(parsed.query)

                print(f"\n📋 Extracted Parameters:")
                print("-"*80)
                print(f"customer_name : {params.get('customer_name', [''])[0]}")
                print(f"address       : {params.get('address', [''])[0]}")
                print(f"tnb-account   : {params.get('tnb-account', [''])[0]}")
                print(f"bill-date     : {params.get('bill-date', [''])[0]}")
                print("-"*80)

            # Parse JSON response
            try:
                result = response.json()

                if 'data' in result:
                    print(f"\n📦 JSON Response:")
                    print("-"*80)
                    print(json.dumps(result['data'], indent=2, ensure_ascii=False))
                    print("-"*80)

                    # Display summary
                    data = result['data']
                    print("\n✅ EXTRACTION SUMMARY")
                    print("="*80)
                    print(f"Customer Name: {data.get('customer_name', 'N/A')}")
                    print(f"TNB Account   : {data.get('tnb_account', 'N/A')}")
                    print(f"Address       : {data.get('address', 'N/A')}")
                    print(f"Bill Date     : {data.get('bill_date', 'N/A')}")
                    print(f"Response Time : {data.get('response_time', 0):.2f}s")
                    print("="*80)

            except json.JSONDecodeError:
                print("\n❌ Could not parse JSON response")

        except requests.exceptions.ConnectionError:
            print("\n❌ Error: Could not connect to API server")
            print("💡 Make sure the API server is running:")
            print("   python api/tnb_extractor_api.py")
        except Exception as e:
            print(f"\n❌ Error: {e}")


def test_api_with_python_redirect():
    """Test API by following the redirect"""

    print("\n" + "="*80)
    print("🧪 TEST 3: Follow Redirect URL")
    print("="*80)

    # API endpoint
    url = "http://localhost:5000/api/extract-tnb"

    # Prepare file upload
    with open("TNB1.pdf", "rb") as f:
        files = {"file": f}
        data = {"account_name": "yamal", "model": "gemini-3-flash"}

        # Send POST request and follow redirect
        try:
            response = requests.post(url, files=files, data=data)

            print(f"\n📥 Final Response Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()

                if 'data' in result:
                    data = result['data']
                    print("\n✅ Extracted Data (from redirect):")
                    print("-"*80)
                    print(f"Customer Name: {data.get('customer_name', 'N/A')}")
                    print(f"TNB Account   : {data.get('tnb_account', 'N/A')}")
                    print(f"Address       : {data.get('address', 'N/A')}")
                    print(f"Bill Date     : {data.get('bill_date', 'N/A')}")
                    print("-"*80)

        except Exception as e:
            print(f"\n❌ Error: {e}")


def get_api_documentation():
    """Get API documentation from GET endpoint"""

    print("\n" + "="*80)
    print("📚 API DOCUMENTATION")
    print("="*80)

    try:
        response = requests.get("http://localhost:5000/api/extract-tnb")
        doc = response.json()

        print(f"\n{doc.get('name', 'TNB Bill Extractor API')} v{doc.get('version', '1.0')}")
        print(f"\n{doc.get('description', '')}")

        print("\n📌 Endpoints:")
        for endpoint_name, endpoint_info in doc.get('endpoints', {}).items():
            print(f"\n{endpoint_name}:")
            print(f"  {endpoint_info.get('description', '')}")

            if 'parameters' in endpoint_info:
                print("  Parameters:")
                for param_name, param_desc in endpoint_info.get('parameters', {}).items():
                    print(f"    - {param_name}: {param_desc}")

            if 'example' in endpoint_info:
                print("  Example:")
                for key, value in endpoint_info.get('example', {}).items():
                    print(f"    {key}: {value}")

        print("\n" + "="*80)

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("💡 Start the API server first:")
        print("   python api/tnb_extractor_api.py")


def main():
    """Main test function"""

    import json

    print("\n" + "="*80)
    print("🧪 TNB BILL EXTRACTOR API TEST")
    print("="*80)

    # Test 1: Show curl command
    test_api_with_curl()

    # Test 2: Python requests (no redirect)
    test_api_with_python()

    # Test 3: Follow redirect
    test_api_with_python_redirect()

    # Test 4: Get API documentation
    get_api_documentation()

    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETED")
    print("="*80)
    print("\n💡 To start the API server:")
    print("   cd E:\\perplexity-wrapper")
    print("   python api/tnb_extractor_api.py")
    print("\n🌐 API will be available at:")
    print("   http://localhost:5000/api/extract-tnb")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
