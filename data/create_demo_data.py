# create_demo_data.py
# Creates a small demo dataset for online deployment

import pandas as pd
import numpy as np

print("Creating demo dataset...")

# Load original dataset
df = pd.read_csv("data/creditcard.csv")

# Take sample - 1000 legit + all 492 fraud
legit = df[df['Class'] == 0].sample(n=1000, random_state=42)
fraud = df[df['Class'] == 1]

demo = pd.concat([legit, fraud]).sample(frac=1, random_state=42)
demo.to_csv("data/demo_data.csv", index=False)

print(f"✅ Demo dataset created!")
print(f"📊 Total rows: {len(demo)}")
print(f"🚨 Fraud rows: {len(fraud)}")
print(f"✅ Legit rows: {len(legit)}")
