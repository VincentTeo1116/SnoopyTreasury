
from typing import TypedDict, Optional, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
import json
from datetime import datetime

# Fix imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from tools import (
    fetch_current_rate, fetch_historical_rate, predict_bank_markup,
    calculate_final_amount, reconcile_payment, save_transaction_to_db,
    export_transaction_report, get_supported_banks
)

from config import MATCH_TOLERANCE_PERCENT, MAX_CLARIFICATION_ATTEMPTS, SUPPORTED_BANKS

class AgentState(TypedDict):
    # User input
    user_input: str
    file_path: Optional[str]
    
    # OCR extracted data
    ocr_data: dict
    extracted_amount: Optional[float]
    extracted_currency: Optional[str]
    extracted_bank: Optional[str]
    extracted_date: Optional[str]
    
    # Agent state
    missing_fields: list
    clarification_count: int
    intent: Optional[Literal["BEFORE", "AFTER"]]
    
    # Calculation data (BEFORE)
    market_rate: Optional[float]
    predicted_markup: Optional[float]
    predicted_final_amount: Optional[float]
    
    # Reconciliation data (AFTER)
    actual_received_rm: Optional[float]
    payment_date: Optional[str]
    reconciliation_result: Optional[dict]
    
    # Output
    response_message: str
    saved_transaction_id: Optional[str]
    report_paths: Optional[dict]

class TreasuryAgent:
    def __init__(self, use_llm=False, llm=None):
        self.use_llm = use_llm
        self.llm = llm
        self.supported_banks = SUPPORTED_BANKS
        self.build_graph()
    
    def build_graph(self):
        """Build the LangGraph state machine"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("check_ocr_data", self.check_ocr_data)
        workflow.add_node("ask_missing_info", self.ask_missing_info)
        workflow.add_node("determine_intent", self.determine_intent)
        workflow.add_node("ask_intent", self.ask_intent)
        workflow.add_node("process_before", self.process_before)
        workflow.add_node("process_after", self.process_after)
        workflow.add_node("offer_export", self.offer_export)
        workflow.add_node("save_to_db", self.save_to_db)
        workflow.add_node("format_response", self.format_response)
        
        # Set entry point
        workflow.set_entry_point("check_ocr_data")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "check_ocr_data",
            self.route_after_check,
            {
                "complete": "determine_intent",
                "incomplete": "ask_missing_info"
            }
        )
        
        workflow.add_edge("ask_missing_info", "check_ocr_data")  # Loop back
        
        workflow.add_conditional_edges(
            "determine_intent",
            self.route_after_intent,
            {
                "before": "process_before",
                "after": "process_after",
                "ask": "ask_intent"
            }
        )
        
        workflow.add_edge("ask_intent", "determine_intent")  # Loop back
        
        workflow.add_edge("process_before", "offer_export")
        workflow.add_edge("process_after", "offer_export")
        workflow.add_edge("offer_export", "save_to_db")
        workflow.add_edge("save_to_db", "format_response")
        workflow.add_edge("format_response", END)
        
        self.graph = workflow.compile()

        def check_ocr_data(self, state: AgentState) -> AgentState:
            """Check what data was extracted from OCR"""
            ocr = state.get("ocr_data", {})
            
            missing = []
            
            # Check for amount (could be string or float)
            amount = ocr.get("amount")
            if amount is None or amount == "N/A" or amount == 0:
                missing.append("amount")
            else:
                # Convert to float if it's a string
                try:
                    state["extracted_amount"] = float(amount) if amount != "N/A" else None
                except:
                    state["extracted_amount"] = None
                    missing.append("amount")
            
            # Check currency
            currency = ocr.get("currency")
            if currency is None or currency == "N/A":
                missing.append("currency")
            else:
                state["extracted_currency"] = currency
            
            # Check bank
            bank = ocr.get("bank_name") or ocr.get("bank")
            if bank is None or bank == "Not Specified" or bank == "N/A":
                missing.append("bank")
            else:
                state["extracted_bank"] = bank
            
            state["extracted_date"] = ocr.get("invoice_date") or ocr.get("date")
            state["missing_fields"] = missing
            
            # Store formatted amount if available
            if ocr.get("formatted_amount"):
                state["formatted_amount"] = ocr.get("formatted_amount")
            
            return state        
    
    def route_after_check(self, state: AgentState) -> str:
        """Route based on whether data is complete"""
        if state["missing_fields"]:
            return "incomplete"
        return "complete"
    
    def ask_missing_info(self, state: AgentState) -> AgentState:
        """Ask user for missing information"""
        missing = state["missing_fields"]
        
        questions = []
        if "amount" in missing:
            questions.append("What is the invoice amount?")
        if "currency" in missing:
            questions.append(f"What currency? (USD, MYR, EUR, GBP, SGD)")
        if "bank" in missing:
            banks_str = ", ".join(self.supported_banks)
            questions.append(f"Which bank? ({banks_str})")
        
        state["response_message"] = f"📋 Missing information:\n" + "\n".join(f"  • {q}" for q in questions)
        state["clarification_count"] = state.get("clarification_count", 0) + 1
        
        return state
    
    def determine_intent(self, state: AgentState) -> AgentState:
        """Determine if user wants BEFORE or AFTER"""
        user_input = state.get("user_input", "").lower()
        
        # Check for explicit keywords
        if any(word in user_input for word in ["predict", "estimate", "before", "what will i get", "how much"]):
            state["intent"] = "BEFORE"
        elif any(word in user_input for word in ["reconcile", "after", "check", "verify", "already received", "got"]):
            state["intent"] = "AFTER"
        else:
            state["intent"] = None
        
        return state
    
    def route_after_intent(self, state: AgentState) -> str:
        """Route based on intent detection"""
        if state["intent"] == "BEFORE":
            return "before"
        elif state["intent"] == "AFTER":
            return "after"
        else:
            return "ask"
    
    def ask_intent(self, state: AgentState) -> AgentState:
        """Ask user whether BEFORE or AFTER scenario"""
        state["response_message"] = """
