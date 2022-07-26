import os
import uuid

import stripe
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from starlette import status
from starlette.responses import RedirectResponse, Response

from core.config import Settings
from services.prices_service import PriceService, get_price_service
from services.products_service import ProductService, get_products_service
from services.subscription_service import SubscriptionService, get_subscription_service
from services.webhook_service import WebhookSubscriptionService, get_webhook_service

static_dir = str(os.path.abspath(os.path.join(
    __file__, "../../../", 'static/')))

templates = Jinja2Templates(directory=static_dir)
router = APIRouter()
settings = Settings()
stripe.api_key = settings.stripe_key


@router.get(
    '/',
    response_class=HTMLResponse,
)
async def index(
    request: Request,
    product_service: ProductService = Depends(get_products_service),
    price_service: PriceService = Depends(get_price_service),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Start page endpoint for subscriptions."""
    # TODO get user id from jwt token
    user_id_mock = uuid.uuid4()
    if await subscription_service.check_user_has_subscription(user_id_mock):
        return templates.TemplateResponse(
            'index.html',
            {
                "request": request,
                "has_subscription": True,
            }
        )
    if product := await product_service.check_product(settings.product_name):
        prices = await price_service.get_all_in_product(product.id)
        return templates.TemplateResponse(
            'index.html',
            {
                "request": request,
                "prices": prices,
            }
        )


@router.get('/checkout-session', response_model=stripe.checkout.Session)
async def get_checkout_session(
    sessionId: str,
):
    stripe.api_key = settings.stripe_key
    id = sessionId
    checkout_session = stripe.checkout.Session.retrieve(id)
    return checkout_session


@router.get('/canceled', response_class=HTMLResponse)
async def canceled_payment(request: Request):
    return templates.TemplateResponse('canceled.html', {"request": request})


@router.get('/success', response_class=HTMLResponse)
async def success_payment(request: Request, session_id: str):
    return templates.TemplateResponse('success.html', {"request": request, 'session_id': session_id})


@router.post('/create-checkout-session')
async def create_checkout_session(
    price_id: str,
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    try:
        # TODO get user id from jwt token
        user_id_mock = uuid.uuid4()
        checkout_session = await subscription_service.create_subscription_session(user_id_mock, price_id)
        return RedirectResponse(
            checkout_session.url,
            status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))


@router.post('/webhook')
async def webhook_received(
    request: Request,
    stripe_signature: Optional[str] = Header(None),
    webhook_service: WebhookSubscriptionService = Depends(get_webhook_service),
):
    webhook_secret = settings.stripe_webhook_secret
    request_data = await request.body()

    if webhook_secret:
        # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
        signature = stripe_signature
        try:
            event = stripe.Webhook.construct_event(
                payload=request_data,
                sig_header=signature,
                secret=webhook_secret,
            )
            print(event['type'])
        except Exception as e:
            return print(e)

        await webhook_service.handling_event(event)

        return Response("Success", status_code=status.HTTP_200_OK)

    return Response("Webhook signature is not verified.", status_code=status.HTTP_403_FORBIDDEN)
