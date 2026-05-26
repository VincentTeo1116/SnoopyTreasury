import base64
import requests
import os
import re
import tempfile
import sys
from datetime import datetime, timedelta
from dateutil import parser
from pdf2image import convert_from_path
import streamlit as st

# ================= CONFIGURATION =================
try:
    API_KEY = st.secrets["GOOGLE_VISION_API_KEY"]
except:
    API_KEY = os.getenv("GOOGLE_VISION_API_KEY", "AIzaSyA2diDij3p7ARLIA0ANhv3tahW1PNh0uGY")

# Poppler path for Windows local development
POPPLER_PATH = r"C:\Users\Vincent\Documents\Release-26.02.0-0\poppler-26.02.0\Library\bin"
POPPLER_PATH = POPPLER_PATH if os.path.exists(POPPLER_PATH) else None


# ================= PDF TO IMAGE (Cross-Platform) =================
def pdf_to_image(pdf_path):
    """
    Convert first page of PDF to image.
    Works on: Windows (with poppler_path), Linux (auto-detected from PATH)
    """
    try:
        # Try Linux/Cloud deployment (poppler in PATH)
        pages = convert_from_path(pdf_path, 300, poppler_path=None)
    except Exception:
        try:
            # Fallback for Windows with specific path
            if POPPLER_PATH:
                pages = convert_from_path(pdf_path, 300, poppler_path=POPPLER_PATH)
            else:
                raise Exception("Poppler not found. Please install poppler-utils.")
        except Exception as e:
            raise Exception(f"PDF conversion failed: {str(e)}")

    if not pages:
        raise Exception("No pages found in PDF")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    pages[0].save(temp_file.name, "JPEG")

    return temp_file.name


# ================= OCR FUNCTION (Google Vision API) =================
def extract_text(file_path):
    """Extract text from image using Google Cloud Vision API"""
    with open(file_path, "rb") as f:
        img = base64.b64encode(f.read()).decode()

    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"

    payload = {
        "requests": [{
            "image": {"content": img},
            "features": [{"type": "TEXT_DETECTION"}]
        }]
    }

    response = requests.post(url, json=payload)
    res = response.json()

    if "error" in res:
        raise Exception(f"Google Vision API error: {res['error'].get('message', 'Unknown error')}")

    if "responses" not in res or not res["responses"]:
        return ""

    return res["responses"][0].get("fullTextAnnotation", {}).get("text", "")


# ================= DOCUMENT CLASSIFICATION =================
def classify_document(text):
    """Classify document as INVOICE, BANK_STATEMENT, or CODING_DOCUMENT"""
    t = text.lower()

    invoice_keywords = [
        "invoice", "total", "amount due", "payment due", "bill to",
        "seller", "purchaser", "tax invoice", "order number"
    ]

    bank_keywords = [
        "statement", "balance", "transaction history", "account summary",
        "opening balance", "closing balance", "bank statement",
        "recipient bank", "beneficiary bank"
    ]

    coding_keywords = [
        "class", "public static", "python", "java", "function",
        "void main", "def ", "import ", "print"
    ]

    invoice_score = sum(1 for k in invoice_keywords if k in t)
    bank_score = sum(1 for k in bank_keywords if k in t)
    coding_score = sum(1 for k in coding_keywords if k in t)

    if coding_score > invoice_score and coding_score > 2:
        return "CODING_DOCUMENT"
    if bank_score > invoice_score:
        return "BANK_STATEMENT"
    return "INVOICE"


# ================= COMPANY NAME EXTRACTION =================
def extract_company(text):
    """Extract company/vendor name from invoice text"""
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    keywords = ["seller", "company", "from", "billed to", "supplier", "invoice from", "vendor"]

    for i, line in enumerate(lines):
        low = line.lower()

        if any(k in low for k in keywords):
            for j in range(i + 1, min(i + 5, len(lines))):
                nxt = lines[j].strip()
                if nxt and not any(x in nxt.lower() for x in [
                    "address", "phone", "email", "invoice", "date", "ref", ":"
                ]):
                    return nxt

    # Fallback: first meaningful line that isn't a common header
    skip_words = ["invoice", "bill", "date", "statement", "account"]
    for line in lines[:10]:
        if len(line) > 5 and any(c.isalpha() for c in line):
            if not any(x in line.lower() for x in skip_words):
                return line

    return "N/A"

