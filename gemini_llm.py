"""Gemini LLM Integration for Treasury Agent"""

import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
try:
    import streamlit as st
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
except Exception:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class GeminiHandler:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-3.6-flash')

    def explain_prediction(self, amount: float, currency: str, bank: str, 
                          market_rate: float, markup: float, final_amount: float) -> str:
        """Generate human-friendly explanation of prediction"""
        
        prompt = f"""
        You are a treasury assistant explaining currency conversion to an SME business owner.
        
        Convert this technical data into a simple, friendly explanation:
        
        Invoice: {amount} {currency}
        Bank: {bank}
        Market rate: 1 {currency} = RM {market_rate:.4f}
        Bank markup: {markup*100:.2f}%
        Final amount after fees: RM {final_amount:,.2f}
        
        Write a short paragraph (2-3 sentences) explaining what this means for the business owner.
        Be helpful and clear, avoid jargon.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Based on current rates, your {amount} {currency} invoice via {bank} will become approximately RM {final_amount:,.2f} after bank fees and markup."
    
    def explain_discrepancy(self, expected: float, actual: float, 
                           difference: float, percent: float) -> str:
        """Generate explanation for payment discrepancy"""
        
        prompt = f"""
        You are a treasury assistant explaining a payment discrepancy.
        
        Expected amount: RM {expected:,.2f}
        Actual received: RM {actual:,.2f}
        Difference: RM {difference:,.2f} ({percent}%)
        
        Write a short paragraph explaining:
        1. Whether this is a significant discrepancy
        2. Possible reasons (exchange rate fluctuations, bank fees, timing)
        3. What the business owner should do next
        
        Keep it helpful and actionable (2-3 sentences).
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            if abs(percent) < 1:
                return f"Good news! The payment of RM {actual:,.2f} is within normal range of the expected RM {expected:,.2f}. The small difference is likely due to daily exchange rate fluctuations."
            else:
                return f"Alert: There's a {percent}% difference (RM {difference:,.2f}) between expected and received amount. Please check the exchange rate applied by your bank or verify if any additional fees were charged."
    
    def extract_bank_from_text(self, text: str) -> str:
        """Use Gemini to extract bank name from OCR text"""
        
        prompt = f"""
        From the following invoice/bank statement text, extract the bank name.
        If multiple banks mentioned, return the one that appears to be the beneficiary/receiving bank.
        Return ONLY the bank name, nothing else.
        
        If no bank found, return "Not Found"
        
        Text: {text[:1500]}
        """
        
        try:
            response = self.model.generate_content(prompt)
            bank = response.text.strip()
            return bank if bank != "Not Found" else None
        except Exception as e:
            return None
    
    def extract_amount_from_text(self, text: str) -> dict:
        """Use Gemini to extract amount and currency"""
        
        prompt = f"""
        From the following invoice/bank statement text, extract:
        1. The total amount (as a number)
        2. The currency (USD, MYR, EUR, GBP, SGD)
        
        Return ONLY in this format: amount|currency
        Example: 10000|USD
        
        Text: {text[:1500]}
        """
        
        try:
            response = self.model.generate_content(prompt)
            parts = response.text.strip().split('|')
            if len(parts) == 2:
                return {"amount": float(parts[0]), "currency": parts[1]}
        except Exception as e:
            pass
        return {"amount": None, "currency": None}

# Singleton
_gemini = None

def get_gemini():
    global _gemini
    if _gemini is None:
        _gemini = GeminiHandler()
    return _gemini