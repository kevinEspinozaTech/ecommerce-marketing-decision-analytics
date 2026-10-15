/*
===============================================================================
PROJECT 01 — AI-Powered Marketing Decision & Content Automation System
===============================================================================

FILE:
05_snapshot_export.sql

STAGE:
Stage 3 — Data Model & Power BI (frozen snapshot preparation)

PURPOSE:
Extract faithful, unjoined copies of the four tables needed for the
order_item-grain star schema. Each query is exported to one CSV in data/raw/
by scripts/export_snapshot.py. Joins (e.g. order_items → inventory_items.cost)
are intentionally NOT done here; they are done later in Power Query.

SOURCE DATASET:
bigquery-public-data.thelook_ecommerce

EXPORTS:
1. order_items      — all 11 columns
2. inventory_items  — id, product_id, cost
3. products         — id, category, name, brand, retail_price, department
4. users            — id, age, gender, country, traffic_source, created_at

SNAPSHOT CONSISTENCY:
Every query reads the table as of the same instant @snapshot_ts
(BigQuery time travel: FOR SYSTEM_TIME AS OF), so all four extracts describe
one consistent state of the dataset. @snapshot_ts is a TIMESTAMP query
parameter supplied by the script. To run a block manually in the BigQuery
console, replace @snapshot_ts with TIMESTAMP('YYYY-MM-DD HH:MM:SS UTC').

FORMATTING:
Timestamps are exported as 'YYYY-MM-DD HH:MM:SS' in UTC, without offset.
Sub-second precision is dropped by this formatting.

DATA MINIMIZATION:
users excludes first_name, last_name, email, state, street_address,
postal_code, city, latitude, longitude, and user_geom.
products excludes cost (not the COGS source — inventory_items.cost is),
sku, and distribution_center_id.

IMPORTANT:
TheLook is a synthetic and dynamic public dataset.
Each export is a dated snapshot, not a permanent property of the dataset.
These queries are read-only; they do not modify the source data.

The '-- @export: <name>' marker lines are used by the export script to split
this file into one query per output file. Do not remove or rename them.
===============================================================================
*/


-- @export: order_items
-- =============================================================================
-- 1. ORDER ITEMS (fact source, grain = one row per order item)
-- =============================================================================

SELECT
    id,
    order_id,
    user_id,
    product_id,
    inventory_item_id,
    status,
    FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', created_at, 'UTC')   AS created_at,
    FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', shipped_at, 'UTC')   AS shipped_at,
    FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', delivered_at, 'UTC') AS delivered_at,
    FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', returned_at, 'UTC')  AS returned_at,
    sale_price
FROM `bigquery-public-data.thelook_ecommerce.order_items`
    FOR SYSTEM_TIME AS OF @snapshot_ts
ORDER BY id;


-- @export: inventory_items
-- =============================================================================
-- 2. INVENTORY ITEMS (COGS source: cost per physical unit)
-- =============================================================================

SELECT
    id,
    product_id,
    cost
FROM `bigquery-public-data.thelook_ecommerce.inventory_items`
    FOR SYSTEM_TIME AS OF @snapshot_ts
ORDER BY id;


-- @export: products
-- =============================================================================
-- 3. PRODUCTS (product dimension source)
-- =============================================================================

SELECT
    id,
    category,
    name,
    brand,
    retail_price,
    department
FROM `bigquery-public-data.thelook_ecommerce.products`
    FOR SYSTEM_TIME AS OF @snapshot_ts
ORDER BY id;


-- @export: users
-- =============================================================================
-- 4. USERS (customer dimension source, personal data excluded)
-- =============================================================================

SELECT
    id,
    age,
    gender,
    country,
    traffic_source,
    FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', created_at, 'UTC') AS created_at
FROM `bigquery-public-data.thelook_ecommerce.users`
    FOR SYSTEM_TIME AS OF @snapshot_ts
ORDER BY id;
