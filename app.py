import streamlit as st
import yfinance as yf
import pandas as pd
import math
from fpdf import FPDF
import base64

# --- Page Configuration ---
st.set_page_config(page_title="SEF Terminal Pro", page_icon="🛡️", layout="wide")

# --- Helper Functions (PDF & Tech) ---
def generate_sef_report(ticker, price, anchor, target, rr, qty):
    return f"SEF REPORT: {ticker}\nPrice: {price}\nAnchor: {anchor}\nTarget: {target}\nR:R: 1:{round(rr,2)}\nQty: {qty}"

def download_pdf(content, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in content.split('\n'):
        pdf.cell(0, 10, txt=line, ln=True)
    pdf_output = pdf.output(dest='S').encode('latin-1')
    b64 = base64.b64encode(pdf_output).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}" style="background-color: #ff4b4b; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; font-weight: bold;">📥 PDF</a>'

# --- Main Interface ---
st.title("🛡️ SEF Terminal | Professional Hub")

# Sidebar for Portfolio
balance = st.sidebar.number_input("Portfolio Balance", value=100000)
risk_pct = st.sidebar.slider("Risk %", 0.5, 5.0, 1.0)

st.markdown("---")

# --- الفكرة هنا: وضع كل المدخلات والأزرار في صف واحد مقسم لـ 6 أعمدة ---
# 1: Ticker | 2: Price | 3: Anchor | 4: Target | 5: Radar Button | 6: Analyze Button
c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.2, 1.2, 1.2, 1.2, 1.5])

with c1:
    ticker = st.text_input("Ticker", "4009.SR").upper()
with c2:
    curr_p = st.number_input("Price", value=33.90)
with c3:
    # Anchor logic
    anc_val = st.session_state.get('radar_anchor', 31.72)
    anc_p = st.number_input("Anchor", value=float(anc_val))
with c4:
    tar_p = st.number_input("Target", value=39.36)
with c5:
    st.write("##") # للمحاذاة الرأسية
    if st.button("🛰️ Radar", use_container_width=True):
        try:
            data = yf.Ticker(ticker).history(period="1y")
            st.session_state['radar_anchor'] = round(data['Low'].tail(20).min(), 2)
            st.rerun() # لإعادة التحميل وتحديث رقم المرساة
        except: st.error("Error")
with c6:
    st.write("##") # للمحاذاة الرأسية
    run_analysis = st.button("📊 Analyze", use_container_width=True)

st.markdown("---")

# --- تنفيذ النتائج والشارت تحت بعض ---
if run_analysis:
    risk_s = abs(curr_p - anc_p)
    rr = (tar_p - curr_p) / risk_s if risk_s > 0 else 0
    qty = math.floor((balance * (risk_pct/100)) / risk_s) if risk_s > 0 else 0
    
    # 1. Metrics & Report in 2 columns
    res_col1, res_col2 = st.columns([1, 2])
    with res_col1:
        st.metric("Risk:Reward", f"1:{round(rr, 2)}")
        st.metric("Position Size", f"{qty} Shares")
        # PDF Button
        report = generate_sef_report(ticker, curr_p, anc_p, tar_p, rr, qty)
        st.markdown(download_pdf(report, f"SEF_{ticker}.pdf"), unsafe_allow_html=True)
    
    with res_col2:
        st.code(report, language='text')

    # 2. Chart (يظهر بعرض الصفحة كاملة)
    st.subheader(f"📈 {ticker} Technical Chart")
    hist = yf.Ticker(ticker).history(period="6mo")
    if not hist.empty:
        chart_df = hist[['Close']].copy()
        chart_df['Anchor'] = anc_p
        chart_df['Target'] = tar_p
        st.line_chart(chart_df)
        
    if rr >= 3:
        st.balloons()
