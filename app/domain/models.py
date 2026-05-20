from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class OrderStatus(StrEnum):
    SHIPPED = "shipped"
    PENDING_SHIPMENT = "pending_shipment"


class CanonicalOrderLine(BaseModel):
    model_config = ConfigDict(frozen=True)

    natural_line_key: str
    product_id: int
    product_name: str | None = None

    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=Decimal("0"))
    discount_rate: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))

    @computed_field
    @property
    def line_subtotal(self) -> Decimal:
        return money(self.unit_price * Decimal(self.quantity))

    @computed_field
    @property
    def line_discount(self) -> Decimal:
        return money(self.line_subtotal * self.discount_rate)

    @computed_field
    @property
    def line_total(self) -> Decimal:
        return money(self.line_subtotal - self.line_discount)


class CanonicalOrder(BaseModel):
    model_config = ConfigDict(frozen=True)

    natural_key: str
    source_order_id: int

    customer_id: str | None = None
    customer_name: str | None = None

    order_date: date
    required_date: date | None = None
    shipped_date: date | None = None

    status: OrderStatus
    currency: str = "USD"

    freight_amount: Decimal = Field(ge=Decimal("0"))

    lines: list[CanonicalOrderLine] = Field(min_length=1)

    @field_validator("currency")
    @classmethod
    def currency_must_be_uppercase(cls, value: str) -> str:
        if len(value) != 3:
            raise ValueError("currency must be a 3-letter ISO-like code")
        return value.upper()

    @computed_field
    @property
    def subtotal_amount(self) -> Decimal:
        return money(sum((line.line_subtotal for line in self.lines), Decimal("0")))

    @computed_field
    @property
    def discount_amount(self) -> Decimal:
        return money(sum((line.line_discount for line in self.lines), Decimal("0")))

    @computed_field
    @property
    def lines_total_amount(self) -> Decimal:
        return money(sum((line.line_total for line in self.lines), Decimal("0")))

    @computed_field
    @property
    def total_amount(self) -> Decimal:
        return money(self.lines_total_amount + self.freight_amount)


def money(value: Decimal) -> Decimal:
    """
    Normalize money to 2 decimals.

    Northwind stores monetary values with numeric affinity. We convert them to
    Decimal and quantize them to make totals deterministic.
    """
    return Decimal(value).quantize(Decimal("0.01"))