# ================= BANK NAME EXTRACTION =================
def extract_bank_name(text):
    """Extract bank name from text. Defaults to 'Not Specified' if not found."""
    banks = [
        "Maybank", "CIMB", "Public Bank", "RHB", "HSBC",
        "OCBC", "UOB", "Standard Chartered", "AmBank",
        "DBS", "Citibank", "Bank Islam", "Affin Bank",
        "Hong Leong Bank", "Bank Rakyat", "Bank Muamalat",
        "Vietcombank", "BIDV", "VietinBank", "Agribank", "Techcombank",
        "Sacombank", "ACB", "VPBank", "MB Bank", "SHB"
    ]

    for b in banks:
        if b.lower() in text.lower():
            return b

    # Default: Not Specified
    return "Not Specified"

# ================= AMOUNT EXTRACTION =================
def extract_amount(text):
    """Extract total amount (largest amount, typically the invoice total)"""
    patterns = [
        r"Grand Total\s*:?\s*([\d,]+\.\d{2})",
        r"Total\s*:?\s*([\d,]+\.\d{2})",
        r"Amount Due\s*:?\s*([\d,]+\.\d{2})",
        r"Total Amount\s*:?\s*([\d,]+\.\d{2})",
        r"Invoice Total\s*:?\s*([\d,]+\.\d{2})",
        r"Tổng cộng\s*:?\s*([\d,]+\.?\d*)",  # Vietnamese
        r"Thành tiền\s*:?\s*([\d,]+\.?\d*)",  # Vietnamese
        r"Số tiền\s*:?\s*([\d,]+\.?\d*)",  # Vietnamese
    ]

    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        if matches:
            # Return the last match (often the final total)
            amount_str = matches[-1].replace(",", "").strip()
            # Handle VND amounts without decimal
            if '.' in amount_str:
                return amount_str
            else:
                return amount_str

    # Fallback: find the largest amount in the document
    amounts = re.findall(r"\d+(?:[.,]\d{3})*(?:\.\d{2})?", text)
    if amounts:
        clean_amounts = []
        for amt in amounts:
            clean = amt.replace(",", "")
            if '.' in clean and len(clean.split('.')[1]) == 2:
                try:
                    clean_amounts.append(float(clean))
                except:
                    pass
            elif clean.isdigit():
                clean_amounts.append(float(clean))
        
        if clean_amounts:
            largest = max(clean_amounts)
            if largest == int(largest):
                return f"{int(largest)}"
            else:
                return f"{largest:.2f}"

    return "N/A"

