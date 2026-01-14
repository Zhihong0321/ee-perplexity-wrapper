#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test TNB Bill Extractor"""

import asyncio
import sys
import os
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.tnb_extractor import extract_tnb_bill


async def main():
    """Test TNB bill extractor"""

    print("="*80)
    print("🧪 TNB BILL EXTRACTOR TEST")
    print("="*80)

    # Test with TNB1.pdf
    with open("TNB1.pdf", "rb") as f:
        pdf_content = f.read()

    result = await extract_tnb_bill("TNB1.pdf", pdf_content, account_name="test_user")

    print(f"\n✅ Extraction Status: {'Success' if result['success'] else 'Failed'}")
    print(f"⏱️  Response Time: {result['response_time']:.2f} seconds")
    print(f"\n📋 Extracted Data:")
    print("-"*80)
    print(f"Customer Name: {result.get('customer_name', 'N/A')}")
    print(f"TNB Account:    {result.get('tnb_account', 'N/A')}")
    print(f"Address:        {result.get('address', 'N/A')}")
    print(f"Bill Date:      {result.get('bill_date', 'N/A')}")
    print("-"*80)

    if result.get('error'):
        print(f"\n❌ Error: {result['error']}")

    if result.get('raw_answer'):
        print(f"\n📄 Raw Answer (first 300 chars):")
        print("-"*80)
        print(result['raw_answer'][:300])
        if len(result['raw_answer']) > 300:
            print("\n... (truncated)")

    print("\n" + "="*80)

    # Also print strict JSON if available
    if result.get('customer_name'):
        print("\n🔧 STRICT JSON OUTPUT:")
        print("-"*80)
        json_output = {
            "customer_name": result['customer_name'],
            "tnb_account": result['tnb_account'],
            "address": result['address'],
            "bill_date": result['bill_date']
        }
        print(json.dumps(json_output, indent=2, ensure_ascii=False))
        print("-"*80)


if __name__ == "__main__":
    asyncio.run(main())
