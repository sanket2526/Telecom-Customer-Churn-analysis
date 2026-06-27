SELECT 
	customer_id,
    age,
    gender,
    region,
    contract_type,
    tenure_months,
    monthly_charges,
    AVG(support_tickets) AS avg_monthly_tickets,
    AVG(data_usage_gb) AS avg_data_usage,
    churn
FROM customer_churn
GROUP BY 
	customer_id, age, gender, region, contract_type,
    tenure_months, monthly_charges, churn
HAVING 
	churn = 0								-- not yet churned (still saveable)
    AND monthly_charges > 60				-- high value customers
    AND tenure_months BETWEEN 7 AND 24		-- in the risky tenure window
    AND AVG(support_tickets) > 20 			-- showing frustration signals
ORDER BY monthly_charges DESC
LIMIT 20;
