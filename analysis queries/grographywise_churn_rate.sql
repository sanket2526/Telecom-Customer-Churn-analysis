SELECT
	region,
    COUNT(*) AS total_customers,
    SUM(churn) AS churned_customers,
    ROUND(SUM(churn)/COUNT(*)*100, 2) AS churn_rate_per
FROM (
	SELECT 
		customer_id,
        region,
        MAX(churn) AS churn
	FROM customer_churn
    GROUP BY customer_id, region
) AS customer_level
GROUP BY region
ORDER BY churn_rate_per DESC;

