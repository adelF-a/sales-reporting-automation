WITH MonthlyStats AS (
    SELECT
        Month,
        COUNT(*) AS Transactions,
        COUNT(DISTINCT Customer_ID) AS Active_Customers,
        ROUND(SUM(Revenue), 2) AS Revenue,
        ROUND(SUM(Cost), 2) AS Cost,
        ROUND(SUM(Profit), 2) AS Profit
    FROM sales
    GROUP BY Month
), WithPrevious AS (
    SELECT *, LAG(Revenue) OVER (ORDER BY Month) AS Previous_Month_Revenue
    FROM MonthlyStats
)
SELECT
    Month,
    Transactions,
    Active_Customers,
    Revenue,
    Cost,
    Profit,
    ROUND(100.0 * Profit / NULLIF(Revenue, 0), 2) AS Profit_Margin_Pct,
    ROUND(100.0 * (Revenue - Previous_Month_Revenue)
          / NULLIF(Previous_Month_Revenue, 0), 2) AS Revenue_Growth_Pct
FROM WithPrevious
ORDER BY Month;
