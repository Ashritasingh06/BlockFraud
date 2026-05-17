# database_setup.py
# This file connects Python to PostgreSQL and loads our dataset

import pandas as pd
from sqlalchemy import create_engine, text

# ─────────────────────────────────────────
# STEP 1: Connect to PostgreSQL
# Replace 'admin123' with YOUR password
# ─────────────────────────────────────────
DB_PASSWORD = "admin123"  # ← change this
DB_NAME = "blockfraud"

engine = create_engine(
    f"postgresql://postgres:{DB_PASSWORD}@localhost:5432/{DB_NAME}"
)

print("✅ Connected to PostgreSQL successfully!")

# ─────────────────────────────────────────
# STEP 2: Load the CSV dataset
# ─────────────────────────────────────────
print("📂 Loading dataset...")
df = pd.read_csv("data/creditcard.csv")

print(f"✅ Dataset loaded! Shape: {df.shape}")
print(f"📊 Total transactions: {len(df)}")
print(f"🚨 Fraud cases: {df['Class'].sum()}")
print(f"✅ Legit cases: {len(df) - df['Class'].sum()}")

# ─────────────────────────────────────────
# STEP 3: Save dataset to SQL database
# ─────────────────────────────────────────
print("\n⏳ Uploading data to PostgreSQL (takes 1-2 mins)...")

df.to_sql(
    name="transactions",       # table name
    con=engine,
    if_exists="replace",       # replace if already exists
    index=False,
    chunksize=1000             # upload 1000 rows at a time
)

print("✅ Data uploaded to PostgreSQL successfully!")

# ─────────────────────────────────────────
# STEP 4: Verify data in SQL
# ─────────────────────────────────────────
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM transactions"))
    count = result.fetchone()[0]
    print(f"\n📦 Total rows in database: {count}")

    result2 = conn.execute(text(
        "SELECT COUNT(*) FROM transactions WHERE \"Class\" = 1"
    ))
    fraud_count = result2.fetchone()[0]
    print(f"🚨 Fraud rows in database: {fraud_count}")

print("\n🎉 Phase 1 Complete! Database is ready!")