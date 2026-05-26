#!/usr/bin/env python3
"""Global Treasury Agent - CLI Entry Point"""

import sys
from pathlib import Path
from config import print_config
from vision import extract_invoice_data
from langgraph_agent import get_agent

def print_welcome():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         🌍 GLOBAL TREASURY AGENT - AI Reconciliation         ║
║                                                              ║
║  Predict MYR amounts or reconcile cross-border payments     ║
╚══════════════════════════════════════════════════════════════╝
    """)

def main():
    print_welcome()
    print_config()
    print("\n" + "="*60)
    
    # Initialize agent
    agent = get_agent(use_llm=False)  # Deterministic mode for MVP
    
    print("\n💡 Examples:")
    print("  • Upload invoice: /path/to/invoice.pdf")
    print("  • Predict: 'Predict USD 10000 with Maybank'")
    print("  • Reconcile: 'I received RM 42900 for invoice INV-123'")
    print("  • Type 'exit' to quit\n")
    
    while True:
        try:
            user_input = input("\n🔹 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Check if user provided a file path
            file_path = None
            ocr_data = None
            
            if Path(user_input).exists():
                file_path = user_input
                print(f"📄 Processing file: {file_path}")
                ocr_data = extract_invoice_data(file_path)
                print(f"✅ OCR extracted: {ocr_data}")
                user_input = "Process this invoice"
            
            # Run agent
            result = agent.run(user_input, file_path, ocr_data)
            
            print(f"\n🤖 Agent: {result['response']}")
            
            # Handle export (simple yes/no)
            if "Would you like to export" in result['response']:
                export_choice = input("🔹 You: ").strip().lower()
                if export_choice in ['yes', 'y']:
                    from tools import export_transaction_report
                    export_result = export_transaction_report.invoke({
                        "transactions": [result.get('data', {})],
                        "report_type": "both"
                    })
                    if export_result.get('success'):
                        print(f"✅ Reports saved to exports/ directory")
                    else:
                        print(f"❌ Export failed: {export_result.get('error')}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()