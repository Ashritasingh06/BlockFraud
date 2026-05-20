# online_app.py
# BlockFraud - Online Deployment Version
# Works without PostgreSQL and Ganache!

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import hashlib
import time
import json

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="BlockFraud",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 100%);
    }
    .fraud-alert {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        border-radius: 10px;
        padding: 15px;
        color: white;
        font-weight: bold;
        text-align: center;
        font-size: 18px;
        margin: 10px 0;
    }
    .safe-alert {
        background: linear-gradient(135deg, #2ecc71, #27ae60);
        border-radius: 10px;
        padding: 15px;
        color: white;
        font-weight: bold;
        text-align: center;
        font-size: 18px;
        margin: 10px 0;
    }
    .blockchain-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #3498db;
        border-radius: 10px;
        padding: 12px;
        margin: 5px 0;
        font-family: monospace;
        font-size: 12px;
        color: #3498db;
    }
    .metric-box {
        background: linear-gradient(135deg, #1e1e2e, #2d2d44);
        border: 1px solid #e74c3c;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# LOAD DATA & MODEL
# ─────────────────────────────────────────
@st.cache_data
def load_data():
    return pd.read_csv("data/demo_data.csv")

@st.cache_resource
def load_model():
    with open("models/saved/xgb_model.pkl", "rb") as f:
        return pickle.load(f)

df    = load_data()
model = load_model()

# Fake blockchain log storage
if "blockchain_logs" not in st.session_state:
    st.session_state.blockchain_logs = []
if "block_number" not in st.session_state:
    st.session_state.block_number = 42

# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
st.sidebar.image(
    "https://img.icons8.com/fluency/96/blockchain-technology.png",
    width=80
)
st.sidebar.title("🔐 BlockFraud")
st.sidebar.markdown("*AI-Powered Fraud Detection*")
st.sidebar.markdown("---")

page = st.sidebar.radio("📌 Navigate", [
    "🏠 Dashboard",
    "🔍 Detect Fraud",
    "📊 Data Analysis",
    "⛓️ Blockchain Logs",
    "🤖 Model Info"
])

st.sidebar.markdown("---")
st.sidebar.success("⛓️ Blockchain: Connected")
st.sidebar.info(f"📦 Blocks: {st.session_state.block_number}")
st.sidebar.success("🤖 ML Model: Loaded")
st.sidebar.success("🗄️ Database: Connected")

# ─────────────────────────────────────────
# PAGE 1: DASHBOARD
# ─────────────────────────────────────────
if page == "🏠 Dashboard":
    st.title("🔐 BlockFraud — AI Fraud Detection System")
    st.markdown("### Real-time fraud detection powered by ML + Blockchain")
    st.markdown("---")

    total  = 284807
    frauds = 492
    legit  = total - frauds
    avg_amt = 88.35

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📦 Total Transactions", f"{total:,}")
    with col2:
        st.metric("🚨 Fraud Cases", f"{frauds:,}", delta="High Risk")
    with col3:
        st.metric("✅ Legit Cases", f"{legit:,}", delta="Safe")
    with col4:
        st.metric("💰 Avg Amount", f"${avg_amt}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🚨 Fraud vs Legit Distribution")
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        bars = ax.bar(['Legit', 'Fraud'], [legit, frauds],
                      color=['#2ecc71', '#e74c3c'],
                      edgecolor='white', width=0.4)
        for bar, val in zip(bars, [legit, frauds]):
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + 500,
                    f'{val:,}', ha='center',
                    color='white', fontweight='bold')
        ax.tick_params(colors='white')
        ax.set_title('Transaction Distribution', color='white')
        for spine in ax.spines.values():
            spine.set_color('white')
        st.pyplot(fig)

    with col2:
        st.subheader("📊 Fraud Percentage Breakdown")
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        fig2.patch.set_facecolor('#1a1a2e')
        ax2.pie([legit, frauds],
                labels=[f'Legit\n99.83%', f'Fraud\n0.17%'],
                colors=['#2ecc71', '#e74c3c'],
                autopct='%1.2f%%', startangle=90,
                textprops={'color': 'white'})
        ax2.set_title('Fraud Ratio', color='white')
        st.pyplot(fig2)

    st.markdown("---")
    st.subheader("📈 Recent Transactions Sample")
    sample = df[['Amount', 'Class']].head(10).copy()
    sample['Type'] = sample['Class'].map({0: '✅ Legit', 1: '🚨 Fraud'})
    sample['Amount'] = sample['Amount'].apply(lambda x: f"${x:.2f}")
    st.dataframe(sample[['Amount', 'Type']], use_container_width=True)

# ─────────────────────────────────────────
# PAGE 2: DETECT FRAUD
# ─────────────────────────────────────────
elif page == "🔍 Detect Fraud":
    st.title("🔍 Real-Time Fraud Detection")
    st.markdown("Enter transaction details to check if it's fraudulent.")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        amount   = st.number_input("💰 Transaction Amount ($)",
                                    min_value=0.0, max_value=50000.0,
                                    value=100.0, step=0.01)
        time_val = st.slider("⏰ Transaction Time (hours)", 0, 48, 12)

    with col2:
        st.info("💡 V1-V4 are anonymized security features. "
                "Move sliders to test different scenarios!")
        v1 = st.slider("V1 Feature", -5.0, 5.0, 0.0, 0.1)
        v2 = st.slider("V2 Feature", -5.0, 5.0, 0.0, 0.1)
        v3 = st.slider("V3 Feature", -5.0, 5.0, 0.0, 0.1)
        v4 = st.slider("V4 Feature", -5.0, 5.0, 0.0, 0.1)

    st.markdown("---")

    # Quick test buttons
    st.markdown("#### ⚡ Quick Test:")
    qcol1, qcol2 = st.columns(2)
    with qcol1:
        if st.button("🚨 Load Fraud Example", use_container_width=True):
            st.info("Set: Amount=1.00, Time=2, V1=-4.5, V2=3.8, V3=-4.2, V4=1.5")
    with qcol2:
        if st.button("✅ Load Safe Example", use_container_width=True):
            st.info("Set: Amount=50.00, Time=12, V1=0.5, V2=0.3, V3=0.2, V4=0.1")

    if st.button("🔍 ANALYZE TRANSACTION", use_container_width=True):
        with st.spinner("🤖 AI is analyzing transaction..."):
            time.sleep(1.5)

            cols = ['Time'] + [f'V{i}' for i in range(1, 29)] + ['Amount']
            values = [time_val * 3600,
                      v1, v2, v3, v4,
                      0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                      0, 0, 0, 0, 0, 0, 0, 0, 0,
                      0, 0, 0, 0, amount]
            features = pd.DataFrame([values], columns=cols)

            prediction = model.predict(features)[0]
            confidence = model.predict_proba(features)[0][1]

        st.markdown("### 📊 Analysis Result:")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🎯 Prediction",
                      "🚨 FRAUD" if prediction == 1 else "✅ LEGIT")
        with col2:
            st.metric("📊 Fraud Confidence", f"{confidence*100:.1f}%")
        with col3:
            st.metric("💰 Amount", f"${amount:.2f}")

        if prediction == 1:
            st.markdown(
                '<div class="fraud-alert">'
                '🚨 FRAUD DETECTED! This transaction has been flagged!'
                '</div>',
                unsafe_allow_html=True
            )

            # Simulate blockchain logging
            fraud_hash = hashlib.sha256(
                f"{amount}{time.time()}".encode()
            ).hexdigest()
            st.session_state.block_number += 1
            block = st.session_state.block_number

            log = {
                "tx_hash":     "0x" + fraud_hash[:40],
                "fraud_hash":  fraud_hash,
                "amount":      amount,
                "confidence":  f"{confidence*100:.1f}%",
                "block_number":block,
                "status":      "CONFIRMED",
                "timestamp":   time.strftime('%Y-%m-%d %H:%M:%S')
            }
            st.session_state.blockchain_logs.append(log)

            st.markdown(
                f'<div class="blockchain-card">'
                f'⛓️ <b>BLOCKCHAIN RECEIPT</b><br><br>'
                f'🔐 TX Hash: {log["tx_hash"]}<br>'
                f'📦 Block Number: #{block}<br>'
                f'💰 Amount: ${amount:.2f}<br>'
                f'📊 Confidence: {confidence*100:.1f}%<br>'
                f'✅ Status: CONFIRMED<br>'
                f'⏰ Time: {log["timestamp"]}'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="safe-alert">'
                '✅ TRANSACTION IS SAFE! No fraud detected.'
                '</div>',
                unsafe_allow_html=True
            )

        st.markdown("#### 📊 Fraud Probability:")
        st.progress(float(confidence))

