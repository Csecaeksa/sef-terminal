import streamlit as st
import pandas as pd
import yfinance as yf
import math
from fpdf import FPDF

# --- 1. Page Config ---
st.set_page_config(page_title="SEF Terminal Pro", layout="wide")
st.markdown("<style>.stAppToolbar {display: none;}</style>", unsafe_allow_html=True)

# --- 2. Google Sheets Configuration (Read Only) ---
# Your Sheet URL
SHEET_ID = "18TzVTveneHK5i3LTambckEfMgRbkwkOcenBmFTaNXVs"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def load_remote_data(ticker):
    try:
        df = pd.read_csv(SHEET_URL)
        # Match Ticker column from your sheet
        row = df[df['Ticker'].astype(str).str.strip() == str(ticker).strip()]
        if not row.empty:
            return float(row.iloc[0]['Stop']), float(row.iloc[0]['Target']), float(row.iloc[0]['FairValue'])
    except:
        pass
    return 0.0, 0.0, 0.0

# --- 3. Load TASI Data ---
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

# --- 4. Secure Session State ---
if 'ready' not in st.session_state:
    st.session_state.update({
        'price': 0.0, 'stop': 0.0, 'target': 0.0, 'fv_val': 0.0,
        'sma50': 0.0, 'sma100': 0.0, 'sma200': 0.0, 
        'ready': False, 'company_name': '---',
        'chg': 0.0, 'pct': 0.0, 'low52': 0.0, 'high52': 1.0,
        'last_symbol': ''
    })

# --- 5. Main UI Header ---
st.title("🛡️ SEF Terminal | Ultimate Hub")
st.markdown("<p style='font-weight: bold; color: #555;'>Created By Abu Yahia</p>", unsafe_allow_html=True)

# --- 6. Input Controls ---
c1, c2, c3, c4, c5, c6 = st.columns([2.0, 0.8, 0.8, 0.8, 0.8, 1.2])

with c1:
    selected_stock = st.selectbox("Search Stock:", options=options)
    symbol = tasi_mapping[selected_stock]
    
    # Auto-load from Google Sheets when stock changes
    if symbol != st.session_state['last_symbol']:
        s_s, t_s, fv_s = load_remote_data(symbol)
        st.session_state.update({'stop': s_s, 'target': t_s, 'fv_val': fv_s, 'last_symbol': symbol})

p_in = c2.number_input("Market Price", value=float(st.session_state['price']), format="%.2f")
s_in = c3.number_input("Anchor Level", value=float(st.session_state['stop']), format="%.2f")
t_in = c4.number_input("Target Price", value=float(st.session_state['target']), format="%.2f")
fv_in = c5.number_input("Fair Value", value=float(st.session_state['fv_val']), format="%.2f")

# --- 7. Buttons Logic ---
with c6:
    st.write("##")
    btn_col1, btn_col2 = st.columns(2)
    radar_btn = btn_col1.button("🛰️ Radar", use_container_width=True)
    analyze_btn = btn_col2.button("📊 Analyze", use_container_width=True)

if radar_btn:
    raw = yf.download(f"{symbol}.SR", period="2y", progress=False)
    if not raw.empty:
        if isinstance(raw.columns, pd.MultiIndex): raw.columns = raw.columns.get_level_values(0)
        close = raw['Close']
        cur, prev = float(close.iloc[-1]), float(close.iloc[-2])
        st.session_state.update({
            'price': cur, 'chg': cur - prev, 'pct': ((cur - prev) / prev) * 100,
            'company_name': selected_stock.split('|')[0].strip(),
            'low52': float(raw['Low'].tail(252).min()),
            'high52': float(raw['High'].tail(252).max()),
            'sma50': float(close.rolling(50).mean().iloc[-1]),
            'sma100': float(close.rolling(100).mean().iloc[-1]),
            'sma200': float(close.rolling(200).mean().iloc[-1]),
            'ready': True
        })
        st.rerun()

if analyze_btn:
    st.session_state.update({'stop': s_in, 'target': t_in, 'fv_val': fv_in, 'ready': True})

# --- 8. THE STRATEGIC REPORT (Original Template) ---
if st.session_state['ready']:
    st.markdown("---")
    risk_amt = abs(p_in - s_in)
    rr_ratio = (t_in - p_in) / risk_amt if risk_amt > 0 else 0
    balance = st.sidebar.number_input("Portfolio", value=100000)
    risk_pct = st.sidebar.slider("Risk %", 0.5, 5.0, 1.0)
    shares = math.floor((balance * (risk_pct/100)) / risk_amt) if risk_amt > 0 else 0
    
    p50 = ((p_in - st.session_state['sma50']) / st.session_state['sma50']) * 100 if st.session_state['sma50'] else 0
    p100 = ((p_in - st.session_state['sma100']) / st.session_state['sma100']) * 100 if st.session_state['sma100'] else 0
    p200 = ((p_in - st.session_state['sma200']) / st.session_state['sma200']) * 100 if st.session_state['sma200'] else 0
    
    result_status = "VALID (Good Risk/Reward)" if rr_ratio >= 2 else "DANGEROUS (Avoid - Poor Reward)"

    report_text = f"""SEF STRATEGIC ANALYSIS REPORT
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
- Quantity: {shares} Shares | Risk Cash: {balance * (risk_pct/100):.2f}

RESULT: {result_status}
------------------------------
"Capital preservation is the first priority." """

    st.subheader("📄 Strategic Analysis Report")
    st.code(report_text, language="text")

    # --- PDF Export Button ---
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    for line in report_text.split('\n'):
        pdf.cell(200, 8, txt=line, ln=True)
    
    pdf_output = pdf.output(dest='S').encode('latin-1')
    st.download_button(label="📥 Download PDF Report", 
                       data=pdf_output, 
                       file_name=f"Report_{symbol}.pdf", 
                       mime="application/pdf")
