"""Punto de entrada: carga un archivo JSON de transacciones multifuente,
las normaliza y valida, y lanza la interfaz interactiva para explorarlas."""
import json
import sys
from pathlib import Path

from interfaz import menu
from normalizacion import cargar_reglas, normalizar_transaccion
from validacion import validar_transaccion

RUTA_POR_DEFECTO = Path(__file__).parent / "datos" / "transacciones.json"


def procesar_archivo(ruta_archivo: Path, reglas: dict) -> list:
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        datos = json.load(f)

    if not isinstance(datos, list):
        raise ValueError("el archivo debe contener una lista JSON de transacciones")

    transacciones = []
    for registro in datos:
        if not isinstance(registro, dict):
            continue  # un elemento que no es un objeto JSON no es una transaccion
        tx, diagnosticos = normalizar_transaccion(registro, reglas)
        validar_transaccion(tx, diagnosticos)
        transacciones.append(tx)
    return transacciones


def pedir_ruta() -> Path:
    entrada = input(f"Ruta del archivo JSON (Enter para usar '{RUTA_POR_DEFECTO}'): ").strip()
    return Path(entrada) if entrada else RUTA_POR_DEFECTO


def main() -> None:
    reglas = cargar_reglas()
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else pedir_ruta()

    transacciones = None
    while transacciones is None:
        try:
            transacciones = procesar_archivo(ruta, reglas)
        except FileNotFoundError:
            print(f"Error: no se encontro el archivo '{ruta}'.\n")
            ruta = pedir_ruta()
        except json.JSONDecodeError:
            print(f"Error: '{ruta}' no contiene un JSON valido.\n")
            ruta = pedir_ruta()
        except ValueError as error:
            print(f"Error: {error}.\n")
            ruta = pedir_ruta()

    if not transacciones:
        print("El archivo no contiene transacciones para procesar.")
        return

    menu(transacciones)


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nEntrada interrumpida. Hasta luego.")
