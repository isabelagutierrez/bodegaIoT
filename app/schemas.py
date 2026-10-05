import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------- Productos ----------
class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    category: str | None = None
    unit: str = "unit"


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    category: str | None = None
    unit: str | None = None


class ProductOut(ProductCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------- Movimientos e inventario ----------
class MovementType(str, Enum):
    RECEIPT = "RECEIPT"        # entrada
    SHIPMENT = "SHIPMENT"      # salida
    ADJUSTMENT = "ADJUSTMENT"  # ajuste: delta con signo (+/-)
    RETURN = "RETURN"          # devolución (entra)


class MovementCreate(BaseModel):
    product_id: uuid.UUID
    type: MovementType
    quantity: int
    reference: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def check_quantity(self):
        if self.quantity == 0:
            raise ValueError("quantity no puede ser 0")
        if self.type != MovementType.ADJUSTMENT and self.quantity < 0:
            raise ValueError("quantity debe ser positiva (solo ADJUSTMENT admite negativos)")
        return self


class MovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    product_id: uuid.UUID
    warehouse_id: str
    type: str
    quantity: int
    reference: str | None
    created_at: datetime


class InventoryOut(BaseModel):
    product_id: uuid.UUID
    warehouse_id: str
    quantity: int
    reserved_quantity: int
    available: int
    updated_at: datetime
