-- Replace YOUR_PROJECT with your GCP project ID
-- Run this once in BigQuery console before activating either n8n workflow

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.stripe_data_2.payments` (
  payment_id      STRING NOT NULL,
  customer_id     STRING,
  customer_name   STRING,
  customer_email  STRING,
  amount          FLOAT64,
  currency        STRING,
  status          STRING,
  failure_reason  STRING,
  failure_code    STRING,
  created_at      TIMESTAMP,
  synced_at       TIMESTAMP
);
