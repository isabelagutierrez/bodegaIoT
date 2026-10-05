import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import create_app


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    app = create_app(engine=engine)
    app.config["TESTING"] = True
    return app.test_client()


def make_product(client, sku="SKU-1"):
    r = client.post("/products", json={"sku": sku, "name": "Taladro"})
    assert r.status_code == 201
    return r.json["id"]


def move(client, pid, type_, qty, ref=None):
    return client.post("/inventory/movements",
                       json={"product_id": pid, "type": type_, "quantity": qty, "reference": ref})


def stock(client, pid):
    return client.get(f"/inventory/{pid}").json["quantity"]


def test_health(client):
    assert client.get("/health").json == {"status": "ok"}


def test_product_crud_and_duplicate_sku(client):
    pid = make_product(client)
    assert client.get(f"/products/{pid}").json["sku"] == "SKU-1"
    assert client.put(f"/products/{pid}", json={"name": "Taladro pro"}).json["name"] == "Taladro pro"
    assert client.post("/products", json={"sku": "SKU-1", "name": "otro"}).status_code == 409
    assert client.delete(f"/products/{pid}").status_code == 204
    assert client.get(f"/products/{pid}").status_code == 404


def test_new_product_has_zero_inventory(client):
    pid = make_product(client)
    assert stock(client, pid) == 0


def test_receipt_then_shipment(client):
    pid = make_product(client)
    assert move(client, pid, "RECEIPT", 10).status_code == 201
    assert move(client, pid, "SHIPMENT", 4).status_code == 201
    assert stock(client, pid) == 6


def test_shipment_cannot_make_inventory_negative(client):
    pid = make_product(client)
    move(client, pid, "RECEIPT", 10)
    assert move(client, pid, "SHIPMENT", 15).status_code == 409
    assert stock(client, pid) == 10
    assert len(client.get(f"/inventory/{pid}/movements").json) == 1  # no se registró la salida


def test_adjustment_is_a_signed_delta(client):
    pid = make_product(client)
    move(client, pid, "RECEIPT", 50)
    assert move(client, pid, "ADJUSTMENT", -20).status_code == 201
    assert stock(client, pid) == 30
    kardex = client.get(f"/inventory/{pid}/movements").json
    assert sum(m["quantity"] for m in kardex) == 30  # el stock es la suma del kardex


def test_validation_and_not_found(client):
    pid = make_product(client)
    assert move(client, pid, "RECEIPT", -1).status_code == 422
    assert move(client, pid, "SHIPMENT", 0).status_code == 422
    assert move(client, pid, "TRANSFER_OUT", 1).status_code == 422
    assert move(client, "00000000-0000-0000-0000-000000000000", "RECEIPT", 1).status_code == 404
    assert client.get("/inventory/00000000-0000-0000-0000-000000000000").status_code == 404


def test_cannot_delete_product_with_movements(client):
    pid = make_product(client)
    move(client, pid, "RECEIPT", 5, "OC-100")
    assert client.delete(f"/products/{pid}").status_code == 409


def test_front_page_is_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Bodega" in r.data
