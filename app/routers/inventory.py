import uuid

from flask import Blueprint, request
from sqlalchemy import select

from ..database import get_db
from ..errors import ApiError
from ..models import InventoryMovement, Product
from ..schemas import InventoryOut, MovementCreate, MovementOut
from ..services import inventory as service

bp = Blueprint("inventory", __name__, url_prefix="/inventory")


@bp.post("/movements")
def create_movement():
    data = MovementCreate.model_validate(request.get_json(silent=True) or {})
    movement = service.execute_movement(get_db(), data)
    return MovementOut.model_validate(movement).model_dump(mode="json"), 201


@bp.get("/<uuid:product_id>")
def get_inventory(product_id: uuid.UUID):
    inv = service.get_inventory_row(get_db(), product_id)
    return InventoryOut(
        product_id=inv.product_id,
        warehouse_id=inv.warehouse_id,
        quantity=inv.quantity,
        reserved_quantity=inv.reserved_quantity,
        available=inv.quantity - inv.reserved_quantity,
        updated_at=inv.updated_at,
    ).model_dump(mode="json")


@bp.get("/<uuid:product_id>/movements")
def list_movements(product_id: uuid.UUID):
    db = get_db()
    skip = request.args.get("skip", 0, type=int)
    limit = request.args.get("limit", 50, type=int)
    if db.get(Product, product_id) is None:
        raise ApiError(404, "Producto no encontrado")
    stmt = (
        select(InventoryMovement)
        .where(InventoryMovement.product_id == product_id)
        .order_by(InventoryMovement.created_at.desc())
        .offset(skip)
        .limit(min(limit, 200))
    )
    return [MovementOut.model_validate(m).model_dump(mode="json") for m in db.scalars(stmt).all()]
