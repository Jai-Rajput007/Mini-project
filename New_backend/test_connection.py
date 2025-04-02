#!/usr/bin/env python
"""
Simple test script to verify MongoDB connection works properly.
This can be used to diagnose connection issues before starting the main application.

Usage:
    python test_connection.py
"""

import os
import sys
import motor.motor_asyncio
from dotenv import load_dotenv
import asyncio
import time

# Load environment variables
load_dotenv()

# MongoDB URL from environment or default working credentials
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://jaisrajputdev:newpass1234@mycluster.7ay65.mongodb.net/?retryWrites=true&w=majority")
DB_NAME = os.getenv("DB_NAME", "Vulnerability")

async def test_mongodb_connection():
    """Test connection to MongoDB"""
    print(f"Testing MongoDB connection...")
    print(f"Connection string: {MONGODB_URL.replace(MONGODB_URL.split('@')[0], '***:***')}")
    print(f"Database name: {DB_NAME}")
    print("-" * 60)
    
    try:
        print("Connecting to MongoDB...")
        start_time = time.time()
        client = motor.motor_asyncio.AsyncIOMotorClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        
        # Test connection by fetching server info
        await client.server_info()
        end_time = time.time()
        
        print(f"✅ Successfully connected to MongoDB! ({(end_time - start_time):.2f}s)")
        print("Connection test passed.")
        
        # Test database access
        db = client[DB_NAME]
        collections = await db.list_collection_names()
        print(f"✅ Successfully accessed database '{DB_NAME}'")
        print(f"Collections found: {len(collections)}")
        if collections:
            print(f"Available collections: {', '.join(collections)}")
        else:
            print("No collections found. This is normal for a new database.")
        
        # Close the connection
        client.close()
        print("Connection closed properly.")
        return True
    
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {str(e)}")
        print("\nPossible solutions:")
        print("1. Check your internet connection")
        print("2. Verify the MongoDB connection string in your .env file")
        print("3. Make sure your IP address is allowed in MongoDB Atlas")
        print("4. Check if MongoDB service is running (if using local MongoDB)")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("MongoDB Connection Test")
    print("=" * 60)
    
    result = asyncio.run(test_mongodb_connection())
    
    print("\nOverall Test Result:")
    if result:
        print("✅ All tests PASSED")
        sys.exit(0)
    else:
        print("❌ Tests FAILED")
        sys.exit(1) 