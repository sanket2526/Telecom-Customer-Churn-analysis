SELECT
	ROUND(SUM(monthly_charges), 2) AS total_monthly_revenue,
    ROUND(SUM(CASE WHEN churn = 1
			  THEN monthly_charges ELSE 0 END), 2) AS revenue_at_risk,
	ROUND(SUM(CASE WHEN churn = 1
              THEN monthly_charges ELSE 0 END)/SUM(monthly_charges)*100, 2) AS revenue_at_risk_per
FROM (
	SELECT
		customer_id,
        MAX(churn) AS churn,
        AVG(monthly_charges) AS monthly_charges
	FROM customer_churn
    GROUP BY customer_id
) AS customer_level;
