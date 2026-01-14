import streamlit as st

# 1. إعدادات الصفحة لتناسب الهاتف (الأيقونة والعنوان)
st.set_page_config(
    page_title="SEF Structural Pro",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# تحسين المظهر للهاتف عبر CSS
st.markdown("""
    <style>
    .report-text {
        font-family: 'Courier New', Courier, monospace;
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2e7d32;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 SEF Structural Analysis")
st.subheader("Wall Street Edition - Price Action")

# 2. مدخلات المستخدم
col1, col2 = st.columns(2)
with col1:
    price = st.number_input("Current Price (سعر الدخول)", value=44.54)
    anchor = st.number_input("Anchor / SL (وقف الخسارة)", value=42.0)
with col2:
    target = st.number_input("Target (الهدف)", value=50.0)
    risk_amount = st.number_input("Risk Cash (المبلغ المخاطر به)", value=1000.0)

# 3. العمليات الحسابية (المنطق البرمجي)
if price > anchor:
    # حساب المسافات
    risk_dist = price - anchor
    reward_dist = target - price
    
    # حساب النسب المئوية (الإضافة الجديدة)
    risk_pct = (risk_dist / price) * 100
    reward_pct = (reward_dist / price) * 100
    
    # حساب نسبة العائد للمخاطرة
    rr_ratio = reward_dist / risk_dist if risk_dist != 0 else 0
    
    # حساب الكمية
    quantity = int(risk_amount / risk_dist) if risk_dist != 0 else 0
    
    # تحديد النتيجة
    if rr_ratio >= 2:
        result = "🟡 GOOD (Acceptable Trade)"
        color = "green"
    elif rr_ratio >= 1:
        result = "🟠 FAIR (High Risk)"
        color = "orange"
    else:
        result = "🔴 DANGEROUS (Avoid)"
        color = "red"

    # 4. عرض التقرير النهائي
    st.divider()
    st.markdown(f"### Result: :{color}[{result}]")
    
    report = f"""
    <div class="report-text">
    <strong>SEF STRATEGIC ANALYSIS REPORT</strong><br>
    -------------------------------------<br>
    <strong>1. LEVELS:</strong><br>
    - Entry: {price}<br>
    - Anchor (SL): {anchor}<br>
    - Target: {target}<br><br>
    
    <strong>2. METRICS:</strong><br>
    - R:R Ratio: 1:{rr_ratio:.2f}<br>
    - <strong>Quantity: {quantity} Shares</strong><br>
    - Risk Cash: {risk_amount}<br>
    - <strong>Risk to SL: -{risk_pct:.2f}%</strong><br>
    - <strong>Reward to Target: +{reward_pct:.2f}%</strong><br>
    -------------------------------------<br>
    <em>Price Action: Breakout Confirmed</em>
    </div>
    """
    st.markdown(report, unsafe_allow_html=True)

else:
    st.error("خطأ: سعر الدخول يجب أن يكون أعلى من وقف الخسارة.")

# تذييل الصفحة
st.caption("Developed for Institutional Grade Analysis | Wall Street Standards")
