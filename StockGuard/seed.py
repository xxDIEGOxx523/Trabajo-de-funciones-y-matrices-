"""
seed.py - Semilla de datos precargados del pub (Lunes a Jueves).
Simula cuatro días de operación real con entradas, salidas, traspasos entre
secciones (Frío <-> Plancha) y conteos físicos con diferencias acumuladas.
"""
import os
from database import DB_PATH, init_db, get_connection

SECCIONES = ["Frío", "Plancha", "Meriendas", "Papas"]

INGREDIENTES_SEMILLA = [
    ("Frío", "Camarón", 4.50, 1.00, 1.80, 14500),
    ("Frío", "Pollo", 2.00, 0.80, 1.40, 5200),
    ("Frío", "Palta", 5.00, 1.20, 2.00, 4800),
    ("Frío", "Salmón", 3.50, 0.80, 1.50, 16900),

    ("Plancha", "Pollo", 11.00, 2.50, 4.00, 5200),
    ("Plancha", "Camarón", 2.20, 1.00, 1.60, 14500),
    ("Plancha", "Carne de Plancha", 7.00, 2.00, 3.50, 11800),
    ("Plancha", "Machas", 3.00, 0.80, 1.50, 15900),

    ("Meriendas", "Pan Brioche", 6.00, 1.50, 2.50, 3200),
    ("Meriendas", "Queso Laminado", 4.00, 1.00, 1.80, 7900),
    ("Meriendas", "Jamón Ahumado", 3.50, 0.80, 1.40, 8400),

    ("Papas", "Papas Fritas", 25.00, 6.00, 10.00, 2400),
    ("Papas", "Posta", 6.50, 1.50, 2.50, 12500),
    ("Papas", "Queso Cheddar", 4.50, 1.00, 1.80, 8900),
    ("Papas", "Cebollín", 2.50, 0.50, 1.00, 3500),
    ("Papas", "Tomate", 4.00, 1.00, 1.80, 2200),
    ("Papas", "Mayonesa", 5.00, 1.20, 2.00, 4100),
]

MOVIMIENTOS_HISTORICOS = [
    # --- LUNES ---
    ("2026-11-16 12:30", "Lunes", "Almuerzo", "Plancha", "Pollo", "SALIDA", 2.20, "C. Muñoz", "Platos calientes almuerzo"),
    ("2026-11-16 14:10", "Lunes", "Almuerzo", "Papas", "Papas Fritas", "SALIDA", 5.50, "J. Soto", "Chorrillanas y acompañamientos"),
    ("2026-11-16 19:45", "Lunes", "Noche", "Frío", "Camarón", "TRASPASO_OUT", 0.60, "M. Rojas", "Traspaso hacia Plancha"),
    ("2026-11-16 19:45", "Lunes", "Noche", "Plancha", "Camarón", "TRASPASO_IN", 0.60, "M. Rojas", "Recibido desde Frío"),
    ("2026-11-16 21:20", "Lunes", "Noche", "Plancha", "Camarón", "SALIDA", 1.10, "C. Muñoz", "Salteados noche"),
    ("2026-11-16 22:00", "Lunes", "Noche", "Papas", "Posta", "SALIDA", 1.10, "J. Soto", "Chorrillanas de posta"),

    # --- MARTES ---
    ("2026-11-17 10:00", "Martes", "Apertura", "Plancha", "Pollo", "ENTRADA", 2.00, "Admin", "Reposición proveedor local"),
    ("2026-11-17 10:15", "Martes", "Apertura", "Papas", "Papas Fritas", "ENTRADA", 10.00, "Admin", "Compra 4 bolsas 2.5 kg"),
    ("2026-11-17 13:40", "Martes", "Almuerzo", "Plancha", "Carne de Plancha", "SALIDA", 1.50, "C. Muñoz", "Churrascos y tablas"),
    ("2026-11-17 18:15", "Martes", "Tarde", "Meriendas", "Pan Brioche", "SALIDA", 1.80, "A. Vega", "Sándwiches tarde"),
    ("2026-11-17 20:30", "Martes", "Noche", "Plancha", "Pollo", "TRASPASO_OUT", 0.80, "C. Muñoz", "Traspaso hacia Frío"),
    ("2026-11-17 20:30", "Martes", "Noche", "Frío", "Pollo", "TRASPASO_IN", 0.80, "C. Muñoz", "Recibido desde Plancha"),
    ("2026-11-17 21:50", "Martes", "Noche", "Frío", "Pollo", "SALIDA", 1.30, "M. Rojas", "Ensaladas César"),

    # --- MIÉRCOLES ---
    ("2026-11-18 13:20", "Miércoles", "Almuerzo", "Frío", "Camarón", "SALIDA", 0.90, "M. Rojas", "Ceviches y entradas"),
    ("2026-11-18 15:00", "Miércoles", "Tarde", "Meriendas", "Queso Laminado", "SALIDA", 1.20, "A. Vega", "Meriendas y completos"),
    ("2026-11-18 20:10", "Miércoles", "Noche", "Plancha", "Machas", "SALIDA", 1.80, "C. Muñoz", "Machas a la parmesana"),
    ("2026-11-18 21:30", "Miércoles", "Noche", "Papas", "Papas Fritas", "SALIDA", 7.50, "J. Soto", "Alta demanda noche"),
    ("2026-11-18 22:15", "Miércoles", "Noche", "Papas", "Posta", "SALIDA", 0.40, "J. Soto", "Papas bravas con posta"),
    ("2026-11-18 23:10", "Miércoles", "Cierre", "Frío", "Palta", "MERMA", 0.45, "M. Rojas", "Merma por oxidación"),

    # --- JUEVES ---
    ("2026-11-19 13:50", "Jueves", "Almuerzo", "Plancha", "Pollo", "SALIDA", 2.00, "C. Muñoz", "Menú ejecutivo"),
    ("2026-11-19 19:30", "Jueves", "Noche", "Frío", "Camarón", "TRASPASO_OUT", 0.40, "M. Rojas", "Traspaso hacia Plancha"),
    ("2026-11-19 19:30", "Jueves", "Noche", "Plancha", "Camarón", "TRASPASO_IN", 0.40, "M. Rojas", "Recibido desde Frío"),
    ("2026-11-19 21:40", "Jueves", "Noche", "Plancha", "Camarón", "SALIDA", 1.30, "C. Muñoz", "Tablas de mariscos"),
    ("2026-11-19 22:00", "Jueves", "Noche", "Plancha", "Carne de Plancha", "SALIDA", 1.00, "C. Muñoz", "Platos calientes"),
    ("2026-11-19 22:30", "Jueves", "Noche", "Papas", "Queso Cheddar", "SALIDA", 1.20, "J. Soto", "Papas cheddar"),
]

