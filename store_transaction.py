from datetime import datetime
import uuid
import json
from pathlib import Path

try:
    from .firebase_client import get_db, is_connected
except ImportError:
    from firebase_client import get_db, is_connected

TRANSACTIONS_COLLECTION = "transactions"
TRAINING_DATA_COLLECTION = "training_data"


def store_transaction(transaction_data: dict) -> dict:
    # Generate transaction ID if not provided
    if "id" not in transaction_data:
        transaction_data["id"] = str(uuid.uuid4())[:8]
    
    # Add timestamp
    transaction_data["timestamp"] = datetime.now().isoformat()
    
    # ALWAYS save locally first (backup)
    local_path = Path("local_transactions.json")
    existing = []
    
    if local_path.exists():
        try:
            with open(local_path, 'r') as f:
                content = f.read().strip()
                if content:
                    existing = json.loads(content)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ Could not read local_transactions.json: {e}")
            existing = []
    
    # Check if this transaction already exists (update)
    found = False
    for i, tx in enumerate(existing):
        if tx.get("id") == transaction_data["id"]:
            existing[i] = transaction_data
            found = True
            break
    
    if not found:
        existing.append(transaction_data)
    
    with open(local_path, 'w') as f:
        json.dump(existing, f, indent=2)
    
    # Try Firebase if available
    firebase_success = False
    firebase_error = None
    
    if is_connected():
        try:
            db = get_db()
            doc_ref = db.collection(TRANSACTIONS_COLLECTION).document(transaction_data["id"])
            doc_ref.set(transaction_data)
            firebase_success = True
            print(f"✅ Saved to Firebase: {transaction_data['id']}")
        except Exception as e:
            firebase_error = str(e)
            print(f"❌ Firebase save failed: {e}")
    else:
        print("⚠️ Firebase not connected, saving only locally")
    
    return {
        "success": True, 
        "firebase_success": firebase_success,
        "firebase_error": firebase_error,
        "transaction_id": transaction_data["id"],
        "timestamp": transaction_data["timestamp"],
        "local_saved": True,
        "message": "Saved locally" + (" + Firebase" if firebase_success else "")
    }


def store_training_data(features: dict, target_markup: float, source_transaction_id: str = None) -> dict:
    training_record = {
        "features": features,
        "target_markup": target_markup,
        "source_transaction_id": source_transaction_id,
        "timestamp": datetime.now().isoformat()
    }
    
    if not is_connected():
        return {
            "success": False,
            "error": "Firebase not connected",
            "local_saved": True
        }
    
    try:
        db = get_db()
        doc_ref = db.collection(TRAINING_DATA_COLLECTION).document()
        doc_ref.set(training_record)
        
        return {
            "success": True,
            "training_data_id": doc_ref.id,
            "timestamp": training_record["timestamp"]
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_all_transactions(limit: int = 100) -> list:
    """
    Retrieve all transactions from Firebase
    
    Args:
        limit: Maximum number of transactions to retrieve
    
    Returns:
        List of transaction dictionaries
    """
    
    if not is_connected():
        # Try to read from local file
        local_path = Path("local_transactions.json")
        if local_path.exists():
            try:
                with open(local_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        return data[:limit]
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ Could not read local_transactions.json: {e}")
        return []
    
    try:
        db = get_db()
        docs = db.collection(TRANSACTIONS_COLLECTION).order_by("timestamp", direction="DESCENDING").limit(limit).stream()
        
        transactions = []
        for doc in docs:
            data = doc.to_dict()
            data["firebase_id"] = doc.id
            transactions.append(data)
        
        return transactions
    
    except Exception as e:
        print(f"Error retrieving transactions: {e}")
        return []


def get_training_data(bank: str = None, currency: str = None, limit: int = 1000) -> list:
    """
    Retrieve training data for ML model training
    
    Args:
        bank: Filter by bank (optional)
        currency: Filter by currency (optional)
        limit: Maximum records to retrieve
    
    Returns:
        List of training records
    """
    
    if not is_connected():
        return []
    
    try:
        db = get_db()
        query = db.collection(TRAINING_DATA_COLLECTION)
        
        if bank:
            query = query.where("features.bank_name", "==", bank)
        if currency:
            query = query.where("features.currency", "==", currency)
        
        docs = query.limit(limit).stream()
        
        training_data = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            training_data.append(data)
        
        return training_data
    
    except Exception as e:
        print(f"Error retrieving training data: {e}")
        return []


def delete_transaction(transaction_id: str) -> dict:
    """
    Delete a transaction from Firebase
    
    Args:
        transaction_id: ID of transaction to delete
    
    Returns:
        dict with success status
    """
    
    if not is_connected():
        return {"success": False, "error": "Firebase not connected"}
    
    try:
        db = get_db()
        db.collection(TRANSACTIONS_COLLECTION).document(transaction_id).delete()
        return {"success": True, "transaction_id": transaction_id}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


# For testing directly
if __name__ == "__main__":
    # Test storing a transaction
    test_transaction = {
        "amount": 10000,
        "currency": "USD",
        "bank": "Maybank",
        "predicted_amount": 42998.97,
        "actual_amount": 42800.00,
        "difference": -198.97,
        "status": "DISCREPANCY",
        "markup_rate": 0.025,
        "market_rate": 4.25,
        "fee_percent": 0.012,
        "fee_fixed": 5.00
    }
    
    result = store_transaction(test_transaction)
    print("Store result:", result)
    
    # Retrieve all transactions
    all_transactions = get_all_transactions()
    print(f"Retrieved {len(all_transactions)} transactions")