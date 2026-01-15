import streamlit as st
import pandas as pd
import yfinance as yf
import math

# --- 1. Page Configuration ---
st.set_page_config(page_title="SEF Terminal Pro", layout="wide")

# --- 2. Load Data from TASI.csv ---
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

# --- 3. Initialize Session State ---
if 'price' not in st.session_state:
    st.session_state.update({
        'price': 0.0, 'stop': 0.0, 'target': 0.0,
        'sma50': 0.0, 'sma100': 0.0, 'sma200': 0.0, 'ready': False
    })

# --- 4. UI Layout ---
st.title("🛡️ SEF Terminal Pro | Fixed Visuals")
st.markdown("---")

c1, c2, c3, c4, c5, c6 = st.columns([2.5, 1, 1, 1, 0.8, 1])

with c1:
    selected_stock = st.selectbox("Search Stock:", options=options)
    symbol = tasi_mapping[selected_stock]

with c2: p_in = st.number_input("Price", value=float(st.session_state['price']), format="%.2f")
with c3: s_in = st.number_input("Stop Loss", value=float(st.session_state['stop']), format="%.2f")
with c4: t_in = st.number_input("Target", value=float(st.session_state['target']), format="%.2f")

# --- 5. Radar Button ---
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

# --- 6. Technical Indicators (STRICT COLOR LOGIC) ---
if st.session_state['ready']:
    st.subheader("📊 Technical Indicators")
    m_cols = st.columns(3)
    ma_data = [("SMA 50", st.session_state['sma50']), 
               ("SMA 100", st.session_state['sma100']), 
               ("SMA 200", st.session_state['sma200'])]
    
    for i, (label, val) in enumerate(ma_data):
        diff = st.session_state['price'] - val
        # الهلال الأحمر هنا: نجبره يصير أحمر إذا كان تحت المتوسط
        # delta_color="inverse" تجعل السالب أحمر والموجب أخضر
        st_color = "inverse" if diff < 0 else "normal"
        
        m_cols[i].metric(label, f"{val:.2f}", delta=f"{diff:.2f} SAR", delta_color=st_color)

# --- 7. Chart with Support Line ---
if analyze_btn:
    risk_amt = abs(p_in - s_in)
    if risk_amt > 0:
        shares = math.floor((1000 * 1.0) / risk_amt) # Placeholder calculation
        st.markdown("---")
        st.success(f"Strategy for: {selected_stock}")
        
        # Financial Chart
        chart_raw = yf.download(f"{symbol}.SR", period="1y", progress=False)
        if isinstance(chart_raw.columns, pd.MultiIndex): chart_raw.columns = chart_raw.columns.get_level_values(0)
        
        plot_df = chart_raw[['Close']].copy()
        plot_df['SMA 50'] = plot_df['Close'].rolling(50).mean()
        plot_df['SMA 100'] = plot_df['Close'].rolling(100).mean()
        plot_df['SMA 200'] = plot_df['Close'].rolling(200).mean()
        plot_df['Support'] = st.session_state['stop'] # خط الدعم الأفقي
        
        st.line_chart(plot_df)