# ================= CURRENCY EXTRACTION (Global Support) =================
def extract_currency(text):
    """
    Extract currency from text - Supports 50+ global currencies.
    Returns currency code (e.g., USD, EUR, VND, JPY, etc.)
    """
    t = text.upper()
    
    # Comprehensive currency mapping with symbols and codes
    currencies = {
        # Asia-Pacific
        "VND": ["VND", "ĐỒNG", "DONG", "₫"],
        "JPY": ["JPY", "¥", "YEN"],
        "CNY": ["CNY", "RMB", "YUAN", "¥"],
        "KRW": ["KRW", "₩", "WON"],
        "SGD": ["SGD", "S$"],
        "MYR": ["MYR", "RM"],
        "THB": ["THB", "฿", "BAHT"],
        "IDR": ["IDR", "RP", "RUPIAH"],
        "PHP": ["PHP", "₱", "PESO"],
        "INR": ["INR", "₹", "RUPEES"],
        "PKR": ["PKR", "₨", "RUPEE"],
        "BDT": ["BDT", "৳", "TAKA"],
        "LKR": ["LKR", "₨", "RUPEE"],
        "NPR": ["NPR", "₨", "RUPEE"],
        "AUD": ["AUD", "A$"],
        "NZD": ["NZD", "NZ$"],
        
        # North America
        "USD": ["USD", "$", "US DOLLAR", "DOLLARS"],
        "CAD": ["CAD", "C$", "CANADIAN DOLLAR"],
        "MXN": ["MXN", "MX$", "MEXICAN PESO"],
        
        # South America
        "BRL": ["BRL", "R$", "REAL"],
        "ARS": ["ARS", "$", "PESO ARGENTINO"],
        "CLP": ["CLP", "$", "PESO CHILENO"],
        "PEN": ["PEN", "S/", "SOL"],
        "COP": ["COP", "$", "PESO COLOMBIANO"],
        
        # Europe
        "EUR": ["EUR", "€", "EURO"],
        "GBP": ["GBP", "£", "POUND", "STERLING"],
        "CHF": ["CHF", "SWISS FRANC"],
        "SEK": ["SEK", "KR", "SWEDISH KRONA"],
        "NOK": ["NOK", "KR", "NORWEGIAN KRONE"],
        "DKK": ["DKK", "KR", "DANISH KRONE"],
        "PLN": ["PLN", "ZŁ", "ZLOTY"],
        "CZK": ["CZK", "KČ", "KORUNA"],
        "HUF": ["HUF", "FT", "FORINT"],
        "RON": ["RON", "LEI", "LEU"],
        "BGN": ["BGN", "ЛВ", "LEV"],
        "HRK": ["HRK", "KN", "KUNA"],
        "RUB": ["RUB", "₽", "ROUBLE"],
        "TRY": ["TRY", "₺", "LIRA"],
        
        # Middle East
        "AED": ["AED", "د.إ", "DIRHAM"],
        "SAR": ["SAR", "﷼", "RIYAL"],
        "QAR": ["QAR", "﷼", "RIYAL"],
        "KWD": ["KWD", "د.ك", "DINAR"],
        "BHD": ["BHD", "د.ب", "DINAR"],
        "OMR": ["OMR", "﷼", "RIAL"],
        "ILS": ["ILS", "₪", "SHEKEL"],
        
        # Africa
        "ZAR": ["ZAR", "R", "RAND"],
        "EGP": ["EGP", "£", "POUND"],
        "NGN": ["NGN", "₦", "NAIRA"],
        "KES": ["KES", "KSH", "SHILLING"],
        "GHS": ["GHS", "₵", "CEDI"],
        "MAD": ["MAD", "د.م.", "DIRHAM"],
        
        # Crypto (optional)
        "BTC": ["BTC", "BITCOIN", "₿"],
        "ETH": ["ETH", "ETHEREUM"],
        "USDT": ["USDT", "TETHER"],
    }
    
    # First pass: Check for currency codes and symbols
    for currency_code, symbols in currencies.items():
        for symbol in symbols:
            if symbol in t:
                # Special handling for $ symbol (could be USD, AUD, CAD, etc.)
                if symbol == "$":
                    # Check context for other currencies
                    if "AUD" in t or "A$" in t:
                        return "AUD"
                    elif "CAD" in t or "C$" in t:
                        return "CAD"
                    elif "MXN" in t:
                        return "MXN"
                    elif "SGD" in t:
                        return "SGD"
                    else:
                        return "USD"  # Default to USD
                elif symbol == "¥":
                    # Determine if Japanese Yen or Chinese Yuan
                    if "CNY" in t or "YUAN" in t or "RMB" in t:
                        return "CNY"
                    else:
                        return "JPY"  # Default to JPY
                elif symbol == "KRW" or symbol == "₩":
                    return "KRW"
                elif symbol == "£":
                    if "EGP" in t:
                        return "EGP"
                    else:
                        return "GBP"
                else:
                    return currency_code
    
    # Second pass: Look for currency patterns in text
    currency_patterns = [
        (r"(?:USD|US\s*DOLLARS?)\s*([\d,]+\.?\d*)", "USD"),
        (r"(?:EUR|EURO)\s*([\d,]+\.?\d*)", "EUR"),
        (r"(?:GBP|POUNDS?)\s*([\d,]+\.?\d*)", "GBP"),
        (r"(?:VND|ĐỒNG|DONG)\s*([\d,]+\.?\d*)", "VND"),
        (r"(?:JPY|YEN)\s*([\d,]+\.?\d*)", "JPY"),
        (r"(?:CNY|YUAN|RMB)\s*([\d,]+\.?\d*)", "CNY"),
        (r"(?:MYR|RM)\s*([\d,]+\.?\d*)", "MYR"),
        (r"(?:SGD|S\$)\s*([\d,]+\.?\d*)", "SGD"),
        (r"(?:THB|BAHT)\s*([\d,]+\.?\d*)", "THB"),
        (r"(?:IDR|RUPIAH)\s*([\d,]+\.?\d*)", "IDR"),
        (r"(?:INR|₹|RUPEES?)\s*([\d,]+\.?\d*)", "INR"),
        (r"(?:AUD|A\$)\s*([\d,]+\.?\d*)", "AUD"),
        (r"(?:CAD|C\$)\s*([\d,]+\.?\d*)", "CAD"),
        (r"(?:CHF|SWISS\s*FRANC)\s*([\d,]+\.?\d*)", "CHF"),
        (r"(?:RUB|₽|ROUBLES?)\s*([\d,]+\.?\d*)", "RUB"),
        (r"(?:TRY|₺|LIRA)\s*([\d,]+\.?\d*)", "TRY"),
        (r"(?:BRL|R\$)\s*([\d,]+\.?\d*)", "BRL"),
        (r"(?:KRW|₩|WON)\s*([\d,]+\.?\d*)", "KRW"),
    ]
    
    for pattern, currency_code in currency_patterns:
        if re.search(pattern, t, re.IGNORECASE):
            return currency_code
    
    # Third pass: Check for large numbers (often indicate VND, IDR, etc.)
    amounts = re.findall(r"\d{1,3}(?:[.,]\d{3})*", t)
    for amount in amounts:
        clean_amount = amount.replace(",", "").replace(".", "")
        if clean_amount.isdigit():
            amount_int = int(clean_amount)
            if amount_int > 1000000:
                if "VND" in t or "ĐỒNG" in t:
                    return "VND"
                elif "IDR" in t or "RUPIAH" in t:
                    return "IDR"
                elif "JPY" not in t and amount_int > 10000000:
                    return "VND"
            elif amount_int > 100000 and amount_int <= 1000000:
                if "JPY" in t or "YEN" in t:
                    return "JPY"
                elif "KRW" in t or "WON" in t:
                    return "KRW"
    
    return "N/A"

