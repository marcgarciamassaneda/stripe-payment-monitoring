"""
Seed Stripe test mode with realistic customers and payment data.
Run multiple times (ideally on different days) to populate the dashboard.

Install: pip install stripe
Usage:   STRIPE_SECRET_KEY=sk_test_... python populate_test_data.py
"""

import os
import random
import time
import stripe

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_YOUR_KEY_HERE")

FAIL_CARDS = {
    "card_declined":       "tok_chargeDeclined",
    "insufficient_funds":  "tok_chargeDeclinedInsufficientFunds",
    "expired_card":        "tok_chargeDeclinedExpiredCard",
}

CUSTOMERS = [
    {"name": "Alice Johnson",  "email": "alice@example.com"},
    {"name": "Bob Martinez",   "email": "bob@example.com"},
    {"name": "Carol White",    "email": "carol@example.com"},
    {"name": "David Lee",      "email": "david@example.com"},
    {"name": "Eva Rossi",      "email": "eva@example.com"},
    {"name": "Frank Nguyen",   "email": "frank@example.com"},
]

AMOUNTS = [1499, 2999, 4999, 9900, 14900, 24900, 49900]


def create_successful_payment(customer_id: str) -> None:
    try:
        stripe.PaymentIntent.create(
            amount=random.choice(AMOUNTS),
            currency="usd",
            customer=customer_id,
            payment_method="pm_card_visa",
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
        )
        print(f"  ✓ succeeded")
    except stripe.error.CardError as e:
        print(f"  ✗ unexpected card error: {e.user_message}")


def create_failed_payment(customer_id: str) -> None:
    reason, token = random.choice(list(FAIL_CARDS.items()))
    try:
        stripe.PaymentIntent.create(
            amount=random.choice(AMOUNTS),
            currency="usd",
            customer=customer_id,
            payment_method_data={"type": "card", "card": {"token": token}},
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
        )
    except stripe.error.CardError:
        print(f"  ✗ failed ({reason})")
    except Exception as e:
        print(f"  ✗ error: {e}")


def run():
    print("Creating customers and payments in Stripe test mode...\n")
    for data in CUSTOMERS:
        customer = stripe.Customer.create(**data)
        print(f"Customer: {data['name']} ({customer.id})")

        # 2 successes, 1 failure per customer per run
        for _ in range(2):
            create_successful_payment(customer.id)
            time.sleep(0.5)

        # ~40% chance of a second failure to vary the failure rate
        failures = 2 if random.random() < 0.4 else 1
        for _ in range(failures):
            create_failed_payment(customer.id)
            time.sleep(0.5)

        print()

    print("Done. Run again tomorrow (or adjust your clock) for multi-day data.")


if __name__ == "__main__":
    run()
