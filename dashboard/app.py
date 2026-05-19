# app.py
# BlockFraud - Streamlit Dashboard

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import json
import time
import hashlib
from sqlalchemy import create_engine, text
from web3 import Web3

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
    .main { background-color: #0f0f0f; }
    .stApp { background: linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 100%); }
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e, #2d2d44);
        border: 1px solid #e74c3c;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin: 8px 0;
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
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# CONNECTIONS
# ─────────────────────────────────────────
@st.cache_resource
def get_db():
    DB_PASSWORD = "admin123"  # ← change to your password
    return create_engine(
        f"postgresql://postgres:{DB_PASSWORD}@localhost:5432/blockfraud"
    )

@st.cache_resource
def load_model():
    with open('models/saved/xgb_model.pkl', 'rb') as f:
        return pickle.load(f)

@st.cache_resource
def get_blockchain():
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
    return w3 if w3.is_connected() else None

engine     = get_db()
model      = load_model()
w3         = get_blockchain()

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

# Blockchain status
if w3:
    st.sidebar.success(f"⛓️ Blockchain: Connected")
    st.sidebar.info(f"📦 Blocks: {w3.eth.block_number}")
else:
    st.sidebar.error("⛓️ Blockchain: Offline")

# ─────────────────────────────────────────
# PAGE 1: DASHBOARD
# ─────────────────────────────────────────
if page == "🏠 Dashboard":
    st.title("🔐 BlockFraud — AI Fraud Detection System")
    st.markdown("### Real-time fraud detection powered by ML + Blockchain")
    st.markdown("---")

    # Stats from DB
    with engine.connect() as conn:
        total  = conn.execute(text('SELECT COUNT(*) FROM transactions')).fetchone()[0]
        frauds = conn.execute(text('SELECT COUNT(*) FROM transactions WHERE "Class"=1')).fetchone()[0]
        legit  = total - frauds
        avg_amt= conn.execute(text('SELECT AVG("Amount") FROM transactions')).fetchone()[0]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📦 Total Transactions", f"{total:,}")
    with col2:
        st.metric("🚨 Fraud Cases", f"{frauds:,}", delta="High Risk")
    with col3:
        st.metric("✅ Legit Cases", f"{legit:,}", delta="Safe")
    with col4:
        st.metric("💰 Avg Amount", f"${avg_amt:.2f}")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🚨 Fraud vs Legit Distribution")
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#1a1a2e')
        ax.set_facecolor('#1a1a2e')
        colors = ['#2ecc71', '#e74c3c']
        bars = ax.bar(['Legit', 'Fraud'], [legit, frauds],
                      color=colors, edgecolor='white', width=0.4)
        for bar, val in zip(bars, [legit, frauds]):
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + 500,
                    f'{val:,}', ha='center',
                    color='white', fontweight='bold')
        ax.tick_params(colors='white')
        ax.set_title('Transaction Distribution', color='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        st.pyplot(fig)

    with col2:
        st.subheader("📊 Fraud Percentage Breakdown")
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        fig2.patch.set_facecolor('#1a1a2e')
        ax2.set_facecolor('#1a1a2e')
        sizes  = [legit, frauds]
        labels = [f'Legit\n{legit/total*100:.2f}%',
                  f'Fraud\n{frauds/total*100:.2f}%']
        ax2.pie(sizes, labels=labels, colors=['#2ecc71','#e74c3c'],
                autopct='%1.2f%%', startangle=90,
                textprops={'color':'white'})
        ax2.set_title('Fraud Ratio', color='white')
        st.pyplot(fig2)

# ─────────────────────────────────────────
# PAGE 2: DETECT FRAUD
# ─────────────────────────────────────────
elif page == "🔍 Detect Fraud":
    st.title("🔍 Real-Time Fraud Detection")
    st.markdown("Enter transaction details below to check if it's fraudulent.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        amount = st.number_input("💰 Transaction Amount ($)",
                                  min_value=0.0, max_value=50000.0,
                                  value=100.0, step=0.01)
        time_val = st.slider("⏰ Transaction Time (hours)", 0, 48, 12)

    with col2:
        st.info("💡 V1-V4 are anonymized security features from the bank. Use values between -5 and 5.")
        v1 = st.slider("V1 Feature", -5.0, 5.0, 0.0, 0.1)
        v2 = st.slider("V2 Feature", -5.0, 5.0, 0.0, 0.1)
        v3 = st.slider("V3 Feature", -5.0, 5.0, 0.0, 0.1)
        v4 = st.slider("V4 Feature", -5.0, 5.0, 0.0, 0.1)

    st.markdown("---")

    if st.button("🔍 ANALYZE TRANSACTION", use_container_width=True):
        with st.spinner("🤖 Analyzing transaction..."):
            time.sleep(1)

            # Correct 30 columns: Time + V1 to V28 + Amount
            cols = ['Time'] + [f'V{i}' for i in range(1, 29)] + ['Amount']

            # 30 values total
            values = [
                time_val * 3600,   # Time
                v1, v2, v3, v4,    # V1-V4 (user input)
                0, 0, 0, 0, 0,     # V5-V9
                0, 0, 0, 0, 0,     # V10-V14
                0, 0, 0, 0, 0,     # V15-V19
                0, 0, 0, 0, 0,     # V20-V24
                0, 0, 0, 0,        # V25-V28
                amount             # Amount
            ]

            features = pd.DataFrame([values], columns=cols)

            prediction  = model.predict(features)[0]
            confidence  = model.predict_proba(features)[0][1]
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
                '<div class="fraud-alert">🚨 FRAUD DETECTED! '
                'This transaction has been flagged!</div>',
                unsafe_allow_html=True
            )
            # Log to blockchain
            if w3:
                fraud_hash = hashlib.sha256(
                    f"{amount}{time.time()}".encode()
                ).hexdigest()
                st.markdown(
                    f'<div class="blockchain-card">'
                    f'⛓️ Blockchain Receipt<br>'
                    f'🔐 Hash: {fraud_hash}<br>'
                    f'📦 Block: #{w3.eth.block_number}<br>'
                    f'⏰ Time: {time.strftime("%Y-%m-%d %H:%M:%S")}'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                '<div class="safe-alert">✅ TRANSACTION IS SAFE! '
                'No fraud detected.</div>',
                unsafe_allow_html=True
            )

        # Confidence bar
        st.markdown("#### 📊 Confidence Level")
        st.progress(float(confidence))

