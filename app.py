import streamlit as st
import pandas as pd
import yfinance as yf
import math
from fpdf import FPDF

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="SEF Terminal Pro", layout="wide")

# إخفاء شريط الأدوات العلوي لمظهر أكثر احترافية
st.markdown("<style>.stAppToolbar {display: none;}</style>", unsafe_allow_html=True)

# --- 2. دالة تحميل بيانات TASI ---
@st.cache_data
def load_tasi_data():
    try:
        df = pd.read_csv("TASI.csv")
        df.columns = [c.strip() for c in df.columns]
        df['Ticker'] = df['Ticker'].astype(str).str.strip()
        df['Name_Ar'] = df['Company Name (Arabic)'].astype(str).str.strip()
        df['Display'] = df['Name_Ar'] + " | " + df['Ticker']
        mapping = dict(zip(df['Display'], df['Ticker']))
        return sorted(list(mapping.keys())), mapping
    except Exception as e:
        return [], {}

options, tasi_mapping = load_tasi_data()

# --- 3. إدارة الذاكرة (Session State) ---
if 'ready' not in st.session_state:
    st.session_state.update({
        'price': 0.0, 'stop': 0.0, 'target': 0.0,
        'sma50': 0.0, 'sma100': 0.0, 'sma200': 0.0, 
        'ready': False, 'company_name': '---', 'chg': 0.0, 'pct': 0.0
    })

# --- 4. العنوان والتوقيع وإخلاء المسؤولية ---
st.title("🛡️ SEF Terminal Pro | Final Benchmark")

# إضافة التوقيع وإخلاء المسؤولية تحت العنوان مباشرة
st.markdown("""
    <div style='text-align: left; margin-top: -20px; margin-bottom: 20px;'>
        <span style='color: #555; font-size: 1.1em; font-weight: bold;'>🖋️ Created By Abu Yahia</span>
        <span style='color: #cc0000; font-size: 0.85em; margin-left: 20px; font-weight: 500;'>
            ⚠️ هذا التطبيق للأغراض التعليمية فقط وليس نصيحة مالية | ⚠️ Educational purposes only. Not financial advice.
        </span>
    </div>
    """, unsafe_allow_html=True)

