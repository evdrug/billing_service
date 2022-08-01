from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends

from models.history import (
    BillingHistory, UserSubscriptions, SubscriptionUpdate
)
from services.admin_services import (
    BillingHistoryService,
    get_billing_history_service,
)

router = APIRouter()


# todo проверить токен на право админа
@router.get('/billing-history/{user_uuid}',
            response_model=List[BillingHistory],
            summary='История пользователя',
            description='История пользователя',
            tags=['Admin'])
async def get_user_history(
        user_uuid: UUID,
        product_service: BillingHistoryService = Depends(
            get_billing_history_service
        )
) -> List[BillingHistory]:
    user_history = await product_service.get_user_history(
        user_uuid
    )
    if not user_history:
        return []
    return user_history


@router.get('/subscriptions/{user_uuid}',
            response_model=List[UserSubscriptions],
            summary='Подписки пользователя',
            description='Подписки пользователя',
            tags=['Admin'])
async def get_user_subscriptions(
        user_uuid: UUID,
        product_service: BillingHistoryService = Depends(
            get_billing_history_service
        )
) -> List[UserSubscriptions]:
    user_subscriptions = await product_service.get_user_subscriptions(
        user_uuid
    )
    if not user_subscriptions:
        return []
    return user_subscriptions


@router.put('/subscriptions',
            response_model=str,
            summary='Изменение подписки пользователя',
            description='Изменение подписки пользователя',
            tags=['Admin'])
async def update_user_subscriptions(
        item: SubscriptionUpdate,
        product_service: BillingHistoryService = Depends(
            get_billing_history_service
        )
) -> str:
    return await product_service.update_user_subscriptions(
        item.user_uuid,
        item.price_uuid,
        item.subscription_id
    )
