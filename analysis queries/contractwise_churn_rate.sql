SELECT
	contract_type,
    COUNT(*) AS total_customers,
    SUM(churn) As churned_customers,
    ROUND(SUM(churn)/COUNT(*)*100, 2) AS churn_rate_per
FROM (
	SELECT
		customer_id,
        contract_type,
        MAX(churn) AS churn
	FROM customer_churn
    GROUP BY customer_id, contract_type
) AS customer_level
GROUP BY contract_type
ORDER BY churn_rate_per DESC;
