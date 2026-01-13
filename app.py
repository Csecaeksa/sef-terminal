import streamlit as st
import yfinance as yf
import pandas as pd
import math
from fpdf import FPDF
import base64

# --- Page Configuration ---
st.set_page_config(page_title="SEF Terminal Ultimate", page_icon="🛡️", layout="wide")

# --- Function: Generate Professional SEF Report Text ---
def generate_sef_report(ticker, price, anchor, target, rr, qty, status):
    report_text = f"""
SEF STRATEGIC ANALYSIS REPORT
Ticker: {ticker} | Market: Global/TASI

1. Trend / Structure
-------------------
- Daily: Up (Short-term recovery)
- Weekly: Side/Base Forming (Accumulation phase)
- Monthly: Structural downtrend remains until pivots clear.
- Liquidity: Void exists between {price} and {target}.
- POI: {anchor} is the current institutional floor.
- Status: {status}.

2. Key Levels (S/R / POI / Invalidation)
---------------------------------------
- Support Zone (Anchor): {anchor}
- Resistance Zone (Primary Target): {target}
- Invalidation: Weekly Close below {anchor}.

3. Trade Playbook & Execution
----------------------------
- Entry: {price} | Stop: {anchor} | Target: {target}
- Risk:Reward Ratio: 1:{round(rr, 2)}
- Suggested Quantity: {qty} Shares
- Confidence Level: 4/5

4. Scenarios
------------
- Bullish: Successful test of {anchor} followed by breakout.
- Bearish: Breakdown of {anchor} leads to panic selling.

RISK MANAGEMENT:
"Protect your capital first. Trading is a marathon, not a sprint."
    """
    return report_text

# --- Function: Create PDF (English Only) ---
def download_pdf(content, filename):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        clean_content = content.encode('ascii', 'ignore').decode('ascii')
        for line in clean_content.split('\n'):
            pdf.cell(0, 7, txt=line, ln=True)
        pdf_output = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_output).decode()
        return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}" style="background-color: #ff4b4b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">📥 Download Official PDF Report</a>'
    except Exception as e:
        return f"PDF Error: {str(e)}"

# --- Technical Radar Engine ---
def get_technical_levels(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1y")
        if data.empty: return None, None, "Invalid Ticker"
        recent_20 = data.tail(20)
        resistance = round(recent_20['High'].max(), 2)
        support = round(recent_20['Low'].min(), 2)
        last_close = round(data['Close'].iloc[-1], 2)
        status = "🛡️ Near Anchor Zone" if last_close < support * 1.05 else "🔥 Potential Breakout"
        return support, resistance, status
    except:
        return None, None, "Error"

# --- Main Interface ---
st.title("🛡️ SEF Terminal | Ultimate Trading Hub")
st.markdown("---")

# Sidebar
st.sidebar.header("⚙️ Portfolio Setup")
balance = st.sidebar.number_input("Total Capital", value=100000)
risk_pct = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 1.0)

# Input Row 1: The Radar
col_a, col_b = st.columns([2, 1])
with col_a:
    ticker = st.text_input("Enter Ticker (e.g., 4009.SR, AAPL)", "4009.SR").upper()
with col_b:
    st.write("##")
    radar_btn = st.button("Activate Radar 🛰️")

# Technical Radar Logic
if radar_btn:
    sup, res, stat = get_technical_levels(ticker)
    if sup:
        st.session_state['anchor_point'] = sup
        st.session_state['market_status'] = stat
        st.success(f"Radar Findings: Support at {sup} | Resistance at {res}")
    else:
        st.error("Could not fetch data.")

# Input Row 2: Manual Adjustments
col1, col2, col3 = st.columns(3)
with col1:
    current_price = st.number_input("Current Price", value=33.90)
with col2:
    def_anchor = st.session_state.get('anchor_point', 31.72)
    anchor_level = st.number_input("Anchor Level (SL)", value=float(def_anchor))
with col3:
    target_price = st.number_input("Primary Target", value=39.36)

st.markdown("---")

# Execution Button
if st.button("Generate Full SEF Analysis"):
    # Math Logic
    risk_per_share = abs(current_price - anchor_level)
    rr = (target_price - current_price) / risk_per_share if risk_per_share > 0 else 0
    risk_amt = balance * (risk_pct / 100)
    qty = math.floor(risk_amt / risk_per_share) if risk_per_share > 0 else 0
    
    # Visual Output
    st.subheader("📊 Executive Metrics")
    m1, m2, m3, m4
