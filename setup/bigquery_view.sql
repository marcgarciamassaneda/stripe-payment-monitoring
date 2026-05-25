-- Replace YOUR_PROJECT_ID with your GCP project ID
-- Run after the payments table has rows (after daily sync or test data load)

CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.stripe_data_2.weekly_health` AS
WITH base AS (
  SELECT
    DATE(created_at)                             AS payment_date,
    DATE_TRUNC(DATE(created_at), WEEK(MONDAY))   AS week_start,
    status,
    amount,
    currency,
    failure_reason,
    failure_code,
    customer_name
  FROM `YOUR_PROJECT_ID.stripe_data_2.payments`
  WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
)
SELECT
  week_start,
  payment_date,
  status,
  amount,
  currency,
  failure_reason,
  failure_code,
  customer_name,
  CASE WHEN status != 'succeeded' THEN amount ELSE 0 END AS revenue_at_risk
FROM base;
