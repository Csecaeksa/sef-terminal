import streamlit as st
import pandas as pd
import yfinance as yf
import math

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="SEF Terminal Pro", layout="wide")

# --- 2. تحميل ملف الـ 262 شركة ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("TASI.csv")
        # تنظيف أسماء الأعمدة من أي مسافات زائدة
        df.columns = [c.strip() for c in df.columns]
        df['Ticker'] = df['Ticker'].astype(str).str.strip()
        df['Name_Ar'] = df['Company Name (Arabic)'].astype(str).str.strip()
        df['Display'] = df['Name_Ar'] + " | " + df['Ticker']
        mapping = dict(zip(df['Display'], df['Ticker']))
        return sorted(list(mapping.keys())), mapping
    except Exception as e:
        st.error(f"خطأ في قراءة TASI.csv: {e}")
        return [], {}

options, tasi_mapping = load_data()

# --- 3. دالة جلب البيانات الفنية (مع حل مشكلة Multi-index) ---
def get_clean_data(ticker):
    try:
        # جلب بيانات سنتين لضمان المتوسطات
        df = yf.download(f"{ticker}.SR", period="2y", progress=False)
        if df.empty: return None

        # إجبار البيانات على أن تكون سلسلة بسيطة (Single Level)
        # هذه الخطوة هي التي تصلح "الضربة" التي حدثت في الكود
        close = df['Close'].iloc[:, 0] if len(df['Close'].shape) > 1 else df['Close']
        low = df['Low'].iloc[:, 0] if len(df['Low'].shape) > 1 else df['Low']
        high = df['High'].iloc[:, 0] if len(df['High'].shape) > 1 else df['High']

        results = {
            "p": float(close.iloc[-1]),
            "m50": float(close.rolling(window=50).mean().iloc[-1]),
            "m100": float(close.rolling(window=100).mean().iloc[-1]),
            "m200": float(close.rolling(window=200).mean().iloc[-1]),
            "l20": float(low.tail(20).min()),
            "h20": float(high.tail(20).max())
        }
        return results
    except Exception as e:
        st.error(f"خطأ في جلب بيانات الرمز {ticker}: {e}")
        return None

# --- 4. واجهة المستخدم ---
st.title("🛡️ SEF Terminal Pro | الإصدار المصلح")
st.write(f"✅ الشركات النشطة: **{len(options)}**")

if 'store' not in st.session_state:
    st.session_state.update({'p': 0.0, 'a': 0.0, 't': 0.0, 'tech': None})

st.markdown("---")

c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 0.8, 1])

with c1:
    choice = st.selectbox("🔍 اختر السهم:", options=options)
    t_code = tasi_mapping[choice]

with c2: p_in = st.number_input("السعر", value=float(st.session_state['p']), format="%.2f")
with c3: a_in = st.number_input("الوقف", value=float(st.session_state['a']), format="%.2f")
with c4: t_in = st.number_input("الهدف", value=float(st.session_state['t']), format="%.2f")

# زر الرادار المصلح
with c5:
    st.write("##")
    if st.button("🛰️ Radar", use_container_width=True):
        data = get_clean_data(t_code)
        if data:
            st.session_state.update({'p': data['p'], 'a': data['l20'], 't': data['h20'], 'tech': data})
            st.rerun()

# زر التحليل
with c6:
    st.write("##")
    do_analyze = st.button("📊 Analyze", use_container_width=True)

# --- 5. عرض المتوسطات ---
if st.session_state['tech']:
    st.subheader("📈 المتوسطات الحسابية (SMA)")
    d = st.session_state['tech']
    cols = st.columns(3)
    
    def draw_ma(col, title, val, cur):
        diff = cur - val
        col.metric(title, f"{val:.2f}", delta=f"{diff:.2f}", delta_color="normal" if diff >= 0 else "inverse")

    draw_ma(cols[0], "SMA 50", d['m50'], d['p'])
    draw_ma(cols[1], "SMA 100", d['m100'], d['p'])
    draw_ma(cols[2], "SMA 200", d['m200'], d['p'])

# --- 6. نتائج التحليل المالي ---
if do_analyze:
    risk_val = abs(p_in - a_in)
    if risk_val > 0:
        balance = st.sidebar.number_input("المحفظة", value=100000)
        risk_p = st.sidebar.slider("مخاطرة %", 0.5, 5.0, 1.0)
        qty = math.floor((balance * (risk_p/100)) / risk_val)
        
        st.markdown("---")
        st.success(f"📊 تحليل سهم: {choice}")
        r_cols = st.columns(3)
        r_cols[0].metric("الكمية", f"{qty} سهم")
        r_cols[1].metric("الوقف %", f"-{round((risk_val/p_in)*100, 2)}%")
        r_cols[2].metric("الهدف R:R", f"1:{round((t_in - p_in) / risk_val, 2)}")

        # الشارت
        st.line_chart(yf.download(f"{t_code}.SR", period="1y", progress=False)['Close'])
