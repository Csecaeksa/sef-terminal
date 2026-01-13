import streamlit as st
import yfinance as yf
import pandas as pd
import math
from fpdf import FPDF
import base64

# --- الإعدادات العامة ---
st.set_page_config(page_title="SEF Terminal Ultimate", page_icon="🛡️", layout="wide")

# --- دالة إنشاء التقرير النصي ---
def generate_sef_report(ticker, price, anchor, target, rr, qty, status):
    return f"""
SEF STRATEGIC ANALYSIS REPORT
Ticker: {ticker} | Price: {price}

1. Trend / Structure: {status}
2. Support (Anchor): {anchor}
3. Target: {target}
4. R:R Ratio: 1:{round(rr, 2)}
5. Position Size: {qty} Shares

"Capital preservation is the first priority."
    """

# --- دالة تحميل الـ PDF ---
def download_pdf(content, filename):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in content.split('\n'):
            pdf.cell(0, 10, txt=line, ln=True)
        pdf_output = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_output).decode()
        return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}" style="background-color: #ff4b4b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">📥 Download PDF Report</a>'
    except: return "PDF Error"

# --- محرك الرادار الفني ---
def get_tech(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1y")
        if data.empty: return None, None
        return round(data['Low'].tail(20).min(), 2), round(data['High'].tail(20).max(), 2)
    except: return None, None

# --- واجهة المستخدم الرئيسية ---
st.title("🛡️ SEF Terminal | Ultimate Hub")

# السايدبار
balance = st.sidebar.number_input("Portfolio Balance", value=100000)
risk_pct = st.sidebar.slider("Risk %", 0.5, 5.0, 1.0)

# --- الصف الأول: رمز السهم وزر الرادار ---
col_r1, col_r2 = st.columns([3, 1])
with col_r1:
    ticker = st.text_input("Ticker Symbol", "4009.SR").upper()
with col_r2:
    st.write("##") # للمحاذاة
    if st.button("Activate Radar 🛰️", use_container_width=True):
        sup, res = get_tech(ticker)
        if sup:
            st.session_state['anchor'] = sup
            st.success(f"Radar: Support @ {sup}")

# --- الصف الثاني: المدخلات وزر التحليل (كلهم جنب بعض) ---
c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
with c1:
    curr_p = st.number_input("Price", value=33.90)
with c2:
    anc_p = st.number_input("Anchor", value=float(st.session_state.get('anchor', 31.72)))
with c3:
    tar_p = st.number_input("Target", value=39.36)
with c4:
    st.write("##") # للمحاذاة
    run_analysis = st.button("Analyze & Report 📊", use_container_width=True)

st.markdown("---")

# --- تنفيذ التحليل عند الضغط على الزر ---
if run_analysis:
    risk_s = abs(curr_p - anc_p)
    rr = (tar_p - curr_p) / risk_s if risk_s > 0 else 0
    qty = math.floor((balance * (risk_pct/100)) / risk_s) if risk_s > 0 else 0
    
    # عرض النتائج
    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.metric("R:R Ratio", f"1:{round(rr, 2)}")
        st.metric("Quantity", f"{qty} Shares")
    with res_col2:
        report = generate_sef_report(ticker, curr_p, anc_p, tar_p, rr, qty, "Analysis Done")
        st.code(report)
        st.markdown(download_pdf(report, f"SEF_{ticker}.pdf"), unsafe_allow_html=True)
    
    # الشارت
    st.line_chart(yf.Ticker(ticker).history(period="6mo")['Close'])
