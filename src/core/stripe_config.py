from typing import Optional

import stripe

from core.config import Settings

settings = Settings()
stripe_loc = None


def stripe_init():
    stripe_loc = stripe
    stripe_loc.api_key = settings.stripe_key
    return stripe_loc


async def get_stripe() -> stripe:
    return stripe_loc
