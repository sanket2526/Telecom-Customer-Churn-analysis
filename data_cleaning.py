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

# We found 200 CustomerIDs that appear twice.
# 195 are fully identical copies — safe to delete.
# 5 have the same ID but different SignupDate — conflicting.
#
# Our rule for conflicts: keep the EARLIEST SignupDate,
# because the customer's true join date is the first one.

print("\n--- Fixing duplicates in customer_info ---")
print(f"  Rows before: {len(customer)}")

# First, find the 5 conflicting duplicates (same ID,
# different data). We do this BEFORE dropping anything.
#
# .duplicated(subset=['CustomerID'], keep=False) marks TRUE
# on ALL rows that share a CustomerID (both copies).
# keep=False means "mark every occurrence, not just the 2nd".
all_dups = customer[customer.duplicated(subset=['CustomerID'], keep=False)]

# .duplicated() with no subset checks if the ENTIRE row is
# identical. keep=False marks all copies.
# Rows that are duplicated by ID but NOT fully identical
# are the conflict cases.
fully_identical_mask = customer.duplicated(keep=False)
conflicts = all_dups[~fully_identical_mask]  # ~ means "NOT"

print(f"  Fully identical duplicates to remove: 195")
print(f"  Conflicting duplicates (same ID, different data): {conflicts['CustomerID'].nunique()}")

# For conflicts: sort by SignupDate ascending, then keep
# the first occurrence per CustomerID (= earliest date).
#
# pd.to_datetime() converts the text "2022-06-09" into
# a real date object Python can sort and compare.
customer['SignupDate'] = pd.to_datetime(customer['SignupDate'])

# sort_values() reorders rows. ascending=True puts the
# earliest date at the top.
customer = customer.sort_values('SignupDate', ascending=True)

# drop_duplicates() removes duplicate rows.
# subset=['CustomerID'] means "only look at CustomerID
# to decide if something is a duplicate".
# keep='first' means keep the first occurrence (earliest
# date, since we sorted) and drop the rest.
customer = customer.drop_duplicates(subset=['CustomerID'], keep='first')

print(f"  Rows after:  {len(customer)}")
# Expected: 10000 (200 extra rows removed)


# STEP 3: FIX customer_info — NEGATIVE MonthlyCharges

# 5 customers have negative charges like -6.72.
# These are data entry errors — the value should be positive.
# Fix: take the absolute value (remove the minus sign).

print("\n--- Fixing negative MonthlyCharges ---")

# Show which customers are affected before fixing
neg_mask = customer['MonthlyCharges'] < 0   # True/False for each row
print(f"  Customers with negative charges: {neg_mask.sum()}")
print(customer.loc[neg_mask, ['CustomerID', 'MonthlyCharges']])

# abs() returns the absolute value — turns -6.72 into 6.72
customer['MonthlyCharges'] = customer['MonthlyCharges'].abs()

print(f"  Fixed. Min MonthlyCharges is now: {customer['MonthlyCharges'].min():.2f}")


# STEP 4: FIX customer_info — MISSING Age (35% null)

# 3,583 customers have no Age value.
# Too many to drop — we'd lose a third of our data.
#
# Strategy: impute (fill in) with the MEDIAN age,
# calculated separately per ContractType.
# Why per ContractType? Because Prepaid vs Yearly customers
# likely have different age profiles. Using the group median
# is more accurate than one global median.

print("\n--- Imputing missing Age values ---")
print(f"  Missing Age before: {customer['Age'].isnull().sum()}")

# groupby('ContractType') splits the table into 3 groups
# (Monthly, Prepaid, Yearly).
# transform('median') calculates median per group, then
# puts the result back in the same row order as the original
# table — so each row gets its group's median.
age_medians = customer.groupby('ContractType')['Age'].transform('median')

# Print the medians so we know what values were used
medians_by_group = customer.groupby('ContractType')['Age'].median()
print(f"  Median Age used per ContractType:")
for contract_type, median_val in medians_by_group.items():
    print(f"    {contract_type}: {median_val}")