# ================= ENHANCED AMOUNT WITH CURRENCY =================
def extract_amount_with_currency(text):
    """
    Extract amount and currency together.
    Returns dictionary with amount, currency, and formatted string.
    """
    result = {
        "amount": "N/A",
        "currency": "N/A",
        "formatted": "N/A",
        "raw_match": "N/A"
    }
    
    # Currency-specific amount patterns
    patterns = [
        # Pattern 1: Currency symbol then amount
        (r'(?:USD|US\s*DOLLARS?)\s*:?\s*([\d,]+\.?\d*)', "USD"),
        (r'\$\s*([\d,]+\.?\d*)', "USD"),
        (r'(?:EUR|EURO)\s*:?\s*([\d,]+\.?\d*)', "EUR"),
        (r'€\s*([\d,]+\.?\d*)', "EUR"),
        (r'(?:GBP|POUNDS?)\s*:?\s*([\d,]+\.?\d*)', "GBP"),
        (r'£\s*([\d,]+\.?\d*)', "GBP"),
        (r'(?:VND|ĐỒNG|DONG)\s*:?\s*([\d,]+\.?\d*)', "VND"),
        (r'₫\s*([\d,]+\.?\d*)', "VND"),
        (r'(?:JPY|YEN)\s*:?\s*([\d,]+\.?\d*)', "JPY"),
        (r'¥\s*([\d,]+\.?\d*)', "JPY"),
        (r'(?:CNY|YUAN|RMB)\s*:?\s*([\d,]+\.?\d*)', "CNY"),
        (r'(?:MYR|RM)\s*:?\s*([\d,]+\.?\d*)', "MYR"),
        (r'RM\s*([\d,]+\.?\d*)', "MYR"),
        (r'(?:SGD|S\$)\s*:?\s*([\d,]+\.?\d*)', "SGD"),
        (r'(?:THB|BAHT)\s*:?\s*([\d,]+\.?\d*)', "THB"),
        (r'฿\s*([\d,]+\.?\d*)', "THB"),
        (r'(?:IDR|RUPIAH)\s*:?\s*([\d,]+\.?\d*)', "IDR"),
        (r'RP\s*([\d,]+\.?\d*)', "IDR"),
        (r'(?:INR|₹|RUPEES?)\s*:?\s*([\d,]+\.?\d*)', "INR"),
        (r'₹\s*([\d,]+\.?\d*)', "INR"),
        (r'(?:KRW|₩|WON)\s*:?\s*([\d,]+\.?\d*)', "KRW"),
        (r'₩\s*([\d,]+\.?\d*)', "KRW"),
        (r'(?:AUD|A\$)\s*:?\s*([\d,]+\.?\d*)', "AUD"),
        (r'(?:CAD|C\$)\s*:?\s*([\d,]+\.?\d*)', "CAD"),
        (r'(?:CHF|SWISS\s*FRANC)\s*:?\s*([\d,]+\.?\d*)', "CHF"),
        (r'(?:RUB|₽|ROUBLES?)\s*:?\s*([\d,]+\.?\d*)', "RUB"),
        (r'₽\s*([\d,]+\.?\d*)', "RUB"),
        (r'(?:TRY|₺|LIRA)\s*:?\s*([\d,]+\.?\d*)', "TRY"),
        (r'₺\s*([\d,]+\.?\d*)', "TRY"),
        (r'(?:BRL|R\$)\s*:?\s*([\d,]+\.?\d*)', "BRL"),
        
        # Pattern 2: Amount then currency symbol
        (r'([\d,]+\.?\d*)\s*(?:USD|US\s*DOLLARS?)', "USD"),
        (r'([\d,]+\.?\d*)\s*\$', "USD"),
        (r'([\d,]+\.?\d*)\s*(?:EUR|EURO)', "EUR"),
        (r'([\d,]+\.?\d*)\s*€', "EUR"),
        (r'([\d,]+\.?\d*)\s*(?:GBP|POUNDS?)', "GBP"),
        (r'([\d,]+\.?\d*)\s*£', "GBP"),
        (r'([\d,]+\.?\d*)\s*(?:VND|ĐỒNG|DONG)', "VND"),
        (r'([\d,]+\.?\d*)\s*₫', "VND"),
        (r'([\d,]+\.?\d*)\s*(?:JPY|YEN)', "JPY"),
        (r'([\d,]+\.?\d*)\s*¥', "JPY"),
        (r'([\d,]+\.?\d*)\s*(?:MYR|RM)', "MYR"),
        (r'([\d,]+\.?\d*)\s*RM', "MYR"),
        (r'([\d,]+\.?\d*)\s*(?:SGD|S\$)', "SGD"),
        (r'([\d,]+\.?\d*)\s*(?:THB|BAHT)', "THB"),
        (r'([\d,]+\.?\d*)\s*฿', "THB"),
        (r'([\d,]+\.?\d*)\s*(?:IDR|RUPIAH)', "IDR"),
        (r'([\d,]+\.?\d*)\s*(?:INR|₹|RUPEES?)', "INR"),
        (r'([\d,]+\.?\d*)\s*₹', "INR"),
        (r'([\d,]+\.?\d*)\s*(?:KRW|₩|WON)', "KRW"),
        (r'([\d,]+\.?\d*)\s*₩', "KRW"),
        (r'([\d,]+\.?\d*)\s*(?:AUD|A\$)', "AUD"),
        (r'([\d,]+\.?\d*)\s*(?:CAD|C\$)', "CAD"),
    ]
    
    # Try to find matching patterns
    for pattern, currency_code in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Get the last match (often the total amount)
            amount_str = matches[-1].replace(",", "").strip()
            # Handle amounts with or without decimal
            if '.' in amount_str and len(amount_str.split('.')[1]) == 2:
                result["amount"] = amount_str
            else:
                # Remove any thousand separators
                amount_str = amount_str.replace(".", "")
                result["amount"] = amount_str
            result["currency"] = currency_code
            result["formatted"] = f"{currency_code} {result['amount']}"
            result["raw_match"] = matches[-1]
            return result
    
    # If no specific pattern found, try generic extraction
    result["amount"] = extract_amount(text)
    result["currency"] = extract_currency(text)
    if result["currency"] != "N/A" and result["amount"] != "N/A":
        result["formatted"] = f"{result['currency']} {result['amount']}"
    
    return result

