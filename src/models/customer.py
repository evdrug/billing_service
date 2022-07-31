from pydantic import BaseModel
from uuid import UUID


class UserCustomer(BaseModel):
    id: UUID
    user_id: UUID
    stripe_customer_id: str
