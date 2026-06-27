from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parent / "telecom-customer-churn-data-quality-challenge"

# STEP 1: LOAD THE RAW FILES

print("Loading raw files...")

# pd.read_csv() reads a CSV file and store it as a "DataFrame"

customer = pd.read_csv(DATA_DIR / "customer_info.csv")
usage = pd.read_csv(DATA_DIR / "usage_data.csv")
churn = pd.read_csv(DATA_DIR / "churn_labels.csv")

# .shape gives us (rows, columns)

print(f" customer_info : {customer.shape[0]} rows, {customer.shape[1]} columns")
print(f" usage_data : {usage.shape[0]} rows, {usage.shape[1]} columns")
print(f" churn_labels : {churn.shape[0]} rows, {churn.shape[1]} columns")


# STEP 2: FIX customer_info — DUPLICATE ROWS

# found 200 duplicate entries - 195 with same data, 5 with same ID but different SignupDate
# deleted 195 entries and in those 5 kept one with earliest SignupDate

print("\n--- Fixing duplicates in customer_info ---")
print(f"  Rows before: {len(customer)}")

all_dups = customer[customer.duplicated(subset=['CustomerID'], keep=False)]

fully_identical_mask = customer.duplicated(keep=False)
conflicts = all_dups[~fully_identical_mask]  # ~ means "NOT"

print(f"  Fully identical duplicates to remove: 195")
print(f"  Conflicting duplicates (same ID, different data): {conflicts['CustomerID'].nunique()}")

customer['SignupDate'] = pd.to_datetime(customer['SignupDate'])

customer = customer.sort_values('SignupDate', ascending=True)

# sorted in ascending order and dropped the others except first entry
customer = customer.drop_duplicates(subset=['CustomerID'], keep='first')

print(f"  Rows after:  {len(customer)}")

# STEP 3: FIX customer_info — NEGATIVE MonthlyCharges

# 5 customers have negative charges like -6.72.

print("\n--- Fixing negative MonthlyCharges ---")

neg_mask = customer['MonthlyCharges'] < 0   
print(f"  Customers with negative charges: {neg_mask.sum()}")
print(customer.loc[neg_mask, ['CustomerID', 'MonthlyCharges']])

# took absolute of those values
customer['MonthlyCharges'] = customer['MonthlyCharges'].abs()

print(f"  Fixed. Min MonthlyCharges is now: {customer['MonthlyCharges'].min():.2f}")


# STEP 4: FIX customer_info — MISSING Age (35% null)

# 3,583 customers have no Age value.
# Too many to drop — we'd lose a third of our data.
#
# Strategy: impute (fill in) with the MEDIAN age, calculated separately per ContractType. Because Prepaid vs Yearly customers
# likely have different age profiles. 

print("\n--- Imputing missing Age values ---")
print(f"  Missing Age before: {customer['Age'].isnull().sum()}")

age_medians = customer.groupby('ContractType')['Age'].transform('median')

medians_by_group = customer.groupby('ContractType')['Age'].median()
print(f"  Median Age used per ContractType:")
for contract_type, median_val in medians_by_group.items():
    print(f"    {contract_type}: {median_val}")

# replaced missing values with medians using fillna() 
customer['Age'] = customer['Age'].fillna(age_medians)

customer['Age'] = customer['Age'].round(0).astype(int)

print(f"  Missing Age after:  {customer['Age'].isnull().sum()}")


# STEP 5: MERGE ALL THREE TABLES

# Now we have 3 clean tables. Joined these tables to make one master table using CustomerID as the common key.

print("\n--- Merging all three tables ---")

# customer_info + churn_labels
merged = pd.merge(customer, churn, on='CustomerID', how='inner')
print(f"  After customer + churn merge: {merged.shape}")

# Second merge: add usage_data
merged = pd.merge(merged, usage, on='CustomerID', how='inner')
print(f"  After adding usage data:       {merged.shape}")
# Expected: 120,000 rows (10,000 customers × 12 months)


# STEP 6: ADD DERIVED COLUMNS

print("\n--- Adding derived columns ---")

# TENURE: How many months has each customer been with us?
# Calculate from SignupDate to the end of our data (Dec 2023).

reference_date = pd.Timestamp('2023-12-31')

# (reference_date - merged['SignupDate']) gives a
# "timedelta" — a duration. .dt.days extracts the number
# of days from that duration. Dividing by 30.44 gives months.
merged['TenureMonths'] = (
    (reference_date - merged['SignupDate']).dt.days / 30.44
).round(0).astype(int)

merged['TenureMonths'] = merged['TenureMonths'].clip(lower=0)

# TENURE BAND: Group tenure into buckets for segmentation.
merged['TenureBand'] = pd.cut(
    merged['TenureMonths'],
    bins=[0, 6, 12, 24, 60, 999],
    labels=['0-6 months', '7-12 months', '13-24 months',
            '25-60 months', '60+ months'],
    right=True
)

# REVENUE AT RISK: monthly revenue we are loosing due to churned customers.
merged['RevenueAtRisk'] = merged.apply(
    lambda row: row['MonthlyCharges'] if row['Churn'] == 1 else 0,
    axis=1   # axis=1 means apply row by row
)

print(f"  Added: TenureMonths, TenureBand, RevenueAtRisk")


# STEP 7: FINAL VALIDATION

print("\n--- Final validation ---")
print(f"  Final shape: {merged.shape}")
print(f"  Columns: {list(merged.columns)}")
print(f"\n  Null counts:")
print(merged.isnull().sum()[merged.isnull().sum() > 0])  # only show columns WITH nulls

print(f"\n  Churn rate: {merged['Churn'].mean()*100:.2f}%")
print(f"  Unique customers: {merged['CustomerID'].nunique()}")
print(f"  Month range: {merged['Month'].min()} → {merged['Month'].max()}")

print(f"\n  Sample of final data (3 rows):")
print(merged.head(3).to_string())


# STEP 8: SAVE CLEANED FILE

output_path = "telecom_churn_cleaned.csv"
merged.to_csv(output_path, index=False)
print(f"\n✓ Saved cleaned file: {output_path}")
print(f"  ({merged.shape[0]:,} rows × {merged.shape[1]} columns)")
print("\nData cleaning complete. Ready for MySQL import.")

