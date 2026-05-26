import json
from typing import Dict, Optional

# Bank fee configuration
BANK_FEES = {
    "Maybank": {
        "USD": 10.00, 
        "EUR": 10.00,
        "GBP": 10.00,
        "SGD": 10.00,
        "MYR": 10.00,
        "default": 10.00
    },
    "CIMB": {
        "USD": 10.00,
        "EUR": 10.00,
        "GBP": 10.00,
        "SGD": 10.00,
        "MYR": 10.00,
        "default": 10.00
    },
    "Public Bank": {
        "USD": 30.00,
        "SGD": 10.00,
        "EUR": 30.00,
        "GBP": 30.00,
        "MYR": 30.00,
        "default": 30.00
    },
    "RHB": {
        "USD": 20.00,
        "EUR": 20.00,
        "GBP": 20.00,
        "SGD": 20.00,
        "MYR": 20.00,
        "default": 20.00
    },
    "Hong Leong": {
        "USD": 30.00,
        "EUR": 30.00,
        "GBP": 30.00,
        "SGD": 30.00,
        "MYR": 30.00,
        "default": 30.00
    }
}

# Special case: Hong Leong small amount
HONG_LEONG_SMALL_THRESHOLD = 10.00
HONG_LEONG_SMALL_FEE = 10.00

# Default fee (if bank not found)
DEFAULT_FEE = 10.00


def get_bank_fee(bank: str, currency: str = "USD", amount_rm: float = None) -> float:

    bank_config = BANK_FEES.get(bank, {})
    
    # Hong Leong special: small amounts get lower fee
    if bank == "Hong Leong" and amount_rm and amount_rm <= HONG_LEONG_SMALL_THRESHOLD:
        return HONG_LEONG_SMALL_FEE
    
    # Get fee for specific currency
    fee = bank_config.get(currency, bank_config.get("default", DEFAULT_FEE))
    
    return fee


def calculate_fees_before(amount_rm: float, bank: str, currency: str = "USD") -> dict:

    # Get fixed fee
    fixed_fee = get_bank_fee(bank, currency, amount_rm)
    
    return {
        "percent": 0.0,  # No percentage
        "percent_rate": "0%",
        "percent_amount": 0.0,
        "fixed": fixed_fee,
        "total": fixed_fee,
        "bank": bank,
        "currency": currency,
        "calculation_type": "before"
    }


def calculate_fees_after(amount_received_rm: float, bank: str, currency: str = "USD") -> dict:
    
    fixed_fee = get_bank_fee(bank, currency, amount_received_rm)
    
    # With fixed fee only, amount before fees is simply received + fee
    amount_before_fees = amount_received_rm + fixed_fee
    total_fees = fixed_fee
    
    # Calculate effective fee percent (for display only)
    effective_percent = total_fees / amount_received_rm if amount_received_rm > 0 else 0
    
    return {
        "percent": 0.0,
        "percent_rate": "0%",
        "percent_amount": 0.0,
        "fixed": fixed_fee,
        "total": total_fees,
        "estimated_amount_before_fees": round(amount_before_fees, 2),
        "effective_percent": round(effective_percent, 4),
        "effective_percent_rate": f"{effective_percent * 100:.1f}%",
        "bank": bank,
        "currency": currency,
        "calculation_type": "after"
    }


def calculate_complete_before(
    invoice_amount: float, 
    currency: str, 
    bank: str, 
    markup: float,
    market_rate: float
) -> dict:
       
    # Step 1: Apply markup to get bank rate
    bank_rate = market_rate * (1 + markup)
    
    # Step 2: Convert invoice amount to RM before fees
    amount_before_fees = invoice_amount * bank_rate
    
    # Step 3: Calculate fixed fees
    fees = calculate_fees_before(amount_before_fees, bank, currency)
    
    # Step 4: Calculate final amount
    final_amount = amount_before_fees - fees["total"]
    
    return {
        "invoice_amount": invoice_amount,
        "currency": currency,
        "bank": bank,
        "market_rate": round(market_rate, 4),
        "markup": round(markup, 4),
        "bank_rate": round(bank_rate, 4),
        "amount_before_fees": round(amount_before_fees, 2),
        "fees": fees,
        "final_amount": round(final_amount, 2),
        "calculation_type": "complete_before"
    }


def calculate_complete_after(
    invoice_amount: float,
    currency: str,
    bank: str,
    actual_received_rm: float,
    market_rate: float
) -> dict:

    # Step 1: Calculate fees (fixed only)
    fees_actual = calculate_fees_after(actual_received_rm, bank, currency)
    amount_before_fees_actual = fees_actual["estimated_amount_before_fees"]
    
    # Step 2: Calculate actual bank rate
    actual_bank_rate = amount_before_fees_actual / invoice_amount
    
    # Step 3: Calculate actual markup
    actual_markup = (actual_bank_rate / market_rate) - 1
    
    # Step 4: Calculate expected amount
    expected_bank_rate = market_rate * (1 + 0.025)
    expected_amount_before_fees = invoice_amount * expected_bank_rate
    expected_fees = calculate_fees_before(expected_amount_before_fees, bank, currency)
    expected_amount = expected_amount_before_fees - expected_fees["total"]
    
    # Step 5: Calculate discrepancy
    difference = actual_received_rm - expected_amount
    
    return {
        "invoice_amount": invoice_amount,
        "currency": currency,
        "bank": bank,
        "market_rate": round(market_rate, 4),
        "actual_received": round(actual_received_rm, 2),
        "expected_amount": round(expected_amount, 2),
        "actual_bank_rate": round(actual_bank_rate, 4),
        "actual_markup": round(actual_markup, 4),
        "actual_markup_percent": round(actual_markup * 100, 2),
        "fees_charged": fees_actual,
        "difference": round(difference, 2),
        "difference_percent": round((difference / expected_amount) * 100 if expected_amount > 0 else 0, 2),
        "calculation_type": "complete_after"
    }

def get_bank_fee_summary() -> dict:
    """Return summary of all bank fees for display"""
    return {
        "Maybank": {"fee": "RM 10 (all currencies)"},
        "CIMB": {"fee": "RM 10 (all currencies)"},
        "Public Bank": {"fee": "RM 30 (USD/EUR/GBP/MYR), RM 10 (SGD)"},
        "RHB": {"fee": "RM 20 (all currencies)"},
        "Hong Leong": {"fee": "RM 30 (normal), RM 10 (amount under RM 10)"}
    }
