# Stripe Payment Monitoring System

Automated pipeline that catches failed Stripe payments in real-time, syncs daily data to BigQuery, and delivers a formatted email report — built with n8n, no custom backend required.

**Stack:** n8n · Stripe · Google BigQuery · Looker Studio · Slack · Gmail

---

## What it does

- **Real-time alerts** — Stripe webhook triggers an instant Slack + email notification on every failed payment, including customer name, amount, and failure reason
- **Daily BigQuery sync** — Runs at 00:05 every night, fetches the previous day's payments from Stripe and loads them into BigQuery
- **Email report** — After each sync, sends an HTML email with 4 KPIs and a top failure reasons breakdown

---

## Architecture

```
Stripe
  │
  ├── Webhook (payment_intent.payment_failed)
  │     └── n8n Workflow 1
  │           ├── Slack alert  →  #payments channel
  │           └── Gmail alert  →  inbox
  │
  └── REST API (daily pull)
        └── n8n Workflow 2  [runs at 00:05]
              ├── Delete previous day's rows
              ├── Fetch & insert into BigQuery
              └── Email report (KPIs + top failures)
                    └── Gmail

BigQuery  →  Looker Studio dashboard
```

---

## Workflows

### Workflow 1 — Real-time failure alerts
Triggered by a Stripe webhook on `payment_intent.payment_failed`. Extracts customer details, formats a message, and fires both a Slack notification and a Gmail alert simultaneously.

### Workflow 2 — Daily sync + report
Scheduled cron at 00:05. Fetches yesterday's payment intents from the Stripe API, transforms and inserts each one into BigQuery, then queries the table for daily KPIs and sends an HTML email report.

---

## Dashboard (Looker Studio)

Built on a BigQuery view (`weekly_health`) that deduplicates raw data and adds a `revenue_at_risk` calculated field.

| Chart | Type |
|---|---|
| Total payments / Failed / Failure rate / Revenue at risk | Scorecard ×4 |
| Daily payment volume | Line chart |
| Top failure reasons | Bar chart |
| Weekly trend | Table |

---

## Project Structure

```
stripe_failed_payments/
├── setup/
│   ├── bigquery_schema.sql       # Run once — creates the payments table
│   └── bigquery_view.sql         # Run after first data load — used by Looker Studio
├── scripts/
│   └── populate_test_data.py     # Seeds Stripe test mode with customers + payments
└── n8n/
    ├── workflow1_failure_alerts.json   # Real-time Slack + Gmail alerts
    └── workflow2_daily_sync.json       # Nightly BigQuery sync + email report
```

---

## Setup

### 1. BigQuery

1. Create a dataset named `stripe_data` in BigQuery
2. Open `setup/bigquery_schema.sql`, replace `YOUR_PROJECT_ID` with your GCP project ID, and run it
3. Run `setup/bigquery_view.sql` the same way (after you have data)

### 2. n8n Credentials

Create these four credentials in n8n **before** importing the workflows:

| Name (use exactly) | Type | Details |
|---|---|---|
| `Stripe API` | Header Auth | Name: `Authorization` / Value: `Bearer sk_test_YOUR_KEY` |
| `Slack API` | Slack API | Slack Bot OAuth token |
| `Gmail` | Gmail OAuth2 | Authenticate via Google |
| `Google BigQuery` | Google BigQuery OAuth2 | Authenticate via Google |

### 3. Import workflows

1. n8n → **Workflows** → **Import from file**
2. Import both JSONs from `n8n/`
3. In each workflow, open nodes with `REPLACE_WITH_...` placeholders and assign the credentials above
4. In Workflow 2, replace `YOUR_PROJECT_ID` in the BigQuery nodes
5. Set workflow timezone to your local timezone in **Settings**
6. **Activate** both workflows

### 4. Stripe webhook (Workflow 1)

1. Stripe Dashboard → Developers → Webhooks → **Add endpoint**
2. URL: copy the webhook URL from the `Webhook` node in Workflow 1
3. Event: `payment_intent.payment_failed`

### 5. Looker Studio

1. [lookerstudio.google.com](https://lookerstudio.google.com) → New report → BigQuery
2. Connect to `YOUR_PROJECT_ID` → `stripe_data` → `weekly_health`
3. Build the 4 charts listed in the Dashboard section above

### 6. Seed test data (optional)

```bash
pip install stripe
STRIPE_SECRET_KEY=sk_test_YOUR_KEY python scripts/populate_test_data.py
```

---

## Key technical decisions

**No deduplication node** — the raw table is append-only. Both the BigQuery stats queries and the Looker Studio view use `ROW_NUMBER() OVER (PARTITION BY payment_id)` to deduplicate on read, avoiding BigQuery's streaming buffer restrictions entirely.

**Timezone-aware date logic** — date range calculations use `$now` (Luxon, respects workflow timezone) and BigQuery queries use `CURRENT_DATE('your/timezone')` to ensure "yesterday" is always correct regardless of server UTC offset.

**Single workflow for sync + report** — instead of a separate reporting workflow, the email chain is appended directly after the loop's done output via a `Trigger Once` code node that collapses N items to 1 before the stats queries run.
