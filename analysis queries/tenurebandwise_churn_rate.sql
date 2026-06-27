SELECT 
	CASE
		WHEN tenure_months BETWEEN 0 AND 6 THEN '1. 0-6 months'
        WHEN tenure_months BETWEEN 7 AND 12 THEN '2. 7-12 months'
        WHEN tenure_months BETWEEN 13 AND 24 THEN '3. 13-24 months'
        WHEN tenure_months BETWEEN 25 AND 60 THEN '4. 25-60 months'
        ELSE '5. 60+ months'
	END AS tenure_band,
    COUNT(*) AS total_customers,
    SUM(churn) AS churned_customers,
    ROUND(SUM(churn)/COUNT(*)*100, 2) AS churn_rate_per
FROM (
	SELECT
		customer_id,
        tenure_months,
        MAX(churn) AS churn
	FROM customer_churn
    GROUP BY customer_id, tenure_months
) AS customer_level
GROUP BY tenure_band
ORDER BY tenure_band;
