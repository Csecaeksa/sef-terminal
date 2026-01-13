import streamlit as st
import yfinance as yf
import pandas as pd
import math
from fpdf import FPDF
import base64

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="SEF Terminal Pro", page_icon="🛡️", layout="wide")

# إخفاء شريط الأدوات العلوي لإعطاء مظهر احترافي
st.markdown("""
    <style>
    .stAppToolbar {display: none;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. الدوال الأساسية ---
def fetch_live_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="1mo")
        if df.empty: return None, None, None
        return round(df['Close'].iloc[-1], 2), round(df['Low'].min(), 2), round(df['High'].max(), 2)
    except: return None, None, None

def generate_pdf_link(content, ticker):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="SEF STRATEGIC ANALYSIS", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=10)
        # إضافة إخلاء المسؤولية في الـ PDF أيضاً
        disclaimer = "Disclaimer: Educational purposes only. Not financial advice."
        pdf.cell(200, 10, txt=disclaimer, ln=True, align='L')
        pdf.ln(5)
        pdf.cell(200, 10, txt="Created By Abu Yahia", ln=True, align='L') 
        pdf.ln(10)
        clean_text = content.encode('ascii', 'ignore').decode('ascii')
        for line in clean_text.split('\n'):
            pdf.cell(0, 8, txt=line, ln=True)
        pdf_output = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_output).decode()
        return f'<a href="data:application/octet-stream;base64,{b64}" download="SEF_{ticker}_Report.pdf" style="background-color: #ff4b4b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">📥 Download PDF Report</a>'
    except: return "⚠️ PDF Error"

# --- 3. واجهة المستخدم والتوقيع مع إخلاء المسؤولية ---
st.title("🛡️ SEF Terminal | Ultimate Hub")

# التعديل المطلوب: الاسم + إخلاء المسؤولية بالعربي والإنجليزي
st.markdown("""
    <div style='text-align: left; margin-top: -25px; margin-bottom: 25px;'>
        <div style='font-size: 1.3em; color: #333; font-weight: bold;'>🖋️ Created By Abu Yahia</div>
        <div style='font-size: 0.85em; color: #cc0000; margin-top: 5px; line-height: 1.4;'>
            ⚠️ <b>إخلاء مسؤولية:</b> هذا التطبيق للأغراض التعليمية فقط ولا يعتبر نصيحة مالية أو توصية بالبيع والشراء.<br>
            ⚠️ <b>Disclaimer:</b> This app is for educational purposes only and is not financial advice or a recommendation to buy/sell.
        </div>
    </div>
    """, unsafe_allow_html=True)

# إدارة الذاكرة
if 'p_val' not in st.session_state: st.session_state.update({'p_val': 33.90, 'a_val': 31.72, 't_val': 39.36})

st.markdown("---")

# صف المدخلات
c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.2, 1.2, 1.2, 1.2, 1.5])

with c1:
    ticker = st.text_input("Ticker Symbol", "2222.SR").upper()
with c2:
    p_in = st.number_input("Price", value=float(st.session_state['p_val']), step=0.01)
with c3:
    a_in = st.number_input("Anchor", value=float(st.session_state['a_val']), step=0.01)
with c4:
    t_in = st.number_input("Target", value=float(st.session_state['t_val']), step=0.01)
with c5:
    st.write("##")
    if st.button("🛰️ Radar", use_container_width=True):
        p, a, t = fetch_live_data(ticker)
        if p:
            st.session_state.update({'p_val': p, 'a_val': a, 't_val': t})
            st.rerun()
with c6:
    st.write("##")
    analyze_trigger = st.button("📊 Analyze", use_container_width=True)

st.markdown("---")

# --- 4. التحليل والنتائج ---
if analyze_trigger:
    risk_ps = abs(p_in - a_in)
    risk_amt = 1000.0 
    rr = (t_in - p_in) / risk_ps if risk_ps > 0 else 0
    qty = math.floor(risk_amt / risk_ps) if risk_ps > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Live Price", p_in)
    m2.metric("R:R Ratio", f"1:{round(rr, 2)}")
    m3.metric("Shares", qty)
    m4.metric("Risk Cash", risk_amt)

    # التقرير النصي
    full_report = f"SEF STRATEGIC ANALYSIS\nCreated By Abu Yahia\n--------------------\nTicker: {ticker}\nResult: {'Actionable' if rr >= 2 else 'Wait'}"
    st.code(full_report)
    st.markdown(generate_pdf_link(full_report, ticker), unsafe_allow_html=True)
