#!/usr/bin/env python3
import sys
import os
import traceback

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    try:
        print("Starting Perplexity Multi-Account API Server...")
        print(f"Python version: {sys.version}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Python path: {sys.path[:3]}")
        
        # Test imports first
        try:
            from api.main import app
            print("OK Successfully imported main app")
        except Exception as e:
            print(f"FAIL Failed to import app: {e}")
            traceback.print_exc()
            sys.exit(1)
        
        import uvicorn
        
        # Run with Railway port if available
        port = int(os.environ.get("PORT", 8000))
        host = os.environ.get("HOST", "0.0.0.0")
        
        print(f"Dashboard will be available at: http://{host}:{port}")
        print(f"API docs will be available at: http://{host}:{port}/docs")
        
        # Start server with error handling
        uvicorn.run(app, host=host, port=port, access_log=True)
        
    except Exception as e:
        print(f"Server startup failed: {e}")
        traceback.print_exc()
        sys.exit(1)
