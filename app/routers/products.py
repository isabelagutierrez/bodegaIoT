import uuid

from flask import Blueprint, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..database import WAREHOUSE_ID, get_db
from ..errors import ApiError
from ..models import Inventory, InventoryMovement, Product
from ..schemas import ProductCreate, ProductOut, ProductUpdate

bp = Blueprint("products", __name__, url_prefix="/products")


def _out(product: Product) -> dict:
    return ProductOut.model_validate(product).model_dump(mode="json")


def _get_or_404(db, product_id: uuid.UUID) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise ApiError(404, "Producto no encontrado")
    return product


@bp.post("")
def create_product():
    db = get_db()
    data = ProductCreate.model_validate(request.get_json(silent=True) or {})
    product = Product(**data.model_dump())
    db.add(product)
    try:
        db.flush()  # asigna el id sin cerrar la transacción
        # Fila de inventario en 0: así siempre existe y FOR UPDATE tiene qué bloquear
        db.add(Inventory(product_id=product.id, warehouse_id=WAREHOUSE_ID, quantity=0, reserved_quantity=0))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ApiError(409, f"Ya existe un producto con sku '{data.sku}'")
    db.refresh(product)
    return _out(product), 201


@bp.get("")
def list_products():
    skip = request.args.get("skip", 0, type=int)
    limit = request.args.get("limit", 50, type=int)
    stmt = select(Product).order_by(Product.created_at).offset(skip).limit(min(limit, 200))
    return [_out(p) for p in get_db().scalars(stmt).all()]


@bp.get("/<uuid:product_id>")
def get_product(product_id):
    return _out(_get_or_404(get_db(), product_id))


@bp.put("/<uuid:product_id>")
def update_product(product_id):
    db = get_db()
    product = _get_or_404(db, product_id)
    data = ProductUpdate.model_validate(request.get_json(silent=True) or {})
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return _out(product)


@bp.delete("/<uuid:product_id>")
def delete_product(product_id):
    db = get_db()
    product = _get_or_404(db, product_id)
    if db.scalar(select(InventoryMovement.id).where(InventoryMovement.product_id == product_id).limit(1)):
        raise ApiError(409, "El producto tiene movimientos; no se puede eliminar")
    inv = db.scalar(select(Inventory).where(Inventory.product_id == product_id))
    if inv:
        db.delete(inv)
    db.delete(product)
    db.commit()
    return "", 204
