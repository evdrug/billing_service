from datetime import datetime
from pydantic import BaseModel, Json
from uuid import UUID


class BillingHistory(BaseModel):
    id: UUID
    stripe_customer: UUID
    price: UUID
    stripe_subscription_id: str
    subscription_status: str
    event_type: str
    created_at: datetime
    additional_info: Json
