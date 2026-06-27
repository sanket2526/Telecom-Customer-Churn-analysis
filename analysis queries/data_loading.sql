
LOAD DATA LOCAL INFILE 'D:/analytics projects/telecom churn/telecom_churn_cleaned.csv'
INTO TABLE customer_churn
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS 
(CustomerID, Age, Gender, Region, ContractType, MonthlyCharges, SignupDate, Churn, Month, CallsPerMonth, DataUsageGB, SupportTickets, TenureMonths, TenureBand, RevenueAtRisk);
