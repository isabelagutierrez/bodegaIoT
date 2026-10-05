# Proyecto Integrador — Warehouse Cloud Platform

## Curso

**Computación en la Nube e Internet de las Cosas**

## Descripción

Este proyecto consiste en diseñar, implementar, desplegar y evaluar una plataforma distribuida para la gestión de múltiples bodegas o almacenes.

Cada bodega administra de manera autónoma:

- productos;
- inventario;
- movimientos de entrada y salida;
- reservas;
- usuarios/operadores;
- consultas frecuentes;
- procesos internos.

La plataforma evolucionará progresivamente desde una aplicación sencilla hasta una arquitectura distribuida capaz de manejar:

- múltiples APIs;
- múltiples bases de datos;
- Redis;
- RabbitMQ;
- workers asíncronos;
- balanceo de carga;
- escalamiento horizontal;
- transferencias entre bodegas;
- consistencia eventual;
- Saga y transacciones distribuidas;
- idempotencia;
- reintentos y DLQ;
- una plataforma central de consolidación;
- CQRS y modelos de lectura;
- S3;
- procesamiento Batch;
- AWS Lambda;
- observabilidad;
- pruebas de carga;
- y, como extensión, IoT dentro de las bodegas.

---

# 1. Problema

Una empresa administra varias bodegas distribuidas geográficamente.

Cada bodega recibe productos, almacena inventario, despacha pedidos y realiza ajustes. Algunas bodegas tienen mucho más tráfico que otras.

Por ejemplo:

| Bodega | Carga aproximada | Característica |
|---|---:|---|
| WH-001 | 50 req/s | Baja actividad |
| WH-002 | 800 req/s | Alta lectura |
| WH-003 | 20 req/s | Baja actividad |
| WH-004 | 2.000 req/s | Alta actividad |

La empresa necesita que:

1. cada bodega pueda operar de manera autónoma;
2. las consultas frecuentes sean rápidas;
3. las escrituras sean consistentes dentro de cada bodega;
4. los procesos pesados no bloqueen las APIs;
5. las bodegas puedan escalar de manera independiente;
6. se puedan transferir productos entre bodegas;
7. exista una visión consolidada de toda la empresa;
8. los procesos fallen de forma controlada;
9. exista trazabilidad de extremo a extremo;
10. la plataforma pueda crecer hacia AWS y eventualmente IoT.

---

# 2. Objetivo general

Construir una plataforma cloud distribuida que permita gestionar múltiples bodegas independientes y que evolucione progresivamente desde una aplicación CRUD hasta una arquitectura distribuida, asíncrona, observable y escalable.

El objetivo no es únicamente implementar tecnologías.

El objetivo es comprender **qué problema resuelve cada componente, cuándo introducirlo, qué trade-off genera y qué sucede cuando falla**.

---

# 3. Principio arquitectónico

La plataforma seguirá esta idea:

```text
                 CENTRAL PLATFORM
                       |
             +---------+---------+
             |                   |
        Global API          Global Workers
             |                   |
             |                RabbitMQ
             |                   |
     +-------+-------+-----------+---------+
     |               |                     |
     v               v                     v
 Warehouse A     Warehouse B           Warehouse C
     |               |                     |
 +---+---+        +---+---+            +---+---+
 |       |        |       |            |       |
API    Redis     API    Redis          API    Redis
 |       |        |       |            |       |
 v       |        v       |            v       |
DB A     |       DB B     |           DB C     |
```

Cada bodega es un **dominio operativo autónomo**.

La plataforma central es responsable principalmente de:

- consolidación;
- consultas globales;
- reportes;
- procesamiento empresarial;
- integración;
- analítica;
- coordinación de procesos distribuidos.

La central no debe convertirse desde el inicio en la única base de datos operacional de todas las bodegas. Eso eliminaría buena parte de los problemas distribuidos que el proyecto pretende estudiar.

---

