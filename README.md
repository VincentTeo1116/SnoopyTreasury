# 🌍 SnoopyTreasury - Global Treasury Agent

**An AI-powered cross-border reconciliation system for Malaysian SMEs.** Predict hidden bank fees BEFORE invoicing, upload invoices to database, and match bank statement payments automatically.

---

## 📖 System Overview

SnoopyTreasury helps SMEs:
- **Predict** hidden bank fees before sending invoices
- **Upload** invoices to cloud database
- **Match** bank statement payments to invoices automatically

No expensive APIs, no high bank balance required. Just upload your invoice or bank statement.

---

## 🎯 Core Functions

| Function | Description | Save to DB? |
|----------|-------------|-------------|
| **1. Predict Hidden Fees** | Calculate how much MYR you'll receive after bank markups + fees | ❌ No |
| **2. Upload Invoice** | Store invoice details (amount, currency, customer, due date) | ✅ Yes |
| **3. Upload Bank Statement** | Match payment to invoice, handle partial/over payment | ✅ Yes |

---

## 🚀 Installation Guide

### Prerequisites

- Python 3.9 or higher
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/VincentTeo1116/SnoopyTreasury.git
cd SnoopyTreasury
```

### Step 2: Install Poppler-utils
1. Go to: [Poppler Utils Git Link](https://github.com/oschwartz10612/poppler-windows/releases)
2. Download the latest **Release-xx.x.x-x.zip file (e.g., Release-24.08.0-0.zip)**
3. Extract to a permanent location (maybe in C drive)
4. Update your ``vision.py`` with the correct path
```bash
# Change this:
POPPLER_PATH = r"C:\Users\User\Desktop\currency agent\Release-26.02.0-0\poppler-26.02.0\Library\bin"

# To this (update username if needed):
POPPLER_PATH = r"C:\poppler\Library\bin"
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.
```

### Step 4: Set Up Environment Variables
```bash
GOOGLE_VISION_API_KEY=your_google_vision_api_key
FRANKFURTER_API=https://api.frankfurter.app
```

### Step 5: Run the Application
```bash
streamlit run streamlit_app.py
```
- The app will open at ```http://localhost:8501```

