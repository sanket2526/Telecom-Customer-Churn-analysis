SELECT
    contract_type,
    CASE
        WHEN tenure_months BETWEEN 0  AND 6  THEN '0-6 months'
        WHEN tenure_months BETWEEN 7  AND 12 THEN '7-12 months'
        WHEN tenure_months BETWEEN 13 AND 24 THEN '13-24 months'
        WHEN tenure_months BETWEEN 25 AND 60 THEN '25-60 months'
        ELSE                                      '60+ months'
    END                                             AS tenure_band,
    COUNT(*)                                        AS total_customers,
    SUM(churn)                                      AS churned_customers,
    ROUND(SUM(churn) / COUNT(*) * 100, 2)          AS churn_rate_per,
    ROUND(AVG(monthly_charges), 2)                  AS avg_monthly_charges,
    ROUND(SUM(CASE WHEN churn = 1 
          THEN monthly_charges ELSE 0 END), 2)      AS revenue_at_risk
FROM (
    SELECT
        customer_id,
        contract_type,
        tenure_months,
        MAX(churn)              AS churn,
        AVG(monthly_charges)    AS monthly_charges
    FROM customer_churn
    GROUP BY customer_id, contract_type, tenure_months
) AS customer_level
GROUP BY contract_type, tenure_band
HAVING total_customers >= 50
ORDER BY churn_rate_per DESC
LIMIT 10;
