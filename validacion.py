"""
Reglas de validez de una transaccion ya normalizada.

Responsabilidad de este modulo: decidir que hace que una transaccion sea
invalida o incompleta, y que hacer con ella. La decision tomada aqui es
MARCAR, no descartar: una transaccion invalida se conserva en la lista con
valida=False y la lista de motivos en errores, para poder explorarla desde
la interfaz (opcion "ver transacciones invalidas"). Descartarla de entrada
ocultaria justo los datos que mas interesa revisar en una carga multifuente.

Los campos obligatorios y el criterio de "marcar en vez de descartar" son
decisiones de negocio propias, no sugerencias de la IA (ver NOTA_TECNICA.md).
"""
from modelos import Transaccion

CAMPOS_OBLIGATORIOS = ("id", "monto", "moneda", "estado", "fecha", "cliente_id")


def validar_transaccion(tx: Transaccion, diagnosticos: dict) -> None:
    if tx.fuente == "desconocida":
        tx.agregar_error(diagnosticos.get("fuente", "fuente_no_reconocida"))
        return

    valores = {
        "id": None if tx.id == "SIN_ID" else tx.id,
        "monto": tx.monto,
        "moneda": tx.moneda,
        "estado": tx.estado,
        "fecha": tx.fecha,
        "cliente_id": tx.cliente_id,
    }

    for campo in CAMPOS_OBLIGATORIOS:
        if valores[campo] is None:
            tx.agregar_error(diagnosticos.get(campo, f"{campo}_invalido"))

    # el monto puede haberse convertido bien y aun asi no ser valido como
    # negocio (cero o negativo); ese chequeo es de validacion, no de parsing
    if tx.monto is not None and tx.monto <= 0:
        tx.agregar_error(f"monto_no_positivo:{tx.monto}")
