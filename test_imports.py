import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")
try:
    from lib import perplexity
    print("OK lib.perplexity imported")
except Exception as e:
    print(f"FAIL lib.perplexity failed: {e}")

try:
    from lib.cookie_manager import CookieManager
    print("OK lib.cookie_manager imported")
except Exception as e:
    print(f"FAIL lib.cookie_manager failed: {e}")

try:
    from api.utils import extract_answer, save_resp
    print("OK api.utils imported")
except Exception as e:
    print(f"FAIL api.utils failed: {e}")

try:
    import lib
    print("OK lib imported")
except Exception as e:
    print(f"FAIL lib failed: {e}")

print(f"Current directory: {os.getcwd()}")
print(f"Python path[0]: {sys.path[0]}")
