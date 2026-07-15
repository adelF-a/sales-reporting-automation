SELECT
    Region,
    Product,
    COUNT(*) AS Transactions,
    ROUND(SUM(Revenue), 2) AS Revenue,
    ROUND(SUM(Profit), 2) AS Profit,
    ROUND(100.0 * SUM(Profit) / NULLIF(SUM(Revenue), 0), 2)
        AS Profit_Margin_Pct
FROM sales
GROUP BY Region, Product
ORDER BY Revenue DESC;
