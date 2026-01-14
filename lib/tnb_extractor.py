#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TNB Bill Extractor - Fast extraction with strict JSON output

This module provides a high-performance function to extract specific fields
from TNB electricity bills using gemini-3-flash model.
"""

import asyncio
import json
from typing import Dict, Optional
import sys
import os
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import perplexity
from lib.cookie_manager import CookieManager
from api.config import get_storage_file_path


async def extract_tnb_bill(
    file_path: str,
    file_content: bytes,
    account_name: str = "yamal",
    model: str = "gemini-3-flash"
) -> Dict[str, any]:
    """
    Extract TNB bill information with strict JSON output.

    Args:
        file_path: Path to the PDF file
        file_content: Binary content of the PDF file
        account_name: Account name to use from cookies.json
        model: Model to use (default: gemini-3-flash)

    Returns:
        Dictionary with extracted fields:
        {
            "customer_name": str,
            "tnb_account": str,
            "address": str,
            "bill_date": str,
            "success": bool,
            "response_time": float
        }

    Example:
        >>> result = await extract_tnb_bill("TNB1.pdf", pdf_bytes)
        >>> print(result)
        {
            "customer_name": "Mak Kian Keong",
            "tnb_account": "220012905808",
            "address": "3, Jalan Flora 3F/5, Bandar Rimbayu, 42500 Telok Panglima Garang, Selangor",
            "bill_date": "25.06.2025",
            "success": True,
            "response_time": 7.76
        }
    """

    # Initialize cookie manager
    storage_file = get_storage_file_path("accounts.json")
    cookie_manager = CookieManager(storage_file)

    # Get account cookies
    try:
        cookies = cookie_manager.get_account_cookies(account_name)
    except ValueError as e:
        return {
            "success": False,
            "error": f"Account not found: {e}",
            "customer_name": None,
            "tnb_account": None,
            "address": None,
            "bill_date": None,
            "response_time": 0
        }

    # Initialize client
    client = perplexity.Client(cookies)
    await client.init()

    # Generate thread UUID for later deletion
    from uuid import uuid4
    thread_uuid = str(uuid4())

    # Strict prompt for JSON-only output - no markdown, no explanations
    query = """Extract only these 4 fields from the TNB electricity bill. Return ONLY raw JSON with no markdown formatting, no code blocks, no explanations:

{"customer_name":"","tnb_account":"","address":"","bill_date":""}

Rules:
- Return ONLY the JSON object above with values filled in
- No markdown, no code blocks (```json), no introductory or concluding text
- If a field is not found, return empty string "" for that field
- bill_date format: DD.MM.YYYY"""

    files = {file_path: file_content}

    import time
    start_time = time.time()
    extraction_result = None

    try:
        result = await client.search(
            query,
            mode="auto",
            model=model,
            sources=["web"],
            files=files,
            stream=False,
            language="en-US",
            frontend_context_uuid=thread_uuid,
        )

        end_time = time.time()
        response_time = end_time - start_time

        # Extract answer from blocks - focus on ask_text block only
        blocks = result.get("blocks", [])
        raw_answer = None

        for block in blocks:
            intended_usage = block.get("intended_usage", "")
            if intended_usage in ["ask_text", "ask_text_0_markdown"]:
                markdown_block = block.get("markdown_block", {})
                if isinstance(markdown_block, dict):
                    raw_answer = markdown_block.get("answer")
                    break

        # Parse JSON from answer with strict validation
        extracted_data = {
            "customer_name": None,
            "tnb_account": None,
            "address": None,
            "bill_date": None
        }

        if raw_answer:
            json_str = raw_answer.strip()

            # Remove markdown code blocks if present
            json_str = re.sub(r'```json\s*', '', json_str)
            json_str = re.sub(r'```\s*$', '', json_str)

            # Extract JSON object from response
            if "{" in json_str and "}" in json_str:
                start_idx = json_str.find("{")
                end_idx = json_str.rfind("}") + 1
                json_str = json_str[start_idx:end_idx]

                try:
                    parsed = json.loads(json_str)

                    # Validate and extract required fields
                    extracted_data["customer_name"] = parsed.get("customer_name") or None
                    extracted_data["tnb_account"] = parsed.get("tnb_account") or None
                    extracted_data["address"] = parsed.get("address") or None
                    extracted_data["bill_date"] = parsed.get("bill_date") or None

                    # Clean up values - remove quotes if they're wrapped around
                    for key in extracted_data:
                        if extracted_data[key] and isinstance(extracted_data[key], str):
                            extracted_data[key] = extracted_data[key].strip()

                except json.JSONDecodeError:
                    # JSON parsing failed - data remains None
                    pass

        # Build result - exclude raw_answer to reduce payload size
        extraction_result = {
            "success": any(extracted_data.values()),
            "customer_name": extracted_data["customer_name"],
            "tnb_account": extracted_data["tnb_account"],
            "address": extracted_data["address"],
            "bill_date": extracted_data["bill_date"],
            "response_time": response_time
        }

        return extraction_result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "customer_name": None,
            "tnb_account": None,
            "address": None,
            "bill_date": None,
            "response_time": time.time() - start_time if 'start_time' in locals() else 0
        }

    finally:
        await cookie_manager.mark_account_used(account_name)

        # Auto-delete thread after successful extraction
        if extraction_result and extraction_result.get("success"):
            try:
                await client.delete_thread(thread_uuid)
            except Exception as delete_error:
                # Silently ignore deletion errors
                pass


async def batch_extract_tnb_bills(
    files: list[tuple[str, bytes]],
    account_name: str = "yamal",
    model: str = "gemini-3-flash"
) -> list[Dict[str, any]]:
    """
    Extract information from multiple TNB bills in batch.

    Args:
        files: List of (file_path, file_content) tuples
        account_name: Account name to use
        model: Model to use

    Returns:
        List of extraction results for each file
    """
    results = []

    for file_path, file_content in files:
        result = await extract_tnb_bill(
            file_path,
            file_content,
            account_name=account_name,
            model=model
        )
        result["file_name"] = file_path
        results.append(result)

    return results


# Example usage and testing
async def main():
    """Test the TNB bill extractor"""

    print("="*80)
    print("🧪 TNB BILL EXTRACTOR TEST")
    print("="*80)

    # Test with TNB1.pdf
    with open("TNB1.pdf", "rb") as f:
        pdf_content = f.read()

    result = await extract_tnb_bill("TNB1.pdf", pdf_content)

    print(f"\n✅ Extraction Status: {'Success' if result['success'] else 'Failed'}")
    print(f"⏱️  Response Time: {result['response_time']:.2f} seconds")
    print(f"\n📋 Extracted Data:")
    print("-"*80)
    print(f"Customer Name: {result.get('customer_name', 'N/A')}")
    print(f"TNB Account:    {result.get('tnb_account', 'N/A')}")
    print(f"Address:        {result.get('address', 'N/A')}")
    print(f"Bill Date:      {result.get('bill_date', 'N/A')}")
    print("-"*80)

    if result.get('raw_answer'):
        print(f"\n📄 Raw Answer (first 500 chars):")
        print("-"*80)
        print(result['raw_answer'][:500])
        if len(result['raw_answer']) > 500:
            print("\n... (truncated)")

    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())
