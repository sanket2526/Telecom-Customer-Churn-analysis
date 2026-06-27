SELECT 
	CASE
		WHEN avg_data_gb < 5 THEN '1. Low (<5 GB)'
        WHEN avg_data_gb < 10 THEN '2. Medium (5-9 GB)'
        WHEN avg_data_gb < 20 THEN '3. High (10-19 GB)'
        ELSE '4. Very High (20+ GB)'
	END AS data_usage_bucket,
    COUNT(*) AS total_customers,
    SUM(churn) AS churned_customers,
    ROUND(SUM(churn)/COUNT(*)*100, 2) AS churn_rate_per
FROM (
	SELECT
		customer_id,
        MAX(churn) AS churn,
        AVG(data_usage_gb) AS avg_data_gb
	FROM customer_churn
    GROUP BY customer_id
) AS customer_level
GROUP BY data_usage_bucket
ORDER BY data_usage_bucket;
