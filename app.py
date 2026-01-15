import streamlit as st
import pandas as pd
import yfinance as yf
import math

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="SEF Terminal Pro", layout="wide")

# --- 2. دالة قراءة الـ 262 شركة من ملف TASI.csv ---
@st.cache_data
def load_tasi_complete():
    try:
        # قراءة الملف (تأكد أن اسمه TASI.csv في مجلد المشروع)
        df = pd.read_csv("TASI.csv")
        df['Ticker'] = df['Ticker'].astype(str).str.strip()
        df['Name_Ar'] = df['Company Name (Arabic)'].astype(str).str.strip()
        df['Sector'] = df['Industry Group'].astype(str).str.strip()
        df['Display'] = df['Name_Ar'] + " | " + df['Ticker'] + " (" + df['Sector'] + ")"
        mapping = dict(zip(df['Display'], df['Ticker']))
        return sorted(list(mapping.keys())), mapping
    except Exception as e:
        st.error(f"⚠️ ملف TASI.csv غير موجود أو به خطأ: {e}")
        return [], {}

options, tasi_mapping = load_tasi_complete()

# --- 3. دالة جلب البيانات الفنية والمتوسطات ---
def fetch_technical_data(ticker_symbol):
    try:
        full_ticker = f"{ticker_symbol}.SR"
        stock = yf.Ticker(full_ticker)
        # جلب بيانات سنة كاملة لضمان حساب متوسط 200 يوم
        df = stock.history(period="1y")
        if df.empty or len(df) < 200:
            df = stock.history(period="max")
            
        if df.empty: return None

        curr_p = round(df['Close'].iloc[-1], 2)
        # حساب المتوسطات الحسابية
        sma50 = round(df['Close'].rolling(window=50).mean().iloc[-1], 2)
        sma100 = round(df['Close'].rolling(window=100).mean().iloc[-1], 2)
        sma200 = round(df['Close'].rolling(window=200).mean().iloc[-1], 2)
        
        # بيانات الرادار (أدنى وأعلى سعر في شهر)
        low_month = round(df['Low'].tail(22).min(), 2)
        high_month = round(df['High'].tail(22).max(), 2)
        
        return {
            "price": curr_p,
            "sma50": sma50,
            "sma100": sma100,
            "sma200": sma200,
            "low": low_month,
            "high": high_month
        }
    except:
        return None

# --- 4. واجهة المستخدم ---
st.title("🛡️ SEF Terminal Pro | Technical Analysis")
st.write(f"📊 الشركات المحملة: **{len(options)}** | المطور: أبو يحيى")

# تهيئة الذاكرة المؤقتة للبيانات
if 'p_val' not in st.session_state:
    st.session_state.update({'p_val': 0.0, 'a_val': 0.0, 't_val': 0.0, 'ma50': 0.0, 'ma100': 0.0, 'ma200': 0.0})

st.markdown("---")

# صف البحث والمدخلات
c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 0.8, 1])

with c1:
    selected = st.selectbox("🔍 ابحث في الشركات (اسم أو رمز):", options=options)
    ticker = tasi_mapping[selected]

with c2: p_in = st.number_input("السعر", value=float(st.session_state['p_val']), step=0.01)
with c3: a_in = st.number_input("الوقف", value=float(st.session_state['a_val']), step=0.01)
with c4: t_in = st.number_input("الهدف", value=float(st.session_state['t_val']), step=0.01)

with c5:
    st.write("##")
    if st.button("🛰️ Radar", use_container_width=True):
        data = fetch_technical_data(ticker)
        if data:
            st.session_state.update({
                'p_val': data['price'], 'a_val': data['low'], 't_val': data['high'],
                'ma50': data['sma50'], 'ma100': data['sma100'], 'ma200': data['sma200']
            })
            st.rerun()

with c6:
    st.write("##")
    analyze = st.button("📊 Analyze", use_container_width=True)

# --- 5. عرض المتوسطات الحسابية (تظهر فوراً بعد الرادار) ---
if st.session_state['ma50'] > 0:
    st.markdown("### 📈 المتوسطات الحسابية (SMA)")
    m_cols = st.columns(3)
    
    # تنسيق عرض المتوسطات مع الفرق عن السعر الحالي
    for i, (label, val) in enumerate([("50 يوم", 'ma50'), ("100 يوم", 'ma100'), ("200 يوم", 'ma200')]):
        current_ma = st.session_state[val]
        diff = round(st.session_state['p_val'] - current_ma, 2)
        color = "normal" if diff >= 0 else "inverse" # أخضر لو السعر فوق المتوسط
        m_cols[i].metric(label, f"{current_ma}", delta=f"{diff} ريال", delta_color=color)

# --- 6. نتائج التحليل ---
if analyze:
    risk_ps = abs(p_in - a_in)
    balance = st.sidebar.number_input("المحفظة", value=100000)
    risk_p = st.sidebar.slider("المخاطرة %", 0.5, 5.0, 1.0)
    
    if risk_ps > 0:
        qty = math.floor((balance * (risk_p/100)) / risk_ps)
        rr = round((t_in - p_in) / risk_ps, 2)
        
        st.success(f"✅ تم تحليل سهم: {selected}")
        r1, r2, r3 = st.columns(3)
        r1.metric("الكمية", f"{qty} سهم")
        r2.metric("نسبة الوقف", f"-{round((risk_ps/p_in)*100, 2)}%")
        r3.metric("معامل R:R", f"1:{rr}")
        
        # الشارت
        st.line_chart(yf.Ticker(f"{ticker}.SR").history(period="1y")['Close'])
