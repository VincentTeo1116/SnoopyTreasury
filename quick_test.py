"""End-to-end test: Real OCR → Prediction → Reconciliation"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from vision import extract_invoice_data
from get_live_rate import get_live_rate
from predict_markup import predict_markup
from fee_calculator import calculate_complete_before, calculate_complete_after
from export_report import generate_report
from store_transaction import store_transaction

def e2e_test(image_path):
    """Complete end-to-end test with real image"""
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║              🚀 END-TO-END TEST: OCR → PREDICTION → RECONCILIATION           ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: OCR Extraction
    print("\n📌 STEP 1: OCR EXTRACTION")
    print("-" * 50)
    ocr_result = extract_invoice_data(image_path)
    
    if not ocr_result.get('success'):
        print("❌ OCR failed")
        return
    
    amount = ocr_result.get('amount')
    currency = ocr_result.get('currency')
    bank = ocr_result.get('bank')
    date = ocr_result.get('date')
    
    print(f"✅ Extracted: {amount} {currency} via {bank} (Date: {date})")
    
    if not all([amount, currency, bank]):
        print("❌ Missing required data")
        return
    
    # Step 2: Prediction
    print("\n📌 STEP 2: PREDICTION")
    print("-" * 50)
    
    rate_data = get_live_rate(currency)
    market_rate = rate_data.get('rate', 4.25)
    
    markup_data = predict_markup(bank, currency, amount)
    markup = markup_data.get('predicted_markup', 0.025)
    
    prediction = calculate_complete_before(
        invoice_amount=amount,
        currency=currency,
        bank=bank,
        markup=markup,
        market_rate=market_rate
    )
    
    print(f"✅ Expected amount: RM {prediction['final_amount']:,.2f}")
    
    # Step 3: Ask for actual received amount
    print("\n📌 STEP 3: RECONCILIATION")
    print("-" * 50)
    
    # Simulate or ask for actual amount
    actual = input(f"Enter actual MYR received (or press Enter to use RM {prediction['final_amount']:,.2f}): ")
    
    if actual.strip():
        actual_received = float(actual)
    else:
        actual_received = prediction['final_amount']
    
    reconciliation = calculate_complete_after(
        invoice_amount=amount,
        currency=currency,
        bank=bank,
        actual_received_rm=actual_received,
        market_rate=market_rate
    )
    
    diff_percent = reconciliation['difference_percent']
    if abs(diff_percent) < 0.5:
        print(f"✅ MATCHED within tolerance")
    else:
        print(f"⚠️ DISCREPANCY: {diff_percent}%")
    
    print(f"   Difference: RM {reconciliation['difference']:,.2f}")
    
    # Step 4: Save to database
    print("\n📌 STEP 4: SAVE TRANSACTION")
    print("-" * 50)
    
    transaction = {
        "amount": amount,
        "currency": currency,
        "bank": bank,
        "date": date,
        "predicted_amount": prediction['final_amount'],
        "actual_received": actual_received,
        "difference": reconciliation['difference'],
        "market_rate": market_rate,
        "bank_rate": prediction['bank_rate'],
        "total_fees": prediction['fees']['total']
    }
    
    save_result = store_transaction(transaction)
    if save_result.get('success'):
        print(f"✅ Saved with ID: {save_result.get('transaction_id')}")
    
    # Step 5: Export report
    print("\n📌 STEP 5: EXPORT REPORT")
    print("-" * 50)
    
    export_result = generate_report([transaction], "both")
    if export_result.get('success'):
        print(f"✅ Report exported to exports/ folder")
    
    # Summary
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY")
    print("="*70)
    print(f"   Invoice: {amount:,.2f} {currency}")
    print(f"   Bank: {bank}")
    print(f"   Expected: RM {prediction['final_amount']:,.2f}")
    print(f"   Received: RM {actual_received:,.2f}")
    print(f"   Difference: RM {reconciliation['difference']:,.2f} ({diff_percent}%)")
    print("="*70)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python e2e_test_with_ocr.py <image_path>")
        print("Example: python e2e_test_with_ocr.py invoice.jpg")
        sys.exit(1)
    
    e2e_test(sys.argv[1])