# ================= INVOICE DATE EXTRACTION =================
def extract_invoice_date(text):
    """Extract invoice date from text. Defaults to today's date if not found."""
    # Vietnamese month mappings
    vietnamese_months = {
        'tháng 1': 'January', 'tháng 2': 'February', 'tháng 3': 'March',
        'tháng 4': 'April', 'tháng 5': 'May', 'tháng 6': 'June',
        'tháng 7': 'July', 'tháng 8': 'August', 'tháng 9': 'September',
        'tháng 10': 'October', 'tháng 11': 'November', 'tháng 12': 'December'
    }
    
    # Convert Vietnamese dates to English for parser
    text_en = text
    for vn, en in vietnamese_months.items():
        text_en = text_en.replace(vn, en)
    
    patterns = [
        r"Invoice\s+Date\s*:?\s*(\d{1,2}\s+[A-Za-z]{3,}\s+\d{4})",
        r"Date\s*:?\s*(\d{1,2}\s+[A-Za-z]{3,}\s+\d{4})",
        r"Invoice\s+Date\s*:?\s*(\d{2}/\d{2}/\d{4})",
        r"Date\s*:?\s*(\d{2}/\d{2}/\d{4})",
        r"Invoice\s+Date\s*:?\s*(\d{4}-\d{2}-\d{2})",
        r"Date\s*:?\s*(\d{4}-\d{2}-\d{2})",
        r"Ngày\s+lập\s+hóa\s+đơn\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
        r"Ngày\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
    ]

    for p in patterns:
        match = re.search(p, text_en, re.IGNORECASE)
        if match:
            try:
                return parser.parse(match.group(1)).strftime("%Y-%m-%d")
            except:
                return match.group(1)

    # Default: today's date
    return datetime.now().strftime("%Y-%m-%d")

