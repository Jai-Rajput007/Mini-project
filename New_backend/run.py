#!/usr/bin/env python
"""
Entry point for the Safex Vulnerability Scanner API.
This is the PREFERRED way to run the backend.

Usage:
    python run.py
"""

import os
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print("=" * 80)
    print(f"Starting Safex Vulnerability Scanner API on {host}:{port}")
    print("This is the main entry point for the backend service.")
    print(f"Documentation available at: http://localhost:{port}/docs")
    print("=" * 80)
    
    # This runs the FastAPI app defined in app.main:app
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    ) 