CONTEOS_FISICOS_JUEVES = [
    ("Plancha", "Pollo", 7.40, "Diferencia de 0.60 kg detectada al cierre jueves"),
    ("Plancha", "Camarón", 0.65, "Diferencia de 0.15 kg en mariscos"),
    ("Plancha", "Carne de Plancha", 4.20, "Diferencia de 0.30 kg"),
    ("Plancha", "Machas", 1.05, "Diferencia de 0.15 kg"),
    ("Papas", "Posta", 4.65, "Diferencia de 0.35 kg en posta"),
    ("Papas", "Papas Fritas", 20.80, "Diferencia de 1.20 kg (merma fritura/porción)"),
    ("Frío", "Camarón", 2.40, "Diferencia de 0.20 kg"),
]


def cargar_semilla(force_reset=False):
    if force_reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    init_db()
    conn = get_connection()
    cur = conn.cursor()

    if cur.execute("SELECT COUNT(*) FROM ingredientes").fetchone()[0] > 0 and not force_reset:
        conn.close()
        return False

    for sec, nom, s_ini, s_min, s_ale, precio in INGREDIENTES_SEMILLA:
        cur.execute("""
            INSERT INTO ingredientes (seccion, nombre, stock_inicial, stock_actual, stock_fisico, stock_minimo, stock_alerta, precio_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (sec, nom, s_ini, s_ini, s_ini, s_min, s_ale, precio))

    for fecha, dia, turno, sec, ing, tipo, cant, resp, obs in MOVIMIENTOS_HISTORICOS:
        row = cur.execute(
            "SELECT id, stock_actual FROM ingredientes WHERE seccion = ? AND nombre = ?",
            (sec, ing)
        ).fetchone()
        if not row:
            continue
        nuevo = round(row["stock_actual"] + cant, 3) if tipo in ("ENTRADA", "TRASPASO_IN") else round(max(0.0, row["stock_actual"] - cant), 3)
        cur.execute("UPDATE ingredientes SET stock_actual = ?, stock_fisico = ? WHERE id = ?", (nuevo, nuevo, row["id"]))
        cur.execute("""
            INSERT INTO movimientos (fecha, dia_semana, turno, seccion, ingrediente, tipo, cantidad, responsable, observacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (fecha, dia, turno, sec, ing, tipo, cant, resp, obs))

    for sec, ing, fisico, obs in CONTEOS_FISICOS_JUEVES:
        cur.execute("UPDATE ingredientes SET stock_fisico = ? WHERE seccion = ? AND nombre = ?", (fisico, sec, ing))
        cur.execute("""
            INSERT INTO movimientos (fecha, dia_semana, turno, seccion, ingrediente, tipo, cantidad, responsable, observacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("2026-11-19 23:45", "Jueves", "Cierre", sec, ing, "CONTEO_FISICO", fisico, "Encargado", obs))

    conn.commit()
    conn.close()
    return True


if __name__ == "__main__":
    cargar_semilla(force_reset=True)
    print("Base de datos StockGuard inicializada con datos históricos (Lunes a Jueves).")
