from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class SubscriptionStatus(Enum):
    incomplete = 'incomplete'
    incomplete_expired = 'incomplete_expired'
    trialing = 'trialing'
    active = 'active'
    past_due = 'past_due'
    canceled = 'canceled'
    unpaid = 'unpaid'


class UserSubscriptions(BaseModel):
    id: UUID
    created_at: datetime
    subscription: str
    subscription_id: str

    class Config:
        use_enum_values = True


class BillingHistory(UserSubscriptions):
    subscription_status: SubscriptionStatus
    event_type: str
    user_id: UUID
