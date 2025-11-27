import os

def get_storage_file_path(filename: str = "accounts.json") -> str:
    """
    Determine the persistent storage path for the given filename.
    Priorities:
    1. STORAGE_ROOT env var
    2. /storage (Common Railway volume path)
    3. /app/storage (Alternative path)
    4. Local directory (Fallback)
    """
    env_storage = os.getenv("STORAGE_ROOT")
    possible_paths = []

    if env_storage:
        possible_paths.append(env_storage)

    possible_paths.extend(["/storage", "/app/storage"])

    storage_dir = None
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            storage_dir = path
            break

    if storage_dir:
        file_path = os.path.join(storage_dir, filename)
        print(f"Using persistent storage: {file_path}")
        return file_path
    else:
        print(f"Using local storage: {filename}")
        return filename