📊 What would you like me to do?

1. PREDICT (BEFORE payment) - Estimate how much MYR you'll receive
2. RECONCILE (AFTER payment) - Check if amount received is correct

Please type 'predict' or 'reconcile'
"""
        return state
    
    def process_before(self, state: AgentState) -> AgentState:
        """Handle BEFORE scenario: predict final amount"""
        amount = state["extracted_amount"]
        currency = state["extracted_currency"]
        bank = state["extracted_bank"]
        
        # Fetch market rate
        rate_data = fetch_current_rate.invoke({"currency": currency})
        market_rate = rate_data.get("rate", 4.25)
        
        # Predict markup
        markup_data = predict_bank_markup.invoke({
            "bank": bank,
            "currency": currency,
            "amount": amount
        })
        predicted_markup = markup_data.get("predicted_markup", 0.025)
        
        # Calculate final amount
        calculation = calculate_final_amount.invoke({
            "invoice_amount": amount,
            "currency": currency,
            "bank": bank,
            "market_rate": market_rate,
            "markup": predicted_markup
        })
        
        state["market_rate"] = market_rate
        state["predicted_markup"] = predicted_markup
        state["predicted_final_amount"] = calculation.get("final_amount")
        
        # Build response
        state["response_message"] = f"""
💰 PREDICTION FOR {amount} {currency} → MYR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏦 Bank: {bank}
📈 Market rate: 1 {currency} = RM {market_rate:.4f}
💹 Bank markup: {predicted_markup*100:.2f}%
💱 Bank rate: RM {calculation['bank_rate']:.4f}

📊 Fee breakdown:
   • {calculation['fees']['percent_rate']} fee: RM {calculation['fees']['percent_amount']:.2f}
   • Fixed fee: RM {calculation['fees']['fixed']:.2f}
   • Total fees: RM {calculation['fees']['total']:.2f}

