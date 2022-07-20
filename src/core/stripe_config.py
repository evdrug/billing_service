# from typing import Optional
#
# import stripe
#
# from core.config import Settings
#
# settings = Settings()
# stripe_loc: Optional[stripe] = None
#
#
# def stripe_init():
#     stripe_loc = stripe
#     stripe_loc.api_key = settings.stripe_key
#
#
# async def get_pg() -> stripe:
#     return stripe_loc
