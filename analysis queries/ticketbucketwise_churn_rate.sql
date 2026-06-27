SELECT 
    CASE
        WHEN avg_monthly_tickets < 10  THEN '1. Low (0-9)'
        WHEN avg_monthly_tickets < 20  THEN '2. Medium (10-19)'
        WHEN avg_monthly_tickets < 30  THEN '3. High (20-29)'
        ELSE                                '4. Very High (30+)'
    END                                             AS ticket_bucket,
    COUNT(*)                                        AS total_customers,
    SUM(churn)                                      AS churned_customers,
    ROUND(SUM(churn) / COUNT(*) * 100, 2)          AS churn_rate_per
FROM (
    SELECT
        customer_id,
        MAX(churn)              AS churn,
        AVG(support_tickets)    AS avg_monthly_tickets
    FROM customer_churn
    GROUP BY customer_id
) AS customer_level
GROUP BY ticket_bucket
ORDER BY ticket_bucket;