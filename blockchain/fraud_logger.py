# fraud_logger.py
# Blockchain logger for fraud transactions

from web3 import Web3
import hashlib
import json
import time
import pickle
import pandas as pd
from sqlalchemy import create_engine, text

# ─────────────────────────────────────────
# SETUP DATABASE
# ─────────────────────────────────────────
DB_PASSWORD = "admin123"  # ← change to your password
engine = create_engine(
    f"postgresql://postgres:{DB_PASSWORD}@localhost:5432/blockfraud"
)

# ─────────────────────────────────────────
# STEP 1: Connect to Ganache Blockchain
# ─────────────────────────────────────────
print("⛓️  Connecting to Blockchain...")

GANACHE_URL = "http://127.0.0.1:7545"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

if w3.is_connected():
    print("✅ Connected to Ganache Blockchain!")
    print(f"📦 Total blocks: {w3.eth.block_number}")
    print(f"🔑 Accounts available: {len(w3.eth.accounts)}\n")
else:
    print("❌ Connection failed! Make sure Ganache is running!")
    exit()

# Use first Ganache account as sender
account = w3.eth.accounts[0]
print(f"👛 Using account: {account}\n")

# ─────────────────────────────────────────
# STEP 2: Load ML Model
# ─────────────────────────────────────────
print("🤖 Loading ML Model...")
with open('models/saved/xgb_model.pkl', 'rb') as f:
    model = pickle.load(f)
print("✅ Model loaded!\n")

# ─────────────────────────────────────────
# STEP 3: Create Blockchain Logger Class
# ─────────────────────────────────────────
class FraudBlockchainLogger:
    def __init__(self, web3_instance, account):
        self.w3  = web3_instance
        self.account = account
        self.logged_transactions = []

    def create_fraud_hash(self, transaction_data, prediction):
        """Create a unique hash for each fraud transaction"""
        data_string = json.dumps({
            'amount':     float(transaction_data.get('Amount', 0)),
            'prediction': int(prediction),
            'timestamp':  time.time()
        }, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()

    def log_to_blockchain(self, transaction_data, prediction, confidence):
        """Log a fraud transaction to the blockchain"""
        fraud_hash = self.create_fraud_hash(transaction_data, prediction)

        # Create blockchain transaction
        tx = {
            'from':     self.account,
            'to':       self.w3.eth.accounts[1],  # receiver account
            'value':    self.w3.to_wei(0.001, 'ether'),
            'gas':      100000,
            'gasPrice': self.w3.to_wei('20', 'gwei'),
            'nonce':    self.w3.eth.get_transaction_count(self.account),
        
        }

        # Send transaction to blockchain
        tx_hash = self.w3.eth.send_transaction(tx)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        log_entry = {
            'tx_hash':     tx_hash.hex(),
            'fraud_hash':  fraud_hash,
            'amount':      float(transaction_data.get('Amount', 0)),
            'confidence':  float(confidence),
            'block_number':receipt['blockNumber'],
            'status':      'CONFIRMED' if receipt['status'] == 1 else 'FAILED',
            'timestamp':   time.strftime('%Y-%m-%d %H:%M:%S')
        }

        self.logged_transactions.append(log_entry)
        return log_entry

# ─────────────────────────────────────────
# STEP 4: Run Fraud Detection + Log to Blockchain
# ─────────────────────────────────────────
print("📂 Loading sample transactions from database...")

df = pd.read_sql(
    'SELECT * FROM transactions WHERE "Class" = 1 LIMIT 10',
    engine
)
print(f"✅ Loaded {len(df)} fraud transactions to test\n")

logger = FraudBlockchainLogger(w3, account)

print("🔍 Detecting fraud and logging to blockchain...\n")
print("=" * 65)

for i, row in df.iterrows():
    features = row.drop(['Class']).to_frame().T
    if 'Type' in features.columns:
        features = features.drop('Type', axis=1)

    # Get prediction and confidence
    prediction  = model.predict(features)[0]
    confidence  = model.predict_proba(features)[0][1]

    if prediction == 1:  # Fraud detected!
        log = logger.log_to_blockchain(row.to_dict(), prediction, confidence)

        print(f"🚨 FRAUD DETECTED!")
        print(f"   💰 Amount:      ${row['Amount']:.2f}")
        print(f"   📊 Confidence:  {confidence*100:.1f}%")
        print(f"   ⛓️  Block:       #{log['block_number']}")
        print(f"   🔐 TX Hash:     {log['tx_hash'][:30]}...")
        print(f"   ✅ Status:      {log['status']}")
        print("-" * 65)

# ─────────────────────────────────────────
# STEP 5: Save Blockchain Logs to SQL
# ─────────────────────────────────────────
print("\n💾 Saving blockchain logs to database...")

logs_df = pd.DataFrame(logger.logged_transactions)
logs_df.to_sql(
    'blockchain_logs',
    engine,
    if_exists='replace',
    index=False
)
print("✅ Blockchain logs saved to PostgreSQL!\n")

# ─────────────────────────────────────────
# STEP 6: Save logs to JSON file
# ─────────────────────────────────────────
with open('blockchain/fraud_logs.json', 'w') as f:
    json.dump(logger.logged_transactions, f, indent=4)

print("✅ Logs saved to blockchain/fraud_logs.json\n")

# ─────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────
print("=" * 65)
print(f"🎉 Phase 4 Complete!")
print(f"⛓️  Total blocks on chain: {w3.eth.block_number}")
print(f"🚨 Fraud transactions logged: {len(logger.logged_transactions)}")
print(f"✅ All logs saved to database + JSON file!")
print("=" * 65)