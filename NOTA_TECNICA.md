# Nota técnica — Normalización de transacciones multifuente

**Actividad:** Normalización y Exploración de Transacciones Multifuente
**Autor:** David Valles

## 1. Qué apoyó la IA

Usé Claude en VS Code en momentos puntuales, no para escribir el sistema de principio a fin: para armar el esqueleto de los cuatro módulos (`normalizacion.py`, `validacion.py`, `metricas.py`, `interfaz.py`) una vez que yo ya había decidido qué le correspondía a cada uno; para el parsing de montos con distintos formatos (quitar símbolos y separadores de miles, convertir centavos a monto principal); para el `try/except ValueError` alrededor de `datetime.strptime`; y para el formateo de la tabla de la interfaz. En todos los casos ajusté lo propuesto al probarlo contra los datos de prueba.

## 2. Qué decidí yo

El enunciado es explícito en que la IA no decide el esquema, las reglas de normalización ni los criterios de validez. Decisiones propias:

- **El esquema final** (`modelos.py`): `id`, `fuente`, `monto`, `moneda`, `estado`, `fecha`, `cliente_id`, más `valida` y `errores` para no perder trazabilidad.
- **Los tres formatos de origen**: pasarela de pagos (monto decimal, fecha ISO con hora), core bancario (monto en centavos, estado como código de una letra, fecha `DD/MM/AAAA`) y e-commerce legado (monto en texto con `$` y comas, estado en palabras, fecha con hora sin "T"). Las reglas de mapeo quedaron en `reglas_normalizacion.json`, no en el código, para poder agregar moneda o estado nuevo sin tocar `normalizacion.py`.
- **Marcar en vez de descartar.** Una transacción inválida se conserva con `valida=False` y sus motivos, en vez de descartarse: ocultarla impediría explorar justo los datos de peor calidad, que es el punto de juntar varias fuentes.
- **Seis campos obligatorios** (`id`, `monto`, `moneda`, `estado`, `fecha`, `cliente_id`) en `validacion.py`. Un monto que sí se convirtió pero quedó en cero o negativo también es inválido — eso es una regla de negocio, no de formato, por eso vive en `validacion.py` y no en `normalizacion.py`.
- **Qué entra en las métricas.** Totales por moneda y conteo por estado solo usan transacciones válidas (sumar un monto no convertido no tiene sentido). El conteo por fuente cuenta todo: ahí importa el volumen recibido, no si pasó la validación.
- **Fuera de alcance a propósito:** no se detectan IDs duplicados entre fuentes, no se admite más de una fecha por registro, y una fuente nueva requiere agregar su mapeo de campos en `normalizacion.py` (no es automático). Ampliarlo habría significado inventar reglas que el enunciado no pide.

## 3. Un caso donde la IA se equivocó y lo corregí

La primera versión de `detectar_fuente()` que propuso Claude identificaba la fuente por un solo campo llave (`transaction_id`, `id_transaccion` u `order_ref`). Lo noté al construir el caso de prueba "falta el id": un registro de la pasarela sin `transaction_id` pero con sus demás campos (`amount`, `currency`, `status`, `timestamp`, `customer_id`) caía como `fuente_no_reconocida` en vez de "pasarela con id faltante", que era el error que quería forzar. La corrección fue comparar el conjunto completo de campos del registro contra el conjunto característico de cada fuente y elegir la de más coincidencias, en vez de depender de un solo campo (`normalizacion.py`). Así, a un registro le puede faltar un campo y aun así detectarse bien; solo cae en `fuente_no_reconocida` uno que casi no coincide con ninguna fuente (caso de prueba `{"foo": "bar", "valor": 123}`).

## 4. Qué aprendí

La IA resuelve bien "¿cómo convierto este texto a número?", pero no anticipa un caso borde que no se le describa. El error de `detectar_fuente()` no vino de hacer algo distinto a lo pedido, sino de que "detectar por un campo llave" no cubría un campo faltante — justo el tipo de caso que datos reales van a tener. Lo encontré al construir deliberadamente el caso de prueba más incómodo para cada regla, no al leer el código.

## 5. Evidencia de pruebas

Los archivos de `datos/` y los resultados esperados están en `README.md`. Ejecuté los tres y el detalle por transacción (opción 5, "ver inválidas y motivo") coincide con el motivo que cada registro de `transacciones_con_errores.json` fue diseñado para forzar. También probé archivo inexistente, JSON corrupto y lista vacía: en los tres casos el programa pide la ruta de nuevo o termina con un mensaje claro, sin traceback.
