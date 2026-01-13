import streamlit as st
import yfinance as yf
import pandas as pd
import math
from fpdf import FPDF
import base64

# --- Page Configuration ---
st.set_page_config(page_title="SEF Terminal Pro", page_icon="🛡️", layout="wide")

# --- 1. Functions for Data & Reports ---
def get_radar_data(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1y")
        if data.empty: return None, None, "Invalid"
        # Calculate support (Anchor) and resistance for the last 20 days
        support = round(data['Low'].tail(20).min(), 2)
        resistance = round(data['High'].tail(20).max(), 2)
        status = "🛡️ Near Anchor Zone" if data['Close'].iloc[-1] < support * 1.05 else "🔥 Breakout"
        return support, resistance, status
    except:
        return None, None, "Error"

def generate_sef_full_text(ticker, price, anchor, target, rr, qty, status):
    return f"""
SEF STRATEGIC ANALYSIS REPORT
Ticker: {ticker} | Price: {price}

1. Trend / Structure
-------------------
- Status: {status}
- POI (Point of Interest): {anchor} (Institutional Floor)
- Liquidity Void: Target at {target}

2. Key Levels
-------------
- Anchor Level (SL): {anchor}
- Primary Target: {target}

3. Execution Details
--------------------
- Risk:Reward: 1:{round(rr, 2)}
- Recommended Qty: {qty} Shares

RISK MANAGEMENT:
"Protect your capital first. Trading is a marathon."
    """

def download_pdf(content, filename):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        clean_content = content.encode('ascii', 'ignore').decode('ascii')
        for line in clean_content.split('\n'):
            pdf.cell(0, 8, txt=line, ln=True)
        pdf_output = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_output).decode()
        return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}" style="background-color: #ff4b4b; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">📥 Download PDF Report</a>'
    except:
        return "Error creating PDF"

# --- 2. Main UI Layout ---
st.title("🛡️ SEF Terminal | Professional Hub")

# Sidebar
balance = st.sidebar.number_input("Portfolio Balance", value=100000)
risk_pct = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 1.0)

st.markdown("---")

# --- ROW 1: All Inputs and Buttons in ONE LINE ---
# Using 6 columns to keep buttons next to inputs
c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.2, 1.2, 1.2, 1.2, 1.5])

with c1:
    ticker = st.text_input("Ticker", "4009.SR").upper()
with c2:
    curr_p = st.number_input("Price", value=33.90)
with c3:
    # Anchor persistence using session_state
    if 'radar_val' not in st.session_state:
        st.session_state['radar_val'] = 31.72
    anc_p = st.number_input("Anchor", value=float(st.session_state['radar_val']))
with c4:
    tar_p = st.number_input("Target", value=39.36)
with c5:
    st.write("##") # Vertical alignment
    if st.button("🛰️ Radar", use_container_width=True):
        sup, res, stat = get_radar_data(ticker)
        if sup:
            st.session_state['radar_val'] = sup
            st.session_state['radar_status'] = stat
            st.rerun() # Refresh to update Anchor input box
with c6:
    st.write("##") # Vertical alignment
    run_btn = st.button("📊 Analyze", use_container_width=True)

st.markdown("---")

# --- 3. Results Section (Only shows after clicking Analyze) ---
if run_btn:
    risk_s = abs(curr_p - anc_p)
    rr = (tar_p - curr_p) / risk_s if risk_s > 0 else 0
    qty = math.floor((balance * (risk_pct/100)) / risk_s) if risk_s > 0 else 0
    status_label = st.session_state.get('radar_status', 'Forming')

    # Display Metrics
    st.subheader("📊 Execution Metrics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current Price", curr_p)
    m2.metric("R:R Ratio", f"1:{round(rr, 2)}")
    m3.metric("Shares to Buy", qty)
    m4.metric("Risk Amount", round(balance * (risk_pct/100), 2))

    # Display SEF Structural Report
    st.markdown("---")
    st.subheader("📄 SEF Structural Analysis")
    full_report = generate_sef_full_text(ticker, curr_p, anc_p, tar_p, rr, qty, status_label)
    st.code(full_report, language='text')
    
    # PDF Button
    pdf_link = download_pdf(full_report, f"SEF_{ticker}.pdf")
    st.markdown(pdf_link, unsafe_allow_html=True)

    # Chart
    st.subheader("📈 Technical Chart")
    hist = yf.Ticker(ticker).history(period="6mo")
    if not hist.empty:
        chart_df = hist[['Close']].copy()
        chart_df['Anchor'] = anc_p
        chart_df['Target'] = tar_p
        st.line_chart(chart_df)
    
    if rr >= 3:
        st.balloons()
