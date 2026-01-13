import streamlit as st
import yfinance as yf
import pandas as pd
import math
from fpdf import FPDF
import base64

# --- إعدادات الصفحة ---
st.set_page_config(page_title="SEF Terminal Pro", page_icon="🛡️", layout="wide")

# --- 1. دالة جلب البيانات (الرادار المطور) ---
def fetch_live_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="1mo")
        if df.empty: return None, None, None
        
        # السعر الحالي
        current_p = round(df['Close'].iloc[-1], 2)
        # المرساة (أدنى قاع في شهر)
        auto_anchor = round(df['Low'].min(), 2)
        # الهدف (أعلى قمة في شهر) - تم الإصلاح هنا
        auto_target = round(df['High'].max(), 2)
        
        return current_p, auto_anchor, auto_target
    except:
        return None, None, None

# --- 2. دالة توليد الـ PDF (إصلاح خطأ الـ Unicode) ---
def generate_pdf_link(content, ticker):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="SEF STRATEGIC ANALYSIS", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=11)
        # تنظيف النص من أي رموز غريبة تسبب UnicodeEncodeError
        clean_text = content.encode('ascii', 'ignore').decode('ascii')
        for line in clean_text.split('\n'):
            pdf.cell(0, 8, txt=line, ln=True)
        pdf_output = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_output).decode()
        return f'<a href="data:application/octet-stream;base64,{b64}" download="SEF_{ticker}_Report.pdf" style="background-color: #ff4b4b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; margin-top: 10px;">📥 Download PDF Report</a>'
    except: return "⚠️ PDF Error"

# --- 3. إدارة واجهة المستخدم ---
st.title("🛡️ SEF Terminal | Ultimate Hub")

balance = st.sidebar.number_input("Portfolio Balance", value=100000)
risk_pct = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 1.0)

# تخزين كل القيم في الـ Session State لتكون تفاعلية
if 'p_val' not in st.session_state: st.session_state['p_val'] = 33.90
if 'a_val' not in st.session_state: st.session_state['a_val'] = 31.72
if 't_val' not in st.session_state: st.session_state['t_val'] = 39.36

st.markdown("---")

# صف المدخلات - تم ربط Target Price بالذاكرة التفاعلية
c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.2, 1.2, 1.2, 1.2, 1.5])

with c1:
    ticker = st.text_input("Ticker Symbol", "4009.SR").upper()
with c2:
    p_in = st.number_input("Market Price", value=float(st.session_state['p_val']), step=0.01)
with c3:
    a_in = st.number_input("Anchor Level", value=float(st.session_state['a_val']), step=0.01)
with c4:
    # الآن الهدف يتغير تلقائياً مع الرادار
    t_in = st.number_input("Target Price", value=float(st.session_state['t_val']), step=0.01)
with c5:
    st.write("##")
    if st.button("🛰️ Radar", use_container_width=True):
        p, a, t = fetch_live_data(ticker)
        if p:
            st.session_state['p_val'] = p
            st.session_state['a_val'] = a
            st.session_state['t_val'] = t # تحديث الهدف تلقائياً
            st.rerun()
with c6:
    st.write("##")
    analyze_trigger = st.button("📊 Analyze", use_container_width=True)

st.markdown("---")

# --- 4. النتائج والتقييم ---
if analyze_trigger:
    risk_per_share = abs(p_in - a_in)
    risk_cash = balance * (risk_pct / 100)
    
    if risk_per_share > 0:
        rr = (t_in - p_in) / risk_per_share
        qty = math.floor(risk_cash / risk_per_share)
    else: rr, qty = 0, 0

    # تقييم النتيجة
    if rr >= 3: rr_advice = "🟢 EXCELLENT (Professional)"
    elif 2 <= rr < 3: rr_advice = "🟡 GOOD (Acceptable)"
    else: rr_advice = "🔴 DANGEROUS (Avoid)"

    # عرض المتريكس
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Live Price", p_in)
    m2.metric("R:R Ratio", f"1:{round(rr, 2)}")
    m3.metric("Shares", qty)
    m4.metric("Risk Cash", f"{round(risk_cash, 2)}")

    # بناء التقرير
    full_report = f"""
SEF STRATEGIC ANALYSIS REPORT
Ticker: {ticker} | Price: {p_in}
------------------------------------
1. LEVELS:
- Entry: {p_in} | Anchor (SL): {a_in} | Target: {t_in}

2. METRICS:
- R:R Ratio: 1:{round(rr, 2)}
- Quantity: {qty} Shares
- Total Risk: {round(risk_cash, 2)}

RESULT: {rr_advice}
"Capital preservation is the first priority."
    """
    st.markdown("### 📄 SEF Structural Analysis")
    st.code(full_report, language='text')
    st.markdown(generate_pdf_link(full_report, ticker), unsafe_allow_html=True)

    # الشارت (إصلاح خطأ EMA_200)
    hist = yf.Ticker(ticker).history(period="1y")
    if not hist.empty:
        c_data = hist[['Close']].copy()
        c_data['Anchor'] = a_in
        c_data['Target'] = t_in
        # إضافة المتوسط 200 بشكل صحيح
        c_data['EMA_200'] = c_data['Close'].ewm(span=200, adjust=False).mean()
        st.line_chart(c_data)
    
    if rr >= 3: st.balloons()
