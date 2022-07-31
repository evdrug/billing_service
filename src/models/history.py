from datetime import datetime, date
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class UserSubscriptions(BaseModel):
    status: str
    start_date: date
    end_date: date
    subscription_id: str
    price_id: Optional[UUID] = None
    price_name: Optional[str] = None
    product_name: Optional[str] = None


class SubscriptionStatus(Enum):
    incomplete = 'incomplete'
    incomplete_expired = 'incomplete_expired'
    trialing = 'trialing'
    active = 'active'
    past_due = 'past_due'
    canceled = 'canceled'
    unpaid = 'unpaid'


class BillingHistory(BaseModel):
    id: UUID
    created_at: datetime
    subscription: str
    subscription_id: str
    subscription_status: SubscriptionStatus
    event_type: str
    user_id: UUID

    class Config:
        use_enum_values = True


class SubscriptionUpdate(BaseModel):
    user_uuid: UUID
    price_uuid: UUID
    subscription_id: str