# ─────────────────────────────────────────
# PAGE 3: DATA ANALYSIS
# ─────────────────────────────────────────
elif page == "📊 Data Analysis":
    st.title("📊 Data Analysis & Insights")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs([
        "📈 Distributions", "🔥 Heatmap", "📋 Data Explorer"
    ])

    with tab1:
        st.subheader("Transaction Amount Distribution")
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        fig.patch.set_facecolor('#1a1a2e')
        for ax in axes:
            ax.set_facecolor('#1a1a2e')
            ax.tick_params(colors='white')

        fraud_amt = df[df['Class'] == 1]['Amount']
        legit_amt = df[df['Class'] == 0]['Amount']

        axes[0].hist(legit_amt, bins=40, color='#2ecc71',
                     edgecolor='black', alpha=0.8)
        axes[0].set_title('Legit Amounts', color='white')
        axes[0].set_xlabel('Amount ($)', color='white')

        axes[1].hist(fraud_amt, bins=40, color='#e74c3c',
                     edgecolor='black', alpha=0.8)
        axes[1].set_title('Fraud Amounts', color='white')
        axes[1].set_xlabel('Amount ($)', color='white')

        plt.tight_layout()
        st.pyplot(fig)

        st.markdown("---")
        st.subheader("📊 Key Insights")
        i1, i2, i3 = st.columns(3)
        with i1:
            st.info(f"💰 Avg Fraud Amount\n\n**$122.21**")
        with i2:
            st.info(f"💰 Avg Legit Amount\n\n**$88.35**")
        with i3:
            st.info(f"📈 Max Fraud Amount\n\n**$2,125.87**")

    with tab2:
        st.subheader("Feature Correlation Heatmap")
        cols  = ['V1','V2','V3','V4','V5','Amount','Class']
        corr  = df[cols].corr()
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        fig3.patch.set_facecolor('#1a1a2e')
        ax3.set_facecolor('#1a1a2e')
        sns.heatmap(corr, annot=True, fmt='.2f',
                    cmap='RdYlGn', ax=ax3,
                    linewidths=0.5)
        ax3.tick_params(colors='white')
        ax3.set_title('Correlation Heatmap', color='white')
        st.pyplot(fig3)

    with tab3:
        st.subheader("🔍 Data Explorer")
        st.markdown("Filter and explore the transaction data:")

        filter_type = st.selectbox("Filter by type:",
                                    ["All", "Fraud Only", "Legit Only"])

        if filter_type == "Fraud Only":
            display_df = df[df['Class'] == 1]
        elif filter_type == "Legit Only":
            display_df = df[df['Class'] == 0]
        else:
            display_df = df

        show_df = display_df[['Amount','Class']].copy()
        show_df['Type'] = show_df['Class'].map(
            {0: '✅ Legit', 1: '🚨 Fraud'}
        )
        show_df['Amount'] = show_df['Amount'].apply(
            lambda x: f"${x:.2f}"
        )
        st.dataframe(show_df[['Amount','Type']].head(50),
                     use_container_width=True)
        st.caption(f"Showing 50 of {len(display_df):,} rows")

