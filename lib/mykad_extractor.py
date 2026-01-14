#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MYKAD & Namecard Extractor - Fast extraction with strict JSON output

This module provides a high-performance function to extract personal information
from MYKAD cards or customer namecards using gemini-3-flash model.
"""

import asyncio
import json
from typing import Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import perplexity
from lib.cookie_manager import CookieManager
from api.config import get_storage_file_path


async def extract_mykad_info(
    file_path: str,
    file_content: bytes,
    account_name: str = "yamal",
    model: str = "gemini-3-flash"
) -> Dict[str, any]:
    """
    Extract MYKAD or namecard information with strict JSON output.

    Args:
        file_path: Path to the file (image or PDF)
        file_content: Binary content of the file
        account_name: Account name to use from cookies.json
        model: Model to use (default: gemini-3-flash)

    Returns:
        Dictionary with extracted fields:
        {
            "name": str,
            "mykad_id": str,
            "address": str,
            "contact_number": str,
            "success": bool,
            "response_time": float,
            "raw_answer": str
        }

    Example:
        >>> result = await extract_mykad_info("mykad.jpg", image_bytes)
        >>> print(result)
        {
            "name": "Ahmad bin Ali",
            "mykad_id": "123456-01-1234",
            "address": "No. 123, Jalan Merdeka, 50000 Kuala Lumpur",
            "contact_number": "012-3456789",
            "success": True,
            "response_time": 7.76,
            "raw_answer": "..."
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
            "name": None,
            "mykad_id": None,
            "address": None,
            "contact_number": None,
            "response_time": 0,
            "raw_answer": None
        }

    # Initialize client
    client = perplexity.Client(cookies)
    await client.init()

    # Generate thread UUID for later deletion
    from uuid import uuid4
    thread_uuid = str(uuid4())

    # Optimized prompt for fast extraction with STRICT JSON output
    query = """Extract these fields from MYKAD card or namecard. Return ONLY valid JSON, no other text, no markdown formatting:
{
  "name": "Full Name",
  "mykad_id": "MYKAD Number (format: XXXXXX-XX-XXXX)",
  "address": "Complete Address",
  "contact_number": "Phone Number"
}"""

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

        # Extract answer from blocks
        blocks = result.get("blocks", [])
        raw_answer = None

        for block in blocks:
            intended_usage = block.get("intended_usage", "")
            if intended_usage in ["ask_text", "ask_text_0_markdown"]:
                markdown_block = block.get("markdown_block", {})
                if isinstance(markdown_block, dict):
                    raw_answer = markdown_block.get("answer")
                    break

        # Parse JSON from answer
        if raw_answer:
            # Try to extract JSON from the response
            # The model might wrap it in markdown or text
            json_str = raw_answer.strip()

            # Look for JSON object in the response
            if "{" in json_str and "}" in json_str:
                start_idx = json_str.find("{")
                end_idx = json_str.rfind("}") + 1
                json_str = json_str[start_idx:end_idx]

            try:
                extracted_data = json.loads(json_str)

                extraction_result = {
                    "success": True,
                    "name": extracted_data.get("name"),
                    "mykad_id": extracted_data.get("mykad_id"),
                    "address": extracted_data.get("address"),
                    "contact_number": extracted_data.get("contact_number"),
                    "response_time": response_time,
                    "raw_answer": raw_answer
                }

            except json.JSONDecodeError:
                # JSON parsing failed, try to extract manually
                pass

        # Fallback: Try regex to extract values from markdown answer
        import re

        # Extract name
        name_match = re.search(r'(?:Name|name)[:":\s*"([^"]+)', raw_answer, re.IGNORECASE)
        name = name_match.group(1) if name_match else None

        # Extract MYKAD ID
        mykad_match = re.search(r'(?:MYKAD|mykad_id|ID)[:":\s*"?([\d-]+)', raw_answer, re.IGNORECASE)
        mykad_id = mykad_match.group(1) if mykad_match else None

        # Extract address
        address_match = re.search(r'(?:Address|address)[:":\s*"([^"]+)', raw_answer, re.IGNORECASE)
        address = address_match.group(1) if address_match else None

        # Extract contact number
        contact_match = re.search(r'(?:Contact|contact_number|Phone|phone)[:":\s*"?([^\s"]+)', raw_answer, re.IGNORECASE)
        contact_number = contact_match.group(1) if contact_match else None

        if not extraction_result:
            extraction_result = {
                "success": bool(name or mykad_id or address or contact_number),
                "name": name,
                "mykad_id": mykad_id,
                "address": address,
                "contact_number": contact_number,
                "response_time": response_time,
                "raw_answer": raw_answer
            }

        return extraction_result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "name": None,
            "mykad_id": None,
            "address": None,
            "contact_number": None,
            "response_time": time.time() - start_time if 'start_time' in locals() else 0,
            "raw_answer": None
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


async def batch_extract_mykad_info(
    files: list[tuple[str, bytes]],
    account_name: str = "yamal",
    model: str = "gemini-3-flash"
) -> list[Dict[str, any]]:
    """
    Extract information from multiple MYKAD/namecard files in batch.

    Args:
        files: List of (file_path, file_content) tuples
        account_name: Account name to use
        model: Model to use

    Returns:
        List of extraction results for each file
    """
    results = []

    for file_path, file_content in files:
        result = await extract_mykad_info(
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
    """Test the MYKAD extractor"""

    print("="*80)
    print("🧪 MYKAD & NAMECARD EXTRACTOR TEST")
    print("="*80)

    # Test with a sample file
    test_file = "test_mykad.jpg"
    if os.path.exists(test_file):
        with open(test_file, "rb") as f:
            file_content = f.read()

        result = await extract_mykad_info(test_file, file_content)

        print(f"\n✅ Extraction Status: {'Success' if result['success'] else 'Failed'}")
        print(f"⏱️  Response Time: {result['response_time']:.2f} seconds")
        print(f"\n📋 Extracted Data:")
        print("-"*80)
        print(f"Name:          {result.get('name', 'N/A')}")
        print(f"MYKAD ID:      {result.get('mykad_id', 'N/A')}")
        print(f"Address:       {result.get('address', 'N/A')}")
        print(f"Contact:       {result.get('contact_number', 'N/A')}")
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
