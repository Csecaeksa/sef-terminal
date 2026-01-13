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
        # إجبار المكتبة على جلب أحدث البيانات دون استخدام الكاش
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="5d")
        if df.empty:
            return None, None, "Invalid Ticker"
        
        # جلب سعر الإغلاق الأخير (سعر السوق الحالي)
        current_mkt_price = round(df['Close'].iloc[-1], 2)
        # جلب أدنى سعر في آخر 20 يوم تداول كمرساة (Anchor)
        long_df = stock.history(period="1mo")
        auto_anchor = round(long_df['Low'].tail(20).min(), 2)
        
        status = "🛡️ Near Anchor" if current_mkt_price < auto_anchor * 1.05 else "🔥 Breakout"
        return current_mkt_price, auto_anchor, status
    except Exception as e:
        return None, None, f"Error: {str(e)}"

# --- دالة التقرير الهيكلي SEF ---
def get_sef_text(ticker, price, anchor, target, rr, qty, status):
    return f"""
SEF STRATEGIC ANALYSIS REPORT
-----------------------------
Ticker: {ticker} | Live Price: {price}
Status: {status}

1. Key Levels:
- Anchor (Stop Loss): {anchor}
- Target Price: {target}

2. Execution:
- Risk:Reward Ratio: 1:{round(rr, 2)}
- Recommended Quantity: {qty} Shares

"Capital preservation is the first priority."
    """

# --- الواجهة البرمجية ---
st.title("🛡️ SEF Terminal | Professional Hub")

# الحقول الجانبية
balance = st.sidebar.number_input("Portfolio Balance", value=100000)
risk_pct = st.sidebar.slider("Risk per Trade (%)", 0.5, 5.0, 1.0)

# تعريف الـ Session State لضمان تحديث الأرقام
if 'p_val' not in st.session_state: st.session_state['p_val'] = 33.90
if 'a_val' not in st.session_state: st.session_state['a_val'] = 31.72
if 's_val' not in st.session_state: st.session_state['s_val'] = "Forming"

st.markdown("---")

# --- صف المدخلات والأزرار (كلهم جنب بعض) ---
c1, c2, c3, c4, c5, c6 = st.columns([1.5, 1.2, 1.2, 1.2, 1.2, 1.5])

with c1:
    ticker_input = st.text_input("Ticker Symbol", "2222.SR").upper()
with c2:
    # السعر الحالي - يتحدث تلقائياً من الرادار
    curr_p = st.number_input("Market Price", value=float(st.session_state['p_val']), key="live_p")
with c3:
    # المرساة - تتحدث تلقائياً من الرادار
    anc_p = st.number_input("Anchor Level", value=float(st.session_state['a_val']), key="live_a")
with c4:
    tar_p = st.number_input("Target Price", value=39.36)
with c5:
    st.write("##")
    if st.button("🛰️ Radar", use_container_width=True):
        p, a, s = fetch_live_data(ticker_input)
        if p:
            # تحديث القيم فوراً في ذاكرة التطبيق
            st.session_state['p_val'] = p
            st.session_state['a_val'] = a
            st.session_state['s_val'] = s
            st.rerun() # إعادة تحميل الصفحة لتظهر الأرقام الجديدة (مثل 24.25)
with c6:
    st.write("##")
    analyze_click = st.button("📊 Analyze", use_container_width=True)

st.markdown("---")

# --- عرض النتائج والتحليل الهيكلي ---
if analyze_click:
    # الحسابات بناءً على ما هو مكتوب حالياً في الخانات
    risk_amount = balance * (risk_pct / 100)
    risk_per_share = abs(st.session_state.live_p - st.session_state.live_a)
    
    if risk_per_share > 0:
        rr_ratio = (tar_p - st.session_state.live_p) / risk_per_share
        shares_qty = math.floor(risk_amount / risk_per_share)
    else:
        rr_ratio = 0
        shares_qty = 0

    # عرض البيانات المالية
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Live Price", st.session_state.live_p)
    col_m2.metric("R:R Ratio", f"1:{round(rr_ratio, 2)}")
    col_m3.metric("Shares", shares_qty)
    col_m4.metric("Risk Cash", round(risk_amount, 2))

    # التقرير الهيكلي SEF
    st.markdown("### 📄 SEF Structural Analysis")
    report_text = get_sef_text(ticker_input, st.session_state.live_p, st.session_state.live_a, tar_p, rr_ratio, shares_qty, st.session_state['s_val'])
    st.code(report_text, language='text')

    # الشارت الفني
    st.subheader("📈 Technical Chart Overview")
    hist_data = yf.Ticker(ticker_input).history(period="6mo")
    if not hist_data.empty:
        c_df = hist_data[['Close']].copy()
        c_df['Anchor'] = st.session_state.live_a
        c_df['Target'] = tar_p
        st.line_chart(c_df)
    
    if rr_ratio >= 3: st.balloons()
