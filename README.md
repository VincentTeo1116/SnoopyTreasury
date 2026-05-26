# 🌍 SnoopyTreasury - Global Treasury Agent

**An AI-powered cross-border reconciliation system for Malaysian SMEs.** Predict hidden bank fees BEFORE invoicing, upload invoices to database, and match bank statement payments automatically.

---

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Core Functions](#core-functions)
- [Installation Guide](#installation-guide)
- [User Manual](#user-manual)
- [Tech Stack](#tech-stack)
- [Troubleshooting](#troubleshooting)

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

### Step 2: Install Dependencies
```bash
pip install -r requirements.
```

### Step 3: Set Up Environment Variables
```bash
GOOGLE_VISION_API_KEY=your_google_vision_api_key
FRANKFURTER_API=https://api.frankfurter.app
```

### Step 4: Run the Application
```bash
streamlit run streamlit_app.py
```
- The app will open at ```http://localhost:8501```

