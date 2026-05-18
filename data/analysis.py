# analysis.py
# Exploratory Data Analysis (EDA) for BlockFraud Project

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import os

# ─────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────
DB_PASSWORD = "admin123"  # ← change to your password
DB_NAME = "blockfraud"

engine = create_engine(
    f"postgresql://postgres:{DB_PASSWORD}@localhost:5432/{DB_NAME}"
)

# Create folder to save charts
os.makedirs("data/charts", exist_ok=True)

print("📂 Loading data from PostgreSQL...")
df = pd.read_sql("SELECT * FROM transactions", engine)
print(f"✅ Loaded {len(df)} rows!\n")

# Set style for all charts
sns.set_theme(style="darkgrid")
plt.rcParams['figure.figsize'] = (10, 6)

# ─────────────────────────────────────────
# CHART 1: Fraud vs Legit Transaction Count
# ─────────────────────────────────────────
print("📊 Creating Chart 1: Fraud vs Legit...")

plt.figure(figsize=(8, 5))
colors = ['#2ecc71', '#e74c3c']
labels = ['Legit (0)', 'Fraud (1)']
counts = df['Class'].value_counts()

bars = plt.bar(labels, counts.values, color=colors, edgecolor='black', width=0.4)

for bar, count in zip(bars, counts.values):
    plt.text(bar.get_x() + bar.get_width()/2,
             bar.get_height() + 1000,
             f'{count:,}', ha='center', fontsize=12, fontweight='bold')

plt.title('Fraud vs Legitimate Transactions', fontsize=16, fontweight='bold')
plt.ylabel('Number of Transactions', fontsize=12)
plt.xlabel('Transaction Type', fontsize=12)
plt.tight_layout()
plt.savefig('data/charts/chart1_fraud_vs_legit.png', dpi=150)
plt.show()
print("✅ Chart 1 saved!\n")

# ─────────────────────────────────────────
# CHART 2: Transaction Amount Distribution
# ─────────────────────────────────────────
print("📊 Creating Chart 2: Amount Distribution...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

fraud = df[df['Class'] == 1]['Amount']
legit = df[df['Class'] == 0]['Amount']

axes[0].hist(legit, bins=50, color='#2ecc71', edgecolor='black', alpha=0.7)
axes[0].set_title('Legit Transaction Amounts', fontsize=13, fontweight='bold')
axes[0].set_xlabel('Amount ($)')
axes[0].set_ylabel('Frequency')

axes[1].hist(fraud, bins=50, color='#e74c3c', edgecolor='black', alpha=0.7)
axes[1].set_title('Fraud Transaction Amounts', fontsize=13, fontweight='bold')
axes[1].set_xlabel('Amount ($)')
axes[1].set_ylabel('Frequency')

plt.suptitle('Transaction Amount Distribution', fontsize=15, fontweight='bold')
plt.tight_layout()
plt.savefig('data/charts/chart2_amount_distribution.png', dpi=150)
plt.show()
print("✅ Chart 2 saved!\n")

# ─────────────────────────────────────────
# CHART 3: Fraud Amount Box Plot
# ─────────────────────────────────────────
print("📊 Creating Chart 3: Box Plot...")

plt.figure(figsize=(8, 6))
df['Type'] = df['Class'].map({0: 'Legit', 1: 'Fraud'})
sns.boxplot(x='Type', y='Amount', data=df,
            palette={'Legit': '#2ecc71', 'Fraud': '#e74c3c'})
plt.title('Transaction Amount by Type (Box Plot)', fontsize=15, fontweight='bold')
plt.xlabel('Transaction Type', fontsize=12)
plt.ylabel('Amount ($)', fontsize=12)
plt.tight_layout()
plt.savefig('data/charts/chart3_boxplot.png', dpi=150)
plt.show()
print("✅ Chart 3 saved!\n")

# ─────────────────────────────────────────
# CHART 4: Correlation Heatmap
# ─────────────────────────────────────────
print("📊 Creating Chart 4: Correlation Heatmap...")

plt.figure(figsize=(16, 10))
cols = ['V1','V2','V3','V4','V5','Amount','Class']
corr = df[cols].corr()

sns.heatmap(corr, annot=True, fmt=".2f", cmap='RdYlGn',
            linewidths=0.5, square=True, cbar_kws={"shrink": 0.8})
plt.title('Feature Correlation Heatmap', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('data/charts/chart4_heatmap.png', dpi=150)
plt.show()
print("✅ Chart 4 saved!\n")

# ─────────────────────────────────────────
# CHART 5: Fraud Over Time
# ─────────────────────────────────────────
print("📊 Creating Chart 5: Fraud Over Time...")

plt.figure(figsize=(12, 5))
fraud_time = df[df['Class'] == 1]['Time'] / 3600
legit_time = df[df['Class'] == 0]['Time'] / 3600

plt.hist(legit_time, bins=48, alpha=0.6, color='#2ecc71',
         label='Legit', edgecolor='black')
plt.hist(fraud_time, bins=48, alpha=0.8, color='#e74c3c',
         label='Fraud', edgecolor='black')

plt.title('Transaction Frequency Over Time', fontsize=15, fontweight='bold')
plt.xlabel('Hours Since First Transaction', fontsize=12)
plt.ylabel('Number of Transactions', fontsize=12)
plt.legend(fontsize=12)
plt.tight_layout()
plt.savefig('data/charts/chart5_fraud_over_time.png', dpi=150)
plt.show()
print("✅ Chart 5 saved!\n")

# ─────────────────────────────────────────
# SUMMARY STATS FROM SQL
# ─────────────────────────────────────────
print("=" * 50)
print("📋 SUMMARY STATISTICS FROM DATABASE")
print("=" * 50)

from sqlalchemy import text
with engine.connect() as conn:
    # Average fraud amount
    r1 = conn.execute(text(
        'SELECT AVG("Amount") FROM transactions WHERE "Class" = 1'
    ))
    print(f"💰 Avg Fraud Amount:  ${r1.fetchone()[0]:.2f}")

    # Average legit amount
    r2 = conn.execute(text(
        'SELECT AVG("Amount") FROM transactions WHERE "Class" = 0'
    ))
    print(f"💰 Avg Legit Amount:  ${r2.fetchone()[0]:.2f}")

    # Max fraud amount
    r3 = conn.execute(text(
        'SELECT MAX("Amount") FROM transactions WHERE "Class" = 1'
    ))
    print(f"📈 Max Fraud Amount:  ${r3.fetchone()[0]:.2f}")

    # Fraud percentage
    r4 = conn.execute(text(
        'SELECT ROUND(100.0 * SUM("Class") / COUNT(*), 4) FROM transactions'
    ))
    print(f"🚨 Fraud Percentage:  {r4.fetchone()[0]}%")

print("=" * 50)
print("\n🎉 Phase 2 Complete! All 5 charts saved in data/charts/")