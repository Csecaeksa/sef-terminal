import streamlit as st
import pandas as pd
import yfinance as yf
import math
from fpdf import FPDF

# --- 1. Page Config ---
st.set_page_config(page_title="SEF Terminal Pro", layout="wide")
st.markdown("<style>.stAppToolbar {display: none;}</style>", unsafe_allow_html=True)

# --- 2. Database Logic (الربط مع ملف stock_database.csv) ---
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
    
    # الربط التلقائي: تحميل البيانات من الملف عند تغيير السهم
    if symbol != st.session_state['last_symbol']:
        s_db, t_db, fv_db = load_stored_data(symbol)
        st.session_state.update({'stop': s_db, 'target': t_db, 'fv_val': fv_db, 'last_symbol': symbol})

p_in = c2.number_input("Market Price", value=float(st.session_state['price']), format="%.2f")
s_in = c3.number_input("Anchor Level", value=float(st.session_state['stop']), format="%.2f")
t_in = c4.number_input("Target Price", value=float(st.session_state['target']), format="%.2f")
fv_in = c5.number_input("Fair Value", value=float(st.session_state['fv_val']), format="%.2f")

# --- 7. Ticker Info Bar ---
if st.session_state['ready']:
    color = "#09AB3B" if st.session_state['chg'] >= 0 else "#FF4B4B"
    total_range = st.session_state['high52'] - st.session_state['low52']
    pos_52 = ((p_in - st.session_state['low52']) / total_range) * 100 if total_range > 0 else 0
    pos_fv = max(5, min(95, 50 + (((p_in - fv_in)/fv_in)*200))) if fv_in > 0 else 50

    st.markdown(f"""
        <div style="background-color: #f8f9fb; padding: 20px; border-radius: 10px; border-left: 8px solid {color}; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin: 0;">{st.session_state['company_name']}</h2>
                <div
