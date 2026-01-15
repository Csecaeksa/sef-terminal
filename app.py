import streamlit as st
import pandas as pd
import yfinance as yf
import math

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="SEF Terminal Pro", layout="wide")

# --- 2. دالة قراءة الـ 262 شركة من ملفك TASI.csv ---
@st.cache_data
def load_tasi_complete():
    try:
        # تأكد من رفع ملفك باسم TASI.csv على GitHub
        df = pd.read_csv("TASI.csv")
        df['Ticker'] = df['Ticker'].astype(str).str.strip()
        df['Name_Ar'] = df['Company Name (Arabic)'].astype(str).str.strip()
        df['Display'] = df['Name_Ar'] + " | " + df['Ticker']
        mapping = dict(zip(df['Display'], df['Ticker']))
        return sorted(list(mapping.keys())), mapping
    except Exception as e:
        st.error(f"خطأ في تحميل الـ 262 شركة: {e}")
        return [], {}

options, tasi_mapping = load_tasi_complete()

# --- 3. دالة جلب البيانات والمتوسطات ---
def fetch_technical_data(ticker_symbol):
    try:
        full_ticker = f"{ticker_symbol}.SR"
        stock = yf.Ticker(full_ticker)
        # نحتاج بيانات سنة على الأقل لحساب متوسط 200 يوم
        df = stock.history(period="1y")
        if df.empty or len(df) < 200:
            # إذا كان السهم جديداً، نجلب المتاح
            df = stock.history(period="max")
            
        curr_p = round(df['Close'].iloc[-1], 2)
        
        # حساب المتوسطات
        ma50 = round(df['Close'].rolling(window=50).mean().iloc[-1], 2)
        ma100 = round(df['Close'].rolling(window=100).mean().iloc[-1], 2)
        ma200 = round(df['Close'].rolling(window=200).mean().iloc[-1], 2)
        
        # الوقف والهدف التلقائي (للرادار)
        low_month = round(df['Low'].tail(22).min(), 2)
        high_month = round(df['High'].tail(22).max(), 2)
        
        return curr_p, ma50, ma100, ma200, low_month, high_month
    except:
        return None, None, None, None, None, None

# --- 4. واجهة المستخدم ---
st.title("🛡️ SEF Terminal Pro | Technical Edition")
st.write(f"📊 الشركات المحملة: **{len(options)}** | المطور: أبو يحيى")

if 'p_val' not in st.session_state: 
    st.session_state.update({'p_val': 0.0, 'a_val': 0.0, 't_val': 0.0, 'ma_data': {}})

st.markdown("---")

# صف البحث والمدخلات
c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1.0, 1.0, 1.0, 0.8, 1.0])

with c1:
    selected_stock = st.selectbox("🔍 ابحث في الـ 262 شركة:", options=options)
    ticker = tasi_mapping[selected_stock]

with c2: p_in = st.number_input("السعر الحالي", value=float(st.session_state['p_val']), step=0.01)
with c3: a_in = st.number_input("الوقف (Anchor)", value=float(st.session_state['a_val']), step=0.01)
with c4: t_in = st.number_input("الهدف (Target)", value=float(st.session_state['t_val']), step=0.01)

with c5:
    st.write("##")
    if st.button("🛰️ Radar", use_container_width=True):
        p, m50, m100, m200, low, high = fetch_technical_data(ticker)
        if p:
            st.session_state.update({
                'p_val': p, 'a_val': low, 't_val': high,
                'ma_data': {'50': m50, '100': m100, '200': m200}
            })
            st.rerun()

with c6:
    st.write("##")
    analyze = st.button("📊 Analyze", use_container_width=True)

# --- 5. عرض المتوسطات والتحليل ---
if st.session_state['ma_data']:
    ma = st.session_state['ma_data']
    cols = st.columns(3)
    for i, period in enumerate(['50', '100', '200']):
        val = ma[period]
        diff = round(st.session_state['p_val'] - val, 2)
        color = "normal" if diff >= 0 else "inverse"
        cols[i].metric(f"SMA {period}", val, delta=diff, delta_color=color)

if analyze:
    risk_ps = abs(p_in - a_in)
    if risk_ps > 0:
        balance = st.sidebar.number_input("المحفظة", value=100000)
        risk_pct = st.sidebar.slider("المخاطرة %", 0.5, 5.0, 1.0)
        qty = math.floor((balance * (risk_pct/100)) / risk_ps)
        rr = round((t_in - p_in) / risk_ps, 2)
        
        st.success(f"📈 تحليل: {selected_stock}")
        res1, res2, res3 = st.columns(3)
        res1.metric("عدد الأسهم", qty)
        res2.metric("نسبة الوقف", f"-{round((risk_ps/p_in)*100, 2)}%")
        res3.metric("معامل R:R", f"1:{rr}")
        
        # الشارت مع المتوسطات
        hist = yf.Ticker(f"{ticker}.SR").history(period="1y")
        st.line_chart(hist['Close'], use_container_width=True)
