"""
invoice_manager.py - Core Functions 2 & 3
- Upload invoice to database
- Upload bank statement and match to invoices
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from store_transaction import store_transaction, get_all_transactions
from matching import process_payment_match


# ================= CORE FUNCTION 2: UPLOAD INVOICE =================
def upload_invoice(
    invoice_number: str,
    amount: float,
    currency: str,
    from_company: str,      # Who owes (customer)
    to_company: str,        # Who is owed (you)
    invoice_date: str,
    due_date: str = None,
    file_path: str = None
) -> Dict:
    """
    Store invoice in database.
    Called AFTER OCR extracts invoice data.
    """
    
    # Set default due date if not provided (30 days from invoice date)
    if not due_date:
        try:
            inv_date = datetime.strptime(invoice_date, "%Y-%m-%d")
            due_date = (inv_date + timedelta(days=30)).strftime("%Y-%m-%d")
        except:
            due_date = invoice_date
    
    # Create invoice record
    invoice_data = {
        "id": str(uuid.uuid4())[:8],
        "type": "invoice",
        "invoice_number": invoice_number,
        "amount": amount,
        "currency": currency,
        "from_company": from_company,
        "to_company": to_company,
        "invoice_date": invoice_date,
        "due_date": due_date,
        "remaining_balance": amount,  # Full amount initially
        "status": "PENDING",  # PENDING, PARTIAL, PAID, OVERDUE
        "file_path": file_path,
        "created_at": datetime.now().isoformat()
    }
    
    # Store in database
    result = store_transaction(invoice_data)
    
    return {
        "success": result.get("success", False),
        "invoice_id": invoice_data["id"],
        "invoice_number": invoice_number,
        "status": "RECORDED",
        "message": f"Invoice {invoice_number} recorded. Amount due: {currency} {amount:,.2f}"
    }


# ================= CORE FUNCTION 3: MATCH PAYMENT =================
def match_bank_statement(
    payment_amount: float,
    payment_currency: str,
    payment_date: str,
    from_company: str,
    to_company: str,
    reference: str = None,
    file_path: str = None
) -> Dict:
    """
    Match bank statement payment to outstanding invoices.
    Called AFTER OCR extracts payment data.
    """
    
    # Step 1: Get all unpaid invoices for this customer
    all_transactions = get_all_transactions()
    
    unpaid_invoices = []
    for t in all_transactions:
        if (t.get("type") == "invoice" and 
            t.get("from_company") == from_company and 
            t.get("status") in ["PENDING", "PARTIAL"]):
            unpaid_invoices.append(t)
    
    if not unpaid_invoices:
        # No invoices found - store as unallocated payment
        payment_data = {
            "id": str(uuid.uuid4())[:8],
            "type": "payment",
            "amount": payment_amount,
            "currency": payment_currency,
            "date": payment_date,
            "from_company": from_company,
            "to_company": to_company,
            "reference": reference,
            "file_path": file_path,
            "matched_invoice_id": None,
            "status": "UNMATCHED",
            "created_at": datetime.now().isoformat()
        }
        store_transaction(payment_data)
        
        return {
            "success": False,
            "status": "NO_INVOICES",
            "message": f"No unpaid invoices found for {from_company}. Payment recorded as unallocated.",
            "payment_id": payment_data["id"],
            "suggested_action": "Create invoice for this customer first"
        }
    
    # Step 2: Find best matching invoice
    payment = {
        "amount": payment_amount,
        "currency": payment_currency,
        "date": payment_date,
        "from_company": from_company,
        "to_company": to_company,
        "reference": reference
    }
    
    match_result = process_payment_match(payment, unpaid_invoices)
    
    # Step 3: Store the payment record
    payment_data = {
        "id": str(uuid.uuid4())[:8],
        "type": "payment",
        "amount": payment_amount,
        "currency": payment_currency,
        "date": payment_date,
        "from_company": from_company,
        "to_company": to_company,
        "reference": reference,
        "file_path": file_path,
        "matched_invoice_id": match_result.get("matched_invoice", {}).get("id") if match_result.get("matched_invoice") else None,
        "match_confidence": match_result.get("match_confidence"),
        "action_needed": match_result.get("action_needed"),
        "status": "MATCHED" if match_result.get("matched_invoice") else "UNMATCHED",
        "created_at": datetime.now().isoformat()
    }
    store_transaction(payment_data)
    
    # Step 4: Update invoice if matched
    updated_invoice = None
    if match_result.get("matched_invoice") and match_result.get("action_needed") != "UNMATCHED":
        invoice_id = match_result["matched_invoice"]["id"]
        
        # Find and update the invoice
        for inv in unpaid_invoices:
            if inv.get("id") == invoice_id:
                # Calculate new remaining balance
                paid_amount = min(payment_amount, inv.get("remaining_balance", inv.get("amount", 0)))
                new_remaining = inv.get("remaining_balance", inv.get("amount", 0)) - paid_amount
                
                # Determine new status
                if new_remaining <= 0:
                    new_status = "PAID"
                else:
                    new_status = "PARTIAL"
                
                # Update invoice fields
                inv["remaining_balance"] = max(0, new_remaining)
                inv["status"] = new_status
                inv["last_payment_date"] = datetime.now().isoformat()
                inv["last_payment_amount"] = paid_amount
                
                # IMPORTANT: Also update the original amount if needed
                if "amount" not in inv:
                    inv["amount"] = inv.get("original_amount", paid_amount)
                
                # Save updated invoice back to database
                store_result = store_transaction(inv)
                print(f"DEBUG: Store result for invoice {invoice_id}: {store_result}")
                
                updated_invoice = inv
                break
    
    # Step 5: Return result
    return {
        "success": True,
        "payment_id": payment_data["id"],
        "payment_amount": payment_amount,
        "payment_currency": payment_currency,
        "match_found": match_result.get("matched_invoice") is not None,
        "match_confidence": match_result.get("match_confidence"),
        "confidence_score": match_result.get("confidence_score"),
        "matched_invoice": match_result.get("matched_invoice"),
        "action_needed": match_result.get("action_needed"),
        "message": match_result.get("message"),
        "invoice_updated": updated_invoice is not None,
        "suggested_action": _get_suggested_action(match_result)
    }


def _get_suggested_action(match_result: Dict) -> str:
    """Get suggested next action based on match result"""
    action = match_result.get("action_needed")
    
    if action == "MARK_PAID":
        return "Invoice fully paid. Status updated to PAID."
    elif action == "PARTIAL_PAYMENT":
        return f"Partial payment recorded. Remaining balance updated."
    elif action == "OVERPAYMENT":
        return f"Overpayment detected. Please contact customer for refund."
    else:
        return "No match found. Review payment manually."


# ================= GET ALL INVOICES =================
def get_all_invoices(status: str = None) -> List[Dict]:
    """Get all invoices, optionally filtered by status"""
    all_transactions = get_all_transactions()
    
    invoices = []
    for t in all_transactions:
        if t.get("type") == "invoice":
            if status is None or t.get("status") == status:
                invoices.append(t)
    
    return invoices


# ================= GET ALL PAYMENTS =================
def get_all_payments() -> List[Dict]:
    """Get all payment transactions"""
    all_transactions = get_all_transactions()
    
    payments = []
    for t in all_transactions:
        if t.get("type") == "payment":
            payments.append(t)
    
    return payments