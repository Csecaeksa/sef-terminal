import streamlit as st
import pandas as pd
import yfinance as yf
import math
from fpdf import FPDF

# --- 1. Page Config ---
st.set_page_config(page_title="ChartFund Pro", layout="wide")

# --- 2. Load TASI Data ---
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

# --- 3. Secure Session State ---
if 'ready' not in st.session_state:
    st.session_state.update({
        'price': 0.0, 'stop': 0.0, 'target': 0.0,
        'sma50': 0.0, 'sma100': 0.0, 'sma200': 0.0, 'ready': False
    })

# --- 4. Main UI (تعديل العنوان والاسم وإخلاء المسؤولية فقط) ---
col_logo, col_title = st.columns([1, 8])
with col_logo:
    # أيقونة الروبوت
    st.image("https://r.jina.ai/i/053b93f7762649b3806a642921578334", width=100)
with col_title:
    st.title("ChartFund Pro")
    st.write("**Created by AbuYahia**")
    st.caption("⚠️ This content is for informational purposes only and not investment advice.")

st.markdown("---")

c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 0.8, 1])

with c1:
    selected_stock = st.selectbox("Search Stock:", options=options)
    symbol = tasi_mapping[selected_stock]

with c2: p_in = st.number_input("Price", value=float(st.session_state['price']), format="%.2f")
with c3: s_in = st.number_input("Stop Loss", value=float(st.session_state['stop']), format="%.2f")
with c4: t_in = st.number_input("Target", value=float(st.session_state['target']), format="%.2f")

# --- 5. Radar Engine ---
with c5:
    st.write("##")
    if st.button("🛰️ RADAR", use_container_width=True):
        raw = yf.download(f"{symbol}.SR", period="2y", progress=False)
        if not raw.empty:
            if isinstance(raw.columns, pd.MultiIndex): raw.columns = raw.columns.get_level_values(0)
            close = raw['Close']
            st.session_state.update({
                'price': float(close.iloc[-1]),
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

# --- 6. Technical Indicators ---
if st.session_state['ready']:
    st.subheader("📈 Technical Indicators")
    m_cols = st.columns(3)
    ma_list = [("SMA 50", st.session_state['sma50']), ("SMA 100", st.session_state['sma100']), ("SMA 200", st.session_state['sma200'])]
    for i, (label, val) in enumerate(ma_list):
        diff = p_in - val
        color = "#FF4B4B" if diff < 0 else "#09AB3B"
        dist_pct = (diff / val) * 100
        m_cols[i].markdown(f"""
            <div style="background-color: #f8f9fb; padding: 15px; border-radius: 10px; border-left: 6px solid {color};">
                <p style="margin:0; font-size:14px; color:#5c5c5c;">{label}</p>
                <h3 style="margin:0; color:#31333F;">{val:.2f}</h3>
                <p style="margin:0; font-size:16px; color:{color}; font-weight:bold;">{dist_pct:+.2f}%</p>
            </div>
        """, unsafe_allow_html=True)

# --- 7. Structural Analysis & PDF ---
if analyze_btn or st.session_state['ready']:
    st.markdown("---")
    risk_amt = abs(p_in - s_in)
    rr_ratio = (t_in - p_in) / risk_amt if risk_amt > 0 else 0
    balance = st.sidebar.number_input("Portfolio", value=100000)
    risk_pct = st.sidebar.slider("Risk %", 0.5, 5.0, 1.0)
    shares = math.floor((balance * (risk_pct/100)) / risk_amt) if risk_amt > 0 else 0

    t_cols = st.columns(4)
    t_cols[0].metric("Live Price", f"{p_in:.2f}")
    t_cols[1].metric("R:R Ratio", f"1:{round(rr_ratio, 2)}")
    t_cols[2].metric("Shares", f"{shares}")
    t_cols[3].metric("Risk Cash", f"{balance * (risk_pct/100):.2f}")

    st.subheader("📄 SEF Structural Analysis")
    result_status = "DANGEROUS (Avoid - Poor Reward)" if rr_ratio < 2 else "VALID (Good Risk/Reward)"
    
    p50 = ((p_in - st.session_state['sma50']) / st.session_state['sma50']) * 100
    p100 = ((p_in - st.session_state['sma100']) / st.session_state['sma100']) * 100
    p200 = ((p_in - st.session_state['sma200']) / st.session_state['sma200']) * 100

    report_text = f"""
    SEF STRATEGIC ANALYSIS REPORT
    📝 Created By Abu Yahia
    ------------------------------
    Ticker: {symbol}.SR | Price: {p_in:.2f}
    
    1. LEVELS:
    - Entry: {p_in:.2f} | Anchor (SL): {s_in:.2f} | Target: {t_in:.2f}

    2. TECHNICALS (MAs & Distance):
    - SMA 50 : {st.session_state['sma50']:.2f} (Dist: {p50:+.2f}%)
    - SMA 100: {st.session_state['sma100']:.2f} (Dist: {p100:+.2f}%)
    - SMA 200: {st.session_state['sma200']:.2f} (Dist: {p200:+.2f}%)

    3. METRICS:
    - R:R Ratio: 1:{round(rr_ratio, 2)}
    - Quantity: {shares} Shares | Risk: {balance * (risk_pct/100):.2f}

    RESULT: {result_status}
    ------------------------------
    "Capital preservation is the first priority."
    """
    st.code(report_text, language="text")

    def create_pdf(content):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)
        for line in content.split('\n'):
            pdf.cell(200, 8, txt=line, ln=True, align='L')
        return pdf.output(dest='S').encode('latin-1')

    pdf_data = create_pdf(report_text)
    
    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_data,
        file_name=f"ChartFund_Report_{symbol}.pdf",
        mime="application/pdf"
    )

    # إعادة الشارت الأصلي كما في نسختك
    chart_raw = yf.download(f"{symbol}.SR", period="1y", progress=False)
    if isinstance(chart_raw.columns, pd.MultiIndex): chart_raw.columns = chart_raw.columns.get_level_values(0)
    plot_df = chart_raw[['Close']].copy()
    plot_df['SMA 50'] = plot_df['Close'].rolling(50).mean()
    plot_df['SMA 100'] = plot_df['Close'].rolling(100).mean()
    plot_df['SMA 200'] = plot_df['Close'].rolling(200).mean()
    st.line_chart(plot_df)
