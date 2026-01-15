import streamlit as st
import pandas as pd
import yfinance as yf
import math

# --- 1. Page Config ---
st.set_page_config(page_title="SEF Terminal Pro", layout="wide")

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
        st.error(f"Error: {e}")
        return [], {}

options, tasi_mapping = load_tasi_data()

# --- 3. Session State ---
if 'price' not in st.session_state:
    st.session_state.update({
        'price': 0.0, 'stop': 0.0, 'target': 0.0,
        'sma50': 0.0, 'sma100': 0.0, 'sma200': 0.0, 'ready': False
    })

# --- 4. Main UI ---
st.title("🛡️ SEF Terminal Pro | STRICT COLOR MODE")

c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 0.8, 1])

with c1:
    selected_stock = st.selectbox("Search Stock:", options=options)
    symbol = tasi_mapping[selected_stock]

with c2: p_in = st.number_input("Price", value=float(st.session_state['price']), format="%.2f")
with c3: s_in = st.number_input("Stop Loss", value=float(st.session_state['stop']), format="%.2f")
with c4: t_in = st.number_input("Target", value=float(st.session_state['target']), format="%.2f")

# --- 5. Radar Logic ---
with c5:
    st.write("##")
    if st.button("🛰️ RADAR", use_container_width=True):
        try:
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
        except Exception as e: st.error(f"Error: {e}")

with c6:
    st.write("##")
    analyze_btn = st.button("📊 ANALYZE", use_container_width=True)

# --- 6. Technical Indicators (MANUAL HTML COLORING) ---
if st.session_state['ready']:
    st.subheader("📊 Technical Indicators (Manual Color Override)")
    m_cols = st.columns(3)
    ma_list = [
        ("SMA 50", st.session_state['sma50']),
        ("SMA 100", st.session_state['sma100']),
        ("SMA 200", st.session_state['sma200'])
    ]
    
    for i, (label, val) in enumerate(ma_list):
        diff = st.session_state['price'] - val
        # تحديد اللون يدوياً
        color = "#FF4B4B" if diff < 0 else "#09AB3B" # أحمر للسلبي وأخضر للإيجابي
        direction = "↓" if diff < 0 else "↑"
        
        # حقن HTML لعرض الأرقام بالألوان الصحيحة غصب عن المتصفح
        m_cols[i].markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid {color};">
                <p style="margin:0; font-size:14px; color:#555;">{label}</p>
                <h2 style="margin:0; color:#31333F;">{val:.2f}</h2>
                <p style="margin:0; font-size:18px; color:{color}; font-weight:bold;">
                    {direction} {abs(diff):.2f} SAR
                </p>
            </div>
        """, unsafe_allow_html=True)

# --- 7. Chart Section ---
if analyze_btn:
    st.markdown("---")
    chart_raw = yf.download(f"{symbol}.SR", period="1y", progress=False)
    if isinstance(chart_raw.columns, pd.MultiIndex): chart_raw.columns = chart_raw.columns.get_level_values(0)
    
    plot_df = chart_raw[['Close']].copy()
    plot_df['SMA 50'] = plot_df['Close'].rolling(50).mean()
    plot_df['SMA 100'] = plot_df['Close'].rolling(100).mean()
    plot_df['SMA 200'] = plot_df['Close'].rolling(200).mean()
    plot_df['Support'] = st.session_state['stop']
    
    st.line_chart(plot_df)
