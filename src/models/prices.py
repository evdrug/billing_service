from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TypePrice(Enum):
    recurring = 'recurring'
    one_time = 'one_time'


class TypeRecurring(Enum):
    licensed = 'licensed'
    metered = 'metered'


class Price(BaseModel):
    id: UUID
    stripe_product_id: str
    name: str
    active: bool
    type: str
    unit_amount: int
    currency: str
    permission_id: int
    product_id: UUID
    stripe_price_id: Optional[str]
    interval: Optional[str]
    interval_count: Optional[int]
    using_type: Optional[str]



