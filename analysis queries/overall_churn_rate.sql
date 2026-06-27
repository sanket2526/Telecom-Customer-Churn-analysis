SELECT 
	COUNT(*) AS total_customers,
    SUM(churn) AS churned_customers,
    ROUND(SUM(churn)/COUNT(*)*100, 2) AS churn_rate_per
FROM (
	SELECT 
		customer_id,
        MAX(churn) AS churn
	FROM customer_churn
    GROUP BY customer_id
) AS customer_level;