# --- 5. شريط معلومات السهم (مثل الصورة التي أرسلتها) ---
if st.session_state['ready']:
    color = "#09AB3B" if st.session_state['chg'] >= 0 else "#FF4B4B"
    sign = "+" if st.session_state['chg'] >= 0 else ""
    
    st.markdown(f"""
        <div style="background-color: #f8f9fb; padding: 20px; border-radius: 10px; border-left: 8px solid {color}; margin-bottom: 25px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
            <h2 style="margin: 0; color: #131722; font-size: 1.6em;">{st.session_state['company_name']}</h2>
            <div style="display: flex; align-items: baseline; gap: 15px; margin-top: 10px;">
                <span style="font-size: 2.8em; font-weight: bold; color: #131722;">{st.session_state['price']:.2f}</span>
                <span style="font-size: 1.3em; color: {color}; font-weight: bold;">
                    {sign}{st.session_state['chg']:.2f} ({sign}{st.session_state['pct']:.2f}%) {'▲' if st.session_state['chg'] >= 0 else '▼'}
                </span>
                <span style="color: #787b86; font-size: 0.9em;">Currency in SAR • TASI Market Data</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 6. واجهة المدخلات ---
c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 0.8, 1])

with c1:
    selected_stock = st.selectbox("Search Stock:", options=options)
    symbol = tasi_mapping[selected_stock]

with c2: p_in = st.number_input("Price", value=float(st.session_state['price']), format="%.2f")
with c3: s_in = st.number_input("Stop Loss", value=float(st.session_state['stop']), format="%.2f")
with c4: t_in = st.number_input("Target", value=float(st.session_state['target']), format="%.2f")

with c5:
    st.write("##")
    if st.button("🛰️ RADAR", use_container_width=True):
        raw = yf.download(f"{symbol}.SR", period="2y", progress=False)
        if not raw.empty:
            if isinstance(raw.columns, pd.MultiIndex): raw.columns = raw.columns.get_level_values(0)
            close = raw['Close']
            current_p = float(close.iloc[-1])
            prev_p = float(close.iloc[-2])
            change = current_p - prev_p
            
            st.session_state.update({
                'price': current_p,
                'chg': change,
                'pct': (change / prev_p) * 100,
                'company_name': selected_stock.split('|')[0].strip(),
                'stop': float(raw['Low'].tail(20).min()),
                'target': float(raw['High'].tail(20).max()),
                'sma50': float(close.rolling(50).mean().iloc[-1]),
                'sma100': float(close.rolling(100).mean().iloc[-1]),
                'sma200': float(close.rolling(200).mean().iloc[-1]),
                'ready': True
            })
            st.rerun()

with c6:
    st.write("##")
    analyze_btn = st.button("📊 ANALYZE", use_container_width=True)

# --- 7. المؤشرات الفنية والتحليل ---
if st.session_state['ready']:
    st.subheader("📈 Technical Indicators")
    m_cols = st.columns(3)
    ma_list = [("SMA 50", st.session_state['sma50']), ("SMA 100", st.session_state['sma100']), ("SMA 200", st.session_state['sma200'])]
    for i, (label, val) in enumerate(ma_list):
        diff = p_in - val
        color_ma = "#FF4B4B" if diff < 0 else "#09AB3B"
        dist_pct = (diff / val) * 100
        m_cols[i].markdown(f"""
            <div style="background-color: #f8f9fb; padding: 15px; border-radius: 10px; border-left: 6px solid {color_ma};">
                <p style="margin:0; font-size:14px; color:#5c5c5c;">{label}</p>
                <h3 style="margin:0; color:#31333F;">{val:.2f}</h3>
                <p style="margin:0; font-size:16px; color:{color_ma}; font-weight:bold;">{dist_pct:+.2f}%</p>
            </div>
        """, unsafe_allow_html=True)

if analyze_btn or st.session_state['ready']:
    st.markdown("---")
    risk_amt = abs(p_in - s_in)
    rr_ratio = (t_in - p_in) / risk_amt if risk_amt > 0 else 0
    balance = st.sidebar.number_input("Portfolio", value=100000)
    risk_pct = st.sidebar.slider("Risk %", 0.5, 5.0, 1.0)
    shares = math.floor((balance * (risk_pct/100)) / risk_amt) if risk_amt > 0 else 0

    t_cols = st.columns(4)
    t_cols[0].metric("Market Price", f"{p_in:.2f}")
    t_cols[1].metric("R:R Ratio", f"1:{round(rr_ratio, 2)}")
    t_cols[2].metric("Shares", f"{shares}")
    t_cols[3].metric("Risk Cash", f"{balance * (risk_pct/100):.2f}")

    # التقرير الفني
    st.subheader("📄 SEF Structural Analysis")
    result_status = "DANGEROUS" if rr_ratio < 2 else "VALID"
    
    report_text = f"""
    SEF STRATEGIC ANALYSIS REPORT
    Created By Abu Yahia
    ------------------------------
    Ticker: {symbol}.SR | Price: {p_in:.2f}
    
    1. LEVELS:
    - Entry: {p_in:.2f} | Stop: {s_in:.2f} | Target: {t_in:.2f}

    2. METRICS:
    - R:R Ratio: 1:{round(rr_ratio, 2)}
    - Shares: {shares} | Risk: {balance * (risk_pct/100):.2f}

    DISCLAIMER: Educational purposes only.
    ------------------------------
    "Capital preservation is the first priority."
    """
    st.code(report_text, language="text")

    # الشارت
    chart_raw = yf.download(f"{symbol}.SR", period="1y", progress=False)
    if not chart_raw.empty:
        if isinstance(chart_raw.columns, pd.MultiIndex): chart_raw.columns = chart_raw.columns.get_level_values(0)
        plot_df = chart_raw[['Close']].copy()
        plot_df['SMA 50'] = plot_df['Close'].rolling(50).mean()
        plot_df['SMA 200'] = plot_df['Close'].rolling(200).mean()
        st.line_chart(plot_df)
