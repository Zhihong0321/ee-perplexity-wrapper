#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for MYKAD extractor module directly
"""

import asyncio
import os
from lib.mykad_extractor import extract_mykad_info


async def test_mykad_extractor():
    """Test the MYKAD extractor function"""

    print("="*80)
    print("🧪 MYKAD EXTRACTOR MODULE TEST")
    print("="*80)

    # Test files to look for
    test_files = [
        "mykad_front.jpg",
        "mykad_back.jpg",
        "test_mykad.jpg",
        "mykad.jpg",
        "namecard.jpg",
        "test.jpg"
    ]

    test_file = None
    for file in test_files:
        if os.path.exists(file):
            test_file = file
            break

    if not test_file:
        print("\n⚠️  No test file found!")
        print("Please provide one of these files:")
        for file in test_files:
            print(f"  - {file}")
        return

    print(f"\n📁 Testing with file: {test_file}")

    # Read file content
    with open(test_file, "rb") as f:
        file_content = f.read()

    # Extract information
    print("\n⏳ Extracting information...")
    result = await extract_mykad_info(test_file, file_content, account_name="yamal")

    # Display results
    print(f"\n✅ Extraction Status: {'Success' if result['success'] else 'Failed'}")
    print(f"⏱️  Response Time: {result['response_time']:.2f} seconds")
    print(f"\n📋 Extracted Data:")
    print("-"*80)
    print(f"Name:           {result.get('name', 'N/A')}")
    print(f"MYKAD ID:       {result.get('mykad_id', 'N/A')}")
    print(f"Address:        {result.get('address', 'N/A')}")
    print(f"Contact Number: {result.get('contact_number', 'N/A')}")
    print("-"*80)

    if result.get('error'):
        print(f"\n❌ Error: {result['error']}")

    if result.get('raw_answer'):
        print(f"\n📄 Raw Answer (first 500 chars):")
        print("-"*80)
        print(result['raw_answer'][:500])
        if len(result['raw_answer']) > 500:
            print("\n... (truncated)")

    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(test_mykad_extractor())
