"""
database.py - Gestión de base de datos SQLite para StockGuard (Versión Terminal).
Almacena secciones, ingredientes, movimientos históricos, traspasos y conteos físicos.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stockguard.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ingredientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seccion TEXT NOT NULL,
            nombre TEXT NOT NULL,
            stock_inicial REAL NOT NULL,
            stock_actual REAL NOT NULL,
            stock_fisico REAL NOT NULL,
            stock_minimo REAL NOT NULL,
            stock_alerta REAL NOT NULL,
            precio_kg INTEGER NOT NULL,
            UNIQUE(seccion, nombre)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            dia_semana TEXT NOT NULL,
            turno TEXT NOT NULL,
            seccion TEXT NOT NULL,
            ingrediente TEXT NOT NULL,
            tipo TEXT NOT NULL,
            cantidad REAL NOT NULL,
            responsable TEXT NOT NULL,
            observacion TEXT DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()


def get_all_ingredientes():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM ingredientes ORDER BY seccion, nombre").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_ingredientes_by_seccion(seccion):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM ingredientes WHERE seccion = ? ORDER BY nombre", (seccion,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_movimientos(filtro_seccion=None, filtro_dia=None):
    conn = get_connection()
    query = "SELECT * FROM movimientos WHERE 1=1"
    params = []
    if filtro_seccion and filtro_seccion != "Todas":
        query += " AND seccion = ?"
        params.append(filtro_seccion)
    if filtro_dia and filtro_dia != "Todos":
        query += " AND dia_semana = ?"
        params.append(filtro_dia)
    query += " ORDER BY id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def registrar_movimiento(fecha, dia_semana, turno, seccion, ingrediente, tipo, cantidad, responsable, observacion=""):
    conn = get_connection()
    cur = conn.cursor()

    row = cur.execute(
        "SELECT id, stock_actual, stock_fisico FROM ingredientes WHERE seccion = ? AND nombre = ?",
        (seccion, ingrediente)
    ).fetchone()

    if not row:
        conn.close()
        raise ValueError(f"Ingrediente '{ingrediente}' no encontrado en '{seccion}'.")

    stock_actual = row["stock_actual"]

    if tipo in ("ENTRADA", "TRASPASO_IN"):
        nuevo_stock = round(stock_actual + cantidad, 3)
        cur.execute("UPDATE ingredientes SET stock_actual = ? WHERE id = ?", (nuevo_stock, row["id"]))
    elif tipo in ("SALIDA", "MERMA", "TRASPASO_OUT"):
        if cantidad > stock_actual:
            conn.close()
            raise ValueError(f"Stock insuficiente ({stock_actual:.2f} kg disponibles).")
        nuevo_stock = round(stock_actual - cantidad, 3)
        cur.execute("UPDATE ingredientes SET stock_actual = ? WHERE id = ?", (nuevo_stock, row["id"]))
    elif tipo == "CONTEO_FISICO":
        cur.execute("UPDATE ingredientes SET stock_fisico = ? WHERE id = ?", (round(cantidad, 3), row["id"]))
    else:
        conn.close()
        raise ValueError(f"Tipo de movimiento no válido: {tipo}")

    cur.execute("""
        INSERT INTO movimientos (fecha, dia_semana, turno, seccion, ingrediente, tipo, cantidad, responsable, observacion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (fecha, dia_semana, turno, seccion, ingrediente, tipo, round(cantidad, 3), responsable, observacion))

    conn.commit()
    conn.close()


def agregar_ingrediente(seccion, nombre, stock_inicial, stock_minimo, stock_alerta, precio_kg):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ingredientes (seccion, nombre, stock_inicial, stock_actual, stock_fisico, stock_minimo, stock_alerta, precio_kg)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (seccion, nombre, stock_inicial, stock_inicial, stock_inicial, stock_minimo, stock_alerta, precio_kg))
    conn.commit()
    conn.close()


def traspasar_ingrediente(fecha, dia_semana, turno, origen, destino, ingrediente, cantidad, responsable):
    if origen == destino:
        raise ValueError("La sección de origen y destino deben ser distintas.")
    conn = get_connection()
    cur = conn.cursor()
    orig = cur.execute(
        "SELECT * FROM ingredientes WHERE seccion = ? AND nombre = ?", (origen, ingrediente)
    ).fetchone()
    if not orig:
        conn.close()
        raise ValueError(f"'{ingrediente}' no existe en {origen}.")
    if cantidad > orig["stock_actual"]:
        conn.close()
        raise ValueError(f"Stock insuficiente en {origen} ({orig['stock_actual']:.2f} kg).")

    dest = cur.execute(
        "SELECT * FROM ingredientes WHERE seccion = ? AND nombre = ?", (destino, ingrediente)
    ).fetchone()
    if not dest:
        cur.execute("""
            INSERT INTO ingredientes (seccion, nombre, stock_inicial, stock_actual, stock_fisico, stock_minimo, stock_alerta, precio_kg)
            VALUES (?, ?, 0.0, 0.0, 0.0, ?, ?, ?)
        """, (destino, ingrediente, orig["stock_minimo"], orig["stock_alerta"], orig["precio_kg"]))
    conn.commit()
    conn.close()

    registrar_movimiento(
        fecha, dia_semana, turno, origen, ingrediente, "TRASPASO_OUT", cantidad, responsable,
        f"Traspaso hacia {destino}"
    )
    registrar_movimiento(
        fecha, dia_semana, turno, destino, ingrediente, "TRASPASO_IN", cantidad, responsable,
        f"Recibido desde {origen}"
    )
