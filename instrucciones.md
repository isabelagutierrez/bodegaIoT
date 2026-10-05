# Instrucciones paso a paso

Abre la terminal de VS Code con `` Ctrl+` `` y ubícate en la carpeta del proyecto:

```bash
cd /home/dark/Descargas/warehouse-api-fusion
```

## 1. Tests (opcional, sin Docker)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q
```

Debe decir `9 passed`.

## 2. Levantar UNA bodega

```bash
docker compose up -d --build
docker compose ps           # db "healthy" y api "Up"
curl localhost:8000/health  # {"status":"ok"}
```

Abre en el navegador http://localhost:8000. Desde el panel puedes:

- crear un producto,
- registrar una entrada (`RECEIPT`) y una salida (`SHIPMENT`),
- ver el kardex (historial de movimientos).

Prueba también una salida mayor al stock disponible: debe rechazarla con el mensaje "Stock insuficiente".

## 3. Ver logs si algo falla

```bash
docker compose logs api
```

## 4. Apagar la bodega única y limpiar datos

```bash
docker compose down -v
```

## 5. Levantar las 4 bodegas

```bash
docker compose -f docker-compose.4wh.yml up -d --build
docker compose -f docker-compose.4wh.yml ps
```

Abre cada front:

- http://localhost:8001 (WH-001)
- http://localhost:8002 (WH-002)
- http://localhost:8003 (WH-003)
- http://localhost:8004 (WH-004)

Crea un producto en una y verifica que **no aparece** en las demás.

## 6. Apagar las 4 y dejarlas limpias

```bash
docker compose -f docker-compose.4wh.yml down -v
```

> **Nota:** haz el paso 4 antes del 5, para no tener 5 bases de datos corriendo a la vez.
