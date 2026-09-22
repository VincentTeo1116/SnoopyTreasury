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
- Poppler-utils

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

### Step 3: Firebase Setup 

SnoopyTreasury uses Firebase Firestore as its cloud database. If you skip this step, the system will automatically fall back to local JSON storage.

### A: Create a Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **Create Project** --> Enter a project name (e.g., `SnoopyTreasury`)
3. Disable Google Analytics (optional) --> Click **Create Project**

### B: Enable Firestore Database
1. In the left menu, click **Firestore Database**
2. Click **Create Database**
3. Choose **Start in test mode**
4. Select a region (e.g., `asia-southeast1` for Malaysia)
5. Click **Enable**

### C: Generate Service Account Key
1. Go to **Project Settings** (gear icon) → **Service Accounts** tab
2. Click **Generate new private key**
3. Click **Generate Key** — a `.json` file will download
4. Rename the file to `serviceAccountKey.json`
5. Place it in your project root folder

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Set Up Environment Variables
```bash
#API Keys
GOOGLE_VISION_API_KEY=your_google_vision_api_key
GEMINI_API_KEY=your_gemini_api_key

FRANKFURTER_API=https://api.frankfurter.app

# Firebase
FIREBASE_SERVICE_ACCOUNT_PATH=serviceAccountKey.json

# Google Vision
GOOGLE_APPLICATION_CREDENTIALS=vision_service_account.json
```

### Step 5: Run the Application
```bash
streamlit run streamlit_app.py
```
- The app will open at ```http://localhost:8501```

## ❓ Troubleshooting

### OCR doesn't work?
- Ensure Poppler is installed correctly (see Step 2)
- For cloud deployment, `poppler-utils` must be in `packages.txt`

### Firebase not connecting?
- Check `serviceAccountKey.json` is in project root
- For Streamlit Cloud, add `serviceAccountKey` to Secrets

### PDF conversion fails?
- Verify Poppler path in `vision.py`
- For Windows, use absolute path like `C:\poppler\Library\bin`

### "use_container_width" warning?
- This is a deprecation warning - the app still works fine

