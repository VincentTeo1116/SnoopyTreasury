import requests
from datetime import datetime
import json
import os
from dotenv import load_dotenv

load_dotenv()

FRANKFURTER_API = os.getenv("FRANKFURTER_API", "https://api.frankfurter.app")

# Fallback rates (in case API fails)
FALLBACK_RATES = {
    "USD": 4.25,
    "EUR": 4.60,
    "GBP": 5.20,
    "SGD": 3.15,
    "CNY": 0.59,
    "AUD": 2.80,
    "JPY": 0.027,
    "MYR": 1.00
}

def get_live_rate(currency: str, date: str = None) -> dict:
    # Build URL
    if date is None:
        # Live rate
        url = f"{FRANKFURTER_API}/latest?from={currency}&to=MYR"
    else:
        # Historical rate for specific date
        url = f"{FRANKFURTER_API}/{date}?from={currency}&to=MYR"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "rates" in data and "MYR" in data["rates"]:
            rate = data["rates"]["MYR"]
            return {
                "rate": round(rate, 4),
                "currency": currency,
                "target_currency": "MYR",
                "date": data.get("date", date or datetime.now().strftime("%Y-%m-%d")),
                "source": "api",
                "api_name": "frankfurter",
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
        else:
            raise ValueError("MYR rate not found in response")
            
    except Exception as e:
        print(f"API error: {e}, using fallback rate")
        
        rate = FALLBACK_RATES.get(currency, 4.25)
        
        return {
            "rate": rate,
            "currency": currency,
            "target_currency": "MYR",
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "source": "fallback",
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "warning": f"Using fallback rate. API error: {str(e)}"
        }


def get_historical_rate(currency: str, start_date: str, end_date: str) -> dict:
    url = f"{FRANKFURTER_API}/{start_date}..{end_date}?from={currency}&to=MYR"
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        rates = {}
        for date, values in data.get("rates", {}).items():
            rates[date] = values.get("MYR")
        
        return {
            "currency": currency,
            "target_currency": "MYR",
            "start_date": start_date,
            "end_date": end_date,
            "rates": rates,
            "source": "api",
            "api_name": "frankfurter",
            "success": True
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Frankfurter API supports up to 1 year date range"
        }


def get_rate_batch(currencies: list, base: str = "USD") -> dict:
    symbols = ",".join(currencies)
    url = f"{FRANKFURTER_API}/latest?from={base}&to={symbols}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "rates" in data:
            return {
                "base": base,
                "date": data.get("date"),
                "rates": data["rates"],
                "source": "api",
                "api_name": "frankfurter",
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
        else:
            return {
                "success": False,
                "error": "No rates found"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }