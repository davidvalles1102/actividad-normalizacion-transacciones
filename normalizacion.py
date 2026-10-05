"""
Normalizacion de transacciones multifuente.

Responsabilidad de este modulo: convertir cada formato de origen al esquema
comun (modelos.Transaccion). Decide COMO convertir un valor (que formato de
fecha probar, como separar centavos, que alias de moneda existen), pero no
decide si el resultado es valido o no: eso es responsabilidad de validacion.py.

Cuando un campo no se puede convertir, se devuelve None junto con un motivo
en el diccionario de diagnosticos; validacion.py decide que hacer con eso.

El esquema final, los tres formatos de origen soportados y los campos que
se consideran obligatorios fueron decisiones propias tomadas antes de pedirle
a la IA que ayudara con el parsing de cada formato (ver NOTA_TECNICA.md).
"""
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

from modelos import Transaccion

RUTA_REGLAS_POR_DEFECTO = Path(__file__).parent / "reglas_normalizacion.json"

# Conjunto de campos caracteristicos de cada fuente. La fuente se detecta por
# cuantos de estos campos aparecen en el registro, no por un solo campo fijo:
# asi, si a una transaccion de la pasarela le falta justo el id, sigue
# detectandose como gateway_pagos por los demas campos (amount, currency...).
CAMPOS_CARACTERISTICOS = {
    "gateway_pagos": {"transaction_id", "amount", "currency", "status", "timestamp", "customer_id"},
    "core_bancario": {"id_transaccion", "monto_centavos", "moneda", "estado_cod", "fecha", "cliente_id"},
    "ecommerce_legacy": {"order_ref", "total", "curr", "payment_status", "created_at", "buyer_id"},
}

CAMPOS_POR_FUENTE = {
    "gateway_pagos": {
        "id": "transaction_id", "monto": "amount", "moneda": "currency",
        "estado": "status", "fecha": "timestamp", "cliente_id": "customer_id",
    },
    "core_bancario": {
        "id": "id_transaccion", "monto": "monto_centavos", "moneda": "moneda",
        "estado": "estado_cod", "fecha": "fecha", "cliente_id": "cliente_id",
    },
    "ecommerce_legacy": {
        "id": "order_ref", "monto": "total", "moneda": "curr",
        "estado": "payment_status", "fecha": "created_at", "cliente_id": "buyer_id",
    },
}


def cargar_reglas(ruta: Path = RUTA_REGLAS_POR_DEFECTO) -> dict:
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def _sin_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def detectar_fuente(registro: dict) -> Optional[str]:
    claves = set(registro.keys())
    mejor_fuente, mejor_coincidencias = None, 0
    for fuente, campos in CAMPOS_CARACTERISTICOS.items():
        coincidencias = len(claves & campos)
        if coincidencias > mejor_coincidencias:
            mejor_fuente, mejor_coincidencias = fuente, coincidencias
    return mejor_fuente


def convertir_monto(valor_crudo, fuente: str):
    """Devuelve (monto_normalizado, motivo_de_falla). No juzga si el monto es
    valido como negocio (eso es de validacion.py): solo intenta convertirlo."""
    if valor_crudo is None or valor_crudo == "":
        return None, "monto_ausente"
    try:
        if fuente == "core_bancario":
            # esta fuente entrega el monto en centavos, como entero
            centavos = float(str(valor_crudo).strip())
            return round(centavos / 100, 2), None
        texto = re.sub(r"[^0-9.\-]", "", str(valor_crudo).replace(",", ""))
        if texto in ("", "-", "."):
            return None, f"monto_no_numerico:{valor_crudo}"
        return round(float(texto), 2), None
    except (TypeError, ValueError):
        return None, f"monto_no_numerico:{valor_crudo}"


def convertir_moneda(valor_crudo, reglas: dict):
    if not valor_crudo:
        return None, "moneda_faltante"
    clave = _sin_acentos(str(valor_crudo)).strip().upper()
    for codigo, alias in reglas["monedas_soportadas"].items():
        if clave == codigo or clave in [_sin_acentos(a).upper() for a in alias]:
            return codigo, None
    return None, f"moneda_no_soportada:{valor_crudo}"


def convertir_estado(valor_crudo, fuente: str, reglas: dict):
    if not valor_crudo:
        return None, "estado_faltante"
    mapa = reglas["mapeo_estados"].get(fuente, {})
    for crudo, normalizado in mapa.items():
        if str(valor_crudo).strip().upper() == str(crudo).strip().upper():
            return normalizado, None
    return None, f"estado_desconocido:{valor_crudo}"


def convertir_fecha(valor_crudo, fuente: str, reglas: dict):
    if not valor_crudo:
        return None, "fecha_faltante"
    formato = reglas["formatos_fecha"].get(fuente)
    if not formato:
        return None, "formato_fecha_no_definido"
    try:
        dt = datetime.strptime(str(valor_crudo).strip(), formato)
        return dt.strftime("%Y-%m-%d"), None
    except ValueError:
        return None, f"fecha_invalida:{valor_crudo}"


def normalizar_transaccion(registro: dict, reglas: dict):
    """Devuelve (Transaccion, diagnosticos). diagnosticos solo trae entradas
    para los campos que NO se pudieron convertir; validacion.py decide con
    eso si la transaccion queda marcada como invalida."""
    fuente = detectar_fuente(registro)
    diagnosticos = {}

    if fuente is None:
        id_crudo = (
            registro.get("transaction_id")
            or registro.get("id_transaccion")
            or registro.get("order_ref")
        )
        tx = Transaccion(
            id=str(id_crudo) if id_crudo else "SIN_ID",
            fuente="desconocida", monto=None, moneda=None, estado=None, fecha=None,
            cliente_id=None, original=registro,
        )
        diagnosticos["fuente"] = "fuente_no_reconocida"
        return tx, diagnosticos

    campos = CAMPOS_POR_FUENTE[fuente]
    id_crudo = registro.get(campos["id"])
    cliente_crudo = registro.get(campos["cliente_id"])

    monto, diag_monto = convertir_monto(registro.get(campos["monto"]), fuente)
    moneda, diag_moneda = convertir_moneda(registro.get(campos["moneda"]), reglas)
    estado, diag_estado = convertir_estado(registro.get(campos["estado"]), fuente, reglas)
    fecha, diag_fecha = convertir_fecha(registro.get(campos["fecha"]), fuente, reglas)

    tx = Transaccion(
        id=str(id_crudo) if id_crudo else "SIN_ID",
        fuente=fuente,
        monto=monto, moneda=moneda, estado=estado, fecha=fecha,
        cliente_id=str(cliente_crudo) if cliente_crudo else None,
        original=registro,
    )

    if not id_crudo:
        diagnosticos["id"] = "id_ausente"
    if diag_monto:
        diagnosticos["monto"] = diag_monto
    if diag_moneda:
        diagnosticos["moneda"] = diag_moneda
    if diag_estado:
        diagnosticos["estado"] = diag_estado
    if diag_fecha:
        diagnosticos["fecha"] = diag_fecha
    if not cliente_crudo:
        diagnosticos["cliente_id"] = "cliente_ausente"

    return tx, diagnosticos
