"""
Interfaz CLI interactiva para explorar las transacciones ya normalizadas.

Responsabilidad de este modulo: mostrar y filtrar, no transformar datos.
Si una columna no tiene sentido mostrar (p. ej. el monto de una transaccion
invalida que no pudo convertirse), se imprime "-" en vez de fallar.
"""
from metricas import calcular_metricas

TAMANO_PAGINA = 10
SEP = "  "
COL_ID, COL_FUENTE, COL_MONTO, COL_MONEDA = 16, 17, 12, 7
COL_ESTADO, COL_FECHA, COL_CLIENTE = 13, 12, 10


def _celda(valor, ancho):
    texto = "-" if valor is None else str(valor)
    return texto[:ancho].ljust(ancho)


def _formatear_fila(t) -> str:
    monto = "-" if t.monto is None else f"{t.monto:,.2f}"
    return SEP.join([
        _celda(t.id, COL_ID),
        _celda(t.fuente, COL_FUENTE),
        monto.rjust(COL_MONTO),
        _celda(t.moneda, COL_MONEDA),
        _celda(t.estado, COL_ESTADO),
        _celda(t.fecha, COL_FECHA),
        _celda(t.cliente_id, COL_CLIENTE),
    ])


def _encabezado() -> None:
    fila = SEP.join([
        _celda("ID", COL_ID),
        _celda("FUENTE", COL_FUENTE),
        "MONTO".rjust(COL_MONTO),
        _celda("MONEDA", COL_MONEDA),
        _celda("ESTADO", COL_ESTADO),
        _celda("FECHA", COL_FECHA),
        _celda("CLIENTE", COL_CLIENTE),
    ])
    print(fila)
    print("-" * len(fila))


def listar(transacciones) -> None:
    if not transacciones:
        print("No hay transacciones que coincidan con ese criterio.\n")
        return
    _encabezado()
    for i, t in enumerate(transacciones, 1):
        print(_formatear_fila(t))
        if i % TAMANO_PAGINA == 0 and i < len(transacciones):
            seguir = input(f"-- {i}/{len(transacciones)} - Enter para continuar, 'q' para salir -- ")
            if seguir.strip().lower() == "q":
                break
    print()


def _elegir_de_lista(opciones, etiqueta: str):
    if not opciones:
        print(f"No hay valores de {etiqueta} disponibles en los datos cargados.\n")
        return None
    print(f"\n{etiqueta.capitalize()} disponibles:")
    for i, op in enumerate(opciones, 1):
        print(f"  {i}) {op}")
    seleccion = input("Elige un numero (Enter para cancelar): ").strip()
    if not seleccion:
        return None
    try:
        indice = int(seleccion) - 1
        if indice < 0:
            raise ValueError
        return opciones[indice]
    except (ValueError, IndexError):
        print("Opcion no valida.\n")
        return None


def filtrar_por_estado(transacciones) -> None:
    estados = sorted({t.estado for t in transacciones if t.estado})
    elegido = _elegir_de_lista(estados, "estado")
    if elegido:
        listar([t for t in transacciones if t.estado == elegido])


def filtrar_por_moneda(transacciones) -> None:
    monedas = sorted({t.moneda for t in transacciones if t.moneda})
    elegido = _elegir_de_lista(monedas, "moneda")
    if elegido:
        listar([t for t in transacciones if t.moneda == elegido])


def filtrar_por_fuente(transacciones) -> None:
    fuentes = sorted({t.fuente for t in transacciones})
    elegido = _elegir_de_lista(fuentes, "fuente")
    if elegido:
        listar([t for t in transacciones if t.fuente == elegido])


def mostrar_invalidas(transacciones) -> None:
    invalidas = [t for t in transacciones if not t.valida]
    if not invalidas:
        print("No hay transacciones invalidas en este archivo.\n")
        return
    for t in invalidas:
        print(f"[{t.id}] fuente={t.fuente} -> {', '.join(t.errores)}")
    print(f"\nTotal invalidas: {len(invalidas)} de {len(transacciones)}\n")


def mostrar_metricas(transacciones) -> None:
    m = calcular_metricas(transacciones)
    print("\n== Metricas ==")
    print(f"Total procesadas : {m['total_procesadas']}")
    print(f"Validas          : {m['validas']}")
    print(f"Invalidas        : {m['invalidas']}")

    print("\nPor estado (solo validas):")
    for estado, cantidad in sorted(m["conteo_por_estado"].items()):
        print(f"  {estado:<13}{cantidad}")

    print("\nPor fuente (validas + invalidas):")
    for fuente, cantidad in sorted(m["conteo_por_fuente"].items()):
        print(f"  {fuente:<17}{cantidad}")

    print("\nTotales por moneda (solo validas):")
    for moneda, total in sorted(m["totales_por_moneda"].items()):
        print(f"  {moneda}: {total:,.2f}")
    print()


def buscar(transacciones) -> None:
    termino = input("ID o cliente a buscar (coincidencia parcial): ").strip().lower()
    if not termino:
        return
    resultados = [
        t for t in transacciones
        if termino in t.id.lower() or (t.cliente_id and termino in t.cliente_id.lower())
    ]
    listar(resultados)


def ver_registro_original(transacciones) -> None:
    id_buscado = input("ID exacto de la transaccion: ").strip()
    for t in transacciones:
        if t.id == id_buscado:
            print(f"\nRegistro original recibido de '{t.fuente}':")
            for clave, valor in t.original.items():
                print(f"  {clave}: {valor}")
            if not t.valida:
                print(f"  (invalida por: {', '.join(t.errores)})")
            print()
            return
    print("No se encontro ninguna transaccion con ese ID.\n")


OPCIONES = {
    "1": ("Listar todas", listar),
    "2": ("Filtrar por estado", filtrar_por_estado),
    "3": ("Filtrar por moneda", filtrar_por_moneda),
    "4": ("Filtrar por fuente", filtrar_por_fuente),
    "5": ("Ver transacciones invalidas y motivo", mostrar_invalidas),
    "6": ("Ver metricas generales", mostrar_metricas),
    "7": ("Buscar por ID o cliente", buscar),
    "8": ("Ver registro original de una transaccion", ver_registro_original),
}


def menu(transacciones) -> None:
    while True:
        m = calcular_metricas(transacciones)
        print(f"\n=== Transacciones cargadas: {m['total_procesadas']} "
              f"(validas: {m['validas']}, invalidas: {m['invalidas']}) ===")
        for clave, (etiqueta, _) in OPCIONES.items():
            print(f"{clave}) {etiqueta}")
        print("9) Salir")

        opcion = input("> ").strip()
        if opcion == "9":
            print("Hasta luego.")
            break
        if opcion in OPCIONES:
            _, funcion = OPCIONES[opcion]
            funcion(transacciones)
        else:
            print("Opcion no valida.\n")
