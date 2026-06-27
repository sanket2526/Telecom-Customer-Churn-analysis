USE telecom_churn;

CREATE TABLE customer_churn (
	customer_id VARCHAR(20),
    age INT,
    gender VARCHAR(10),
    region VARCHAR(20),
    contract_type VARCHAR(20),
    monthly_charges DECIMAL(10,2),
	signup_date DATE,
    churn TINYINT,
    month INT,
    calls_per_month INT,
    data_usage_gb DECIMAL(10,2),
    support_tickets INT,
    tenure_months INT,
    tenure_band VARCHAR(20),
    revenue_at_risk DECIMAL(10,2)
);