import streamlit as st
import yfinance as yf
import pandas as pd
import math
from fpdf import FPDF
import base64

# --- 1. إعدادات الصفحة ---
icon_url = "https://i.ibb.co/vzR0jXJX/robot-icon.png"
st.set_page_config(page_title="SEF Terminal Pro", page_icon=icon_url, layout="wide")

# --- 2. تحميل البيانات من ملفك (TASI) ---
@st.cache_data
def load_tasi_data():
    try:
        # قراءة الملف الذي رفعته (CSV المستخرج من XLSX)
        df = pd.read_csv("TASI.xlsx - Market Watch Today-2025-10-27.csv", skiprows=4)
        df.columns = ['Ticker', 'Name_En', 'Name_Ar', 'Sector']
        # تنظيف الرموز
        df['Ticker'] = df['Ticker'].astype(str).str.split('.').str[0]
        # تجهيز قائمة العرض
        df['Display'] = df['Name_Ar'] + " | " + df['Ticker'] + " (" + df['Sector'] + ")"
        mapping = dict(zip(df['Display'], df['Ticker']))
        return list(mapping.keys()), mapping
    except:
        # قائمة طوارئ في حال لم يجد الكود الملف (تضم دراية والراجحي والقياديات)
        emergency_data = {
            "الراجحي | 1120 (Banks)": "1120",
            "أرامكو | 2222 (Energy)": "2222",
            "دراية ريت | 4339 (REITs)": "4339",
            "سابك للمغذيات | 2020 (Materials)": "2020",
            "الإنماء | 1150 (Banks)": "1150",
            "سليمان الحبيب | 4013 (Health)": "4013"
        }
        return list(emergency_data.keys()), emergency_data

options, tasi_mapping = load_tasi_data()

# --- 3. الدوال الأساسية ---
def fetch_live_data(ticker_symbol):
    try:
        full_ticker = f"{ticker_symbol}.SR"
        stock = yf.Ticker(full_ticker)
        df = stock.history(period="1mo")
        if df.empty: return None, None, None
        return round(df['Close'].iloc[-1], 2), round(df['Low'].min(), 2), round(df['High'].max(), 2)
    except: return None, None, None

def generate_pdf(content, ticker):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="SEF STRATEGIC ANALYSIS - ABU YAHIA", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=10)
        for line in content.encode('ascii', 'ignore').decode('ascii').split('\n'):
            pdf.cell(0, 7, txt=line, ln=True)
        pdf_output = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_output).decode()
        return f'<a href="data:application/octet-stream;base64,{b64}" download="SEF_{ticker}.pdf" style="background-color: #ff4b4b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">📥 Download PDF Report</a>'
    except: return ""

# --- 4. واجهة المستخدم ---
st.title("🛡️ SEF Terminal Pro | TASI Explorer")
st.write("🖋️ **Created By Abu Yahia** | النسخة الشاملة")

if 'p_val' not in st.session_state: st.session_state.update({'p_val': 0.0, 'a_val': 0.0, 't_val': 0.0})

balance = st.sidebar.number_input("Portfolio Balance (المحفظة)", value=100000)
risk_pct_input = st.sidebar.slider("Risk per Trade (%) نسبة المخاطرة", 0.5, 5.0, 1.0)

st.markdown("---")

c1, c2, c3, c4, c5, c6 = st.columns([2.2, 1.1, 1.1, 1.1, 1.0, 1.2])

with c1:
    selected_stock = st.selectbox("🔍 Search Stocks (Name or Code)", options=options)
    ticker_code = tasi_mapping[selected_stock]

with c2: p_in = st.number_input("Price", value=float(st.session_state['p_val']), step=0.01)
with c3: a_in = st.number_input("Anchor (SL)", value=float(st.session_state['a_val']), step=0.01)
with c4: t_in = st.number_input("Target", value=float(st.session_state['t_val']), step=0.01)

with c5:
    st.write("##")
    if st.button("🛰️ Radar", use_container_width=True):
        p, a, t = fetch_live_data(ticker_code)
        if p:
            st.session_state.update({'p_val': p, 'a_val': a, 't_val': t})
            st.rerun()

with c6:
    st.write("##")
    analyze_trigger = st.button("📊 Analyze", use_container_width=True)

st.markdown("---")

# --- 5. النتائج والتحليل ---
if analyze_trigger:
    risk_per_share = abs(p_in - a_in)
    risk_cash = balance * (risk_pct_input / 100)
    
    dist_to_sl_pct = (risk_per_share / p_in) * 100 if p_in != 0 else 0
    dist_to_t_pct = ((t_in - p_in) / p_in) * 100 if p_in != 0 else 0
    
    rr = (t_in - p_in) / risk_per_share if risk_per_share > 0 else 0
    qty = math.floor(risk_cash / risk_per_share) if risk_per_share > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Live Price", p_in)
    m2.metric("R:R Ratio", f"1:{round(rr, 2)}")
    m3.metric("Shares", qty)
    m4.metric("Risk Cash", round(risk_cash, 2))

    report = f"""
SEF STRATEGIC REPORT
------------------------------------
Asset: {selected_stock}
------------------------------------
- Entry Price: {p_in}
- Anchor (SL): {a_in}
- Target Price: {t_in}
- Risk to SL: -{round(dist_to_sl_pct, 2)}%
- Potential Reward: +{round(dist_to_t_pct, 2)}%
- Quantity: {qty} Shares
- Strategy R:R: 1:{round(rr, 2)}
------------------------------------
    """
    st.code(report)
    st.markdown(generate_pdf(report, ticker_code), unsafe_allow_html=True)
    st.line_chart(yf.Ticker(f"{ticker_code}.SR").history(period="1y")['Close'], use_container_width=True)
