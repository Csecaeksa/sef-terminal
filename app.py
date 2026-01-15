import streamlit as st
import pandas as pd
import yfinance as yf
import math

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="SEF Terminal Pro", layout="wide")

# --- 2. قراءة ملف الـ 262 شركة (TASI.csv) ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("TASI.csv")
        df['Ticker'] = df['Ticker'].astype(str).str.strip()
        df['Name_Ar'] = df['Company Name (Arabic)'].astype(str).str.strip()
        df['Display'] = df['Name_Ar'] + " | " + df['Ticker']
        mapping = dict(zip(df['Display'], df['Ticker']))
        return sorted(list(mapping.keys())), mapping
    except Exception as e:
        st.error(f"تأكد من وجود ملف TASI.csv بجانب الكود. الخطأ: {e}")
        return [], {}

options, tasi_mapping = load_data()

# --- 3. دالة جلب البيانات (حل مشكلة Multi-index) ---
def get_stock_data(ticker):
    try:
        # جلب بيانات سنتين لضمان حساب متوسط 200 يوم
        df = yf.download(f"{ticker}.SR", period="2y", progress=False)
        
        if df.empty:
            return None
        
        # حل مشكلة اختفاء السعر: استخراج السلسلة السعرية بغض النظر عن عدد الأعمدة
        close_prices = df['Close'].iloc[:, 0] if isinstance(df['Close'], pd.DataFrame) else df['Close']
        low_prices = df['Low'].iloc[:, 0] if isinstance(df['Low'], pd.DataFrame) else df['Low']
        high_prices = df['High'].iloc[:, 0] if isinstance(df['High'], pd.DataFrame) else df['High']

        results = {
            "current_price": float(close_prices.iloc[-1]),
            "sma50": float(close_prices.rolling(window=50).mean().iloc[-1]),
            "sma100": float(close_prices.rolling(window=100).mean().iloc[-1]),
            "sma200": float(close_prices.rolling(window=200).mean().iloc[-1]),
            "low_20": float(low_prices.tail(20).min()),
            "high_20": float(high_prices.tail(20).max())
        }
        return results
    except Exception as e:
        st.error(f"خطأ أثناء جلب البيانات: {e}")
        return None

# --- 4. واجهة المستخدم ---
st.title("🛡️ SEF Terminal Pro | 262 Companies")
st.write(f"✅ الشركات المحملة: **{len(options)}** شركة")

if 'app_data' not in st.session_state:
    st.session_state.update({'p_in': 0.0, 'a_in': 0.0, 't_in': 0.0, 'ma_results': None})

st.markdown("---")

c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 0.8, 1])

with c1:
    selected = st.selectbox("🔍 اختر السهم:", options=options)
    ticker_code = tasi_mapping[selected]

with c2: p_in = st.number_input("السعر", value=float(st.session_state['p_in']), step=0.01)
with c3: a_in = st.number_input("الوقف", value=float(st.session_state['a_in']), step=0.01)
with c4: t_in = st.number_input("الهدف", value=float(st.session_state['t_in']), step=0.01)

with c5:
    st.write("##")
    if st.button("🛰️ Radar", use_container_width=True):
        res = get_stock_data(ticker_code)
        if res:
            st.session_state.update({
                'ma_results': res,
                'p_in': res['current_price'],
                'a_in': res['low_20'],
                't_in': res['high_20']
            })
            st.rerun()

with c6:
    st.write("##")
    analyze = st.button("📊 Analyze", use_container_width=True)

# --- 5. عرض المتوسطات (SMA) ---
if st.session_state['ma_results']:
    r = st.session_state['ma_results']
    st.subheader("📈 المتوسطات المتحركة (SMA)")
    m1, m2, m3 = st.columns(3)
    
    def plot_metric(col, label, ma_val, price):
        diff = price - ma_val
        status = "فوق المتوسط (إيجابي)" if diff >= 0 else "تحت المتوسط (سلبي)"
        col.metric(label, f"{ma_val:.2f}", delta=f"{diff:.2f} ريال", delta_color="normal" if diff >= 0 else "inverse")
        col.caption(status)

    plot_metric(m1, "متوسط 50 يوم", r['sma50'], r['current_price'])
    plot_metric(m2, "متوسط 100 يوم", r['sma100'], r['current_price'])
    plot_metric(m3, "متوسط 200 يوم", r['sma200'], r['current_price'])

# --- 6. التحليل وإدارة المخاطر ---
if analyze:
    risk_ps = abs(p_in - a_in)
    if risk_ps > 0:
        balance = st.sidebar.number_input("حجم المحفظة", value=100000)
        risk_pct = st.sidebar.slider("مخاطرة الصفقة %", 0.5, 5.0, 1.0)
        qty = math.floor((balance * (risk_pct/100)) / risk_ps)
        
        st.markdown("---")
        st.success(f"📊 نتيجة التحليل لـ {selected}")
        res_c = st.columns(3)
        res_c[0].metric("الكمية المستهدفة", f"{qty} سهم")
        res_c[1].metric("نسبة الوقف", f"-{round((risk_ps/p_in)*100, 2)}%")
        res_c[2].metric("معامل R:R", f"1:{round((t_in - p_in) / risk_ps, 2)}")

        # رسم بياني للسعر
        chart_data = yf.download(f"{ticker_code}.SR", period="1y", progress=False)['Close']
        st.line_chart(chart_data)
