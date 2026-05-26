import sys
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from firebase_client import initialize_firebase

firebase_ok = initialize_firebase()
if firebase_ok:
    print("✅ Firebase ready")
else:
    print("⚠️ Firebase not available - using local storage")

# Import your backend modules
from vision import process_document, handle_uploaded_file
from invoice_manager import upload_invoice, match_bank_statement, get_all_invoices, get_all_payments
from predict_markup import predict_markup
from get_live_rate import get_live_rate
from fee_calculator import calculate_complete_before, calculate_complete_after
from export_report import generate_report
from gemini_llm import get_gemini
from store_transaction import store_transaction, get_all_transactions

# Page configuration
st.set_page_config(
    page_title="Global Treasury Agent",
    page_icon="https://img.icons8.com/color/96/currency-exchange.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
<style>
    .main > div {
        padding: 1.5rem !important;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 95% !important;
    }

    section.main > div {
        padding-top: 0.5rem !important;
    }
    
    .row-widget.stHorizontalBlock {
        gap: 0.35rem !important;
    }

    div[data-testid="column"] > div {
        padding: 0.15rem !important;
    }

    section[data-testid="stSidebar"] {
        width: 280px;
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding: 0rem !important;
    }
    
    .stButton button {
        width: 100%;
        text-align: left;
        padding: 0.5rem 1rem !important;
        margin: 0;
        border-radius: 10px;
        border: none;
        background-color: transparent;
        color: #333;
        font-weight: 500;
        transition: all 0.3s ease;
        justify-content: left;
    }
    
    .stButton button:hover {
        background-color: #E3F2FD;
        color: #1E3A5F;
        transform: translateX(5px);
    }
    
    .stButton button:active {
        background-color: #2196F3;
        color: white;
    }
    
    .stButton button[kind="primary"] {
        background-color: #001d43;
        color: white;
    }
    
    .stButton button[kind="primary"]:hover {
        background-color: #2E5A8F;
    }
    
    .stDownloadButton button {
        width: 100%;
        text-align: left;
        padding: 0.5rem 1rem !important;
        margin: 0;
        border-radius: 10px;
        border: none;
        background-color: transparent;
        color: #333;
        font-weight: 500;
        transition: all 0.3s ease;
        justify-content: left;
    }
    
    .stDownloadButton button:hover {
        background-color: #E3F2FD;
        color: #1E3A5F;
        transform: translateX(5px);
    }
    
    .stDownloadButton button:active {
        background-color: #2196F3;
        color: white;
    }
    
    .stDownloadButton button[kind="primary"] {
        background-color: #001d43;
        color: white;
    }
    
    .stDownloadButton button[kind="primary"]:hover {
        background-color: #2E5A8F;
    }

    .streamlit-expanderHeader {
        padding: 0.3rem !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0rem 0rem !important;
        font-size: 0.85rem !important;
    }

    .element-container {
        margin-bottom: 0 !important;
    }
    
    hr {
        margin: 0.5rem 0 !important;
    }

    h1, h2, h3, h4 {
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
    }

    p {
        margin-bottom: 0.25rem !important;
    }

    .stDataFrame {
        font-size: 0.85rem !important;
    }

    .stFileUploader {
        margin-bottom: 0.5rem !important;
    }

    .stAlert {
        padding: 0.4rem !important;
        margin-bottom: 0.5rem !important;
    }

    [data-testid="stMetric"] {
        padding: 0.3rem !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
    }

    .success-box, .warning-box, .info-box {
        padding: 0.5rem !important;
        margin: 0.5rem 0 !important;
    }
            
    .stDataFrame {
        border-radius: 10px !important;
        overflow: hidden !important;
    }

    .stDataFrame thead th {
        background-color: #1E3A5F !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.75rem !important;
    }

    .stDataFrame tbody tr:hover {
        background-color: #E3F2FD !important;
    }

    .status-paid {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
    }

    .status-pending {
        background-color: #FFF3E0;
        color: #ED6C02;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
    }

    .status-partial {
        background-color: #E3F2FD;
        color: #1E3A5F;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
    }

    .status-unmatched {
        background-color: #FFEBEE;
        color: #D32F2F;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
    }

    .ai-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.2rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'prediction_result' not in st.session_state:
    st.session_state.prediction_result = None
if 'last_invoice' not in st.session_state:
    st.session_state.last_invoice = None
if 'last_payment' not in st.session_state:
    st.session_state.last_payment = None
if 'gemini' not in st.session_state:
    st.session_state.gemini = None
if 'llm_enabled' not in st.session_state:
    st.session_state.llm_enabled = False

# Initialize Gemini
try:
    st.session_state.gemini = get_gemini()
    st.session_state.llm_enabled = True
    use_llm = True
except:
    st.session_state.llm_enabled = False
    st.session_state.gemini = None
    use_llm = False

# ================= AI HELPER FUNCTIONS =================
def show_ai_prediction_explanation(amount, currency, bank, market_rate, markup, final_amount):
    """Display AI explanation for prediction"""
    if not st.session_state.llm_enabled or st.session_state.gemini is None:
        return
    
    with st.spinner("Generating AI explanation..."):
        try:
            explanation = st.session_state.gemini.explain_prediction(
                amount=amount,
                currency=currency,
                bank=bank,
                market_rate=market_rate,
                markup=markup,
                final_amount=final_amount
            )
            st.markdown(f'<div class="ai-box"><i class="bi bi-robot"></i><strong>AI Insight</strong><br><br>{explanation}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.info(f"💡 Quick tip: Your {amount} {currency} will be around RM {final_amount:,.2f} after {bank}'s fees.")

def show_ai_discrepancy_explanation(expected, actual, difference, percent, bank, currency):
    """Display AI explanation for discrepancy"""
    if not st.session_state.llm_enabled or st.session_state.gemini is None:
        # Fallback simple explanation
        if abs(percent) < 0.5:
            st.info("✅ This small difference is normal due to daily exchange rate fluctuations.")
        elif abs(percent) < 3:
            st.warning(f"⚠️ The {percent:.1f}% difference suggests bank fees or a different exchange rate was applied.")
        else:
            st.error(f"❌ The {percent:.1f}% difference is significant. Contact your bank to verify the exchange rate.")
        return
    
    with st.spinner("🤖 Analyzing discrepancy..."):
        try:
            explanation = st.session_state.gemini.explain_discrepancy(
                expected=expected,
                actual=actual,
                difference=difference,
                percent=percent
            )
            st.markdown(f'<div class="ai-box">🤖 <strong>AI Analysis</strong><br><br>{explanation}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"AI analysis temporarily unavailable. Difference: {percent:.1f}%")

# ================= DASHBOARD PAGE =================
def dashboard_page():
    st.markdown('<h1 class="main-header">Treasury Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">Overview of your treasury operations</p>', unsafe_allow_html=True)
    
    # Get data
    invoices = get_all_invoices()
    payments = get_all_payments()
    
    # Calculate metrics
    total_outstanding = sum(inv.get('remaining_balance', 0) for inv in invoices if inv.get('status') in ['PENDING', 'PARTIAL'])
    total_collected = sum(inv.get('amount', 0) for inv in invoices if inv.get('status') == 'PAID')
    pending_count = len([inv for inv in invoices if inv.get('status') in ['PENDING', 'PARTIAL']])
    unmatched_count = len([pay for pay in payments if pay.get('status') == 'UNMATCHED'])
    
    # ========== METRICS ROW ==========
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="background-color: white; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h5 style="color: #666; margin: 0;"><i class="bi bi-currency-dollar"></i> Outstanding Amount</h5>
            <p style="font-size: 1.8rem; font-weight: bold; margin: 0; color: #1E3A5F;">RM {total_outstanding:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background-color: white; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h5 style="color: #666; margin: 0;"><i class="bi bi-wallet-fill"></i> Total Collected</h5>
            <p style="font-size: 1.8rem; font-weight: bold; margin: 0; color: #2E7D32;">RM {total_collected:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background-color: white; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h5 style="color: #666; margin: 0;"><i class="bi bi-receipt"></i> Pending Invoices</h5>
            <p style="font-size: 1.8rem; font-weight: bold; margin: 0; color: #ED6C02;">{pending_count}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="background-color: white; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h5 style="color: #666; margin: 0;"><i class="bi bi-exclamation-circle"></i> Unmatched Payments</h5>
            <p style="font-size: 1.8rem; font-weight: bold; margin: 0; color: #D32F2F;">{unmatched_count}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ========== CHARTS ROW ==========
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h3 style="color: #1E3A5F;"><i class="bi bi-receipt"></i> Invoices by Status</h3>', unsafe_allow_html=True)
        
        status_data = {
            "Paid": len([i for i in invoices if i.get('status') == 'PAID']),
            "Partial": len([i for i in invoices if i.get('status') == 'PARTIAL']),
            "Pending": len([i for i in invoices if i.get('status') == 'PENDING']),
            "Overdue": len([i for i in invoices if i.get('due_date') and i.get('status') != 'PAID' and datetime.now().strftime("%Y-%m-%d") > i.get('due_date')])
        }
        
        status_df = pd.DataFrame({
            'Status': list(status_data.keys()),
            'Count': list(status_data.values())
        })
        
        st.bar_chart(status_df.set_index('Status'), use_container_width=True)
        
        cols = st.columns(4)
        colors = ['#2E7D32', '#ED6C02', '#1E3A5F', '#D32F2F']
        for i, (status, count) in enumerate(status_data.items()):
            with cols[i]:
                st.markdown(f"""
                <div style="text-align: center;">
                    <p style="color: {colors[i]}; font-weight: bold; margin: 0;">{count}</p>
                    <p style="color: #666; font-size: 0.8rem; margin: 0;">{status}</p>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown('<h3 style="color: #1E3A5F;"><i class="bi bi-cash-coin"></i> Outstanding by Customer</h3>', unsafe_allow_html=True)
        
        customer_balances = {}
        for inv in invoices:
            if inv.get('status') in ['PENDING', 'PARTIAL']:
                customer = inv.get('from_company', 'Unknown')
                customer_balances[customer] = customer_balances.get(customer, 0) + inv.get('remaining_balance', 0)
        
        if customer_balances:
            sorted_customers = dict(sorted(customer_balances.items(), key=lambda x: x[1], reverse=True))
            
            customer_df = pd.DataFrame({
                'Customer': list(sorted_customers.keys())[:5],
                'Amount': list(sorted_customers.values())[:5]
            })
            
            st.bar_chart(customer_df.set_index('Customer'), use_container_width=True)
            
            st.markdown("---")
            for customer, amount in list(sorted_customers.items())[:5]:
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 5px 0;">
                    <span style="color: #333;">{customer}</span>
                    <span style="color: #1E3A5F; font-weight: bold;">RM {amount:,.2f}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No outstanding invoices")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ========== RECENT ACTIVITY ==========
    st.markdown('<h3 style="color: #1E3A5F;"><i class="bi bi-activity"></i> Recent Activity</h3>', unsafe_allow_html=True)
    
    recent_activities = []
    
    for pay in payments[:5]:
        recent_activities.append({
            "type": "payment",
            "title": "Payment Received",
            "customer": pay.get('from_company', 'Unknown'),
            "amount": pay.get('amount', 0),
            "currency": pay.get('currency', 'MYR'),
            "status": "success",
            "time": pay.get('timestamp', '')
        })
    
    for inv in invoices[:5]:
        recent_activities.append({
            "type": "invoice",
            "title": "Invoice Created",
            "customer": inv.get('from_company', 'Unknown'),
            "amount": inv.get('amount', 0),
            "currency": inv.get('currency', 'MYR'),
            "status": "info" if inv.get('status') == 'PENDING' else "warning" if inv.get('status') == 'PARTIAL' else "success",
            "time": inv.get('created_at', '')
        })
    
    recent_activities.sort(key=lambda x: x.get('time', ''), reverse=True)
    
    for activity in recent_activities[:4]:
        if activity['type'] == 'payment':
            icon = '<i class="bi bi-check-circle-fill"></i>'
            color = "#2E7D32"
            bg_color = "#E8F5E9"
        else:
            icon = '<i class="bi bi-receipt-cutoff"></i>'
            color = "#1E3A5F"
            bg_color = "#E3F2FD"
        
        st.markdown(f"""
        <div style="background-color: {bg_color}; padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 1.2rem;">{icon}</span>
                <span style="font-weight: bold; margin-left: 10px;">{activity['title']}</span>
                <span style="color: #666; margin-left: 10px;">{activity['customer']}</span>
            </div>
            <div style="text-align: right;">
                <span style="color: {color}; font-weight: bold;">{activity['currency']} {activity['amount']:,.2f}</span>
                <div style="font-size: 0.8rem; color: #999;">{activity['time'][:19] if activity['time'] else 'Just now'}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    if not recent_activities:
        st.info("No recent activity")

# ================= UPLOAD INVOICE PAGE =================
def upload_invoice_page():
    st.markdown('<h1 class="main-header">Upload Invoice</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">Upload an invoice (image or PDF). The system will extract details and store them in your database. Supports 50+ currencies including VND, USD, EUR, etc.</p>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose invoice file",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Upload invoice from customer"
    )
    
    if uploaded_file is not None:
        with st.spinner("Processing invoice with OCR..."):
            file_path = handle_uploaded_file(uploaded_file)
            ocr_result = process_document(file_path)
        
        if ocr_result and ocr_result.get('success'):
            st.success("✅ OCR completed!")
            
            st.subheader("📊 Extracted Information")
            
            if ocr_result.get('formatted_amount') and ocr_result.get('formatted_amount') != 'N/A':
                st.info(f"🔍 OCR detected: **{ocr_result.get('formatted_amount')}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                try:
                    extracted_amount = float(ocr_result.get('amount', 0)) if ocr_result.get('amount') not in ['N/A', 'Not Found'] else 0.0
                except:
                    extracted_amount = 0.0
                
                amount = st.number_input(
                    "Invoice Amount",
                    value=extracted_amount,
                    step=100.0
                )
                
                detected_currency = ocr_result.get('currency', 'USD')
                st.caption(f"🔍 Detected currency: {detected_currency}")
                
                use_detected = st.checkbox(f"Use detected currency ({detected_currency})", value=True)
                
                if use_detected:
                    currency = detected_currency
                    st.text_input("Currency", value=currency, disabled=True, key="currency_display")
                else:
                    currency = st.text_input("Enter Currency Code", value="USD", placeholder="e.g., VND, USD, PHP, PKR").upper()
            
            with col2:
                from_company = st.text_input("Customer Name", value=ocr_result.get('company_name', ''))
                invoice_date = st.date_input("Invoice Date", value=datetime.now(), key="invoice_date_main")
                due_date = st.date_input("Due Date", value=datetime.now(), key="due_date_main")
            
            if ocr_result.get('bank_name') and ocr_result.get('bank_name') != "Not Specified":
                st.info(f"🏦 Detected bank: {ocr_result.get('bank_name')}")
            
            invoice_number = st.text_input("Invoice Number", value=f"INV-{datetime.now().strftime('%Y%m%d')}")
            
            if st.button("💾 Save Invoice to Database", type="primary"):
                result = upload_invoice(
                    invoice_number=invoice_number,
                    amount=amount,
                    currency=currency,
                    from_company=from_company,
                    to_company=company_name,
                    invoice_date=invoice_date.strftime("%Y-%m-%d"),
                    due_date=due_date.strftime("%Y-%m-%d"),
                    file_path=file_path
                )
                
                if result.get('success'):
                    st.session_state.last_invoice = result
                    st.success(f"✅ Invoice {invoice_number} saved! ID: {result['invoice_id']}")
                    st.balloons()
                else:
                    st.error(f"Failed: {result.get('message')}")
        else:
            st.error(f"OCR failed: {ocr_result.get('error', 'Unknown error')}. Please try again or enter details manually.")

# ================= UPLOAD PAYMENT PAGE =================
def upload_payment_page():
    st.markdown('<h1 class="main-header">Upload Bank Statement</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">Upload a bank statement or payment receipt. The system will match it to the correct invoice. Supports 50+ currencies.</p>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose bank statement file",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Upload bank statement from customer payment"
    )
    
    if uploaded_file is not None:
        with st.spinner("Processing payment document..."):
            file_path = handle_uploaded_file(uploaded_file)
            ocr_result = process_document(file_path)
        
        if ocr_result and ocr_result.get('success'):
            st.success("✅ OCR completed!")
            
            # Display extracted payment information
            st.subheader("📊 Extracted Payment Information")
            
            # Show what OCR detected
            if ocr_result.get('formatted_amount') and ocr_result.get('formatted_amount') != 'N/A':
                st.info(f"🔍 OCR detected: **{ocr_result.get('formatted_amount')}**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                try:
                    extracted_amount = float(ocr_result.get('amount', 0)) if ocr_result.get('amount') not in ['N/A', 'Not Found'] else 0.0
                except:
                    extracted_amount = 0.0
                
                payment_amount = st.number_input(
                    "Payment Amount",
                    value=extracted_amount,
                    step=100.0,
                    help="Enter the amount received"
                )
                
                # Get detected currency
                detected_currency = ocr_result.get('currency', 'USD')
                st.caption(f"🔍 Detected currency: {detected_currency}")
                
                # Allow user to use detected or enter custom
                use_detected = st.checkbox(f"Use detected currency ({detected_currency})", value=True)
                
                if use_detected:
                    payment_currency = detected_currency
                    st.text_input("Currency", value=payment_currency, disabled=True, key="payment_currency_display")
                else:
                    payment_currency = st.selectbox(
                        "Payment Currency",
                        ["MYR", "USD", "EUR", "GBP", "SGD", "CNY", "JPY", "AUD"],
                        help="Select the currency of the payment received"
                    )
            
            with col2:
                from_company = st.text_input("From (Customer Name)", value=ocr_result.get('company_name', '') or "Unknown Customer")
                payment_date = st.date_input("Payment Date", value=datetime.now(), key="payment_date_main")
                reference = st.text_input("Reference Number (optional)", placeholder="REF-12345")
            
            # Show pending invoices for this customer
            pending_invoices = [inv for inv in get_all_invoices() if inv.get('from_company') == from_company and inv.get('status') in ['PENDING', 'PARTIAL']]
            
            if pending_invoices:
                st.markdown("### 📋 Pending Invoices for This Customer")
                for inv in pending_invoices:
                    st.caption(f"• {inv.get('invoice_number')}: {inv.get('currency')} {inv.get('remaining_balance', inv.get('amount')):,.2f} (Status: {inv.get('status')})")
                
                # Auto-match button
                if st.button("🔍 Match Payment to Invoice", type="primary"):
                    with st.spinner("Matching payment..."):
                        result = match_bank_statement(
                            payment_amount=payment_amount,
                            payment_currency=payment_currency,
                            payment_date=payment_date.strftime("%Y-%m-%d"),
                            from_company=from_company,
                            to_company=company_name,
                            reference=reference or None,
                            file_path=file_path
                        )
                    
                    st.session_state.last_payment = result
                    
                    st.markdown("---")
                    st.subheader("📊 Match Result")
                    
                    if result.get('match_found'):
                        st.markdown(f'<div class="success-box">✅ {result.get("message")}</div>', unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Match Confidence", result.get('match_confidence', 'N/A'))
                            st.metric("Confidence Score", f"{result.get('confidence_score', 0)}%")
                        with col2:
                            if result.get('matched_invoice'):
                                inv = result['matched_invoice']
                                st.metric("Matched Invoice", inv.get('invoice_number', 'N/A'))
                                st.metric("Action Needed", result.get('action_needed', 'N/A'))
                    else:
                        st.markdown(f'<div class="warning-box">⚠️ {result.get("message")}</div>', unsafe_allow_html=True)
                    
                    if result.get('success'):
                        st.balloons()
            else:
                st.warning(f"No pending invoices found for {from_company}")
                
                # Manual reconciliation section
                st.markdown("### 📝 Manual Reconciliation")
                st.caption("No pending invoice found. You can manually enter invoice details below.")
                
                col1, col2 = st.columns(2)
                with col1:
                    invoice_amount_manual = st.number_input("Original Invoice Amount", min_value=0.0, value=135.94, step=100.0)
                    invoice_currency_manual = st.selectbox("Invoice Currency", ["USD", "EUR", "GBP", "SGD", "MYR"])
                with col2:
                    bank_manual = st.selectbox("Bank", ["Maybank", "CIMB", "Public Bank", "RHB", "Hong Leong"])
                    payment_date_manual = st.date_input("Payment Date", value=datetime.now(), key="manual_payment_date")
                
                if st.button("🔍 Manually Reconcile", type="primary"):
                    # Convert payment currency to MYR if needed
                    if payment_currency == "MYR":
                        payment_amount_myr = payment_amount
                    else:
                        conversion_rate_data = get_live_rate(payment_currency, payment_date_manual.strftime("%Y-%m-%d"))
                        conversion_rate = conversion_rate_data.get('rate', 1)
                        payment_amount_myr = payment_amount * conversion_rate
                    
                    rate_data = get_live_rate(invoice_currency_manual, payment_date_manual.strftime("%Y-%m-%d"))
                    market_rate = rate_data.get('rate', 4.25)
                    
                    markup_data = predict_markup(bank_manual, invoice_currency_manual, invoice_amount_manual)
                    markup = markup_data.get('predicted_markup', 0.025)
                    
                    expected_calculation = calculate_complete_before(
                        invoice_amount=invoice_amount_manual,
                        currency=invoice_currency_manual,
                        bank=bank_manual,
                        markup=markup,
                        market_rate=market_rate
                    )
                    expected_amount_myr = expected_calculation['final_amount']
                    
                    difference = payment_amount_myr - expected_amount_myr
                    difference_percent = (difference / expected_amount_myr) * 100 if expected_amount_myr > 0 else 0
                    
                    st.markdown("---")
                    st.subheader("📊 Reconciliation Result")
                    
                    if abs(difference_percent) < 0.5:
                        st.markdown('<div class="success-box">✅ MATCHED - Payment is correct</div>', unsafe_allow_html=True)
                    elif abs(difference_percent) < 3:
                        st.markdown('<div class="warning-box">⚠️ NEEDS ATTENTION - Small difference detected</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="warning-box">❌ CONCERNING - Significant discrepancy</div>', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Expected Amount", f"RM {expected_amount_myr:,.2f}")
                    with col2:
                        st.metric("Actual Received", f"{payment_amount} {payment_currency} → RM {payment_amount_myr:,.2f}")
                    with col3:
                        st.metric("Difference", f"RM {difference:,.2f} ({difference_percent:.1f}%)")
                    
                    # AI explanation if available
                    if use_llm:
                        with st.spinner("🤖 Analyzing discrepancy..."):
                            try:
                                explanation = gemini.explain_discrepancy(
                                    expected=expected_amount_myr,
                                    actual=payment_amount_myr,
                                    difference=difference,
                                    percent=difference_percent
                                )
                                st.markdown(f'<div class="info-box">🤖 {explanation}</div>', unsafe_allow_html=True)
                            except:
                                pass
                    
                    # Save button for manual
                    if st.button("💾 Save Payment Record", key="save_manual"):
                        with st.spinner("Saving to database..."):
                            # Save payment using match_bank_statement
                            payment_result = match_bank_statement(
                                payment_amount=payment_amount,
                                payment_currency=payment_currency,
                                payment_date=payment_date_manual.strftime("%Y-%m-%d"),
                                from_company=from_company,
                                to_company=company_name,
                                reference=reference or None,
                                file_path=file_path
                            )
                            
                            if payment_result.get('success'):
                                st.success(f"✅ Payment saved! {payment_result.get('message')}")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"Failed to save payment: {payment_result.get('message')}")
        else:
            st.error(f"OCR failed: {ocr_result.get('error', 'Unknown error')}. Please try again.")

# ================= PREDICT FEES PAGE =================
def quick_calculator_page():
    st.markdown('<h1 class="main-header">⚡ Quick Fee Calculator</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">Quickly estimate how much MYR you\'ll receive after bank fees and markup. No file upload needed.</p>', unsafe_allow_html=True)
    # ========== OPTION SELECTION ==========
    st.markdown("### Input Method")
    st.markdown('<p style="color: #666; margin-bottom: 0.75rem;">Choose how you want to enter invoice details</p>', unsafe_allow_html=True)
    
    input_method = st.radio(
        "",
        ["✏️ Manual Input", "📸 Upload Invoice (OCR)"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # ========== OPTION 1: MANUAL INPUT ==========
    if input_method == "✏️ Manual Input":
        st.markdown("### Invoice Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<p style="color: #666; margin-bottom: 0.25rem;">Invoice Amount</p>', unsafe_allow_html=True)
            amount = st.number_input(
                "", 
                min_value=0.0, 
                value=10000.0, 
                step=1000.0,
                placeholder="Enter amount",
                label_visibility="collapsed"
            )
            
            st.markdown('<p style="color: #666; margin-bottom: 0.25rem; margin-top: 1.2rem;">Currency</p>', unsafe_allow_html=True)
            currency = st.selectbox(
                "", 
                ["USD", "EUR", "GBP", "SGD", "MYR"],
                label_visibility="collapsed"
            )
        
        with col2:
            st.markdown('<p style="color: #666; margin-bottom: 0.25rem;">Choice of Bank</p>', unsafe_allow_html=True)
            bank = st.selectbox(
                "", 
                ["Maybank", "CIMB", "Public Bank", "RHB", "Hong Leong"],
                label_visibility="collapsed"
            )
            st.caption("💰 Transaction fee: Fixed per bank (no need to enter)")
        
        # Center the button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🧮 Calculate", type="primary", use_container_width=True):
                if amount <= 0:
                    st.error("Please enter a valid invoice amount")
                else:
                    with st.spinner("Fetching market rate and calculating..."):
                        # Get live rate
                        rate_data = get_live_rate(currency)
                        market_rate = rate_data.get('rate', 4.25)
                        
                        # Predict markup
                        markup_data = predict_markup(bank, currency, amount)
                        markup = markup_data.get('predicted_markup', 0.025)
                        
                        # Calculate
                        calculation = calculate_complete_before(
                            invoice_amount=amount,
                            currency=currency,
                            bank=bank,
                            markup=markup,
                            market_rate=market_rate
                        )
                        
                        st.session_state.prediction_result = calculation
                        
                        # Display results
                        st.markdown("---")
                        st.subheader("📊 Prediction Result")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Market Rate", f"1 {currency} = RM {market_rate:.4f}")
                        with col2:
                            st.metric("Bank Markup", f"{markup*100:.2f}%")
                        with col3:
                            st.metric("💰 You Will Receive", f"RM {calculation['final_amount']:,.2f}")
                        
                        with st.expander("📋 Detailed Fee Breakdown"):
                            st.write(f"**Invoice Amount:** {currency} {amount:,.2f}")
                            st.write(f"**Bank Rate:** 1 {currency} = RM {calculation['bank_rate']:.4f}")
                            st.write(f"**Amount Before Fees:** RM {calculation['amount_before_fees']:,.2f}")
                            st.write(f"**Fixed Fee:** RM {calculation['fees']['fixed']:.2f}")
                            if calculation['fees']['percent'] > 0:
                                st.write(f"**Percentage Fee:** {calculation['fees']['percent_rate']} = RM {calculation['fees']['percent_amount']:.2f}")
                            st.write(f"**Total Fees:** RM {calculation['fees']['total']:.2f}")
                        
                        # ========== AI EXPLANATION ==========
                        if use_llm:
                            with st.spinner("🤖 Generating AI explanation..."):
                                explanation = st.session_state.gemini.explain_prediction(
                                    amount, currency, bank, market_rate, markup, calculation['final_amount']
                                )
                                st.markdown(f'<div class="info-box">🤖 {explanation}</div>', unsafe_allow_html=True)
                        
                        # ========== SAVE TO HISTORY BUTTON ==========
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            if st.button("💾 Save to History", use_container_width=True):
                                transaction = {
                                    "type": "prediction",
                                    "amount": amount,
                                    "currency": currency,
                                    "bank": bank,
                                    "predicted_amount": calculation['final_amount'],
                                    "market_rate": market_rate,
                                    "markup": markup,
                                    "total_fees": calculation['fees']['total'],
                                    "timestamp": datetime.now().isoformat()
                                }
                                store_transaction(transaction)
                                st.success("✅ Saved to history!")
    
    # ========== OPTION 2: OCR UPLOAD ==========
    else:
        st.markdown("### Upload Invoice for Auto-Extraction")
        st.markdown('<p style="color: #666; margin-bottom: 1rem;">Upload invoice image for OCR processing</p>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Browse Invoice Image",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            help="Upload invoice from customer - amount, currency, and bank will be auto-detected",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            with st.spinner("Processing invoice with OCR..."):
                file_path = handle_uploaded_file(uploaded_file)
                ocr_result = process_document(file_path)
            
            if ocr_result and ocr_result.get('success'):
                st.success("✅ OCR completed!")
                
                st.markdown("### 📊 Extracted Information (Please Confirm)")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('<p style="color: #666; margin-bottom: 0.25rem;">Invoice Amount</p>', unsafe_allow_html=True)
                    try:
                        extracted_amount = float(ocr_result.get('amount', 0)) if ocr_result.get('amount') not in ['N/A', 'Not Found'] else 0.0
                    except:
                        extracted_amount = 0.0
                    
                    amount = st.number_input(
                        "",
                        value=extracted_amount,
                        step=100.0,
                        placeholder="Enter amount",
                        label_visibility="collapsed"
                    )
                    
                    st.markdown('<p style="color: #666; margin-bottom: 0.25rem; margin-top: 1.2rem;">Currency</p>', unsafe_allow_html=True)
                    currency_options = ["USD", "MYR", "EUR", "GBP", "SGD"]
                    default_currency = ocr_result.get('currency', 'USD')
                    default_index = currency_options.index(default_currency) if default_currency in currency_options else 0
                    
                    currency = st.selectbox(
                        "",
                        currency_options,
                        index=default_index,
                        label_visibility="collapsed"
                    )
                
                with col2:
                    st.markdown('<p style="color: #666; margin-bottom: 0.25rem;">Choice of Bank</p>', unsafe_allow_html=True)
                    bank_options = ["Maybank", "CIMB", "Public Bank", "RHB", "Hong Leong"]
                    extracted_bank = ocr_result.get('bank_name', '')
                    default_bank_index = bank_options.index(extracted_bank) if extracted_bank in bank_options else 0
                    
                    bank = st.selectbox(
                        "",
                        bank_options,
                        index=default_bank_index,
                        label_visibility="collapsed"
                    )
                    st.caption("💰 Transaction fee: Fixed per bank (no need to enter)")
                
                # Show extracted company name for info
                if ocr_result.get('company_name') and ocr_result.get('company_name') != "N/A":
                    st.info(f"📌 Customer/Vendor detected: {ocr_result.get('company_name')}")
                
                # Center the button
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🔮 Calculate with Extracted Data", type="primary", use_container_width=True):
                        if amount <= 0:
                            st.error("Please enter a valid invoice amount")
                        else:
                            with st.spinner("Fetching market rate and calculating..."):
                                # Get live rate
                                rate_data = get_live_rate(currency)
                                market_rate = rate_data.get('rate', 4.25)
                                
                                # Predict markup
                                markup_data = predict_markup(bank, currency, amount)
                                markup = markup_data.get('predicted_markup', 0.025)
                                
                                # Calculate
                                calculation = calculate_complete_before(
                                    invoice_amount=amount,
                                    currency=currency,
                                    bank=bank,
                                    markup=markup,
                                    market_rate=market_rate
                                )
                                
                                st.session_state.prediction_result = calculation
                                
                                # Display results
                                st.markdown("---")
                                st.subheader("📊 Prediction Result")
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Market Rate", f"1 {currency} = RM {market_rate:.4f}")
                                with col2:
                                    st.metric("Bank Markup", f"{markup*100:.2f}%")
                                with col3:
                                    st.metric("💰 You Will Receive", f"RM {calculation['final_amount']:,.2f}")
                                
                                with st.expander("📋 Detailed Fee Breakdown"):
                                    st.write(f"**Invoice Amount:** {currency} {amount:,.2f}")
                                    st.write(f"**Bank Rate:** 1 {currency} = RM {calculation['bank_rate']:.4f}")
                                    st.write(f"**Amount Before Fees:** RM {calculation['amount_before_fees']:,.2f}")
                                    st.write(f"**Fixed Fee:** RM {calculation['fees']['fixed']:.2f}")
                                    if calculation['fees']['percent'] > 0:
                                        st.write(f"**Percentage Fee:** {calculation['fees']['percent_rate']} = RM {calculation['fees']['percent_amount']:.2f}")
                                    st.write(f"**Total Fees:** RM {calculation['fees']['total']:.2f}")
                                
                                # ========== AI EXPLANATION ==========
                                if use_llm:
                                    with st.spinner("🤖 Generating AI explanation..."):
                                        explanation = st.session_state.gemini.explain_prediction(
                                            amount, currency, bank, market_rate, markup, calculation['final_amount']
                                        )
                                        st.markdown(f'<div class="info-box">🤖 {explanation}</div>', unsafe_allow_html=True)
                                
                                # ========== SAVE TO HISTORY BUTTON ==========
                                col1, col2, col3 = st.columns([1, 2, 1])
                                with col2:
                                    if st.button("💾 Save to History", use_container_width=True):
                                        transaction = {
                                            "type": "prediction_ocr",
                                            "amount": amount,
                                            "currency": currency,
                                            "bank": bank,
                                            "predicted_amount": calculation['final_amount'],
                                            "market_rate": market_rate,
                                            "markup": markup,
                                            "total_fees": calculation['fees']['total'],
                                            "ocr_source": ocr_result.get('company_name', 'Unknown'),
                                            "timestamp": datetime.now().isoformat()
                                        }
                                        store_transaction(transaction)
                                        st.success("✅ Saved to history!")
            else:
                st.error(f"OCR failed: {ocr_result.get('error', 'Unknown error')}. Please try manual input.")

# ================= HISTORY PAGE =================
def history_page():
    st.markdown('<h1 class="main-header">Transaction History</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">View and search all invoices and payments.</p>', unsafe_allow_html=True)
    
    # Get data
    invoices = get_all_invoices()
    payments = get_all_payments()
    
    # ========== COMBINE AND PREPARE DATA ==========
    combined_transactions = []
    
    # Add invoices
    for inv in invoices:
        combined_transactions.append({
            "Type": "Invoice",
            "ID": inv.get('invoice_number', 'N/A'),
            "Customer": inv.get('from_company', 'N/A'),
            "Amount": f"{inv.get('currency', 'MYR')} {inv.get('amount', 0):,.2f}",
            "Amount_RM": inv.get('amount', 0),  # For sorting
            "Currency": inv.get('currency', 'MYR'),
            "Status": inv.get('status', 'PENDING'),
            "Date": inv.get('invoice_date', '')[:10] if inv.get('invoice_date') else '',
            "Reference": inv.get('invoice_number', 'N/A'),
            "Remaining": inv.get('remaining_balance', 0)
        })
    
    # Add payments
    for pay in payments:
        combined_transactions.append({
            "Type": "Payment",
            "ID": pay.get('id', 'N/A')[:8],
            "Customer": pay.get('from_company', 'N/A'),
            "Amount": f"{pay.get('currency', 'MYR')} {pay.get('amount', 0):,.2f}",
            "Amount_RM": pay.get('amount', 0),  # For sorting
            "Currency": pay.get('currency', 'MYR'),
            "Status": pay.get('status', 'COMPLETED') if pay.get('status') != 'UNMATCHED' else 'PENDING MATCH',
            "Date": pay.get('date', '')[:10] if pay.get('date') else pay.get('timestamp', '')[:10] if pay.get('timestamp') else '',
            "Reference": pay.get('reference', 'N/A'),
            "Matched To": pay.get('matched_invoice_id', 'Unmatched')[:8] if pay.get('matched_invoice_id') else 'Unmatched'
        })
    
    if not combined_transactions:
        st.info("No transactions yet. Upload an invoice or bank statement to get started.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(combined_transactions)
    
    # Sort by date (most recent first)
    df = df.sort_values(by='Date', ascending=False)
    
    # ========== SEARCH AND FILTERS ==========
    st.markdown("### Filter Transactions")
    
    col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 1.5])
    
    with col1:
        search_term = st.text_input("Search by ID, customer, or reference", placeholder="e.g., INV-001, Acme Corp, PO-12345")
    
    with col2:
        type_filter = st.selectbox("Type", ["All", "Invoice", "Payment"])
    
    with col3:
        status_options = ["All", "PAID", "PENDING", "PARTIAL", "COMPLETED", "UNMATCHED", "PENDING MATCH"]
        status_filter = st.selectbox("Status", status_options)
    
    with col4:
        # Date range filter
        min_date = df['Date'].min() if not df['Date'].isna().all() else datetime.now().strftime("%Y-%m-%d")
        max_date = df['Date'].max() if not df['Date'].isna().all() else datetime.now().strftime("%Y-%m-%d")
        date_range = st.date_input("Date Range", [])
    
    # Apply filters
    filtered_df = df.copy()
    
    # Search filter
    if search_term:
        search_term_lower = search_term.lower()
        filtered_df = filtered_df[
            filtered_df['ID'].str.lower().str.contains(search_term_lower, na=False) |
            filtered_df['Customer'].str.lower().str.contains(search_term_lower, na=False) |
            filtered_df['Reference'].str.lower().str.contains(search_term_lower, na=False)
        ]
    
    # Type filter
    if type_filter != "All":
        filtered_df = filtered_df[filtered_df['Type'] == type_filter]
    
    # Status filter
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['Status'] == status_filter]
    
    # Date filter
    if date_range and len(date_range) == 2:
        start_date = date_range[0].strftime("%Y-%m-%d")
        end_date = date_range[1].strftime("%Y-%m-%d")
        filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]
    
    # ========== DISPLAY RESULTS ==========
    st.markdown("---")
    
    # Show row count
    st.markdown(f"### Transactions")
    
    # Select display columns
    display_cols = ['Type', 'ID', 'Customer', 'Amount', 'Status', 'Date', 'Reference']
    
    # Add Matched To for payments
    if 'Matched To' in filtered_df.columns:
        display_cols.append('Matched To')
    
    # Prepare display DataFrame
    display_df = filtered_df[display_cols].copy()
    
    # Style the DataFrame
    def color_status(val):
        if val == 'PAID' or val == 'COMPLETED':
            return 'color: #2E7D32; font-weight: bold;'
        elif val == 'PENDING' or val == 'PENDING MATCH':
            return 'color: #ED6C02; font-weight: bold;'
        elif val == 'PARTIAL':
            return 'color: #1E3A5F; font-weight: bold;'
        elif val == 'UNMATCHED':
            return 'color: #D32F2F; font-weight: bold;'
        return ''
    
    def color_type(val):
        if val == 'Invoice':
            return 'color: #1E3A5F; font-weight: bold;'
        elif val == 'Payment':
            return 'color: #2E7D32; font-weight: bold;'
        return ''
    
    # Apply styling
    styled_df = display_df.style.applymap(color_status, subset=['Status'])
    styled_df = styled_df.applymap(color_type, subset=['Type'])
    
    # Display with custom CSS for better appearance
    st.dataframe(
        styled_df, 
        use_container_width=True,
        column_config={
            "Type": st.column_config.TextColumn("Type", width="small"),
            "ID": st.column_config.TextColumn("ID", width="medium"),
            "Customer": st.column_config.TextColumn("Customer", width="medium"),
            "Amount": st.column_config.TextColumn("Amount", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Date": st.column_config.DateColumn("Date", width="small"),
            "Reference": st.column_config.TextColumn("Reference", width="medium"),
            "Matched To": st.column_config.TextColumn("Matched To", width="small")
        }
    )
    
    # ========== SUMMARY STATISTICS ==========
    st.markdown("---")
    st.markdown("### Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_invoiced = filtered_df[filtered_df['Type'] == 'Invoice']['Amount_RM'].sum() if 'Amount_RM' in filtered_df.columns else 0
        st.markdown(f"""
        <div style="background-color: white; padding: 0.75rem; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px;">
                <i class="bi bi-coin" style="font-size: 1.2rem; color: #1E3A5F;"></i>
                <span style="color: #666; font-size: 0.8rem;">Total Invoiced</span>
            </div>
            <p style="font-size: 1.3rem; font-weight: bold; margin: 0; color: #1E3A5F;">RM {total_invoiced:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        total_paid = filtered_df[filtered_df['Status'].isin(['PAID', 'COMPLETED'])]['Amount_RM'].sum() if 'Amount_RM' in filtered_df.columns else 0
        st.markdown(f"""
        <div style="background-color: white; padding: 0.75rem; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px;">
                <i class="bi bi-wallet-fill" style="font-size: 1.2rem; color: #2E7D32;"></i>
                <span style="color: #666; font-size: 0.8rem;">Total Received</span>
            </div>
            <p style="font-size: 1.3rem; font-weight: bold; margin: 0; color: #2E7D32;">RM {total_paid:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        pending_count = len(filtered_df[filtered_df['Status'].isin(['PENDING', 'PARTIAL'])])
        st.markdown(f"""
        <div style="background-color: white; padding: 0.75rem; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px;">
                <i class="bi bi-receipt" style="font-size: 1.2rem; color: #ED6C02;"></i>
                <span style="color: #666; font-size: 0.8rem;">Pending</span>
            </div>
            <p style="font-size: 1.3rem; font-weight: bold; margin: 0; color: #ED6C02;">{pending_count}</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        unmatched_count = len(filtered_df[filtered_df['Status'] == 'UNMATCHED'])
        st.markdown(f"""
        <div style="background-color: white; padding: 0.75rem; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px;">
                <i class="bi bi-exclamation-circle" style="font-size: 1.2rem; color: #D32F2F;"></i>
                <span style="color: #666; font-size: 0.8rem;">Unmatched</span>
            </div>
            <p style="font-size: 1.3rem; font-weight: bold; margin: 0; color: #D32F2F;">{unmatched_count}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ========== EXPORT BUTTONS ==========
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📥 Export to CSV", width='stretch'):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if st.button("📄 Export to PDF", width='stretch'):
            result = generate_report(filtered_df.to_dict('records'), "pdf")
            if result.get('success'):
                st.success(f"✅ PDF saved: {result['reports']['pdf']['filepath']}")
            else:
                st.error("Export failed")

# ================= REPORTS PAGE =================
def reports_page():
    st.markdown('<h1 class="main-header">Export Reports</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; margin-bottom: 2rem;">Export transactions and generate financial reports.</p>', unsafe_allow_html=True)
    
    invoices = get_all_invoices()
    payments = get_all_payments()
    calculations = get_all_transactions()
    
    total_invoiced = sum(inv.get('amount', 0) for inv in invoices)
    total_paid = sum(pay.get('amount', 0) for pay in payments if pay.get('status') == 'MATCHED')
    total_outstanding = sum(inv.get('remaining_balance', 0) for inv in invoices if inv.get('status') in ['PENDING', 'PARTIAL'])
    
    paid_percentage = (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0
    outstanding_percentage = (total_outstanding / total_invoiced * 100) if total_invoiced > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div style="background-color: white; padding: 1rem; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center;">
            <p style="color: #666; margin-bottom: 5px;"><i class="bi bi-cash-coin"></i> Total Invoiced</p>
            <p style="font-size: 1.8rem; font-weight: bold; margin: 0; color: #1E3A5F;">RM {total_invoiced:,.2f}</p>
            <p style="color: #999; font-size: 0.7rem; margin-top: 5px;">All time</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background-color: white; padding: 1rem; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center;">
            <p style="color: #666; margin-bottom: 5px;"><i class="bi bi-check-circle-fill"></i> Total Paid</p>
            <p style="font-size: 1.8rem; font-weight: bold; margin: 0; color: #2E7D32;">RM {total_paid:,.2f}</p>
            <p style="color: #999; font-size: 0.7rem; margin-top: 5px;">~ {paid_percentage:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background-color: white; padding: 1rem; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center;">
            <p style="color: #666; margin-bottom: 5px;"><i class="bi bi-exclamation-triangle-fill"></i> Outstanding</p>
            <p style="font-size: 1.8rem; font-weight: bold; margin: 0; color: #ED6C02;">RM {total_outstanding:,.2f}</p>
            <p style="color: #999; font-size: 0.7rem; margin-top: 5px;">~ {outstanding_percentage:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background-color: #F8F9FA; padding: 1.2rem; border-radius: 12px; border: 1px solid #E9ECEF; height: 100%;">
            <i class="bi bi-filetype-csv" style="font-size: 2rem; color: #1E3A5F;"></i>
            <h3 style="margin-top: 0.5rem; margin-bottom: 0.5rem;">Export to CSV</h3>
            <p style="color: #666; margin-bottom: 1rem;">Download all transactions as a CSV file</p>
        """, unsafe_allow_html=True)
        
        all_data = invoices + payments + calculations
        if all_data:
            csv_data = []
            for inv in invoices:
                csv_data.append({
                    "Type": "Invoice",
                    "ID": inv.get('invoice_number', 'N/A'),
                    "Customer": inv.get('from_company', 'N/A'),
                    "Amount": f"{inv.get('currency', 'MYR')} {inv.get('amount', 0):,.2f}",
                    "Status": inv.get('status', 'N/A'),
                    "Date": inv.get('invoice_date', ''),
                    "Reference": inv.get('invoice_number', 'N/A')
                })
            for pay in payments:
                csv_data.append({
                    "Type": "Payment",
                    "ID": pay.get('id', 'N/A')[:8],
                    "Customer": pay.get('from_company', 'N/A'),
                    "Amount": f"{pay.get('currency', 'MYR')} {pay.get('amount', 0):,.2f}",
                    "Status": pay.get('status', 'N/A'),
                    "Date": pay.get('date', ''),
                    "Reference": pay.get('reference', 'N/A')
                })
            for calc in calculations:
                csv_data.append({
                    "Type": "Calculation",
                    "ID": calc.get('id', 'N/A')[:8] if calc.get('id') else 'N/A',
                    "Customer": "N/A",
                    "Amount": f"{calc.get('currency', 'MYR')} {calc.get('amount', 0):,.2f}" if calc.get('amount') else "N/A",
                    "Status": calc.get('type', 'N/A'),
                    "Date": calc.get('timestamp', '')[:10] if calc.get('timestamp') else '',
                    "Reference": "N/A"
                })
            
            df_export = pd.DataFrame(csv_data)
            csv = df_export.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="📥 Export CSV",
                data=csv,
                file_name=f"treasury_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                type="primary"
            )
        else:
            st.warning("No data to export")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background-color: #F8F9FA; padding: 1.2rem; border-radius: 12px; border: 1px solid #E9ECEF; height: 100%;">
            <i class="bi bi-filetype-pdf" style="font-size: 2rem; color: #D32F2F;"></i>
            <h3 style="margin-top: 0.5rem; margin-bottom: 0.5rem;">Export to PDF</h3>
            <p style="color: #666; margin-bottom: 1rem;">Generate a comprehensive financial report</p>
        """, unsafe_allow_html=True)
        
        if st.button("📄 Generate PDF Report", use_container_width=True, type="primary"):
            all_data = invoices + payments + calculations
            if all_data:
                result = generate_report(all_data, "pdf")
                if result.get('success'):
                    st.success(f"✅ PDF saved: {result['reports']['pdf']['filepath']}")
                else:
                    st.error("Export failed")
            else:
                st.warning("No data to export")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("""
    <div style="background-color: #E3F2FD; padding: 0.75rem 1rem; border-radius: 8px; margin-top: 1rem;">
        <p style="margin: 0; font-size: 0.85rem; color: #1E3A5F;">
            <i class="bi bi-info-circle"></i> Report Period: Includes all transactions from inception to date
        </p>
    </div>
    """, unsafe_allow_html=True)

# ================= SIDEBAR =================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/currency-exchange.png", width=60)
    st.markdown("### Global Treasury Agent")
    
    # AI Status Indicator
    if st.session_state.llm_enabled:
        st.success("AI Assistant: READY")
    else:
        st.warning("AI Assistant: UNAVAILABLE")
        st.caption("Set GEMINI_API_KEY in .env to enable AI explanations")
    
    st.markdown("---")
    
    # Navigation buttons
    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state.page = "Dashboard"
        st.rerun()
    
    if st.button("📄 Upload Invoice", use_container_width=True):
        st.session_state.page = "Upload Invoice"
        st.rerun()
    
    if st.button("💰 Upload Payment", use_container_width=True):
        st.session_state.page = "Upload Payment"
        st.rerun()
    
    if st.button("⚡ Quick Calculator", use_container_width=True):
        st.session_state.page = "Quick Calculator"
        st.rerun()
    
    if st.button("📜 History", use_container_width=True):
        st.session_state.page = "History"
        st.rerun()
    
    if st.button("📊 Reports", use_container_width=True):
        st.session_state.page = "Reports"
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Company Info**")
    company_name = st.text_input("Your Company Name", "My Business")
    
    st.markdown("---")
    st.caption("v1.0 | Built for SMEs 🇲🇾")
    st.caption("Supports USD, MYR, EUR, GBP, SGD")

# Initialize session state for page
if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

# ================= PAGE ROUTING =================
if st.session_state.page == "Dashboard":
    dashboard_page()
elif st.session_state.page == "Upload Invoice":
    upload_invoice_page()
elif st.session_state.page == "Upload Payment":
    upload_payment_page()
elif st.session_state.page == "Quick Calculator":
    quick_calculator_page()
elif st.session_state.page == "History":
    history_page()
elif st.session_state.page == "Reports":
    reports_page()