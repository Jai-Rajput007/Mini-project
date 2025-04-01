import os
import motor.motor_asyncio
from typing import Optional, Dict, Any, List
from bson import ObjectId
import json

# MongoDB Configuration
# Use environment variables for better security
# Format correctly for special characters
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://jaisrajputdev:newpass1234@mycluster.7ay65.mongodb.net/?retryWrites=true&w=majority")

# Use Vulnerability as database name
DB_NAME = "Vulnerability"

# Global database connection object
_mongo_client = None
_db = None
_using_fallback = False

async def connect_to_mongo() -> Optional[motor.motor_asyncio.AsyncIOMotorDatabase]:
    """
    Connect to MongoDB database
    
    Returns:
        Optional[motor.motor_asyncio.AsyncIOMotorDatabase]: Database connection object
    """
    global _mongo_client, _db, _using_fallback
    
    try:
        # Create a new client and connect to the server
        print(f"Connecting to MongoDB at {MONGODB_URL}")
        _mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
            MONGODB_URL, 
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            tlsAllowInvalidCertificates=True  # Less strict SSL verification for testing
        )
        
        # Verify the connection was successful
        await _mongo_client.server_info()
        print("Successfully connected to MongoDB Atlas!")
        
        # Access the database
        _db = _mongo_client[DB_NAME]
        
        # Create collections if they don't exist
        collections_to_create = ["scans", "scan_results", "users", "reports"]
        existing_collections = await _db.list_collection_names()
        
        for collection in collections_to_create:
            if collection not in existing_collections:
                await _db.create_collection(collection)
                print(f"Created collection: {collection}")
        
        return _db
    
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        print("Please check your MongoDB Atlas credentials and network connection.")
        print("Using local JSON storage fallback instead.")
        
        # Set fallback flag
        _using_fallback = True
        return None

async def close_mongo_connection() -> None:
    """Close the MongoDB connection"""
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        print("MongoDB connection closed")

def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """
    Get the database connection
    
    Returns:
        motor.motor_asyncio.AsyncIOMotorDatabase: Database connection object
    """
    global _db, _using_fallback
    if not _db and not _using_fallback:
        raise Exception("Database not initialized. Call connect_to_mongo() first.")
    return _db

def _get_fallback_dir() -> str:
    """Get fallback directory for local storage"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    fallback_dir = os.path.join(base_dir, "db_fallback")
    
    # Create directory if it doesn't exist
    if not os.path.exists(fallback_dir):
        os.makedirs(fallback_dir)
        
    return fallback_dir

async def save_to_db(collection: str, data: Dict[str, Any]) -> str:
    """
    Save data to database
    
    Args:
        collection: Collection name
        data: Data to save
        
    Returns:
        str: ID of inserted document
    """
    global _using_fallback
    
    try:
        if not _using_fallback:
            db = get_db()
            result = await db[collection].insert_one(data)
            return str(result.inserted_id)
        else:
            # Use fallback JSON storage
            return _save_to_json(collection, data)
    except Exception as e:
        print(f"Error saving to database: {e}")
        # Fallback to local JSON storage
        return _save_to_json(collection, data)

def _save_to_json(collection: str, data: Dict[str, Any]) -> str:
    """Save data to JSON file as fallback"""
    fallback_dir = _get_fallback_dir()
    
    # Create collection directory if it doesn't exist
    collection_dir = os.path.join(fallback_dir, collection)
    if not os.path.exists(collection_dir):
        os.makedirs(collection_dir)
    
    # Use report_id or document_id if available, otherwise generate UUID
    doc_id = data.get("report_id") or data.get("scan_id") or data.get("_id") or str(ObjectId())
    
    # Save to file
    file_path = os.path.join(collection_dir, f"{doc_id}.json")
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
        
    print(f"Saved {collection}/{doc_id} to local storage")
    return doc_id

async def update_in_db(collection: str, filter_query: Dict[str, Any], update_data: Dict[str, Any]) -> bool:
    """
    Update document in database
    
    Args:
        collection: Collection name
        filter_query: Query to find document
        update_data: Data to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    global _using_fallback
    
    try:
        if not _using_fallback:
            db = get_db()
            result = await db[collection].update_one(filter_query, {"$set": update_data})
            return result.modified_count > 0
        else:
            # Use fallback JSON storage
            return _update_in_json(collection, filter_query, update_data)
    except Exception as e:
        print(f"Error updating in database: {e}")
        # Fallback to local JSON storage
        return _update_in_json(collection, filter_query, update_data)

