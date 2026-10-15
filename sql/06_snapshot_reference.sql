/*
===============================================================================
PROJECT 01 — AI-Powered Marketing Decision & Content Automation System
===============================================================================

FILE:
06_snapshot_reference.sql

STAGE:
Stage 3 — Data Model & Power BI (frozen snapshot preparation)

PURPOSE:
Reference evidence for a frozen snapshot. Run at the SAME instant
(@snapshot_ts) as the exports in 05_snapshot_export.sql, its output is stored
in the snapshot manifest and later re-computed from the exported CSV files
as a double check.

SOURCE DATASET:
bigquery-public-data.thelook_ecommerce

FINANCIAL LOGIC:
Reuses the Stage 2 financial baseline (02_financial_validation.sql,
Section 6) unchanged:
- Recognized Revenue and COGS: Complete items only.
- COGS source: inventory_items.cost, joined on
  order_items.inventory_item_id = inventory_items.id (INNER JOIN, validated
  in Stage 2 with zero orphans).
- Processing / Shipped: pending. Returned: reversed. Cancelled: not recognized.

ADDITIONS (not in 02, Section 6):
- Row counts of the four exported tables at @snapshot_ts.
- complete_items: number of Complete order items.
- future_complete_items: Complete items whose delivery date is after the
  snapshot date. Same definition as 03_monthly_performance_analysis.sql
  (Section 1), but anchored to DATE(@snapshot_ts) instead of CURRENT_DATE()
  so the result is reproducible for this snapshot.

PARAMETERS:
@snapshot_ts (TIMESTAMP), supplied by scripts/export_snapshot.py. To run it
manually in the BigQuery console, replace @snapshot_ts with
TIMESTAMP('YYYY-MM-DD HH:MM:SS UTC').

IMPORTANT:
TheLook is a synthetic and dynamic public dataset.
Results describe this snapshot only. This query is read-only.
===============================================================================
*/

WITH oi AS (
    SELECT *
    FROM `bigquery-public-data.thelook_ecommerce.order_items`
        FOR SYSTEM_TIME AS OF @snapshot_ts
),

ii AS (
    SELECT *
    FROM `bigquery-public-data.thelook_ecommerce.inventory_items`
        FOR SYSTEM_TIME AS OF @snapshot_ts
),

row_counts AS (
    SELECT
        (SELECT COUNT(*) FROM oi) AS rows_order_items,
        (SELECT COUNT(*) FROM ii) AS rows_inventory_items,
        (SELECT COUNT(*)
            FROM `bigquery-public-data.thelook_ecommerce.products`
                FOR SYSTEM_TIME AS OF @snapshot_ts) AS rows_products,
        (SELECT COUNT(*)
            FROM `bigquery-public-data.thelook_ecommerce.users`
                FOR SYSTEM_TIME AS OF @snapshot_ts) AS rows_users
),

financials AS (
    SELECT
        COUNTIF(oi.status = 'Complete') AS complete_items,

        COUNTIF(
            oi.status = 'Complete'
            AND DATE(oi.delivered_at) > DATE(@snapshot_ts)
        ) AS future_complete_items,

        ROUND(SUM(
            CASE
                WHEN oi.status = 'Complete' THEN oi.sale_price
                ELSE 0
            END
        ), 2) AS recognized_revenue,

        ROUND(SUM(
            CASE
                WHEN oi.status = 'Complete' THEN ii.cost
                ELSE 0
            END
        ), 2) AS recognized_cogs,

        ROUND(SUM(
            CASE
                WHEN oi.status = 'Complete'
                    THEN oi.sale_price - ii.cost
                ELSE 0
            END
        ), 2) AS gross_profit,

        ROUND(
            SAFE_DIVIDE(
                SUM(CASE
                    WHEN oi.status = 'Complete'
                        THEN oi.sale_price - ii.cost
                    ELSE 0
                END),
                SUM(CASE
                    WHEN oi.status = 'Complete'
                        THEN oi.sale_price
                    ELSE 0
                END)
            ) * 100,
            2
        ) AS gross_margin_pct,

        ROUND(SUM(
            CASE
                WHEN oi.status IN ('Processing', 'Shipped')
                    THEN oi.sale_price
                ELSE 0
            END
        ), 2) AS pending_order_value,

        ROUND(SUM(
            CASE
                WHEN oi.status = 'Returned'
                    THEN oi.sale_price
                ELSE 0
            END
        ), 2) AS return_associated_value,

        ROUND(SUM(
            CASE
                WHEN oi.status = 'Cancelled'
                    THEN oi.sale_price
                ELSE 0
            END
        ), 2) AS cancelled_value

    FROM oi

    INNER JOIN ii
        ON oi.inventory_item_id = ii.id
)

SELECT
    FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', @snapshot_ts, 'UTC') AS snapshot_ts_utc,
    row_counts.*,
    financials.*
FROM row_counts
CROSS JOIN financials;
