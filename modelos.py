"""Esquema normalizado final de una transaccion (una sola forma, sin importar la fuente)."""
from dataclasses import dataclass, field
from typing import Optional

ESTADOS_VALIDOS = {"completada", "pendiente", "fallida", "reembolsada"}


@dataclass
class Transaccion:
    id: str
    fuente: str
    monto: Optional[float]
    moneda: Optional[str]
    estado: Optional[str]
    fecha: Optional[str]
    cliente_id: Optional[str]
    valida: bool = True
    errores: list = field(default_factory=list)
    original: dict = field(default_factory=dict)

    def agregar_error(self, motivo: str) -> None:
        self.valida = False
        self.errores.append(motivo)
