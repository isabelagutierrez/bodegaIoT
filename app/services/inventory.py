import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import WAREHOUSE_ID
from ..errors import ApiError
from ..models import Inventory, InventoryMovement, Product
from ..schemas import MovementCreate, MovementType


def _signed_delta(data: MovementCreate) -> int:
    """Cuánto cambia el inventario (con signo)."""
    if data.type == MovementType.SHIPMENT:
        return -data.quantity
    return data.quantity  # RECEIPT y RETURN suman; ADJUSTMENT ya trae su signo


def get_inventory_row(db: Session, product_id: uuid.UUID) -> Inventory:
    inv = db.scalar(
        select(Inventory).where(
            Inventory.product_id == product_id, Inventory.warehouse_id == WAREHOUSE_ID
        )
    )
    if inv is None:
        raise ApiError(404, "Producto sin inventario en esta bodega")
    return inv


def execute_movement(db: Session, data: MovementCreate) -> InventoryMovement:
    """BEGIN -> bloquear -> validar -> UPDATE inventory -> INSERT movimiento -> COMMIT.
    Ante cualquier error: ROLLBACK (no queda nada a medias)."""
    if db.get(Product, data.product_id) is None:
        raise ApiError(404, "Producto no encontrado")

    try:
        # FOR UPDATE: nadie más modifica esta fila hasta nuestro COMMIT/ROLLBACK
        inv = db.scalar(
            select(Inventory)
            .where(Inventory.product_id == data.product_id, Inventory.warehouse_id == WAREHOUSE_ID)
            .with_for_update()
        )
        if inv is None:
            raise ApiError(404, "Producto sin inventario en esta bodega")

        delta = _signed_delta(data)
        new_quantity = inv.quantity + delta

        # Regla 8.1: nunca negativo (ni por debajo de lo reservado)
        if new_quantity < inv.reserved_quantity:
            raise ApiError(
                409,
                f"Stock insuficiente. Disponible: {inv.quantity - inv.reserved_quantity}, "
                f"solicitado: {-delta}",
            )

        inv.quantity = new_quantity                    # UPDATE inventory
        movement = InventoryMovement(                  # INSERT inventory_movements
            product_id=data.product_id,
            warehouse_id=WAREHOUSE_ID,
            type=data.type.value,
            quantity=delta,
            reference=data.reference,
        )
        db.add(movement)
        db.commit()                                    # COMMIT
    except Exception:
        db.rollback()                                  # ROLLBACK
        raise

    db.refresh(movement)
    return movement
