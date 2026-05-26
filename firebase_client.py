import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import json

load_dotenv()

# Global variables
_db = None
_initialized = False


def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    global _initialized, _db
    
    # If already initialized, just return
    if _initialized:
        return True
    
    # If Firebase app already exists (from elsewhere), use it
    if firebase_admin._apps:
        print("✅ Firebase app already exists, using existing instance")
        _db = firestore.client()
        _initialized = True
        return True
    
    try:
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "serviceAccountKey.json")
        
        print(f"🔍 Looking for service account at: {service_account_path}")
        print(f"📁 Current directory: {os.getcwd()}")
        
        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            _db = firestore.client()
            _initialized = True
            print("✅ Firebase initialized successfully")
            
            # Test connection
            try:
                test_ref = _db.collection("_test").document("connection_test")
                test_ref.set({"timestamp": "test"}, merge=True)
                print("✅ Firebase write test successful!")
                test_ref.delete()
            except Exception as e:
                print(f"⚠️ Firebase write test failed: {e}")
            
            return True
        else:
            print(f"❌ Service account file not found: {service_account_path}")
            return False
        
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return False


def get_db():
    """Get Firestore database instance"""
    global _db
    if _db is None:
        initialize_firebase()
    return _db


def is_connected():
    """Check if Firebase is connected"""
    return _initialized and _db is not None