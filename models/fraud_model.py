# fraud_model.py
# Machine Learning Model for Fraud Detection

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score, roc_curve)
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
import pickle
import os

# ─────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────
DB_PASSWORD = "admin123"  # ← change to your password
engine = create_engine(
    f"postgresql://postgres:{DB_PASSWORD}@localhost:5432/blockfraud"
)

os.makedirs("models/charts", exist_ok=True)
os.makedirs("models/saved", exist_ok=True)

print("📂 Loading data from PostgreSQL...")
df = pd.read_sql("SELECT * FROM transactions", engine)
print(f"✅ Loaded {len(df)} rows!\n")

# ─────────────────────────────────────────
# STEP 1: Prepare Data
# ─────────────────────────────────────────
print("⚙️  Preparing data...")

# Drop helper column if exists
if 'Type' in df.columns:
    df = df.drop('Type', axis=1)

# Features and Target
X = df.drop('Class', axis=1)
y = df['Class']

# Scale Amount and Time
scaler = StandardScaler()
X['Amount'] = scaler.fit_transform(X[['Amount']])
X['Time']   = scaler.fit_transform(X[['Time']])

# Handle class imbalance - undersample legit to balance
fraud = df[df['Class'] == 1]
legit = df[df['Class'] == 0].sample(n=len(fraud)*10,
                                     random_state=42)
balanced = pd.concat([fraud, legit])

X_bal = balanced.drop('Class', axis=1)
if 'Type' in X_bal.columns:
    X_bal = X_bal.drop('Type', axis=1)
y_bal = balanced['Class']

print(f"✅ Balanced dataset: {len(fraud)} fraud | {len(legit)} legit\n")

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X_bal, y_bal, test_size=0.2, random_state=42, stratify=y_bal
)
print(f"📊 Train size: {len(X_train)} | Test size: {len(X_test)}\n")

# ─────────────────────────────────────────
# STEP 2: Train Logistic Regression (Baseline)
# ─────────────────────────────────────────
print("🤖 Training Logistic Regression (baseline)...")
lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train, y_train)
lr_preds = lr.predict(X_test)
lr_auc   = roc_auc_score(y_test, lr.predict_proba(X_test)[:,1])
print(f"✅ Logistic Regression AUC: {lr_auc:.4f}\n")

# ─────────────────────────────────────────
# STEP 3: Train XGBoost (Main Model)
# ─────────────────────────────────────────
print("🚀 Training XGBoost model (this is our main model)...")
xgb = XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    use_label_encoder=False,
    eval_metric='logloss',
    random_state=42
)
xgb.fit(X_train, y_train)
xgb_preds = xgb.predict(X_test)
xgb_auc   = roc_auc_score(y_test, xgb.predict_proba(X_test)[:,1])
print(f"✅ XGBoost AUC: {xgb_auc:.4f}\n")

# ─────────────────────────────────────────
# STEP 4: Print Results
# ─────────────────────────────────────────
print("=" * 55)
print("📋 XGBoost Classification Report")
print("=" * 55)
print(classification_report(y_test, xgb_preds,
      target_names=['Legit', 'Fraud']))

# ─────────────────────────────────────────
# CHART 1: Confusion Matrix
# ─────────────────────────────────────────
print("📊 Creating Confusion Matrix chart...")
cm = confusion_matrix(y_test, xgb_preds)

plt.figure(figsize=(7, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Reds',
            xticklabels=['Legit','Fraud'],
            yticklabels=['Legit','Fraud'],
            linewidths=1)
plt.title('XGBoost Confusion Matrix', fontsize=15, fontweight='bold')
plt.ylabel('Actual', fontsize=12)
plt.xlabel('Predicted', fontsize=12)
plt.tight_layout()
plt.savefig('models/charts/confusion_matrix.png', dpi=150)
plt.show()
print("✅ Confusion Matrix saved!\n")

# ─────────────────────────────────────────
# CHART 2: ROC Curve
# ─────────────────────────────────────────
print("📊 Creating ROC Curve chart...")

fpr_lr,  tpr_lr,  _ = roc_curve(y_test, lr.predict_proba(X_test)[:,1])
fpr_xgb, tpr_xgb, _ = roc_curve(y_test, xgb.predict_proba(X_test)[:,1])

plt.figure(figsize=(8, 6))
plt.plot(fpr_lr,  tpr_lr,  label=f'Logistic Regression (AUC={lr_auc:.3f})',
         color='#3498db', linewidth=2)
plt.plot(fpr_xgb, tpr_xgb, label=f'XGBoost (AUC={xgb_auc:.3f})',
         color='#e74c3c', linewidth=2)
plt.plot([0,1],[0,1], 'k--', label='Random Classifier')
plt.title('ROC Curve Comparison', fontsize=15, fontweight='bold')
plt.xlabel('False Positive Rate', fontsize=12)
plt.ylabel('True Positive Rate', fontsize=12)
plt.legend(fontsize=11)
plt.tight_layout()
plt.savefig('models/charts/roc_curve.png', dpi=150)
plt.show()
print("✅ ROC Curve saved!\n")

# ─────────────────────────────────────────
# CHART 3: Feature Importance
# ─────────────────────────────────────────
print("📊 Creating Feature Importance chart...")

importance = pd.Series(xgb.feature_importances_,
                        index=X_train.columns)
top15 = importance.nlargest(15).sort_values()

plt.figure(figsize=(9, 7))
bars = plt.barh(top15.index, top15.values,
                color='#e74c3c', edgecolor='black', alpha=0.85)
plt.title('Top 15 Important Features (XGBoost)',
          fontsize=15, fontweight='bold')
plt.xlabel('Feature Importance Score', fontsize=12)
plt.tight_layout()
plt.savefig('models/charts/feature_importance.png', dpi=150)
plt.show()
print("✅ Feature Importance saved!\n")

# ─────────────────────────────────────────
# STEP 5: Save the Model
# ─────────────────────────────────────────
print("💾 Saving model to disk...")

with open('models/saved/xgb_model.pkl', 'wb') as f:
    pickle.dump(xgb, f)

with open('models/saved/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

print("✅ Model saved as models/saved/xgb_model.pkl")
print("✅ Scaler saved as models/saved/scaler.pkl\n")

print("=" * 55)
print(f"🎉 Phase 3 Complete!")
print(f"🏆 XGBoost AUC Score: {xgb_auc:.4f}")
print(f"🤖 Model saved and ready for dashboard!")
print("=" * 55)