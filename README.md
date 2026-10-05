# Normalización y Exploración de Transacciones Multifuente

**Autor:** David Valles

**Repositorio:** https://github.com/davidvalles1102/actividad-normalizacion-transacciones

Sistema en Python que recibe transacciones provenientes de tres sistemas distintos (una pasarela de pagos, un core bancario legado y una plataforma de e-commerce legada), las normaliza a un esquema único, valida cada registro y permite explorarlas mediante un menú interactivo en consola.

## Contenido de la carpeta

- `main.py` — punto de entrada: carga el archivo JSON, ejecuta el pipeline de normalización + validación y lanza el menú.
- `modelos.py` — esquema normalizado final (`Transaccion`).
- `normalizacion.py` — detección de fuente y conversión de cada campo (monto, moneda, estado, fecha) a su forma normalizada.
- `validacion.py` — reglas de qué campos son obligatorios y qué hace que una transacción quede marcada como inválida.
- `metricas.py` — totales y conteos sobre las transacciones ya procesadas.
- `interfaz.py` — menú interactivo: listar, filtrar, ver inválidas, ver métricas, buscar, ver registro original.
- `reglas_normalizacion.json` — configuración editable: monedas soportadas (con sus alias), mapeo de estados por fuente y formato de fecha por fuente.
- `datos/transacciones_validas.json` — 9 transacciones (3 por fuente), todas válidas.
- `datos/transacciones_con_errores.json` — 12 transacciones, cada una viola **una sola** regla de validación a propósito.
- `datos/transacciones.json` — las dos anteriores combinadas (21 registros); es el archivo que se carga por defecto, simulando una carga real mixta.
- `NOTA_TECNICA.md` — decisiones de diseño, uso de IA y un caso concreto donde se corrigió una sugerencia de la IA.

## Esquema normalizado

Toda transacción, sin importar su fuente, termina con esta forma:

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | str | Identificador original de la transacción (`"SIN_ID"` si no venía) |
| `fuente` | str | `gateway_pagos`, `core_bancario`, `ecommerce_legacy` o `desconocida` |
| `monto` | float \| None | Monto en unidad principal de moneda (no centavos), 2 decimales |
| `moneda` | str \| None | Código ISO de 3 letras (`USD`, `EUR`, `MXN`, `GTQ`, `HNL`) |
| `estado` | str \| None | `completada`, `pendiente`, `fallida` o `reembolsada` |
| `fecha` | str \| None | `AAAA-MM-DD` |
| `cliente_id` | str \| None | Identificador del cliente |
| `valida` | bool | Si pasó todas las reglas de validación |
| `errores` | list[str] | Motivos de invalidez (vacía si `valida=True`) |
| `original` | dict | Registro crudo tal como llegó, para poder inspeccionarlo desde el menú |

Las transacciones inválidas **no se descartan**: se conservan con `valida=False` para poder explorarlas desde la opción 5 del menú. El por qué de esta decisión está en `NOTA_TECNICA.md`.

## Cómo ejecutarlo

Requiere Python 3 (sin librerías externas).

```bash
python main.py datos/transacciones.json
python main.py datos/transacciones_validas.json
python main.py datos/transacciones_con_errores.json
```

También se puede ejecutar sin argumentos; el programa pide la ruta por consola (y vuelve a pedirla si el archivo no existe o no es un JSON válido):

```bash
python main.py
```

## Resultados esperados

**`transacciones_validas.json`:** 9 procesadas, 9 válidas, 0 inválidas. Por estado: 3 completada / 3 pendiente / 1 fallida / 2 reembolsada. Totales por moneda: USD 325.00, EUR 50.00, GTQ 300.00, HNL 400.00, MXN 1,225.00.

**`transacciones_con_errores.json`:** 12 procesadas, 0 válidas, 12 inválidas — una por cada regla de validación (monto ausente, monto no positivo, monto no numérico, moneda no soportada, moneda faltante, estado desconocido, estado faltante, fecha imposible, fecha con formato equivocado, cliente faltante, id ausente, fuente no reconocida). El detalle de cada motivo se ve con la opción 5 del menú.

**`transacciones.json`:** 21 procesadas, 9 válidas, 12 inválidas (la unión exacta de los dos archivos anteriores).

## Menú interactivo

```
1) Listar todas
2) Filtrar por estado
3) Filtrar por moneda
4) Filtrar por fuente
5) Ver transacciones inválidas y motivo
6) Ver métricas generales
7) Buscar por ID o cliente
8) Ver registro original de una transacción
9) Salir
```

Las opciones 2, 3 y 4 muestran primero los valores que realmente existen en el archivo cargado (no hay que adivinar el texto exacto a escribir).
