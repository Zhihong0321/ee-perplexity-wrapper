#!/usr/bin/env python3
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    from api.main import app
    
    print("Starting Perplexity Multi-Account API Server...")
    print("Dashboard will be available at: http://localhost:8000")
    print("API docs will be available at: http://localhost:8000/docs")
    
    # Run with Railway port if available
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(app, host="0.0.0.0", port=port)