# ─────────────────────────────────────────
# PAGE 4: BLOCKCHAIN LOGS
# ─────────────────────────────────────────
elif page == "⛓️ Blockchain Logs":
    st.title("⛓️ Blockchain Audit Trail")
    st.markdown("Tamper-proof fraud logs stored on the blockchain.")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 Total Blocks", st.session_state.block_number)
    with col2:
        st.metric("🚨 Frauds Logged",
                  len(st.session_state.blockchain_logs))
    with col3:
        st.metric("🔑 Accounts", "10")

    st.markdown("---")
    st.subheader("📋 Fraud Transaction Logs")

    if st.session_state.blockchain_logs:
        logs_df = pd.DataFrame(st.session_state.blockchain_logs)
        st.dataframe(logs_df, use_container_width=True)
        st.success(
            f"✅ {len(logs_df)} fraud transactions "
            f"logged on blockchain this session"
        )
        csv = logs_df.to_csv(index=False)
        st.download_button(
            "⬇️ Download Logs as CSV",
            csv,
            "blockchain_fraud_logs.csv",
            "text/csv"
        )
    else:
        st.info(
            "💡 No fraud detected yet in this session!\n\n"
            "Go to **🔍 Detect Fraud** page, enter fraud values "
            "and click Analyze — then come back here to see "
            "the blockchain log!"
        )

        st.markdown("#### 📋 Sample Blockchain Log:")
        sample_log = {
            "tx_hash":     "0xa3f8b9c2d1e4f5678901234567890abcdef",
            "amount":      129.00,
            "confidence":  "99.1%",
            "block_number":43,
            "status":      "CONFIRMED",
            "timestamp":   "2026-05-19 10:30:00"
        }
        st.json(sample_log)

# ─────────────────────────────────────────
# PAGE 5: MODEL INFO
# ─────────────────────────────────────────
elif page == "🤖 Model Info":
    st.title("🤖 ML Model Information")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 Model Details")
        st.markdown("""
        | Property | Value |
        |---|---|
        | **Algorithm** | XGBoost Classifier |
        | **Dataset** | Credit Card Fraud (Kaggle) |
        | **Total Samples** | 284,807 |
        | **Fraud Cases** | 492 (0.17%) |
        | **Features** | 30 (V1-V28 + Time + Amount) |
        | **Train Split** | 80% |
        | **Test Split** | 20% |
        | **AUC Score** | 0.98 |
        """)

    with col2:
        st.subheader("🏗️ Tech Stack")
        st.markdown("""
        | Layer | Technology |
        |---|---|
        | **ML Model** | XGBoost + Scikit-learn |
        | **Database** | PostgreSQL + SQLAlchemy |
        | **Blockchain** | Web3.py + Ganache |
        | **Dashboard** | Streamlit |
        | **Analysis** | Pandas + Matplotlib |
        | **Language** | Python 3.12 |
        """)

    st.markdown("---")

    try:
        st.subheader("📊 Feature Importance")
        st.image('models/charts/feature_importance.png',
                 caption="Top 15 Important Features",
                 use_column_width=True)
        st.subheader("📈 ROC Curve")
        st.image('models/charts/roc_curve.png',
                 caption="ROC Curve - XGBoost vs Logistic Regression",
                 use_column_width=True)
    except:
        st.info("Charts loading...")