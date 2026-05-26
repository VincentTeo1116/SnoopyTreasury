"""
Test Firebase Write - Run this separately
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from firebase_client import initialize_firebase, get_db, is_connected

print("=" * 60)
print("TESTING FIREBASE WRITE")
print("=" * 60)

# Initialize
print("\n1. Initializing Firebase...")
initialize_firebase()

print(f"\n2. Connected: {is_connected()}")

if not is_connected():
    print("❌ Not connected - check serviceAccountKey.json")
    sys.exit(1)

# Get database
db = get_db()
print(f"✅ Database client: {db}")

# Try to write
print("\n3. Attempting to write to Firestore...")

test_data = {
    "test_id": "test_001",
    "message": "This is a test write",
    "timestamp": "2026-05-25"
}

try:
    # Try writing to a test collection
    doc_ref = db.collection("test_collection").document("test_doc")
    doc_ref.set(test_data)
    print("✅ Write successful!")
    
    # Try reading back
    read_data = doc_ref.get()
    if read_data.exists:
        print(f"✅ Read successful: {read_data.to_dict()}")
    
    
except Exception as e:
    print(f"❌ Write failed: {e}")
    print("\nPossible causes:")
    print("1. Firestore API not enabled in Google Cloud Console")
    print("2. Security rules blocking writes")
    print("3. Service account lacks permissions")
    
print("\n" + "=" * 60)