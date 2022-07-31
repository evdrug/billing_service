import uuid
from typing import Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette import status
from starlette.responses import RedirectResponse, Response

from core.config import Settings, STATIC_DIR
from grpc_auth_client.dependencies import get_user_id
from services.products_service import ProductService, get_products_service
from services.subscription_service import SubscriptionService, get_subscription_service
from services.webhook_service import WebhookSubscriptionService, get_webhook_service

templates = Jinja2Templates(directory=STATIC_DIR)
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
        subscription_service: SubscriptionService = Depends(get_subscription_service),
        user_id: uuid.UUID = Depends(get_user_id),
):
    """Start page endpoint for subscriptions."""
    customer = await subscription_service.check_user_has_subscription(user_id)
    if customer:
        return templates.TemplateResponse(
            'index.html',
            {
                "request": request,
                "has_subscription": True,
                "customer_id": customer.stripe_customer_id,
            }
        )
    if products := await product_service.get_all():
        return templates.TemplateResponse(
            'index.html',
            {
                "request": request,
                "products": products,
                "user_id": user_id,
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
        product_id: str,
        user_id: str,
        subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    try:
        checkout_session = await subscription_service.create_subscription_session(user_id, product_id)
        return RedirectResponse(
            checkout_session.url,
            status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))


@router.post('/create-customer-portal-session')
async def customer_portal_user(customer_id: str):
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url='https://www.kinopoisk.ru/',
    )
    return RedirectResponse(
        session.url,
        status.HTTP_303_SEE_OTHER,
    )


@router.post('/create-portal-session', response_model=stripe.checkout.Session)
async def customer_portal_session(session_id: str):
    """Redirect to customer subscriptions cp."""
    checkout_session_id = session_id
    checkout_session = stripe.checkout.Session.retrieve(checkout_session_id)

    return_url = 'https://www.kinopoisk.ru/'

    portalSession = stripe.billing_portal.Session.create(
        customer=checkout_session.customer,
        return_url=return_url,
    )
    return RedirectResponse(
        portalSession.url,
        status.HTTP_303_SEE_OTHER,
    )


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
        except Exception as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
        print(event['type'])
        await webhook_service.handling_event(event)

        return Response("Success", status_code=status.HTTP_200_OK)

    return Response("Webhook signature is not verified.", status_code=status.HTTP_403_FORBIDDEN)
