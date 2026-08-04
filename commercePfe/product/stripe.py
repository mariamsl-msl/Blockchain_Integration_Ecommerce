import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_TEST_SECRET_KEY
