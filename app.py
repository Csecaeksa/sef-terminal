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
        # قراءة الملف اللي حولته لـ CSV (تأكد أن الاسم TASI.csv)
        df = pd.read_csv("TASI.csv")
        
        # تنظيف البيانات بناءً على أعمدة ملفك
        df['Ticker'] = df['Ticker'].astype(str).str.strip()
        df['Name_Ar'] = df['Company Name (Arabic)'].astype(str).str.strip()
        df['Sector'] = df['Industry Group'].astype(str).str.strip()
        
        # إنشاء نص العرض
        df['Display'] = df['Name_Ar'] + " | " + df['Ticker'] + " (" + df['Sector'] + ")"
        
        mapping = dict(zip(df['Display'], df['Ticker']))
        return sorted(list(mapping.keys())), mapping
    except Exception as e:
        st.error(f"⚠️ تأكد من وجود ملف TASI.csv بجانب الكود. الخطأ: {e}")
        return [], {}

options, tasi_mapping = load_tasi_complete()

# --- 3. دالة جلب البيانات الفنية والمتوسطات ---
def fetch_technical_data(ticker_symbol):
    try:
        full_ticker = f"{ticker_symbol}.SR"
        stock = yf.Ticker(full_ticker)
        # جلب بيانات سنة كاملة لحساب المتوسطات
        df = stock.history(period="1y")
        if df.empty: return None

        # حساب المتوسطات الحسابية البسيطة (SMA)
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['SMA100'] = df['Close'].rolling(window=100).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()

        data = {
            "price": round(df['Close'].iloc[-1], 2),
            "sma50": round(df['SMA50'].iloc[-1], 2) if not pd.isna(df['SMA50'].iloc[-1]) else "N/A",
            "sma100": round(df['SMA100'].iloc[-1], 2) if not pd.isna(df['SMA100'].iloc[-1]) else "N/A",
            "sma200": round(df['SMA200'].iloc[-1], 2) if not pd.isna(df['SMA200'].iloc[-1]) else "N/A",
            "low_month": round(df['Low'].tail(22).min(), 2),
            "high_month": round(df['High'].tail(22).max(), 2)
        }
        return data
    except:
        return None

# --- 4. واجهة المستخدم ---
st.title("🛡️ SEF Terminal Pro | Technical Edition")
st.write(f"📊 عدد الشركات في النظام الآن: **{len(options)}** شركة")

if 'tech_data' not in st.session_state:
    st.session_state.update({'p_val': 0.0, 'a_val': 0.0, 't_val': 0.0, 'tech_data': {}})

st.markdown("---")

# صف البحث والمدخلات
c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 0.8, 1])

with c1:
    selected = st.selectbox("🔍 ابحث في الـ 262 شركة (اسم أو رمز):", options=options)
    ticker = tasi_mapping[selected]

with c2: p_in = st.number_input("السعر الحالي", value=float(st.session_state['p_val']), step=0.01)
with c3: a_in = st.number_input("الوقف (Anchor)", value=float(st.session_state['a_val']), step=0.01)
with c4: t_in = st.number_input("الهدف (Target)", value=float(st.session_state['t_val']), step=0.01)

with c5:
    st.write("##")
    if st.button("🛰️ Radar", use_container_width=True):
        data = fetch_technical_data(ticker)
        if data:
            st.session_state.update({
                'p_val': data['price'], 'a_val': data['low_month'], 
                't_val': data['high_month'], 'tech_data': data
            })
            st.rerun()

with c6:
    st.write("##")
    analyze = st.button("📊 Analyze", use_container_width=True)

# --- 5. عرض المتوسطات (SMA) ---
if st.session_state['tech_data']:
    td = st.session_state['tech_data']
    st.markdown("### 📈 المتوسطات الحسابية (SMA)")
    m_cols = st.columns(3)
    for i, period in enumerate(['50', '100', '200']):
        val = td[f'sma{period}']
        if val != "N/A":
            diff = round(td['price'] - val, 2)
            # لون أخضر إذا السعر فوق المتوسط
            status_color = "normal" if diff >= 0 else "inverse"
            m_cols[i].metric(f"متوسط {period} يوم", val, delta=diff, delta_color=status_color)
        else:
            m_cols[i].metric(f"متوسط {period} يوم", "بيانات غير كافية")

# --- 6. نتائج التحليل المالي ---
if analyze:
    risk_per_share = abs(p_in - a_in)
    balance = st.sidebar.number_input("المحفظة", value=100000)
    risk_p = st.sidebar.slider("المخاطرة %", 0.5, 5.0, 1.0)
    
    if risk_per_share > 0:
        qty = math.floor((balance * (risk_p/100)) / risk_per_share)
        rr = round((t_in - p_in) / risk_per_share, 2)
        
        st.success(f"✅ تم تحليل {selected}")
        r1, r2, r3 = st.columns(3)
        r1.metric("عدد الأسهم", f"{qty} سهم")
        r2.metric("نسبة الوقف", f"-{round((risk_per_share/p_in)*100, 2)}%")
        r3.metric("معامل R:R", f"1:{rr}")
        
        # الشارت
        st.line_chart(yf.Ticker(f"{ticker}.SR").history(period="1y")['Close'])