def _update_in_json(collection: str, filter_query: Dict[str, Any], update_data: Dict[str, Any]) -> bool:
    """Update document in JSON file as fallback"""
    fallback_dir = _get_fallback_dir()
    collection_dir = os.path.join(fallback_dir, collection)
    
    if not os.path.exists(collection_dir):
        return False
    
    # Find matching file based on filter_query
    for filename in os.listdir(collection_dir):
        if not filename.endswith(".json"):
            continue
            
        file_path = os.path.join(collection_dir, filename)
        try:
            with open(file_path, "r") as f:
                doc = json.load(f)
                
            # Check if document matches filter_query
            if all(doc.get(k) == v for k, v in filter_query.items()):
                # Update document
                doc.update(update_data)
                
                # Save updated document
                with open(file_path, "w") as f:
                    json.dump(doc, f, indent=2)
                    
                print(f"Updated {collection}/{filename} in local storage")
                return True
        except Exception as e:
            print(f"Error reading/writing file {file_path}: {e}")
    
    return False

async def find_document(collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Find a document in database
    
    Args:
        collection: Collection name
        query: Query to find document
        
    Returns:
        Optional[Dict[str, Any]]: Document if found, None otherwise
    """
    global _using_fallback
    
    try:
        if not _using_fallback:
            db = get_db()
            document = await db[collection].find_one(query)
            if document and "_id" in document:
                document["_id"] = str(document["_id"])  # Convert ObjectId to string
            return document
        else:
            # Use fallback JSON storage
            return _find_document_in_json(collection, query)
    except Exception as e:
        print(f"Error finding document in database: {e}")
        # Fallback to local JSON storage
        return _find_document_in_json(collection, query)

def _find_document_in_json(collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Find a document in JSON file as fallback"""
    fallback_dir = _get_fallback_dir()
    collection_dir = os.path.join(fallback_dir, collection)
    
    if not os.path.exists(collection_dir):
        return None
    
    # Find matching file based on query
    for filename in os.listdir(collection_dir):
        if not filename.endswith(".json"):
            continue
            
        file_path = os.path.join(collection_dir, filename)
        try:
            with open(file_path, "r") as f:
                doc = json.load(f)
                
            # Check if document matches query
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
    
    return None

async def find_documents(collection: str, query: Dict[str, Any], limit: int = 0, skip: int = 0, 
                         sort_field: str = None, sort_order: int = -1) -> List[Dict[str, Any]]:
    """
    Find documents in database
    
    Args:
        collection: Collection name
        query: Query to find documents
        limit: Maximum number of documents to return
        skip: Number of documents to skip
        sort_field: Field to sort by
        sort_order: Sort order (1 for ascending, -1 for descending)
        
    Returns:
        list: List of documents
    """
    global _using_fallback
    
    try:
        if not _using_fallback:
            db = get_db()
            cursor = db[collection].find(query).skip(skip)
            
            if sort_field:
                cursor = cursor.sort(sort_field, sort_order)
                
            if limit > 0:
                cursor = cursor.limit(limit)
                
            documents = await cursor.to_list(length=None)
            
            # Convert ObjectId to string for each document
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
                    
            return documents
        else:
            # Use fallback JSON storage
            return _find_documents_in_json(collection, query, limit, skip, sort_field, sort_order)
    except Exception as e:
        print(f"Error finding documents in database: {e}")
        # Fallback to local JSON storage
        return _find_documents_in_json(collection, query, limit, skip, sort_field, sort_order)

def _find_documents_in_json(collection: str, query: Dict[str, Any], limit: int = 0, skip: int = 0,
                           sort_field: str = None, sort_order: int = -1) -> List[Dict[str, Any]]:
    """Find documents in JSON files as fallback"""
    fallback_dir = _get_fallback_dir()
    collection_dir = os.path.join(fallback_dir, collection)
    
    if not os.path.exists(collection_dir):
        return []
    
    results = []
    
    # Find matching files based on query
    for filename in os.listdir(collection_dir):
        if not filename.endswith(".json"):
            continue
            
        file_path = os.path.join(collection_dir, filename)
        try:
            with open(file_path, "r") as f:
                doc = json.load(f)
                
            # Check if document matches query
            if all(doc.get(k) == v for k, v in query.items()):
                results.append(doc)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
    
    # Sort results if sort_field provided
    if sort_field and sort_field in results[0] if results else False:
        results.sort(key=lambda x: x.get(sort_field, ""), reverse=(sort_order == -1))
    
    # Apply skip and limit
    return results[skip:skip+limit] if limit > 0 else results[skip:]

async def delete_document(collection: str, query: Dict[str, Any]) -> bool:
    """
    Delete a document from database
    
    Args:
        collection: Collection name
        query: Query to find document to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    global _using_fallback
    
    try:
        if not _using_fallback:
            db = get_db()
            result = await db[collection].delete_one(query)
            return result.deleted_count > 0
        else:
            # Use fallback JSON storage
            return _delete_document_in_json(collection, query)
    except Exception as e:
        print(f"Error deleting document from database: {e}")
        # Fallback to local JSON storage
        return _delete_document_in_json(collection, query)

def _delete_document_in_json(collection: str, query: Dict[str, Any]) -> bool:
    """Delete a document from JSON file as fallback"""
    fallback_dir = _get_fallback_dir()
    collection_dir = os.path.join(fallback_dir, collection)
    
    if not os.path.exists(collection_dir):
        return False
    
    # Find matching file based on query
    for filename in os.listdir(collection_dir):
        if not filename.endswith(".json"):
            continue
            
        file_path = os.path.join(collection_dir, filename)
        try:
            with open(file_path, "r") as f:
                doc = json.load(f)
                
            # Check if document matches query
            if all(doc.get(k) == v for k, v in query.items()):
                # Delete file
                os.remove(file_path)
                print(f"Deleted {collection}/{filename} from local storage")
                return True
        except Exception as e:
            print(f"Error reading/deleting file {file_path}: {e}")
    
    return False

async def get_document_by_id(collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a document by its ID
    
    Args:
        collection: Collection name
        doc_id: Document ID
        
    Returns:
        Optional[Dict[str, Any]]: Document if found, None otherwise
    """
    global _using_fallback
    
    try:
        if not _using_fallback:
            db = get_db()
            try:
                # Try as MongoDB ObjectId
                document = await db[collection].find_one({"_id": ObjectId(doc_id)})
            except Exception:
                # Try as a regular string ID
                document = await db[collection].find_one({"_id": doc_id})
                
            if document:
                document["_id"] = str(document["_id"])
            return document
        else:
            # Use fallback JSON storage
            return _get_document_by_id_in_json(collection, doc_id)
    except Exception as e:
        print(f"Error getting document by ID: {e}")
        # Fallback to local JSON storage
        return _get_document_by_id_in_json(collection, doc_id)

def _get_document_by_id_in_json(collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """Get a document by its ID from JSON file as fallback"""
    fallback_dir = _get_fallback_dir()
    collection_dir = os.path.join(fallback_dir, collection)
    
    if not os.path.exists(collection_dir):
        return None
    
    # Try direct file access first (most efficient)
    file_path = os.path.join(collection_dir, f"{doc_id}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
    
    # If not found, search through all files
    return _find_document_in_json(collection, {"_id": doc_id}) 