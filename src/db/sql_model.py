import uuid
from enum import Enum

from sqlalchemy import Column, ForeignKey, String, DateTime, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import ENUM as pgEnum


from core.db import metadata

Base = declarative_base(metadata=metadata)


class Product(Base):
    __tablename__ = 'product'

    id = Column(UUID(as_uuid=True), primary_key=True,
              default=uuid.uuid4, unique=True, nullable=False)
    stripe_product_id = Column(String(50), nullable=False)
    name = Column(String(250), nullable=False)
    description = Column(String(250), nullable=True)
    created_at = Column(DateTime(True))
    updated_at = Column(DateTime(True))
    active = Column(Boolean, nullable=False, server_default="true")


class Price(Base):
    __tablename__ = 'price'

    id = Column(UUID(as_uuid=True), primary_key=True,
              default=uuid.uuid4, unique=True, nullable=False)
    stripe_product_id = Column(String(50), nullable=False)
    stripe_price_id = Column(String(50), nullable=False)
    name = Column(String(250), nullable=False)
    active = Column(Boolean)
    type = Column(String(250), nullable=False)
    unit_amount = Column(Integer, nullable=False)
    currency = Column(String(250), nullable=False)
    permission_id = Column(Integer, nullable=False)
    product_id = Column(ForeignKey('product.id'), nullable=False)
    interval = Column(String(250), nullable=True)
    interval_count = Column(Integer, nullable=True)
    using_type = Column(String(250), nullable=True)


class StripeCustomer(Base):
    __tablename__ = 'stripe_customer'

    id = Column(UUID(as_uuid=True), primary_key=True,
              default=uuid.uuid4, unique=True, nullable=False)
    user_id = Column(UUID, nullable=False)
    stripe_customer_id = Column(String(50), nullable=False)


class SubscriptionStatus(Enum):
    incomplete = 'incomplete'
    incomplete_expired = 'incomplete_expired'
    trialing = 'trialing'
    active = 'active'
    past_due = 'past_due'
    canceled = 'canceled'
    unpaid = 'unpaid'


class BillingHistory(Base):
    __tablename__ = 'billing_history'

    id = Column(UUID(as_uuid=True), primary_key=True,
              default=uuid.uuid4, unique=True, nullable=False)
    stripe_customer = Column(ForeignKey('stripe_customer.id'), nullable=False)
    price = Column(ForeignKey('price.id'), nullable=False)
    stripe_subscription_id = Column(String(50), nullable=False)
    subscription_status = Column(pgEnum(SubscriptionStatus), nullable=False)
    event_type = Column(String(50), nullable=False)
    created_at = Column(DateTime(True))
    additional_info = Column(JSON, nullable=True)
