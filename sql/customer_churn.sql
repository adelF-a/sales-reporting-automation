WITH MonthlyUsers AS (
    SELECT DISTINCT Month, Customer_ID
    FROM sales
), PreviousMonthBase AS (
    SELECT
        strftime('%Y-%m', date(Month || '-01', '+1 month')) AS Month,
        Customer_ID
    FROM MonthlyUsers
), CustomerMovement AS (
    SELECT
        p.Month,
        COUNT(DISTINCT p.Customer_ID) AS Previous_Users,
        COUNT(DISTINCT CASE WHEN c.Customer_ID IS NOT NULL THEN p.Customer_ID END)
            AS Retained_Users
    FROM PreviousMonthBase p
    INNER JOIN (SELECT DISTINCT Month FROM MonthlyUsers) available
      ON available.Month = p.Month
    LEFT JOIN MonthlyUsers c
      ON c.Month = p.Month AND c.Customer_ID = p.Customer_ID
    GROUP BY p.Month
), NewUsers AS (
    SELECT
        c.Month,
        COUNT(DISTINCT CASE WHEN p.Customer_ID IS NULL THEN c.Customer_ID END)
            AS New_Users
    FROM MonthlyUsers c
    LEFT JOIN PreviousMonthBase p
      ON p.Month = c.Month AND p.Customer_ID = c.Customer_ID
    GROUP BY c.Month
)
SELECT
    m.Month,
    m.Previous_Users,
    m.Retained_Users,
    m.Previous_Users - m.Retained_Users AS Churned_Users,
    COALESCE(n.New_Users, 0) AS New_Users,
    ROUND(100.0 * (m.Previous_Users - m.Retained_Users)
          / NULLIF(m.Previous_Users, 0), 2) AS Churn_Rate_Pct
FROM CustomerMovement m
LEFT JOIN NewUsers n USING (Month)
ORDER BY m.Month;