# 4. Arquitectura evolutiva

El proyecto se desarrolla en fases.

```text
Fase 1
Bodega + API + PostgreSQL
        |
        v
Fase 2
Redis + Cache Aside
        |
        v
Fase 3
RabbitMQ + Workers
        |
        v
Fase 4
Múltiples bodegas
        |
        v
Fase 5
Load Balancer + Escalamiento
        |
        v
Fase 6
Transferencias + Saga
        |
        v
Fase 7
Central + CQRS + Read Model
        |
        v
Fase 8
S3 + Batch
        |
        v
Fase 9
Lambda
        |
        v
Fase 10
Fallos + Idempotencia + DLQ
        |
        v
Fase 11
Observabilidad + Load Testing
        |
        v
Fase 12
IoT en bodegas
```

Cada fase debe funcionar antes de pasar a la siguiente.

---

# 5. Tecnologías sugeridas

## Backend

- Python
- FastAPI o Flask

## Persistencia

- PostgreSQL

## Caché

- Redis

## Mensajería

- RabbitMQ

## Contenedores

- Docker
- Docker Compose

## Cloud

- AWS EC2
- Amazon ECR
- Amazon S3
- Amazon RDS
- AWS Lambda

## Infraestructura como código

- Terraform

## Testing

- pytest
- herramientas de carga como Locust, k6 o equivalente

## Observabilidad

- logs estructurados
- métricas
- correlation IDs
- health checks

## IoT — extensión

- MQTT
- simuladores de sensores

---

# 6. Modelo de dominio

## Product

```text
Product
-------
id
sku
name
description
category
unit
created_at
updated_at
```

## Inventory

```text
Inventory
---------
id
product_id
warehouse_id
quantity
reserved_quantity
updated_at
```

## Inventory Movement

```text
InventoryMovement
-----------------
id
product_id
warehouse_id
type
quantity
reference
created_at
```

Tipos posibles:

```text
RECEIPT
SHIPMENT
ADJUSTMENT
RESERVATION
RELEASE
TRANSFER_OUT
TRANSFER_IN
RETURN
```

## Transfer

```text
Transfer
--------
id
source_warehouse
destination_warehouse
product_id
quantity
status
created_at
updated_at
```

Estados:

```text
REQUESTED
RESERVING_SOURCE
SOURCE_RESERVED
IN_TRANSIT
DESTINATION_PENDING
DESTINATION_RECEIVED
COMPLETED
FAILED
COMPENSATING
CANCELLED
```

---

# 7. API inicial

La primera versión debe ser deliberadamente sencilla.

## Products

```http
POST /products
GET /products
GET /products/{id}
PUT /products/{id}
DELETE /products/{id}
```

## Inventory

```http
GET /inventory/{product_id}
POST /inventory/movements
GET /inventory/{product_id}/movements
```

## Health

```http
GET /health
```

Respuesta:

```json
{
  "status": "ok"
}
```

---

# 8. Fase 1 — Una bodega

## Objetivo

Comprender una arquitectura backend tradicional antes de introducir distribución.

```text
Client
   |
   v
 API
   |
   v
PostgreSQL
```

La aplicación debe permitir:

- crear productos;
- consultar productos;
- registrar entradas;
- registrar salidas;
- consultar inventario;
- consultar movimientos.

---

## 8.1 Reglas

Una salida no puede dejar el inventario negativo.

Ejemplo:

```text
Inventario = 10

Salida = 4

Inventario final = 6
```

Pero:

```text
Inventario = 10

Salida = 15
```

debe ser rechazada.

---

## 8.2 Transacción

Una operación de inventario debe modificar de forma atómica:

1. inventario;
2. movimiento.

Conceptualmente:

```text
BEGIN

UPDATE inventory
SET quantity = quantity - 4

INSERT INTO inventory_movements (...)

COMMIT
```

Si algo falla:

```text
ROLLBACK
```

---