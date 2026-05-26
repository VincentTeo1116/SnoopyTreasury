"""Main Menu System for Treasury Agent"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from vision import process_document
from get_live_rate import get_live_rate
from predict_markup import predict_markup
from fee_calculator import calculate_complete_before, calculate_complete_after
from export_report import generate_report
from store_transaction import store_transaction
from gemini_llm import get_gemini
from invoice_manager import upload_invoice, match_bank_statement, get_all_invoices, get_all_payments

class TreasuryMenu:
    def __init__(self):
        self.gemini = get_gemini()
        self.clear_screen = lambda: os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title):
        print("\n" + "="*70)
        print(f"   {title}")
        print("="*70)
    
    def print_success(self, message):
        print(f"✅ {message}")
    
    def print_error(self, message):
        print(f"❌ {message}")
    
    def print_info(self, message):
        print(f"📌 {message}")
    
    def print_amount(self, amount, currency):
        print(f"💰 Amount: {amount} {currency}")
    
    def show_main_menu(self):
        self.clear_screen()
        print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              🌍 GLOBAL TREASURY AGENT - AI Reconciliation                    ║
║                                                                              ║
║         Process invoices & bank statements with AI-powered OCR              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """)
        print("\n📋 MAIN MENU")
        print("-" * 40)
        print("   [A] Upload INVOICE → Get expected MYR amount")
        print("   [B] Upload BANK STATEMENT → Reconcile payment")
        print("   [C] View transaction history")
        print("   [D] Export all reports")
        print("   [E] Exit")
        print("-" * 40)

    def handle_invoice(self):
        """Option A: Upload invoice → Store in database"""
        self.print_header("💰 UPLOAD INVOICE TO DATABASE")
        
        # Get file path
        file_path = input("\n📁 Enter invoice file path (image or PDF): ").strip().strip('"')
        
        if not Path(file_path).exists():
            self.print_error(f"File not found: {file_path}")
            input("\nPress Enter to continue...")
            return
        
        # Process with OCR
        self.print_info("Processing invoice with OCR...")
        result = process_document(file_path)
        
        if not result or not result.get('success'):
            self.print_error("Failed to process document")
            input("\nPress Enter to continue...")
            return
        
        # Extract data from OCR (now with formatted_amount)
        amount_str = result.get('amount', '0')
        currency = result.get('currency', 'USD')
        company_name = result.get('company_name', '')
        invoice_date = result.get('invoice_date') or datetime.now().strftime("%Y-%m-%d")
        due_date = result.get('due_date')
        formatted_amount = result.get('formatted_amount', 'N/A')
        
        print("\n📊 OCR EXTRACTION RESULTS:")
        if formatted_amount != 'N/A':
            print(f"   Detected: {formatted_amount}")
        print(f"   Amount: {amount_str}")
        print(f"   Currency: {currency}")
        print(f"   Customer/Bank: {company_name}")
        print(f"   Invoice Date: {invoice_date}")
        print(f"   Due Date: {due_date}")
        
        # Allow user to edit/correct
        print("\n✏️ Please confirm or edit the following:")
        invoice_number = input("Invoice Number: ").strip() or f"INV-{datetime.now().strftime('%Y%m%d')}"
        amount = float(input(f"Invoice Amount ({currency}): ") or amount_str)
        
        # Allow currency override
        use_detected = input(f"Use detected currency ({currency})? (y/n): ").lower()
        if use_detected == 'y':
            currency = currency
        else:
            currency = input(f"Enter currency code: ").upper()
        
        from_company = input(f"Customer Name: ") or company_name
        to_company = input(f"Your Company Name: ").strip() or "My Company"
        invoice_date = input(f"Invoice Date (YYYY-MM-DD): ") or invoice_date
        due_date = input(f"Due Date (YYYY-MM-DD, press Enter for 30 days): ") or None
        
        # Upload to database
        self.print_info("Saving invoice to database...")
        upload_result = upload_invoice(
            invoice_number=invoice_number,
            amount=amount,
            currency=currency,
            from_company=from_company,
            to_company=to_company,
            invoice_date=invoice_date,
            due_date=due_date,
            file_path=file_path
        )
        
        if upload_result.get("success"):
            self.print_success(f"Invoice {invoice_number} saved! ID: {upload_result['invoice_id']}")
            print(f"   Status: PENDING")
            print(f"   Amount Due: {currency} {amount:,.2f}")
        else:
            self.print_error(f"Failed to save: {upload_result.get('message')}")
        
        input("\nPress Enter to continue...")
    
    def handle_bank_statement(self):
        """Option B: Upload bank statement → Match payment to invoice"""
        self.print_header("🔍 MATCH PAYMENT TO INVOICE")
        
        # Get file path
        file_path = input("\n📁 Enter bank statement file path (image or PDF): ").strip().strip('"')
        
        if not Path(file_path).exists():
            self.print_error(f"File not found: {file_path}")
            input("\nPress Enter to continue...")
            return
        
        # Process with OCR
        self.print_info("Processing bank statement with OCR...")
        result = process_document(file_path)
        
        if not result:
            self.print_error("Failed to process document")
            input("\nPress Enter to continue...")
            return
        
        # Extract data from OCR
        amount_str = result.get('amount')
        currency = result.get('currency')
        company_name = result.get('company_name')
        payment_date = result.get('invoice_date') or datetime.now().strftime("%Y-%m-%d")
        
        print("\n📊 OCR EXTRACTION RESULTS:")
        print(f"   Payment Amount: {amount_str} {currency}")
        print(f"   From: {company_name}")
        print(f"   Date: {payment_date}")
        
        # Allow user to edit
        print("\n✏️ Please confirm or edit:")
        payment_amount = float(input(f"Payment Amount ({currency}): ") or amount_str)
        payment_currency = input(f"Currency: ").upper() or currency
        from_company = input(f"From Company: ") or company_name
        to_company = input(f"To (Your Company): ").strip() or "My Company"
        payment_date = input(f"Payment Date (YYYY-MM-DD): ") or payment_date
        
        # Show pending invoices for this customer
        from invoice_manager import get_all_invoices
        pending_invoices = [inv for inv in get_all_invoices() if inv.get('from_company') == from_company and inv.get('status') in ['PENDING', 'PARTIAL']]
        
        if pending_invoices:
            print("\n📋 PENDING INVOICES FOR THIS CUSTOMER:")
            for inv in pending_invoices:
                print(f"   - {inv.get('invoice_number')}: {inv.get('currency')} {inv.get('remaining_balance', inv.get('amount')):,.2f} (Status: {inv.get('status')})")
        else:
            print(f"\n⚠️ No pending invoices found for {from_company}")
        
        # Match payment
        self.print_info("\nMatching payment to invoice...")
        match_result = match_bank_statement(
            payment_amount=payment_amount,
            payment_currency=payment_currency,
            payment_date=payment_date,
            from_company=from_company,
            to_company=to_company,
            reference=input("Reference (optional): ").strip() or None,
            file_path=file_path
        )
        
        print("\n" + "="*60)
        print("📊 MATCH RESULT")
        print("="*60)
        print(f"   {match_result.get('message')}")
        print(f"   Match Confidence: {match_result.get('match_confidence', 'N/A')}")
        
        if match_result.get('matched_invoice'):
            inv = match_result['matched_invoice']
            print(f"\n   Matched Invoice: {inv.get('invoice_number')}")
            print(f"   Original Amount: {inv.get('currency')} {inv.get('original_amount'):,.2f}")
            print(f"   Action: {match_result.get('action_needed')}")
        
        # Save to database and export
        if match_result.get('success'):
            export = input("\n📄 Export this report? (y/n): ").lower()
            if export == 'y':
                from export_report import generate_report
                export_result = generate_report([match_result], "both")
                if export_result.get('success'):
                    self.print_success("Report exported to exports/ folder")
        
        input("\nPress Enter to continue...")
    
    def view_history(self):
        """Option C: View all invoices and payments"""
        self.print_header("📜 TRANSACTION HISTORY")
        
        from invoice_manager import get_all_invoices, get_all_payments
        
        # Show invoices
        invoices = get_all_invoices()
        print("\n📄 INVOICES:")
        print("-" * 80)
        print(f"{'#':<5} {'Invoice #':<15} {'Amount':<12} {'Customer':<15} {'Status':<10} {'Balance':<12}")
        print("-" * 80)
        
        for inv in invoices[:20]:
            inv_num = inv.get('invoice_number', 'N/A')[:14]
            amount = f"{inv.get('currency')} {inv.get('amount', 0):,.2f}"
            customer = inv.get('from_company', 'N/A')[:14]
            status = inv.get('status', 'N/A')
            balance = f"{inv.get('currency')} {inv.get('remaining_balance', 0):,.2f}"
            print(f"{inv.get('id', 'N/A')[:4]:<5} {inv_num:<15} {amount:<12} {customer:<15} {status:<10} {balance:<12}")
        
        # Show payments
        payments = get_all_payments()
        print("\n💰 PAYMENTS:")
        print("-" * 80)
        print(f"{'#':<5} {'Amount':<12} {'From':<15} {'Matched To':<15} {'Status':<12}")
        print("-" * 80)
        
        for pay in payments[:20]:
            amount = f"{pay.get('currency')} {pay.get('amount', 0):,.2f}"
            from_comp = pay.get('from_company', 'N/A')[:14]
            matched = pay.get('matched_invoice_id', 'Unmatched')[:14]
            status = pay.get('status', 'N/A')
            print(f"{pay.get('id', 'N/A')[:4]:<5} {amount:<12} {from_comp:<15} {matched:<15} {status:<12}")
        
        if not invoices and not payments:
            self.print_info("No transactions found")
        
        input("\nPress Enter to continue...")
    
    def export_all(self):
        """Option D: Export all reports"""
        self.print_header("📄 EXPORT ALL REPORTS")
        
        from store_transaction import get_all_transactions
        transactions = get_all_transactions(limit=100)
        
        if not transactions:
            self.print_error("No transactions to export")
        else:
            export_result = generate_report(transactions, "both")
            if export_result.get('success'):
                self.print_success(f"Exported {len(transactions)} transactions")
                print(f"   CSV: {export_result['reports'].get('csv', {}).get('filepath', 'N/A')}")
                print(f"   PDF: {export_result['reports'].get('pdf', {}).get('filepath', 'N/A')}")
            else:
                self.print_error(f"Export failed: {export_result.get('error')}")
        
        input("\nPress Enter to continue...")
    
    def run(self):
        """Main loop"""
        while True:
            self.show_main_menu()
            
            choice = input("\n🔹 Select option (A/B/C/D/E): ").upper().strip()
            
            if choice == 'A':
                self.handle_invoice()
            elif choice == 'B':
                self.handle_bank_statement()
            elif choice == 'C':
                self.view_history()
            elif choice == 'D':
                self.export_all()
            elif choice == 'E':
                print("\n👋 Thank you for using Global Treasury Agent!")
                break
            else:
                self.print_error("Invalid option. Please try again.")
                input("\nPress Enter to continue...")

if __name__ == "__main__":
    menu = TreasuryMenu()
    menu.run()