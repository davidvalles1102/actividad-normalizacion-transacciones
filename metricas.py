"""
Metricas sobre transacciones ya normalizadas y validadas.

Decision de diseno: los totales por moneda y el conteo por estado solo
consideran transacciones validas. Sumar montos o estados de transacciones
invalidas (monto no numerico, estado sin reconocer) distorsionaria esos
numeros con datos que ya se sabe que estan mal. El conteo por fuente, en
cambio, cuenta todas las transacciones (validas e invalidas): ahi lo que
interesa es cuanto volumen llego de cada sistema, no si ese registro en
particular paso la validacion.
"""
from collections import Counter, defaultdict

from modelos import Transaccion


def calcular_metricas(transacciones: list[Transaccion]) -> dict:
    validas = [t for t in transacciones if t.valida]
    invalidas = [t for t in transacciones if not t.valida]

    totales_por_moneda = defaultdict(float)
    for t in validas:
        totales_por_moneda[t.moneda] += t.monto

    return {
        "total_procesadas": len(transacciones),
        "validas": len(validas),
        "invalidas": len(invalidas),
        "conteo_por_estado": dict(Counter(t.estado for t in validas)),
        "conteo_por_fuente": dict(Counter(t.fuente for t in transacciones)),
        "totales_por_moneda": {k: round(v, 2) for k, v in totales_por_moneda.items()},
    }
