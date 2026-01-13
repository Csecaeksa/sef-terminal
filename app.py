import streamlit as st
import yfinance as yf
import pandas as pd
import math
from fpdf import FPDF
import base64

# --- إعدادات الصفحة ---
st.set_page_config(page_title="SEF Terminal Pro", page_icon="🛡️", layout="wide")

# --- دالة جلب البيانات الحقيقية ---
def fetch_live_data(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="5d")
        if df.empty:
            return None, None, "Invalid Ticker"
        
        # السعر الحالي الفعلي
        current_mkt_price = round(df['Close'].iloc[-1], 2)
        # أدنى سعر في شهر (المرساة)
        long_df = stock.history(period="1mo")
        auto_anchor = round(long_df['Low'].tail(20).min(), 2)
        
        status = "🛡️ Near Anchor" if current_mkt_price < auto_anchor * 1.05 else "🔥 Breakout"
        return current_mkt_price, auto_anchor, status
    except:
        return None, None, "Error"

# --- واجهة المستخدم ---
st.title("🛡️ SEF Terminal | Professional Hub")

# الحقول الجانبية
balance = st.sidebar.number_input("Portfolio Balance", value=100000)
risk_pct = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 1.0)

# استخدام الـ Session State لتخزين القيم المؤقتة فقط عند الضغط على الرادار
if 'temp_p' not in st.session_state: st.session_state['temp_p'] = 33.90
if 'temp_a' not in st.session_state: st.session_state['temp_a'] = 31.72

st.markdown("---")

# صف المدخلات
c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.2, 1.2, 1.2, 1.2, 1.5])

with c1:
    ticker_input = st.text_input("Ticker Symbol", "2222.SR").upper()
with c2:
    # المدخلات تأخذ قيمتها من الـ Session State لكنها تسمح بالتغيير اليدوي
    price = st.number_input("Market Price", value=float(st.session_state['temp_p']), step=0.01)
with c3:
    anchor = st.number_input("Anchor Level", value=float(st.session_state['temp_a']), step=0.01)
with c4:
    target = st.number_input("Target Price", value=39.36, step=0.01)

with c5:
    st.write("##")
    if st.button("🛰️ Radar", use_container_width=True):
        p, a, s = fetch_live_data(ticker_input)
        if p:
            st.session_state['temp_p'] = p
            st.session_state['temp_a'] = a
            st.rerun() # تحديث الخانات فوراً بالأرقام الجديدة

with c6:
    st.write("##")
    analyze_btn = st.button("📊 Analyze", use_container_width=True)

st.markdown("---")

# --- منطقة النتائج (تتولد فقط عند الضغط على Analyze) ---
if analyze_btn:
    # الحسابات بناءً على الأرقام الحالية في الخانات (تفاعلي 100%)
    risk_amt = balance * (risk_pct / 100)
    risk_per_share = abs(price - anchor)
    
    if risk_per_share > 0:
        rr = (target - price) / risk_per_share
        qty = math.floor(risk_amt / risk_per_share)
    else:
        rr, qty = 0, 0

    # عرض الأرقام الكبيرة
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Live Price", price)
    m2.metric("R:R Ratio", f"1:{round(rr, 2)}")
    m3.metric("Shares", qty)
    m4.metric("Risk Cash", round(risk_amt, 2))

    # التقرير الهيكلي (يأخذ بياناته من الخانات مباشرة)
    st.markdown("### 📄 SEF Structural Analysis")
    report_content = f"""
SEF STRATEGIC ANALYSIS REPORT
-----------------------------
Ticker: {ticker_input} | Price: {price}
Status: {"🔥 Breakout" if price > anchor * 1.1 else "🛡️ Accumulation"}

1. Key Levels:
- Anchor (Stop Loss): {anchor}
- Target Price: {target}

2. Execution:
- Risk:Reward Ratio: 1:{round(rr, 2)}
- Position Size: {qty} Shares
    """
    st.code(report_content, language='text')

    # الشارت التفاعلي
    hist = yf.Ticker(ticker_input).history(period="6mo")
    if not hist.empty:
        df_chart = hist[['Close']].copy()
        df_chart['Anchor'] = anchor
        df_chart['Target'] = target
        st.line_chart(df_chart)
