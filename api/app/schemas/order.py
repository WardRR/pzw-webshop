from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0, le=2_147_483_647)
    quantity: int = Field(gt=0, le=2_147_483_647)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderStatusUpdate(BaseModel):
    status: Literal["pending", "completed", "cancelled"]


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: str
    total_price: Decimal
    created_at: datetime
    items: list[OrderItemRead]