# ================= DUE DATE EXTRACTION (WITH DEFAULT FALLBACK) =================
def extract_due_date(text, invoice_date):
    """
    Extract due date from invoice text.
    If not found, default to invoice_date + 7 days, or today + 7 days.
    """
    patterns = [
        r"Due\s+Date\s*:?\s*(\d{1,2}\s+[A-Za-z]{3,}\s+\d{4})",
        r"Due\s+Date\s*:?\s*(\d{2}/\d{2}/\d{4})",
        r"Due\s+Date\s*:?\s*(\d{4}-\d{2}-\d{2})",
        r"Payment\s+Due\s*:?\s*(\d{1,2}\s+[A-Za-z]{3,}\s+\d{4})",
        r"Payment\s+Due\s*:?\s*(\d{2}/\d{2}/\d{4})",
        r"Due\s+on\s*:?\s*(\d{1,2}\s+[A-Za-z]{3,}\s+\d{4})",
        r"Hạn\s+thanh\s+toán\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})",  # Vietnamese
        r"Ngày\s+đến\s+hạn\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})",  # Vietnamese
    ]

    for p in patterns:
        match = re.search(p, text, re.IGNORECASE)
        if match:
            try:
                dt = parser.parse(match.group(1))
                return dt.strftime("%Y-%m-%d")
            except:
                return match.group(1)

    # Default: 1 week from invoice date (or today if no invoice date)
    if invoice_date and invoice_date != "N/A":
        try:
            base_date = datetime.strptime(invoice_date, "%Y-%m-%d")
        except:
            base_date = datetime.now()
    else:
        base_date = datetime.now()

    return (base_date + timedelta(days=7)).strftime("%Y-%m-%d")

# ================= FILE HANDLER (For Streamlit Upload) =================
def handle_uploaded_file(uploaded_file):
    """
    Handle file uploaded via Streamlit file_uploader.
    Returns path to temporary file.
    """
    # Get file extension
    original_name = uploaded_file.name
    ext = original_name.split('.')[-1].lower()

    # Create temp file with correct extension
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return tmp_file.name

