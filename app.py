import streamlit as st
import pandas as pd
import yfinance as yf
import math

# --- 1. Page Config ---
st.set_page_config(page_title="SEF Terminal Pro", layout="wide")
st.markdown("<style>.stAppToolbar {display: none;}</style>", unsafe_allow_html=True)

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
    except Exception:
        return [], {}

options, tasi_mapping = load_tasi_data()

# --- 3. Session State (Fixed & Secured) ---
if 'ready' not in st.session_state:
    st.session_state.update({
        'price': 0.0, 'stop': 0.0, 'target': 0.0, 'fv_val': 0.0,
        'sma50': 0.0, 'sma100': 0.0, 'sma200': 0.0, 
        'ready': False, 'company_name': '---',
        'chg': 0.0, 'pct': 0.0, 'low52': 0.0, 'high52': 1.0
    })

st.title("🛡️ SEF Terminal | Ultimate Hub")

# --- 4. Inputs Section ---
c1, c2, c3, c4, c5, c6 = st.columns([2.0, 0.8, 0.8, 0.8, 0.8, 1.2])
with c1:
    selected_stock = st.selectbox("Search Stock:", options=options)
    symbol = tasi_mapping[selected_stock]
with c2: p_in = st.number_input("Market Price", value=float(st.session_state['price']), format="%.2f")
with c3: s_in = st.number_input("Anchor Level", value=float(st.session_state['stop']), format="%.2f")
with c4: t_in = st.number_input("Target Price", value=float(st.session_state['target']), format="%.2f")
with c5: fv_in = st.number_input("Fair Value", value=float(st.session_state['fv_val']), format="%.2f")

# Update state immediately
st.session_state['fv_val'] = fv_in

# --- 5. Dynamic Info Bar ---
if st.session_state['ready']:
    color = "#09AB3B" if st.session_state['chg'] >= 0 else "#FF4B4B"
    t_range = st.session_state['high52'] - st.session_state['low52']
    pos_52 = ((p_in - st.session_state['low52']) / t_range) * 100 if t_range > 0 else 0
    
    # Fair Value Indicator Logic
    if fv_in > 0:
        fv_diff = ((p_in - fv_in) / fv_in) * 100
        pos_fv = 50 + (fv_diff * 2)
        pos_fv = max(5, min(95, pos_fv))
    else: pos_fv = 50

    st.markdown(f"""
        <div style="background-color: #f8f9fb; padding: 20px; border-radius: 10px; border-left: 8px solid {color}; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin: 0;">{st.session_state['company_name']}</h2>
                <span style="font-size: 2.5em; font-weight: bold;">{p_in:.2f}</span>
                <span style="color: {color}; font-weight: bold; margin-left:10px;">{st.session_state['chg']:+.2f} ({st.session_state['pct']:+.2f}%)</span>
            </div>
            <div style="display: flex; gap: 30px;">
                <div style="width: 180px;">
                    <p style="margin:0; font-size: 0.8em; color: gray;">Fair Value Status</p>
                    <div style="height: 6px; background: linear-gradient(to right, #09AB3B, #e0e3eb, #FF4B4B); border-radius: 3px; position: relative; margin-top:10px;">
                        <div style="position: absolute; left: {pos_fv}%; top: -4px; width: 14px; height: 14px; background: #131722; border-radius: 50%; border: 2px solid white;"></div>
                    </div>
                </div>
                <div style="width: 180px;">
                    <p style="margin:0; font-size: 0.8em; color: gray;">52 wk Range</p>
                    <div style="height: 6px; background: #e0e3eb; border-radius: 3px; position: relative; margin-top:10px;">
                        <div style="position: absolute; left: {pos_52}%; top: -4px; width: 14px; height: 14px; background: #131722; border-radius: 50%; border: 2px solid white;"></div>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 6. Controls ---
with c6:
    st.write("##")
    radar_col, analyze_col = st.columns(2)
    with radar_col: radar_btn = st.button("🛰️ Radar", use_container_width=True)
    with analyze_col: analyze_btn = st.button("📊 Analyze", use_container_width=True)

if radar_btn:
    raw = yf.download(f"{symbol}.SR", period="2y", progress=False)
    if not raw.empty:
        close = raw['Close']
        if isinstance(close, pd.DataFrame): close = close.iloc[:, 0]
        cur, prev = float(close.iloc[-1]), float(close.iloc[-2])
        st.session_state.update({
            'price': cur, 'chg': cur - prev, 'pct': ((cur - prev) / prev) * 100,
            'company_name': selected_stock.split('|')[0].strip(),
            'low52': float(raw['Low'].tail(252).min()),
            'high52': float(raw['High'].tail(252).max()),
            'stop': float(raw['Low'].tail(20).min()),
            'target': float(raw['High'].tail(20).max()),
            'fv_val': cur,
            'sma50': float(close.rolling(50).mean().iloc[-1]),
            'sma100': float(close.rolling(100).mean().iloc[-1]),
            'sma200': float(close.rolling(200).mean().iloc[-1]),
            'ready': True
        })
        st.rerun()

# --- 7. Full Strategic Report (As requested) ---
if st.session_state['ready']:
    st.markdown("---")
    risk_amt = abs(p_in - s_in)
    rr_ratio = (t_in - p_in) / risk_amt if risk_amt > 0 else 0
    balance = st.sidebar.number_input("Portfolio", value=100000)
    risk_pct = st.sidebar.slider("Risk %", 0.5, 5.0, 1.0)
    shares = math.floor((balance * (risk_pct/100)) / risk_amt) if risk_amt > 0 else 0
    
    # Distance Calculations
    p50 = ((p_in - st.session_state['sma50']) / st.session_state['sma50']) * 100 if st.session_state['sma50'] else 0
    p100 = ((p_in - st.session_state['sma100']) / st.session_state['sma100']) * 100 if st.session_state['sma100'] else 0
    p200 = ((p_in - st.session_state['sma200']) / st.session_state['sma200']) * 100 if st.session_state['sma200'] else 0
    
    result_status = "VALID (Good Risk/Reward)" if rr_ratio >= 2 else "DANGEROUS (Avoid - Poor Reward)"

    # The Detailed Report Text
    report_text = f"""
    SEF STRATEGIC ANALYSIS REPORT
    Created By Abu Yahia
    ------------------------------
    Ticker: {symbol}.SR | Price: {p_in:.2f} | Fair Value: {fv_in:.2f}

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
    
    st.subheader("📄 Structural Analysis")
    st.code(report_text, language="text")

    # Chart with SMAs
    chart_data = yf.download(f"{symbol}.SR", period="1y", progress=False)
    if not chart_data.empty:
        pdf = chart_data[['Close']].copy()
        pdf['SMA 50'] = pdf['Close'].rolling(50).mean()
        pdf['SMA 100'] = pdf['Close'].rolling(100).mean()
        pdf['SMA 200'] = pdf['Close'].rolling(200).mean()
        st.line_chart(pdf)
