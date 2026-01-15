import streamlit as st
import pandas as pd
import yfinance as yf
import math

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="SEF Terminal Pro", layout="wide")

# --- 2. دالة قراءة الـ 262 شركة من ملف TASI.csv ---
@st.cache_data
def load_full_tasi():
    try:
        # يقرأ الملف الذي حولته أنت لـ CSV
        df = pd.read_csv("TASI.csv")
        df['Ticker'] = df['Ticker'].astype(str).str.strip()
        df['Name_Ar'] = df['Company Name (Arabic)'].astype(str).str.strip()
        df['Sector'] = df['Industry Group'].astype(str).str.strip()
        
        # القائمة المنسدلة (الاسم | الرمز)
        df['Display'] = df['Name_Ar'] + " | " + df['Ticker'] + " (" + df['Sector'] + ")"
        mapping = dict(zip(df['Display'], df['Ticker']))
        return sorted(list(mapping.keys())), mapping
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {e}")
        return [], {}

options, tasi_mapping = load_full_tasi()

# --- 3. دالة جلب البيانات الفنية (السعر + المتوسطات) ---
def fetch_tech_data(ticker_symbol):
    try:
        full_ticker = f"{ticker_symbol}.SR"
        stock = yf.Ticker(full_ticker)
        # جلب بيانات سنة لحساب المتوسطات بدقة
        df = stock.history(period="1y")
        if df.empty: return None

        # حساب المتوسطات البسيطة
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['SMA100'] = df['Close'].rolling(window=100).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()

        data = {
            "price": round(df['Close'].iloc[-1], 2),
            "sma50": round(df['SMA50'].iloc[-1], 2) if not math.isnan(df['SMA50'].iloc[-1]) else "N/A",
            "sma100": round(df['SMA100'].iloc[-1], 2) if not math.isnan(df['SMA100'].iloc[-1]) else "N/A",
            "sma200": round(df['SMA200'].iloc[-1], 2) if not math.isnan(df['SMA200'].iloc[-1]) else "N/A",
            "low": round(df['Low'].tail(20).min(), 2), # أدنى سعر في شهر
            "high": round(df['High'].tail(20).max(), 2) # أعلى سعر في شهر
        }
        return data
    except:
        return None

# --- 4. واجهة المستخدم ---
st.title("🛡️ SEF Terminal Pro | Technical Edition")
st.write(f"📊 تم تحميل **{len(options)}** شركة | المطور: أبو يحيى")

if 'tech' not in st.session_state:
    st.session_state.update({'p_in': 0.0, 'a_in': 0.0, 't_in': 0.0, 'tech': {}})

st.markdown("---")

# صف المدخلات الرئيسي
c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 0.8, 1])

with c1:
    selected = st.selectbox("🔍 اختر سهمك من الـ 262 شركة:", options=options)
    ticker = tasi_mapping[selected]

with c2: p_in = st.number_input("السعر الحالي", value=float(st.session_state['p_in']), step=0.01)
with c3: a_in = st.number_input("الوقف (Anchor)", value=float(st.session_state['a_in']), step=0.01)
with c4: t_in = st.number_input("الهدف (Target)", value=float(st.session_state['t_in']), step=0.01)

with c5:
    st.write("##")
    if st.button("🛰️ Radar", use_container_width=True):
        data = fetch_tech_data(ticker)
        if data:
            st.session_state.update({
                'p_in': data['price'], 'a_in': data['low'], 't_in': data['high'], 'tech': data
            })
            st.rerun()

with c6:
    st.write("##")
    analyze = st.button("📊 Analyze", use_container_width=True)

# --- 5. عرض المتوسطات الحسابية ---
if st.session_state['tech']:
    t = st.session_state['tech']
    st.markdown("### 📈 المتوسطات المتحركة (SMA)")
    cols = st.columns(3)
    
    for i, ma_period in enumerate(['50', '100', '200']):
        ma_val = t[f'sma{ma_period}']
        if ma_val != "N/A":
            diff = round(t['price'] - ma_val, 2)
            # اللون أخضر إذا كان السعر فوق المتوسط
            color = "normal" if diff >= 0 else "inverse"
            cols[i].metric(f"SMA {ma_period}", ma_val, delta=diff, delta_color=color)
        else:
            cols[i].metric(f"SMA {ma_period}", "بيانات ناقصة")

# --- 6. نتائج التحليل المالي ---
if analyze:
    risk_ps = abs(p_in - a_in)
    balance = st.sidebar.number_input("المحفظة", value=100000)
    risk_p = st.sidebar.slider("المخاطرة %", 0.5, 5.0, 1.0)
    
    if risk_ps > 0:
        qty = math.floor((balance * (risk_p/100)) / risk_ps)
        rr = round((t_in - p_in) / risk_ps, 2)
        
        st.markdown("---")
        st.success(f"✅ نتيجة التحليل لـ: {selected}")
        r1, r2, r3 = st.columns(3)
        r1.metric("الكمية (Shares)", f"{qty} سهم")
        r2.metric("نسبة الوقف", f"-{round((risk_ps/p_in)*100, 2)}%")
        r3.metric("معامل R:R", f"1:{rr}")
        
        # الشارت الفني
        st.line_chart(yf.Ticker(f"{ticker}.SR").history(period="1y")['Close'])
