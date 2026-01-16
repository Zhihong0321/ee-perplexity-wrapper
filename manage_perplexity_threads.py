#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Perplexity Thread Management Tool

Manage Perplexity threads to free up file upload quota:
- List all threads
- Delete old threads
- Check upload quota status
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.perplexity import Client
from lib.cookie_manager import CookieManager
from api.config import get_storage_file_path


async def list_threads(account_name: str = "yamal", limit: int = 50):
    """List all threads for an account"""
    storage_file = get_storage_file_path("accounts.json")
    cookie_manager = CookieManager(storage_file)

    try:
        cookies = cookie_manager.get_account_cookies(account_name)
    except ValueError as e:
        print(f"❌ Account not found: {e}")
        return

    client = Client(cookies)
    await client.init()

    print(f"\n📋 Threads for account '{account_name}':")
    print("=" * 80)

    result = await client.get_threads(limit=limit, offset=0)
    threads = result.get('threads', [])

    if not threads:
        print("No threads found.")
        return

    print(f"Total threads: {len(threads)}\n")

    for i, thread in enumerate(threads, 1):
        thread_uuid = thread.get('uuid') or thread.get('id', 'N/A')
        title = thread.get('title', 'Untitled')
        created = thread.get('created_at', 'Unknown')
        print(f"{i}. {title}")
        print(f"   UUID: {thread_uuid}")
        print(f"   Created: {created}")
        print()

    return threads


async def delete_all_threads(account_name: str = "yamal"):
    """Delete all threads for an account to free up quota"""
    storage_file = get_storage_file_path("accounts.json")
    cookie_manager = CookieManager(storage_file)

    try:
        cookies = cookie_manager.get_account_cookies(account_name)
    except ValueError as e:
        print(f"❌ Account not found: {e}")
        return

    client = Client(cookies)
    await client.init()

    print(f"\n🗑️  Deleting ALL threads for account '{account_name}'...")
    print("=" * 80)

    result = await client.delete_all_threads()

    print(f"\n✅ Deletion Summary:")
    print(f"   Total threads: {result['total']}")
    print(f"   Deleted: {result['deleted']}")
    print(f"   Failed: {result['failed']}")

    if result['failed'] > 0:
        print("\n❌ Failed deletions:")
        for detail in result['details']:
            if not detail['success']:
                print(f"   - {detail['title']}: {detail.get('error', 'Unknown error')}")


async def delete_old_threads(account_name: str = "yamal", keep_count: int = 10):
    """Delete old threads, keeping the most recent N threads"""
    storage_file = get_storage_file_path("accounts.json")
    cookie_manager = CookieManager(storage_file)

    try:
        cookies = cookie_manager.get_account_cookies(account_name)
    except ValueError as e:
        print(f"❌ Account not found: {e}")
        return

    client = Client(cookies)
    await client.init()

    print(f"\n🗑️  Deleting old threads (keeping latest {keep_count}) for '{account_name}'...")
    print("=" * 80)

    result = await client.get_threads(limit=1000, offset=0)
    threads = result.get('threads', [])

    if len(threads) <= keep_count:
        print(f"Only {len(threads)} threads found. Keeping all.")
        return

    # Delete older threads (keep the most recent)
    threads_to_delete = threads[keep_count:]

    deleted = 0
    failed = 0

    for thread in threads_to_delete:
        thread_uuid = thread.get('uuid') or thread.get('id')
        if not thread_uuid:
            continue

        try:
            await client.delete_thread(thread_uuid)
            deleted += 1
            print(f"✅ Deleted: {thread.get('title', 'Untitled')}")
        except Exception as e:
            failed += 1
            print(f"❌ Failed: {thread.get('title', 'Untitled')} - {e}")

    print(f"\n✅ Summary: Deleted {deleted}, Failed {failed}")


async def check_upload_quota(account_name: str = "yamal"):
    """Check current upload quota status"""
    storage_file = get_storage_file_path("accounts.json")
    cookie_manager = CookieManager(storage_file)

    try:
        cookies = cookie_manager.get_account_cookies(account_name)
    except ValueError as e:
        print(f"❌ Account not found: {e}")
        return

    client = Client(cookies)
    await client.init()

    print(f"\n📊 Upload quota status for '{account_name}':")
    print("=" * 80)

    # Try to get upload URL for a small test file
    import mimetypes
    test_file_info = await client.session.post(
        "https://www.perplexity.ai/rest/uploads/create_upload_url?version=2.18&source=default",
        json={
            "content_type": "application/pdf",
            "file_size": 1000,
            "filename": "test.pdf",
            "force_image": False,
            "source": "default",
        },
    )

    info = test_file_info.json()

    if info.get("rate_limited"):
        print("❌ RATE LIMITED")
        print(f"   Response: {info}")
    else:
        print("✅ Upload quota available")
        print(f"   S3 Bucket URL: {info.get('s3_bucket_url', 'N/A')}")
        print(f"   File UUID: {info.get('file_uuid', 'N/A')}")


async def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("""
Perplexity Thread Management Tool

Usage:
  python manage_perplexity_threads.py <command> [options]

Commands:
  list [account]              List all threads (default: yamal)
  delete-all [account]        Delete ALL threads
  delete-old [account] [N]    Delete old threads, keep latest N (default: 10)
  check-quota [account]       Check upload quota status

Examples:
  python manage_perplexity_threads.py list
  python manage_perplexity_threads.py list test_user
  python manage_perplexity_threads.py delete-all yamal
  python manage_perplexity_threads.py delete-old yamal 20
  python manage_perplexity_threads.py check-quota
        """)
        return

    command = sys.argv[1].lower()
    account_name = sys.argv[2] if len(sys.argv) > 2 else "yamal"

    if command == "list":
        await list_threads(account_name)
    elif command == "delete-all":
        confirm = input(f"⚠️  This will delete ALL threads for '{account_name}'. Continue? (yes/no): ")
        if confirm.lower() == "yes":
            await delete_all_threads(account_name)
        else:
            print("Cancelled.")
    elif command == "delete-old":
        keep_count = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        await delete_old_threads(account_name, keep_count)
    elif command == "check-quota":
        await check_upload_quota(account_name)
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())
