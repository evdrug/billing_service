"""Conactants variables for app."""

# Occurs whenever a new customer is created by checkout session.
CUSTOMER_CREATED_EVENT = 'checkout.session.completed'

# Occurs whenever a customer is signed up for a new plan.
CUSTOMER_SUBSCRIPTION_CREATED = 'customer.subscription.created'

# invoice is successfully paid
PAYMENT_SUCCEEDED = 'invoice.paid'

# payment for an invoice failed
PAYMENT_FAILED = 'invoice.payment_failed'
