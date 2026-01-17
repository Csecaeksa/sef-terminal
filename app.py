import streamlit as st
import pandas as pd
import yfinance as yf
import math
from fpdf import FPDF

# --- 1. Page Config ---
st.set_page_config(page_title="SEF Terminal Pro", layout="wide")
st.markdown("<style>.stAppToolbar {display: none;}</style>", unsafe_allow_html=True)

# --- 2. Database Logic (Read & Write) ---
def load_stored_data(ticker):
    try:
        df = pd.read_csv("stock_database.csv")
        df['Ticker'] = df['Ticker'].astype(str).str.strip()
        row = df[df['Ticker'] == str(ticker).strip()]
        if not row.empty:
            return float(row.iloc[0]['Stop']), float(row.iloc[0]['Target']), float(row.iloc[0]['FairValue'])
    except:
        pass
    return 0.0, 0.0, 0.0

def save_data_to_db(ticker, stop, target, fv):
    try:
        df = pd.read_csv("stock_database.csv")
        df['Ticker'] = df['Ticker'].astype(str).str.strip()
        ticker_str = str(ticker).strip()
        
        if ticker_str in df['Ticker'].values:
            df.loc[df['Ticker'] == ticker_str, ['Stop', 'Target', 'FairValue']] = [stop, target, fv]
        else:
            new_row = pd.DataFrame({'Ticker': [ticker_str], 'Stop': [stop], 'Target': [target], 'FairValue': [fv]})
            df = pd.concat([df, new_row], ignore_index=True)
            
        df.to_csv("stock_database.csv", index=False)
        return True
    except:
        return False

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
c1, c2, c3, c4, c5, c6 = st.columns([2.0, 0.8, 0.8, 0.8, 0.8, 1.5])

with c1:
    selected_stock = st.selectbox("Search Stock:", options=options)
    symbol = tasi_mapping[selected_stock]
    
    if symbol != st.session_state['last_symbol']:
        s_db, t_db, fv_db = load_stored_data(symbol)
        st.session_state.update({
            'stop': s_db, 'target': t_db, 'fv_val': fv_db, 
            'last_symbol': symbol, 'ready': False
        })
        st.rerun()

with c2: p_in = st.number_input("Market Price", value=float(st.session_state['price']), format="%.2f")
with c3: s_in = st.number_input("Anchor Level", value=float(st.session_state['stop']), format="%.2f", key=f"s_{symbol}")
with c4: t_in = st.number_input("Target Price", value=float(st.session_state['target']), format="%.2f", key=f"t_{symbol}")
with c5: fv_in = st.number_input("Fair Value", value=float(st.session_state['fv_val']), format="%.2f", key=f"fv_{symbol}")

# المزامنة
st.session_state.update({'stop': s_in, 'target': t_in, 'fv_val': fv_in})

with c6:
    st.write("##")
    b1, b2, b3 = st.columns(3)
    radar_btn = b1.button("🛰️ Radar", use_container_width=True)
    analyze_btn = b2.button("📊 Analyze", use_container_width=True)
    if b3.button("💾 Save", use_container_width=True):
        if save_data_to_db(symbol, s_in, t_in, fv_in):
            st.toast(f"Saved {symbol}", icon="✅")
        else:
            st.error("Save Failed")

# --- 7. Radar Logic ---
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

# --- 8. Visual Bar ---
if st.session_state['ready']:
    color = "#09AB3B" if st.session_state['chg'] >= 0 else "#FF4B4B"
    total_range = st.session_state['high52'] - st.session_state['low52']
    pos_52 = ((p_in - st.session_state['low52']) / total_range) * 100 if total_range > 0 else 0
    pos_fv = max(5, min(95, 50 + (((p_in - fv_in)/fv_in)*200))) if fv_in > 0 else 50

    st.markdown(f"""
        <div style="background-color: #f8f9fb; padding: 20px; border-radius: 10px; border-left: 8px solid {color}; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin: 0;">{st.session_state['company_name']}</h2>
                <div style="display: flex; align-items: baseline; gap: 15px;">
                    <span style="font-size: 2.8em; font-weight: bold;">{p_in:.2f}</span>
                    <span style="font-size: 1.3em; color: {color};">{st.session_state['chg']:+.2f} ({st.session_state['pct']:+.2f}%)</span>
                </div>
            </div>
            <div style="display: flex; gap: 40px;">
                <div style="width: 150px;">
                    <p style="margin:0; font-size: 0.85em; color: gray;">52W Range</p>
                    <div style="height: 6px; background: #e0e3eb; border-radius: 3px; position: relative; margin-top:10px;">
                        <div style="position: absolute; left: {pos_52}%; top: -4px; width: 14px; height: 14px; background: {color}; border-radius: 50%;"></div>
                    </div>
                </div>
                <div style="width: 180px;">
                    <p style="margin:0; font-size: 0.85em; color: gray;">Fair Value Status</p>
                    <div style="height: 6px; background: linear-gradient(to right, #09AB3B, #e0e3eb, #FF4B4B); border-radius: 3px; position: relative; margin-top:10px;">
                        <div style="position: absolute; left: {pos_fv}%; top: -4px; width: 14px; height: 14px; background: #131722; border-radius: 50%;"></div>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 9. Report & Chart ---
if st.session_state['ready'] or analyze_btn:
    st.markdown("---")
    risk_amt = abs(p_in - s_in)
    rr_ratio = (t_in - p_in) / risk_amt if risk_amt > 0 else 0
    balance = st.sidebar.number_input("Portfolio", value=100000)
    risk_pct = st.sidebar.slider("Risk %", 0.5, 5.0, 1.0)
    shares = math.floor((balance * (risk_pct/100)) / risk_amt) if risk_amt > 0 else 0
    
    p50 = ((p_in - st.session_state['sma50']) / st.session_state['sma50']) * 100 if st.session_state['sma50'] else 0
    p100 = ((p_in - st.session_state['sma100']) / st.session_state['sma100']) * 100 if st.session_state['sma100'] else 0
    p200 = ((p_in - st.session_state['sma200']) / st.session_state['sma200']) * 100 if st.session_state['sma200'] else 0
    
    result_status = "VALID" if rr_ratio >= 2 else "DANGEROUS"

    report_text = f"SEF REPORT\nTicker: {symbol}\nPrice: {p_in:.2f}\nStop: {s_in:.2f}\nTarget: {t_in:.2f}\nFair Value: {fv_in:.2f}\nRR: 1:{rr_ratio:.2f}\nQty: {shares}\nResult: {result_status}"

    st.subheader("📄 Strategic Analysis")
    st.code(report_text, language="text")

    # Chart
    chart_data = yf.download(f"{symbol}.SR", period="1y", progress=False)
    if not chart_data.empty:
        if isinstance(chart_data.columns, pd.MultiIndex): chart_data.columns = chart_data.columns.get_level_values(0)
        df_p = chart_data[['Close']].copy()
        df_p['SMA 50'] = df_p['Close'].rolling(50).mean()
        df_p['SMA 200'] = df_p['Close'].rolling(200).mean()
        st.line_chart(df_p)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt="SEF Strategic Report", ln=True, align='C')
    for line in report_text.split('\n'):
        pdf.cell(200, 8, txt=line, ln=True)
    st.download_button("📥 Download PDF", data=pdf.output(dest='S').encode('latin-1'), file_name=f"{symbol}.pdf")
