import streamlit as st
import yfinance as yf
import pandas as pd
import math
from fpdf import FPDF
import base64

# --- إعدادات الصفحة ---
st.set_page_config(page_title="SEF Terminal Pro", page_icon="🛡️", layout="wide")

# --- 1. الدوال الأساسية ---
def fetch_live_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="1mo")
        if df.empty: return None, None, None
        current_p = round(df['Close'].iloc[-1], 2)
        auto_anchor = round(df['Low'].min(), 2)
        auto_target = round(df['High'].max(), 2)
        return current_p, auto_anchor, auto_target
    except: return None, None, None

def generate_pdf_link(content, ticker):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="SEF STRATEGIC ANALYSIS", ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", size=10)
        # إخلاء المسؤولية في الـ PDF
        pdf.cell(200, 7, txt="Created By Abu Yahia", ln=True, align='L')
        pdf.set_text_color(200, 0, 0)
        pdf.cell(200, 7, txt="Disclaimer: Educational purposes only. Not financial advice.", ln=True, align='L')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
        clean_text = content.encode('ascii', 'ignore').decode('ascii')
        for line in clean_text.split('\n'):
            pdf.cell(0, 8, txt=line, ln=True)
        pdf_output = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_output).decode()
        return f'<a href="data:application/octet-stream;base64,{b64}" download="SEF_{ticker}_Report.pdf" style="background-color: #ff4b4b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; margin-top: 10px;">📥 Download PDF Report</a>'
    except: return "⚠️ PDF Error"

# --- 2. واجهة المستخدم ---
st.title("🛡️ SEF Terminal | Ultimate Hub")

# التوقيع + إخلاء المسؤولية بالعربي والإنجليزي (محاذاة لليسار)
st.markdown("""
    <div style='text-align: left; padding-left: 50px; margin-top: -20px;'>
        <div style='color: #555; font-size: 1.1em; font-weight: bold;'>🖋️ Created By Abu Yahia</div>
        <div style='color: #cc0000; font-size: 0.85em; margin-top: 5px; line-height: 1.4;'>
            ⚠️ <b>إخلاء مسؤولية:</b> هذا التطبيق للأغراض التعليمية فقط ولا يعتبر نصيحة مالية أو توصية بالشراء أو البيع.<br>
            ⚠️ <b>Disclaimer:</b> Educational purposes only. Not financial advice or a recommendation to buy/sell.
        </div>
    </div>
    """, unsafe_allow_html=True)

# السايدبار لإعدادات المحفظة
balance = st.sidebar.number_input("Portfolio Balance", value=100000)
risk_pct = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 1.0)

# إدارة الذاكرة التفاعلية للقيم
if 'p_val' not in st.session_state: st.session_state['p_val'] = 33.90
if 'a_val' not in st.session_state: st.session_state['a_val'] = 31.72
if 't_val' not in st.session_state: st.session_state['t_val'] = 39.36

st.markdown("---")

# صف المدخلات والأزرار التفاعلية
c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.2, 1.2, 1.2, 1.2, 1.5])

with c1:
    ticker = st.text_input("Ticker Symbol", "4009.SR").upper()
with c2:
    p_in = st.number_input("Market Price", value=float(st.session_state['p_val']), step=0.01)
with c3:
    a_in = st.number_input("Anchor Level", value=float(st.session_state['a_val']), step=0.01)
with c4:
    t_in = st.number_input("Target Price", value=float(st.session_state['t_val']), step=0.01)
with c5:
    st.write("##")
    if st.button("🛰️ Radar", use_container_width=True):
        p, a, t = fetch_live_data(ticker)
        if p:
            st.session_state['p_val'] = p
            st.session_state['a_val'] = a
            st.session_state['t_val'] = t
            st.rerun()
with c6:
    st.write("##")
    analyze_trigger = st.button("📊 Analyze", use_container_width=True)

st.markdown("---")

# --- 3. عرض التحليل الذكي ---
if analyze_trigger:
    risk_per_share = abs(p_in - a_in)
    risk_cash = balance * (risk_pct / 100)
    
    if risk_per_share > 0:
        rr = (t_in - p_in) / risk_per_share
        qty = math.floor(risk_cash / risk_per_share)
    else: rr, qty = 0, 0

    if rr >= 3: rr_advice = "🟢 EXCELLENT (Professional Grade)"
    elif 2 <= rr < 3: rr_advice = "🟡 GOOD (Acceptable Trade)"
    else: rr_advice = "🔴 DANGEROUS (Avoid - Poor Reward)"

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Live Price", p_in)
    m2.metric("R:R Ratio", f"1:{round(rr, 2)}")
    m3.metric("Shares", qty)
    m4.metric("Risk Cash", f"{round(risk_cash, 2)}")

    full_report = f"""
SEF STRATEGIC ANALYSIS REPORT
🖋️ Created By Abu Yahia
------------------------------------
Ticker: {ticker} | Price: {p_in}
1. LEVELS:
- Entry: {p_in} | Anchor (SL): {a_in} | Target: {t_in}

2. METRICS:
- R:R Ratio: 1:{round(rr, 2)}
- Quantity: {qty} Shares | Risk: {round(risk_cash, 2)}

RESULT: {rr_advice}
------------------------------------
DISCLAIMER: For educational purposes only.
"Capital preservation is the first priority."
    """
    st.markdown("### 📄 SEF Structural Analysis")
    st.code(full_report, language='text')
    st.markdown(generate_pdf_link(full_report, ticker), unsafe_allow_html=True)

    hist = yf.Ticker(ticker).history(period="1y")
    if not hist.empty:
        c_data = hist[['Close']].copy()
        c_data['Anchor'] = a_in
        c_data['Target'] = t_in
        c_data['EMA_200'] = c_data['Close'].ewm(span=200, adjust=False).mean()
        st.line_chart(c_data)
    
    if rr >= 3: st.balloons()
