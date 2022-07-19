from enum import Enum

import sqlalchemy
from sqlalchemy import Column, ForeignKey, String, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import ENUM as pgEnum


from core.db import metadata

Base = declarative_base(metadata=metadata)


class Product(Base):
    __tablename__ = 'product'

    id = Column(UUID, primary_key=True, index=True)
    stripe_product_id = Column(UUID, nullable=False)
    name = Column(String(250), nullable=False)
    description = Column(String(250), nullable=False)
    created_at = Column(DateTime(True))
    updated_at = Column(DateTime(True))


class Price(Base):
    __tablename__ = 'price'

    id = Column(UUID, primary_key=True, index=True)
    stripe_product_id = Column(UUID, nullable=False)
    name = Column(String(250), nullable=False)
    active = Column(Boolean)
    type = Column(String(250), nullable=False)
    unit_amount = Column(Integer, nullable=False)
    currency = Column(String(250), nullable=False)
    permission_id = Column(UUID, nullable=False)
    product_id = Column(ForeignKey('product.id'), nullable=False)


class StripeCustomer(Base):
    __tablename__ = 'stripe_customer'

    id = Column(UUID, primary_key=True, index=True)
    user_id = Column(UUID, nullable=False)
    stripe_customer_id = Column(UUID, nullable=False)


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

    id = Column(UUID, primary_key=True, index=True)
    stripe_customer = Column(ForeignKey('stripe_customer.id'), nullable=False)
    price = Column(ForeignKey('price.id'), nullable=False)
    stripe_subscription_id = Column(UUID, nullable=False)
    subscription_status = Column(pgEnum(SubscriptionStatus), nullable=False)
    event_type = Column(String(50), nullable=False)
    created_at = Column(DateTime(True))

