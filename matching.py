"""
matching.py - Bank Statement to Invoice Matching
Matches payments to invoices, handles partial payments
"""

from datetime import datetime
from typing import List, Dict, Optional
import json


def _determine_match_type(payment_amount: float, invoice: Dict) -> str:
    """Determine if payment is full, partial, or overpayment"""
    expected = invoice.get('remaining_balance', invoice.get('amount', 0))
    
    if abs(payment_amount - expected) < 1.0:
        return "FULL"
    elif payment_amount < expected:
        return "PARTIAL"
    else:
        return "OVERPAYMENT"


def find_best_invoice_match(
    payment_amount: float,
    payment_currency: str,
    payment_date: str,
    from_company: str,
    invoices: List[Dict]
) -> Dict:
    """
    Find the best matching invoice for a payment.
    """
    best_match = None
    best_score = 0
    
    for invoice in invoices:
        score = 0
        
        # Check company match (most important)
        if invoice.get('from_company') == from_company:
            score += 50
        
        # Check amount match (within tolerance)
        expected_amount = invoice.get('remaining_balance', invoice.get('amount'))
        if expected_amount:
            diff_percent = abs(payment_amount - expected_amount) / expected_amount if expected_amount > 0 else 1
            if diff_percent < 0.01:  # Within 1%
                score += 40
            elif diff_percent < 0.05:  # Within 5%
                score += 20
            elif diff_percent < 0.10:  # Within 10%
                score += 10
        
        # Check date proximity
        invoice_date = invoice.get('due_date') or invoice.get('invoice_date')
        if invoice_date and payment_date:
            try:
                date_diff = abs(
                    datetime.strptime(payment_date, "%Y-%m-%d") - 
                    datetime.strptime(invoice_date, "%Y-%m-%d")
                ).days
                if date_diff < 7:
                    score += 15
                elif date_diff < 30:
                    score += 5
            except:
                pass
        
        # Currency match
        if invoice.get('currency') == payment_currency:
            score += 10
        
        if score > best_score:
            best_score = score
            best_match = invoice
    
    match_type = _determine_match_type(payment_amount, best_match) if best_match else None
    
    return {
        "best_match": best_match,
        "confidence": best_score,
        "confidence_level": "HIGH" if best_score >= 70 else "MEDIUM" if best_score >= 40 else "LOW",
        "match_type": match_type
    }


def process_payment_match(
    payment: Dict,
    invoices: List[Dict],
    tolerance_percent: float = 0.005
) -> Dict:
    """
    Main function to process a bank statement payment against invoices.
    """
    
    # Step 1: Find best matching invoice
    match_result = find_best_invoice_match(
        payment_amount=payment['amount'],
        payment_currency=payment['currency'],
        payment_date=payment['date'],
        from_company=payment['from_company'],
        invoices=invoices
    )
    
    result = {
        "payment_id": payment.get('id'),
        "payment_amount": payment['amount'],
        "payment_currency": payment['currency'],
        "payment_date": payment['date'],
        "from_company": payment['from_company'],
        "matched_invoice": None,
        "match_confidence": match_result['confidence_level'],
        "confidence_score": match_result['confidence'],
        "action_needed": None,
        "remaining_unallocated": payment['amount']
    }
    
    if match_result['best_match'] and match_result['confidence'] >= 40:
        invoice = match_result['best_match']
        expected = invoice.get('remaining_balance', invoice.get('amount', 0))
        
        result['matched_invoice'] = {
            "id": invoice.get('id'),
            "invoice_number": invoice.get('invoice_number'),
            "amount": expected,
            "remaining_before": expected,
            "original_amount": invoice.get('amount'),
            "currency": invoice.get('currency')
        }
        
        # Calculate new remaining balance
        new_remaining = expected - payment['amount']
        
        if match_result['match_type'] == "FULL":
            result['action_needed'] = "MARK_PAID"
            result['remaining_unallocated'] = 0
            result['message'] = f"Payment fully matched invoice {invoice.get('id')}"
            result['invoice_remaining_after'] = 0
            
        elif match_result['match_type'] == "PARTIAL":
            result['action_needed'] = "PARTIAL_PAYMENT"
            result['remaining_unallocated'] = 0
            result['message'] = f"⚠️ Partial payment of {payment['currency']} {payment['amount']:.2f} applied to invoice {invoice.get('id')}. Remaining: {invoice.get('currency')} {new_remaining:.2f}"
            result['invoice_remaining_after'] = max(0, new_remaining)
            
        else:  # OVERPAYMENT
            result['action_needed'] = "OVERPAYMENT"
            result['remaining_unallocated'] = payment['amount'] - expected
            result['message'] = f"⚠️ Overpayment of {payment['currency']} {result['remaining_unallocated']:.2f} for invoice {invoice.get('id')}"
            result['invoice_remaining_after'] = 0
        
    else:
        result['action_needed'] = "UNMATCHED"
        result['message'] = f"❌ No matching invoice found for payment of {payment['currency']} {payment['amount']:.2f} from {payment['from_company']}"
    
    return result


def update_balances_after_match(match_result: Dict):
    """
    Update invoice and company balances after payment matching.
    Returns the updated invoice data.
    """
    
    if not match_result.get('matched_invoice'):
        return {"success": False, "message": "No match to update"}
    
    invoice_id = match_result['matched_invoice']['id']
    new_remaining = match_result.get('invoice_remaining_after', 0)
    
    # Determine new status
    if match_result['action_needed'] == "MARK_PAID":
        status = "PAID"
    elif match_result['action_needed'] == "PARTIAL_PAYMENT":
        status = "PARTIAL"
    else:
        status = "OVERPAID"
    
    return {
        "success": True,
        "invoice_id": invoice_id,
        "new_status": status,
        "remaining_balance": new_remaining,
        "action_needed": match_result['action_needed']
    }
