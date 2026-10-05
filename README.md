# Warehouse API (Flask) — Fase 1

API + front (Flask), PostgreSQL. Una instancia = una bodega.

## 1. Probar una bodega
```bash
docker compose up -d --build        # API+front en http://localhost:8000
curl localhost:8000/health          # {"status":"ok"}
```
Abre http://localhost:8000 para el panel (crear productos, registrar movimientos, ver kardex).

Flujo por curl:
```bash
B=http://localhost:8000
ID=$(curl -s -X POST $B/products -H 'Content-Type: application/json' \
  -d '{"sku":"TAL-1","name":"Taladro"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
mov() { curl -s -X POST $B/inventory/movements -H 'Content-Type: application/json' \
  -d "{\"product_id\":\"$ID\",\"type\":\"$1\",\"quantity\":$2}"; echo; }
mov RECEIPT 10      # entra 10
mov SHIPMENT 4      # sale 4  -> stock 6
mov SHIPMENT 15     # 409: stock insuficiente
curl -s $B/inventory/$ID; echo
curl -s $B/inventory/$ID/movements
```
Apagar (y borrar datos): `docker compose down -v`

## 2. Tests (sin Docker, usan SQLite en memoria)
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q
```

## 3. Cuatro bodegas separadas (clase)
```bash
docker compose -f docker-compose.4wh.yml up -d --build
```
| Bodega | Front/API | PostgreSQL (host) |
|---|---|---|
| WH-001 | http://localhost:8001 | localhost:5441 |
| WH-002 | http://localhost:8002 | localhost:5442 |
| WH-003 | http://localhost:8003 | localhost:5443 |
| WH-004 | http://localhost:8004 | localhost:5444 |

Cada una tiene su propia DB, volumen y red. Credenciales DB: `warehouse/warehouse`, base `warehouse`.
Apagar una sola: `docker compose -f docker-compose.4wh.yml stop api-wh3 db-wh3`.
Apagar todo y borrar datos: `docker compose -f docker-compose.4wh.yml down -v`.