✨ FINAL EXPECTED AMOUNT: RM {calculation['final_amount']:,.2f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Store for potential export
        state["calculation_result"] = calculation
        
        return state
    
    def process_after(self, state: AgentState) -> AgentState:
        """Handle AFTER scenario: reconcile payment"""
        amount = state["extracted_amount"]
        currency = state["extracted_currency"]
        bank = state["extracted_bank"]
        
        # Check if user provided actual received amount
        user_input = state.get("user_input", "")
        
        # Try to extract actual amount from user input
        import re
        match = re.search(r'(\d+[,.]?\d*)', user_input)
        if match:
            actual_str = match.group(1).replace(',', '')
            state["actual_received_rm"] = float(actual_str)
        else:
            # Need to ask
            state["response_message"] = f"How much MYR did you actually receive for {amount} {currency}?"
            return state
        
        # Get payment date (use extracted date or today)
        payment_date = state.get("extracted_date") or datetime.now().strftime("%Y-%m-%d")
        
        # Fetch historical rate
        rate_data = fetch_historical_rate.invoke({
            "currency": currency,
            "date": payment_date
        })
        market_rate = rate_data.get("rate", 4.25)
        
        # Reconcile
        reconciliation = reconcile_payment.invoke({
            "invoice_amount": amount,
            "currency": currency,
            "bank": bank,
            "actual_received_rm": state["actual_received_rm"],
            "market_rate": market_rate
        })
        
        state["reconciliation_result"] = reconciliation
        state["market_rate"] = market_rate
        
        # Build response
        difference = reconciliation.get("difference", 0)
        if abs(difference) < reconciliation.get("expected_amount", 1) * MATCH_TOLERANCE_PERCENT:
            status = "✅ MATCHED"
        else:
            status = "⚠️ DISCREPANCY"
        
        state["response_message"] = f"""
🔍 RECONCILIATION RESULT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: {status}
Invoice: {amount} {currency} via {bank}
Payment date: {payment_date}

Expected amount: RM {reconciliation['expected_amount']:,.2f}
Actual received: RM {reconciliation['actual_received']:,.2f}
Difference: RM {difference:,.2f} ({reconciliation.get('difference_percent', 0)}%)

📊 Actual bank rate: RM {reconciliation['actual_bank_rate']:.4f}
📊 Actual markup: {reconciliation.get('actual_markup_percent', 0)}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        return state
    
    def offer_export(self, state: AgentState) -> AgentState:
        """Offer to export report"""
        state["response_message"] += "\n\n📄 Would you like to export this as a report? (yes/no)"
        return state
    
    def save_to_db(self, state: AgentState) -> AgentState:
        """Save transaction to Firebase"""
        # Create transaction record
        transaction = {
            "amount": state.get("extracted_amount"),
            "currency": state.get("extracted_currency"),
            "bank": state.get("extracted_bank"),
            "intent": state.get("intent"),
            "timestamp": datetime.now().isoformat()
        }
        
        if state.get("predicted_final_amount"):
            transaction["predicted_amount"] = state["predicted_final_amount"]
            transaction["market_rate"] = state.get("market_rate")
            transaction["predicted_markup"] = state.get("predicted_markup")
        
        if state.get("reconciliation_result"):
            transaction.update(state["reconciliation_result"])
        
        # Save
        result = save_transaction_to_db.invoke({"transaction_data": transaction})
        
        if result.get("success"):
            state["saved_transaction_id"] = result.get("transaction_id")
        
        return state
    
    def format_response(self, state: AgentState) -> AgentState:
        """Final formatting of response"""
        # Add save confirmation if applicable
        if state.get("saved_transaction_id"):
            state["response_message"] += f"\n\n💾 Saved to database (ID: {state['saved_transaction_id']})"
        
        return state
    
    def run(self, user_input: str, file_path: str = None, ocr_data: dict = None) -> dict:
        """Run the agent with user input"""
        initial_state = AgentState(
            user_input=user_input,
            file_path=file_path,
            ocr_data=ocr_data or {},
            extracted_amount=None,
            extracted_currency=None,
            extracted_bank=None,
            extracted_date=None,
            missing_fields=[],
            clarification_count=0,
            intent=None,
            market_rate=None,
            predicted_markup=None,
            predicted_final_amount=None,
            actual_received_rm=None,
            payment_date=None,
            reconciliation_result=None,
            response_message="",
            saved_transaction_id=None,
            report_paths=None
        )
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return {
            "response": final_state["response_message"],
            "transaction_id": final_state.get("saved_transaction_id"),
            "data": final_state
        }

# Singleton
_agent = None

def get_agent(use_llm=False, llm=None):
    global _agent
    if _agent is None:
        _agent = TreasuryAgent(use_llm=use_llm, llm=llm)
    return _agent