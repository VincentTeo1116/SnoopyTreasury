"""LangChain tools wrapping your existing modules"""
from langchain_core.tools import tool
from typing import Optional
import sys
from pathlib import Path

# Add current directory to path to fix imports
sys.path.insert(0, str(Path(__file__).parent))

# Import your existing modules (absolute imports, no dots)
from get_live_rate import get_live_rate, get_historical_rate
from predict_markup import predict_markup
from fee_calculator import calculate_complete_before, calculate_complete_after
from export_report import generate_report
from store_transaction import store_transaction
from matching import process_payment_match, update_balances_after_match
from config import SUPPORTED_BANKS

@tool
def fetch_current_rate(currency: str) -> dict:
    """
    Fetch current exchange rate from USD/currency to MYR.
    
    Args:
        currency: Source currency code (USD, EUR, GBP, etc.)
    """
    return get_live_rate(currency)

@tool
def fetch_historical_rate(currency: str, date: str) -> dict:
    """
    Fetch historical exchange rate for a specific date.
    
    Args:
        currency: Source currency code
        date: Date in YYYY-MM-DD format
    """
    return get_live_rate(currency, date)

@tool
def predict_bank_markup(bank: str, currency: str, amount: float = None) -> dict:
    """
    Predict the bank's markup percentage for currency conversion.
    
    Args:
        bank: Bank name (Maybank, CIMB, Public Bank, RHB, Hong Leong)
        currency: Currency being converted
        amount: Optional invoice amount for volume discount
    """
    return predict_markup(bank, currency, amount)

@tool
def calculate_final_amount(
    invoice_amount: float,
    currency: str,
    bank: str,
    market_rate: float,
    markup: float
) -> dict:
    """
    Calculate final MYR amount after bank fees and markup.
    
    Args:
        invoice_amount: Amount in source currency
        currency: Source currency code
        bank: Bank name
        market_rate: Current market exchange rate
        markup: Bank's markup percentage (0.025 = 2.5%)
    """
    return calculate_complete_before(invoice_amount, currency, bank, markup, market_rate)

@tool
def reconcile_payment(
    invoice_amount: float,
    currency: str,
    bank: str,
    actual_received_rm: float,
    market_rate: float
) -> dict:
    """
    Reconcile an actual received payment against expected amount.
    
    Args:
        invoice_amount: Amount in source currency
        currency: Source currency code
        bank: Bank name
        actual_received_rm: Actual MYR amount received
        market_rate: Market rate on payment date
    """
    return calculate_complete_after(invoice_amount, currency, bank, actual_received_rm, market_rate)

@tool
def save_transaction_to_db(transaction_data: dict) -> dict:
    """
    Save transaction record to Firebase.
    
    Args:
        transaction_data: Dictionary with transaction details
    """
    return store_transaction(transaction_data)

@tool
def export_transaction_report(transactions: list, report_type: str = "both") -> dict:
    """
    Export transaction data to CSV and/or PDF.
    
    Args:
        transactions: List of transaction dictionaries
        report_type: "csv", "pdf", or "both"
    """
    return generate_report(transactions, report_type)

@tool
def get_supported_banks() -> list:
    """Return list of supported banks"""
    return SUPPORTED_BANKS

@tool
def match_payment_to_invoice(
    payment_amount: float,
    payment_currency: str,
    payment_date: str,
    from_company: str,
    invoices: list
) -> dict:
    """
    Match a bank statement payment to outstanding invoices.
    
    Args:
        payment_amount: Amount received
        payment_currency: Currency code (USD, MYR, etc.)
        payment_date: Payment date in YYYY-MM-DD
        from_company: Who sent the payment
        invoices: List of unpaid invoices from database
    """
    payment = {
        "amount": payment_amount,
        "currency": payment_currency,
        "date": payment_date,
        "from_company": from_company
    }
    
    result = process_payment_match(payment, invoices)
    return result