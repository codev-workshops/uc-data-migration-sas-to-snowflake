import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import random
import uuid
from calendar import monthrange

# -----------------------------
# Load first 1000 customer rows
# -----------------------------
customers = pd.read_csv("../sample_data/customers.csv").head(1000)

# -----------------------------
# Generate synthetic CUST_ACCOUNTS
# -----------------------------
account_types = ["SAVINGS", "CHECKING", "CREDIT"]

cust_accounts_records = []
for _, row in customers.iterrows():
    num_accounts = random.randint(1, 3)
    for _ in range(num_accounts):
        account_id = str(uuid.uuid4())[:8]
        account_type = random.choice(account_types)
        is_active = random.choice(["ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE","ACTIVE","ACTIVE","INACTIVE"])
        start_date = datetime.now() - timedelta(days=random.randint(30, 2000))
        end_date = None if is_active == "ACTIVE" else start_date + timedelta(days=random.randint(100, 1000))
        cust_accounts_records.append({
            "customer_id": row["customer_id"],
            "account_id": account_id,
            "account_type": account_type,
            "is_active": is_active,
            "start_date": start_date.date(),
            "end_date": end_date.date() if end_date else None
        })

cust_accounts = pd.DataFrame(cust_accounts_records)

# -----------------------------
# Generate synthetic DAILY_BALANCE (July + August)
# -----------------------------
def simulate_month_balances(customer_id, account_id, year, month):
    days = monthrange(year, month)[1]
    balances = []
    # start with an initial balance
    balance = random.uniform(500.0, 5000.0)
    for day in range(1, days+1):
        # simulate credit/debit transactions
        net_change = random.uniform(-500, 500)  # could be negative (debit) or positive (credit)
        balance = max(0, balance + net_change)  # no negative balances
        balances.append({
            "customer_id": customer_id,
            "account_id": account_id,
            "date": date(year, month, day),
            "end_of_day_balance": round(balance, 2)
        })
    return balances

daily_balance_records = []
for _, acc in cust_accounts.iterrows():
    daily_balance_records.extend(simulate_month_balances(acc["customer_id"], acc["account_id"], 2025, 7))
    daily_balance_records.extend(simulate_month_balances(acc["customer_id"], acc["account_id"], 2025, 8))

daily_balance = pd.DataFrame(daily_balance_records)

# -----------------------------
# Compute monthly averages for July and August
# -----------------------------
daily_balance['month'] = pd.to_datetime(daily_balance['date']).dt.to_period('M')

avg_balances = daily_balance.groupby(['customer_id', 'account_id', 'month'])['end_of_day_balance'].mean().reset_index()
avg_balances.rename(columns={'end_of_day_balance': 'average_daily_balance'}, inplace=True)

# merge back if you want them as columns in daily_balance too (optional)
# daily_balance = daily_balance.merge(avg_balances, on=['customer_id','account_id','month'], how='left')

# -----------------------------
# MONTHLY_AMB only for July, using July's daily balances
# -----------------------------
july_daily = daily_balance[daily_balance['month'] == '2025-07']
monthly_amb_records = (
    july_daily.groupby(['customer_id','account_id'])['end_of_day_balance']
    .mean()
    .reset_index()
)

monthly_amb_records['reporting_month_yyyymm'] = '202507'
monthly_amb_records['average_monthly_balance'] = monthly_amb_records['end_of_day_balance'].round(2)
monthly_amb_records['date_computed'] = datetime.now().date()
monthly_amb = monthly_amb_records[['customer_id','account_id','reporting_month_yyyymm','average_monthly_balance','date_computed']]

# -----------------------------
# Save all to CSVs
# -----------------------------
cust_accounts.to_csv("../sample_data/cust_accounts.csv", index=False)
daily_balance.to_csv("../sample_data/daily_balance.csv", index=False)
monthly_amb.to_csv("../sample_data/monthly_amb.csv", index=False)

print("Synthetic data created for CUST_ACCOUNTS, DAILY_BALANCE (Jul+Aug) and MONTHLY_AMB (Jul).")
