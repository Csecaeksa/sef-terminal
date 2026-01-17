import streamlit as st
import pandas as pd
import yfinance as yf
import math
from fpdf import FPDF

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

# --- 3. Session State Initialization ---
if 'ready' not in st.session_state:
    st.session_state.update({
        'price': 0.0, 'stop': 0.0, 'target': 0.0, 'fv_val': 0.0,
        'sma50': 0.0, 'sma100': 0.0, 'sma200': 0.0, 
        'ready': False, 'company_name': '---',
        'chg': 0.0, 'pct': 0.0, 'low52': 0.0, 'high52': 1.0
    })

# --- 4. Inputs Section (PLACED BEFORE BAR CALCULATION) ---
st.title("🛡️ SEF Terminal | Ultimate Hub")

# نضع المدخلات هنا ليتم قراءتها قبل رسم البار العلوي
c1, c2, c3, c4, c5, c6 = st.columns([2.0, 0.8, 0.8, 0.8, 0.8, 1.2])
with c1:
    selected_stock = st.selectbox("Search Stock:", options=options)
    symbol = tasi_mapping[selected_stock]
with c2: p_in = st.number_input("Market Price", value=float(st.session_state['price']), format="%.2f")
with c3: s_in = st.number_input("Anchor Level", value=float(st.session_state['stop']), format="%.2f")
with c4: t_in = st.number_input("Target Price", value=float(st.session_state['target']), format="%.2f")
# خانة الـ Fair Value
with c5: fv_in = st.number_input("Fair Value", value=float(st.session_state['fv_val']), format="%.2f")

# تحديث قيم السحب الفوري
st.session_state['fv_val'] = fv_in
st.session_state['price'] = p_in

# --- 5. Ticker Info Bar (Dynamic Movement Logic) ---
if st.session_state['ready']:
    color = "#09AB3B" if st.session_state['chg'] >= 0 else "#FF4B4B"
    
    # 52-Week Logic
    total_r = st.session_state['high52'] - st.session_state['low52']
    pos_52 = ((p_in - st.session_state['low52']) / total_r) * 100 if total_r > 0 else 0
    
    # Fair Value Movement Logic (INSTANT UPDATE)
    # نقارن السعر الحالي بالـ Fair Value المدخلة
    if fv_in > 0:
        # إذا السعر الحالي أكبر من العادلة = Over
        # إذا السعر الحالي أصغر من العادلة = Under
        fv_diff_pct = ((p_in - fv_in) / fv_in) * 100
        pos_fv = 50 + (fv_diff_pct * 2) # حساسية الحركة
        pos_fv = max(5, min(95, pos_fv))
    else:
        pos_fv = 50

    st.markdown(f"""
        <div style="background-color: #f8f9fb; padding: 20px; border-radius: 10px; border-left: 8px solid {color}; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin: 0; color: #131722; font-size: 1.6em;">{st.session_state['company_name']}</h2>
                <div style="display: flex; align-items: baseline; gap: 15px; margin-top: 10px;">
                    <span style="font-size: 2.8em; font-weight: bold; color: #131722;">{p_in:.2f}</span>
                    <span style="font-size: 1.3em; color: {color}; font-weight: bold;">
                        {st.session_state['chg']:+.2f} ({st.session_state['pct']:+.2f}%)
                    </span>
                </div>
            </div>
            <div style="display: flex; gap: 40px; text-align: right;">
                <div style="width: 200px;">
                    <p style="margin:0; font-size: 0.85em; color: #787b86;">Fair Value Status</p>
                    <div style="display: flex; justify-content: space-between; font-size: 0.75em; font-weight: bold; margin-bottom: 5px;">
                        <span style="color:#09AB3B">Under</span><span style="color:#FF4B4B">Over</span>
                    </div>
                    <div style="height: 6px; background: linear-gradient(to right, #09AB3B, #e0e3eb, #FF4B4B); border-radius: 3px; position: relative;">
                        <div style="position: absolute; left: {pos_fv}%; top: -4px; width: 14px; height: 14px; background: #131722; border-radius: 50%; border: 2px solid white;"></div>
                    </div>
                </div>
                <div style="width: 200px;">
                    <p style="margin:0; font-size: 0.85em; color: #787b86;">52 wk Range</p>
                    <div style="display: flex; justify-content: space-between; font-size: 0.9em; font-weight: bold; margin-bottom: 5px;">
                        <span>{st.session_state['low52']:.2f}</span><span>{st.session_state['high52']:.2f}</span>
                    </div>
                    <div style="height: 6px; background: #e0e3eb; border-radius: 3px; position: relative;">
                        <div style="position: absolute; left: {pos_52}%; top: -4px; width: 14px; height: 14px; background: #131722; border-radius: 50%; border: 2px solid white;"></div>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 6. Buttons & Radar Logic ---
with c6:
    st.write("##")
    radar_col, analyze_col = st.columns(2)
    with radar_col: radar_btn = st.button("🛰️ Radar", use_container_width=True)
    with analyze_col: analyze_btn = st.button("📊 Analyze", use_container_width=True)

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
            'stop': float(raw['Low'].tail(20).min()),
            'target': float(raw['High'].tail(20).max()),
            'fv_val': cur,
            'sma50': float(close.rolling(50).mean().iloc[-1]),
            'sma100': float(close.rolling(100).mean().iloc[-1]),
            'sma200': float(close.rolling(200).mean().iloc[-1]),
            'ready': True
        })
        st.rerun()

# --- 7. Technical Indicators & Results ---
if st.session_state['ready']:
    st.subheader("📈 Technical Indicators")
    m_cols = st.columns(3)
    ma_data = [("SMA 50", st.session_state['sma50']), ("SMA 100", st.session_state['sma100']), ("SMA 200", st.session_state['sma200'])]
    for i, (label, val) in enumerate(ma_data):
        diff = p_in - val
        ma_color = "#FF4B4B" if diff < 0 else "#09AB3B"
        dist = (diff / val) * 100 if val != 0 else 0
        m_cols[i].markdown(f"""
            <div style="background-color: #f8f9fb; padding: 15px; border-radius: 10px; border-left: 6px solid {ma_color};">
                <p style="margin:0; font-size:14px; color:#5c5c5c;">{label}</p>
                <h3 style="margin:0;">{val:.2f}</h3>
                <p style="margin:0; color:{ma_color}; font-weight:bold;">{dist:+.2f}%</p>
            </div>
        """, unsafe_allow_html=True)

if analyze_btn or st.session_state['ready']:
    st.markdown("---")
    risk = abs(p_in - s_in)
    rr = (t_in - p_in) / risk if risk > 0 else 0
    res = "VALID" if rr >= 2 else "DANGEROUS"
    report = f"Ticker: {symbol} | Price: {p_in:.2f} | Fair Value: {fv_in:.2f}\nResult: {res}"
    st.code(report, language="text")
