from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class Product(BaseModel):
    id: UUID
    stripe_product_id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    active: bool

    class Config:
        orm_mode = True