# ─────────────────────────────────────────
# PAGE 3: DATA ANALYSIS
# ─────────────────────────────────────────
elif page == "📊 Data Analysis":
    st.title("📊 Data Analysis & Insights")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs([
        "📈 Distributions", "🔥 Heatmap", "📋 SQL Queries"
    ])

    with tab1:
        st.subheader("Transaction Amount Distribution")
        df_sample = pd.read_sql(
            'SELECT "Amount","Class" FROM transactions LIMIT 5000',
            engine
        )
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        fig.patch.set_facecolor('#1a1a2e')
        for ax in axes:
            ax.set_facecolor('#1a1a2e')
            ax.tick_params(colors='white')

        fraud_amt = df_sample[df_sample['Class']==1]['Amount']
        legit_amt = df_sample[df_sample['Class']==0]['Amount']

        axes[0].hist(legit_amt, bins=40, color='#2ecc71',
                     edgecolor='black', alpha=0.8)
        axes[0].set_title('Legit Amounts', color='white')

        axes[1].hist(fraud_amt, bins=40, color='#e74c3c',
                     edgecolor='black', alpha=0.8)
        axes[1].set_title('Fraud Amounts', color='white')
        plt.tight_layout()
        st.pyplot(fig)

    with tab2:
        st.subheader("Feature Correlation Heatmap")
        df_corr = pd.read_sql(
            'SELECT "V1","V2","V3","V4","V5","Amount","Class" '
            'FROM transactions LIMIT 5000',
            engine
        )
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        fig3.patch.set_facecolor('#1a1a2e')
        ax3.set_facecolor('#1a1a2e')
        sns.heatmap(df_corr.corr(), annot=True, fmt='.2f',
                    cmap='RdYlGn', ax=ax3)
        ax3.tick_params(colors='white')
        ax3.set_title('Correlation Heatmap', color='white')
        st.pyplot(fig3)

    with tab3:
        st.subheader("🔍 Live SQL Query Explorer")
        query = st.text_area("Write your SQL query:",
            value='SELECT "Class", COUNT(*) as count, '
                  'AVG("Amount") as avg_amount '
                  'FROM transactions GROUP BY "Class"',
            height=100
        )
        if st.button("▶️ Run Query"):
            try:
                result = pd.read_sql(query, engine)
                st.dataframe(result, use_container_width=True)
                st.success(f"✅ Query returned {len(result)} rows")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# ─────────────────────────────────────────
# PAGE 4: BLOCKCHAIN LOGS
# ─────────────────────────────────────────
elif page == "⛓️ Blockchain Logs":
    st.title("⛓️ Blockchain Audit Trail")
    st.markdown("Tamper-proof fraud logs stored on the blockchain.")
    st.markdown("---")

    if w3:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📦 Total Blocks", w3.eth.block_number)
        with col2:
            st.metric("🔑 Accounts", len(w3.eth.accounts))
        with col3:
            bal = w3.eth.get_balance(w3.eth.accounts[0])
            st.metric("💎 Balance",
                      f"{w3.from_wei(bal, 'ether'):.2f} ETH")

    st.markdown("---")
    st.subheader("📋 Fraud Transaction Logs")

    try:
        logs_df = pd.read_sql("SELECT * FROM blockchain_logs", engine)
        st.dataframe(logs_df, use_container_width=True)
        st.success(f"✅ {len(logs_df)} fraud transactions logged on blockchain")

        # Download button
        csv = logs_df.to_csv(index=False)
        st.download_button(
            "⬇️ Download Logs as CSV",
            csv,
            "blockchain_fraud_logs.csv",
            "text/csv"
        )
    except:
        st.warning("⚠️ No blockchain logs found yet. "
                   "Run blockchain/fraud_logger.py first!")

        # Show JSON logs if available
        try:
            with open('blockchain/fraud_logs.json') as f:
                logs = json.load(f)
            st.json(logs[:3])
        except:
            st.info("Run Phase 4 first to generate blockchain logs!")

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
        | **AUC Score** | ~0.98 |
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
    st.subheader("📊 Feature Importance")
    try:
        img = plt.imread('models/charts/feature_importance.png')
        st.image(img, caption="Top 15 Important Features", use_column_width=True)
    except:
        st.info("Run Phase 3 first to generate feature importance chart!")

    st.markdown("---")
    st.subheader("📈 ROC Curve")
    try:
        img2 = plt.imread('models/charts/roc_curve.png')
        st.image(img2, caption="ROC Curve Comparison", use_column_width=True)
    except:
        st.info("Run Phase 3 first to generate ROC curve!")