# ================= MAIN PROCESSING FUNCTION =================
def process_document(file_path, is_uploaded_file=False):
    """
    Main function to process document and extract information.
    
    Args:
        file_path: Path to the file (image or PDF)
        is_uploaded_file: If True, file will be deleted after processing
    
    Returns:
        Dictionary with extracted information
    """
    print("🔍 Processing document...")
    temp_files = []

    try:
        # Handle PDF files
        if file_path.lower().endswith(".pdf"):
            print("📄 Converting PDF to image...")
            try:
                file_path = pdf_to_image(file_path)
                temp_files.append(file_path)
                print("✅ PDF converted successfully")
            except Exception as e:
                print(f"⚠️ PDF conversion failed: {e}")
                return {"error": f"PDF conversion failed: {str(e)}"}

        # Run OCR
        print("📷 Running OCR...")
        try:
            text = extract_text(file_path)
        except Exception as e:
            print(f"⚠️ OCR failed: {e}")
            return {"error": f"OCR failed: {str(e)}"}

        if not text or not text.strip():
            print("⚠️ Warning: No text extracted")
            return {"error": "No text extracted from document"}

        print(f"✅ OCR completed: {len(text)} characters extracted")

        # Classify document
        print("\n🏷️ Classifying document type...")
        doc_type = classify_document(text)

        # Display document type
        if doc_type == "INVOICE":
            print("📑 Document identified as: INVOICE")
        elif doc_type == "BANK_STATEMENT":
            print("📑 Document identified as: BANK STATEMENT")
        elif doc_type == "CODING_DOCUMENT":
            print("💻 Document identified as: CODING / EXAM DOCUMENT")

        # Extract information using enhanced currency extraction
        company = extract_company(text)
        bank = extract_bank_name(text)
        
        # Use enhanced currency+amount extraction
        currency_info = extract_amount_with_currency(text)
        amount = currency_info["amount"]
        currency = currency_info["currency"]
        
        invoice_date = extract_invoice_date(text)
        due_date = extract_due_date(text, invoice_date)

        # ================= OUTPUT =================
        print("\n" + "=" * 60)
        print("📊 EXTRACTED INFORMATION")
        print("=" * 60)

        print(f"📌 Document Type: {doc_type}")
        print(f"🏢 Company Name: {company}")
        print(f"🏦 Bank Name: {bank}")
        print(f"💰 Amount: {amount}")
        print(f"💱 Currency: {currency}")
        print(f"💵 Formatted: {currency_info['formatted']}")
        print(f"📅 Invoice Date: {invoice_date}")
        print(f"📅 Due Date: {due_date}")

        # Add note if due date was defaulted
        if invoice_date != "N/A" and due_date != "N/A":
            try:
                inv_dt = datetime.strptime(invoice_date, "%Y-%m-%d")
                due_dt = datetime.strptime(due_date, "%Y-%m-%d")
                if (due_dt - inv_dt).days == 7:
                    print("\n💡 Note: Due date not found in document. Defaulted to 1 week from invoice date.")
            except:
                pass

        print("\n✅ Extraction completed!")

        return {
            "success": True,
            "document_type": doc_type,
            "company_name": company,
            "bank_name": bank,
            "amount": amount,
            "currency": currency,
            "formatted_amount": currency_info['formatted'],
            "invoice_date": invoice_date,
            "due_date": due_date,
            "full_text": text[:500]  # First 500 chars for preview
        }

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return {"success": False, "error": str(e)}

    finally:
        # Clean up temp files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass

# ================= COMMAND LINE INTERFACE =================
if __name__ == "__main__":
    print("=" * 60)
    print("📄 SMART OCR EXTRACTION SYSTEM")
    print("=" * 60)
    print()

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            result = process_document(file_path)
            if not result.get("success"):
                print(f"\n❌ Error: {result.get('error')}")
        else:
            print(f"Error: File '{file_path}' not found!")
    else:
        print("Usage: python vision.py <file_path>")
        print("Example: python vision.py invoice.pdf")