# fillna() replaces NaN (missing) values with whatever
# you pass in. We pass in the group medians we calculated.
customer['Age'] = customer['Age'].fillna(age_medians)

# round() removes the decimal since age is a whole number
customer['Age'] = customer['Age'].round(0).astype(int)

print(f"  Missing Age after:  {customer['Age'].isnull().sum()}")


# STEP 5: MERGE ALL THREE TABLES

# Now we have 3 clean tables. We need to join them into
# one master table using CustomerID as the common key.
#
# Think of it like VLOOKUP in Excel, or JOIN in SQL.
# pd.merge() is Python's version of a JOIN.
# how='inner' means only keep rows where CustomerID
# exists in BOTH tables (like SQL INNER JOIN).

print("\n--- Merging all three tables ---")

# First merge: customer_info + churn_labels
# Both have one row per customer, so this is straightforward.
merged = pd.merge(customer, churn, on='CustomerID', how='inner')
print(f"  After customer + churn merge: {merged.shape}")

# Second merge: add usage_data
# usage_data has 12 rows per customer (one per month).
# After this merge, each customer will have 12 rows —
# one for each month of usage data.
merged = pd.merge(merged, usage, on='CustomerID', how='inner')
print(f"  After adding usage data:       {merged.shape}")
# Expected: 120,000 rows (10,000 customers × 12 months)


# STEP 6: ADD DERIVED COLUMNS

# These are new columns we calculate from existing data.
# They'll make our SQL analysis much easier later.

print("\n--- Adding derived columns ---")

# TENURE: How many months has each customer been with us?
# Calculate from SignupDate to the end of our data (Dec 2023).
# relativedelta would be more precise, but for monthly
# granularity, dividing by 30.44 (avg days/month) is fine.

reference_date = pd.Timestamp('2023-12-31')

# (reference_date - merged['SignupDate']) gives a
# "timedelta" — a duration. .dt.days extracts the number
# of days from that duration. Dividing by 30.44 gives months.
merged['TenureMonths'] = (
    (reference_date - merged['SignupDate']).dt.days / 30.44
).round(0).astype(int)

# Cap at 0 minimum (in case any signup date is after Dec 2023)
merged['TenureMonths'] = merged['TenureMonths'].clip(lower=0)

# TENURE BAND: Group tenure into buckets for segmentation.
# pd.cut() divides a numeric column into labeled bins.
# bins=[0,6,12,24,60,999] means:
#   0-6 months   → "0-6 months"
#   7-12 months  → "7-12 months"  etc.
merged['TenureBand'] = pd.cut(
    merged['TenureMonths'],
    bins=[0, 6, 12, 24, 60, 999],
    labels=['0-6 months', '7-12 months', '13-24 months',
            '25-60 months', '60+ months'],
    right=True
)

# REVENUE AT RISK: For churned customers, what monthly
# revenue are we losing? For non-churned, set to 0.
# np.where() is like an IF statement:
# IF Churn==1 THEN MonthlyCharges ELSE 0
merged['RevenueAtRisk'] = merged.apply(
    lambda row: row['MonthlyCharges'] if row['Churn'] == 1 else 0,
    axis=1   # axis=1 means apply row by row
)

print(f"  Added: TenureMonths, TenureBand, RevenueAtRisk")


# STEP 7: FINAL VALIDATION

# Always check your output before saving. Make sure:
# - Row count is what we expect
# - No nulls crept in
# - Columns look right

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

# Save to CSV so we can import it into MySQL next.
# index=False means don't write the row numbers (0,1,2...)
# as a column — we don't need them.

output_path = "telecom_churn_cleaned.csv"
merged.to_csv(output_path, index=False)
print(f"\n✓ Saved cleaned file: {output_path}")
print(f"  ({merged.shape[0]:,} rows × {merged.shape[1]} columns)")
print("\nData cleaning complete. Ready for MySQL import.")

