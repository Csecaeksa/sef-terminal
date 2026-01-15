import streamlit as st
import pandas as pd
import yfinance as yf
import math

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="SEF Terminal Pro", layout="wide")

# --- 2. تحميل البيانات من ملف TASI.csv ---
@st.cache_data
def load_full_market():
    try:
        # قراءة الملف (تأكد من رفعه باسم TASI.csv)
        df = pd.read_csv("TASI.csv")
        df.columns = [c.strip() for c in df.columns]
        df['Ticker'] = df['Ticker'].astype(str).str.strip()
        df['Name_Ar'] = df['Company Name (Arabic)'].astype(str).str.strip()
        df['Display'] = df['Name_Ar'] + " | " + df['Ticker']
        mapping = dict(zip(df['Display'], df['Ticker']))
        return sorted(list(mapping.keys())), mapping
    except Exception as e:
        st.error(f"خطأ في ملف TASI.csv: {e}")
        return [], {}

options, tasi_mapping = load_full_market()

# --- 3. دالة جلب البيانات الفنية (مُحدثة لحل مشكلة التعطل) ---
def get_clean_technical_data(ticker):
    try:
        # جلب بيانات سنتين لضمان حساب متوسط 200 يوم
        df = yf.download(f"{ticker}.SR", period="2y", progress=False)
        if df.empty: return None

        # تنظيف البيانات من الـ Multi-index (حل المشكلة الأساسي)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # استخراج السلاسل السعرية
        close = df['Close']
        low = df['Low']
        high = df['High']

        return {
            "p": float(close.iloc[-1]),
            "m50": float(close.rolling(window=50).mean().iloc[-1]),
            "m100": float(close.rolling(window=100).mean().iloc[-1]),
            "m200": float(close.rolling(window=200).mean().iloc[-1]),
            "l20": float(low.tail(20).min()),
            "h20": float(high.tail(20).max())
        }
    except Exception as e:
        st.error(f"حدث خطأ فني: {e}")
        return None

# --- 4. واجهة المستخدم والحالة (State) ---
st.title("🛡️ SEF Terminal Pro | Fixed Version")
st.write(f"✅ الشركات في النظام: **{len(options)}** شركة")

# الحفاظ على القيم عند إعادة التشغيل
if 'app_vals' not in st.session_state:
    st.session_state.update({'p': 0.0, 'a': 0.0, 't': 0.0, 'tech': None})

st.markdown("---")

# صف المدخلات والأزرار
c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 0.8, 1])

with c1:
    choice = st.selectbox("🔍 ابحث في الـ 262 شركة:", options=options)
    t_code = tasi_mapping[choice]

with c2: p_in = st.number_input("السعر", value=float(st.session_state['p']), format="%.2f")
with c3: a_in = st.number_input("الوقف", value=float(st.session_state['a']), format="%.2f")
with c4: t_in = st.number_input("الهدف", value=float(st.session_state['t']), format="%.2f")

with c5:
    st.write("##")
    if st.button("🛰️ Radar", use_container_width=True):
        data = get_clean_technical_data(t_code)
        if data:
            st.session_state.update({
                'p': data['p'], 'a': data['l20'], 't': data['h20'], 'tech': data
            })
            st.rerun()

with c6:
    st.write("##")
    # زر Analyze سيقوم بالحساب وعرض الشارت
    analyze_clicked = st.button("📊 Analyze", use_container_width=True)

# --- 5. عرض المتوسطات (SMA) ---
if st.session_state['tech']:
    st.subheader("📈 المتوسطات المتحركة (SMA)")
    d = st.session_state['tech']
    m_cols = st.columns(3)
    
    def draw_metric(col, label, ma_val, price):
        diff = price - ma_val
        col.metric(label, f"{ma_val:.2f}", delta=f"{diff:.2f} ريال", delta_color="normal" if diff >= 0 else "inverse")

    draw_metric(m_cols[0], "SMA 50", d['m50'], d['p'])
    draw_metric(m_cols[1], "SMA 100", d['m100'], d['p'])
    draw_metric(m_cols[2], "SMA 200", d['m200'], d['p'])

# --- 6. نتائج التحليل المالي ---
if analyze_clicked:
    risk_val = abs(p_in - a_in)
    if risk_val > 0:
        balance = st.sidebar.number_input("حجم المحفظة", value=100000)
        risk_p = st.sidebar.slider("مخاطرة الصفقة %", 0.5, 5.0, 1.0)
        qty = math.floor((balance * (risk_p/100)) / risk_val)
        
        st.markdown("---")
        st.success(f"📊 نتيجة التحليل لـ {choice}")
        r_cols = st.columns(3)
        r_cols[0].metric("الكمية المستهدفة", f"{qty} سهم")
        r_cols[1].metric("نسبة الوقف", f"-{round((risk_val/p_in)*100, 2)}%")
        r_cols[2].metric("معامل R:R", f"1:{round((t_in - p_in) / risk_val, 2)}")

        # عرض الشارت (تأكد من تنظيفه أيضاً ليعمل)
        chart_df = yf.download(f"{t_code}.SR", period="1y", progress=False)
        if isinstance(chart_df.columns, pd.MultiIndex): chart_df.columns = chart_df.columns.get_level_values(0)
        st.line_chart(chart_df['Close'])
