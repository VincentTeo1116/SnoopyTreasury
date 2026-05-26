import json
import joblib
import os
from datetime import datetime
from pathlib import Path
import pandas as pd

class MarkupPredictor:
    def __init__(self, model_path: str = None):
        self.model = None
        self.bank_encoder = None
        self.currency_encoder = None
        self.feature_names = None
        self.bank_factors = {}
        self.currency_factors = {}
        self._load_fallback()
        
        # Load trained model if exists
        if model_path and os.path.exists(model_path):
            self._load_model(model_path)
        else:
            default_path = Path(__file__).parent / "bank_markup_model.pkl"
            if default_path.exists():
                self._load_model(default_path)
            else:
                print("⚠️ No model file found, using fallback values")
    
    def _load_model(self, path):
        """Load trained model and encoders from pickle file"""
        try:
            data = joblib.load(path)
            
            if isinstance(data, dict):
                if 'model' in data:
                    self.model = data['model']
                    # Get feature names if available
                    if hasattr(self.model, 'feature_names_in_'):
                        self.feature_names = self.model.feature_names_in_
                        print(f"✅ Loaded model with features: {list(self.feature_names)}")
                    print(f"✅ Loaded trained model from {path}")
                if 'bank_encoder' in data:
                    self.bank_encoder = data['bank_encoder']
                if 'currency_encoder' in data:
                    self.currency_encoder = data['currency_encoder']
            elif hasattr(data, 'predict'):
                self.model = data
                print(f"✅ Loaded trained model from {path}")
            else:
                print(f"⚠️ Unknown format in {path}, using fallback")
        except Exception as e:
            print(f"⚠️ Could not load model: {e}, using fallback")
    
    def _load_fallback(self):
        """Fallback hardcoded values if model not available"""
        self.bank_factors = {
            "Maybank": 0.025,
            "CIMB": 0.018,
            "Public Bank": 0.022,
            "RHB": 0.024,
            "Hong Leong": 0.014
        }
        self.currency_factors = {
            "USD": 0.000,
            "EUR": 0.003,
            "GBP": 0.002,
            "SGD": -0.005,
            "CNY": 0.001
        }
    
    def _encode_bank(self, bank: str):
        """Encode bank name using loaded encoder or fallback mapping"""
        if self.bank_encoder is not None:
            try:
                return self.bank_encoder.transform([bank])[0]
            except ValueError:
                # Bank not in encoder, try case-insensitive match
                for b in self.bank_encoder.classes_:
                    if b.lower() == bank.lower():
                        return self.bank_encoder.transform([b])[0]
                print(f"⚠️ Bank '{bank}' not in encoder, using fallback")
        # Fallback mapping
        bank_mapping = {
            "Maybank": 0, "CIMB": 1, "Public Bank": 2, 
            "RHB": 3, "Hong Leong": 4
        }
        return bank_mapping.get(bank, 0)
    
    def _encode_currency(self, currency: str):
        """Encode currency using loaded encoder or fallback mapping"""
        if self.currency_encoder is not None:
            try:
                return self.currency_encoder.transform([currency])[0]
            except ValueError:
                for c in self.currency_encoder.classes_:
                    if c.lower() == currency.lower():
                        return self.currency_encoder.transform([c])[0]
                print(f"⚠️ Currency '{currency}' not in encoder, using fallback")
        # Fallback mapping
        currency_mapping = {
            "USD": 0, "EUR": 1, "GBP": 2, "SGD": 3, "CNY": 4
        }
        return currency_mapping.get(currency, 0)
    
    def predict(self, bank: str, currency: str, amount: float = None, 
                transaction_fee_pct: float = None, date=None) -> dict:
        """Predict markup using loaded model or fallback"""
        
        # Try using trained model if available
        if self.model is not None and hasattr(self.model, 'predict'):
            try:
                # Handle date
                if date is None:
                    current_date = datetime.now()
                elif isinstance(date, str):
                    current_date = datetime.strptime(date, "%Y-%m-%d")
                else:
                    current_date = date
                
                # Encode bank and currency
                bank_encoded = self._encode_bank(bank)
                currency_encoded = self._encode_currency(currency)
                
                # Default transaction fee if not provided
                if transaction_fee_pct is None:
                    transaction_fee_pct = 1.5
                
                # Create DataFrame with proper feature names
                features_df = pd.DataFrame([[
                    current_date.weekday(), # Day
                    current_date.month, # Month
                    current_date.year, # Year
                    bank_encoded, # Bank_encoded
                    currency_encoded, # Currency_encoded
                    amount or 0, # InvoiceAmount
                    transaction_fee_pct # TransactionFeePct
                ]], columns=[
                    "Day", "Month", "Year", "Bank_encoded", 
                    "Currency_encoded", "InvoiceAmount", "TransactionFeePct"
                ])
                
                predicted_markup = self.model.predict(features_df)[0]

                predicted_markup = predicted_markup / 100
                
                predicted_markup = max(0.005, min(0.05, predicted_markup))
                
                return {
                    "predicted_markup": round(predicted_markup, 4),
                    "confidence": "High",
                    "bank": bank,
                    "currency": currency,
                    "amount": amount,
                    "transaction_fee_pct": transaction_fee_pct,
                    "date": current_date.strftime("%Y-%m-%d"),
                    "source": "trained_model",
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                print(f"⚠️ Model prediction failed: {e}, using fallback")
        
        # Fallback to hardcoded values
        base_markup = self.bank_factors.get(bank, 0.025)
        currency_adjustment = self.currency_factors.get(currency, 0.000)
        predicted_markup = base_markup + currency_adjustment
        
        # Volume discount for large amounts
        if amount and amount > 50000:
            predicted_markup -= 0.002
        elif amount and amount > 100000:
            predicted_markup -= 0.003
        
        predicted_markup = max(0.005, min(0.05, predicted_markup))
        
        return {
            "predicted_markup": round(predicted_markup, 4),
            "confidence": "Medium (using fallback)",
            "bank": bank,
            "currency": currency,
            "amount": amount,
            "source": "fallback",
            "timestamp": datetime.now().isoformat()
        }


_predictor = None

def get_predictor(model_path: str = None):
    global _predictor
    if _predictor is None:
        _predictor = MarkupPredictor(model_path)
    return _predictor

def predict_markup(bank: str, currency: str, amount: float = None, 
                   transaction_fee_pct: float = None, date=None) -> dict:
    predictor = get_predictor()
    return predictor.predict(bank, currency, amount, transaction_fee_pct, date)
