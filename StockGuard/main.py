"""
main.py - StockGuard (Versión Exclusiva de Terminal / CLI).
Control de inventario, registro de mermas, motor vectorial y panel del jefe.
No requiere librerías externas: solo Python 3 estándar.
"""
import os
import csv
import random
import datetime

from database import (
    get_all_ingredientes,
    get_ingredientes_by_seccion,
    get_movimientos,
    registrar_movimiento,
    agregar_ingrediente,
    traspasar_ingrediente,
)
from seed import cargar_semilla, SECCIONES
from math_engine import (
    estado_semaforo,
    calcular_vectores,
    construir_matriz_stock,
    obtener_traspasos_grafo,
)


class StockGuardCLI:
    def __init__(self):
        cargar_semilla(force_reset=False)
        self.turno_actual = "Viernes - Noche"
        self.responsable_actual = "Diego Flórez"

    # ---------------- UTILIDADES DE CONSOLA ----------------
    def limpiar(self):
        os.system("cls" if os.name == "nt" else "clear")

    def pausar(self):
        input("\nPresiona [ENTER] para continuar...")

    def formato_clp(self, valor):
        return f"${int(round(valor)):,}".replace(",", ".")

    def encabezado(self, subtitulo):
        self.limpiar()
        print("=" * 78)
        print(f"  SG STOCKGUARD  |  {subtitulo}")
        print(f"  Turno: {self.turno_actual:<20}  Usuario: {self.responsable_actual}")
        print("=" * 78)

    def elegir_opcion(self, minimo, maximo, texto="Selecciona una opción: "):
        while True:
            val = input(texto).strip()
            if val.isdigit() and minimo <= int(val) <= maximo:
                return int(val)
            print(f"  [!] Ingresa un número entre {minimo} y {maximo}.")

    def leer_float(self, texto, permitir_cero=False):
        while True:
            raw = input(texto).strip().replace(",", ".")
            try:
                num = float(raw)
                if num < 0 or (num == 0 and not permitir_cero):
                    print("  [!] El valor debe ser positivo.")
                    continue
                return round(num, 2)
            except ValueError:
                print("  [!] Ingresa un número válido (ej: 1.50).")

    def elegir_seccion(self, titulo="SELECCIONAR SECCIÓN"):
        print(f"\n--- {titulo} ---")
        for i, sec in enumerate(SECCIONES, 1):
            items = get_ingredientes_by_seccion(sec)
            rojos = sum(1 for x in items if estado_semaforo(x["stock_actual"], x["stock_minimo"], x["stock_alerta"]) == "ROJO")
            alerta = f" [ALERTA ROJA: {rojos}]" if rojos else " [OK]"
            print(f"  {i}. {sec:<12} ({len(items)} insumos){alerta}")
        print("  0. Volver")
        op = self.elegir_opcion(0, len(SECCIONES))
        return None if op == 0 else SECCIONES[op - 1]

    def elegir_ingrediente(self, seccion):
        items = get_ingredientes_by_seccion(seccion)
        if not items:
            print("  [!] No hay ingredientes en esta sección.")
            return None
        print(f"\nIngredientes en {seccion}:")
        for i, it in enumerate(items, 1):
            est = estado_semaforo(it["stock_actual"], it["stock_minimo"], it["stock_alerta"])
            print(f"  {i:>2}. {it['nombre']:<20} | Esperado: {it['stock_actual']:>6.2f} kg | Físico: {it['stock_fisico']:>6.2f} kg | [{est}]")
        print("   0. Volver")
        op = self.elegir_opcion(0, len(items))
        return None if op == 0 else items[op - 1]

    # ---------------- MENÚ PRINCIPAL ----------------
    def ejecutar(self):
        while True:
            vec = calcular_vectores()
            self.encabezado("MENÚ PRINCIPAL (Datos precargados Lun-Jue)")
            print(f"  Resumen rápido -> Merma acumulada: {vec['merma_total_kg']:.2f} kg  |  Pérdida (C = M·p): {self.formato_clp(vec['costo_total_clp'])}")
            print("-" * 78)
            print("  1. Ver inventario por sección (Frío / Plancha / Meriendas / Papas)")
            print("  2. Registrar movimiento (Salida / Merma / Entrada + Balanza Digital)")
            print("  3. Registrar conteo físico de cierre (Calcula merma M = S_e - S_r)")
            print("  4. Traspasar insumo entre secciones (Actualiza grafo)")
            print("  5. Panel del Jefe (Alertas semáforo, historial y exportar CSV)")
            print("  6. Motor Matemático (Vectores, Producto Punto, Matriz y Grafo)")
            print("  7. Guía rápida de fórmulas")
            print("  8. Configuración (Cambiar turno / usuario / agregar insumo / reiniciar semilla)")
            print("  0. Salir")
            print("-" * 78)

            op = self.elegir_opcion(0, 8)
            if op == 1:
                self.ver_inventario()
            elif op == 2:
                self.menu_registrar_movimiento()
            elif op == 3:
                self.menu_conteo_fisico()
            elif op == 4:
                self.menu_traspaso()
            elif op == 5:
                self.panel_jefe()
            elif op == 6:
                self.motor_matematico()
            elif op == 7:
                self.guia_formulas()
            elif op == 8:
                self.menu_configuracion()
            elif op == 0:
                print("\nSaliendo de StockGuard. Todos los datos quedaron guardados en stockguard.db.")
                break

    # ---------------- 1. INVENTARIO POR SECCIÓN ----------------
    def ver_inventario(self):
        self.encabezado("INVENTARIO POR SECCIÓN")
        sec = self.elegir_seccion("Elige una sección para ver su stock")
        if not sec:
            return
        items = get_ingredientes_by_seccion(sec)
        self.encabezado(f"INVENTARIO · SECCIÓN {sec.upper()}")
        print(f"{'Ingrediente':<20} {'Esperado':>10} {'Físico':>10} {'Dif (M)':>10} {'Pérdida':>12} {'Estado':>10}")
        print("-" * 78)
        for it in items:
            dif = round(it["stock_actual"] - it["stock_fisico"], 2)
            costo = int(round(max(0.0, dif) * it["precio_kg"]))
            est = estado_semaforo(it["stock_actual"], it["stock_minimo"], it["stock_alerta"])
            print(
                f"{it['nombre']:<20} {it['stock_actual']:>7.2f} kg {it['stock_fisico']:>7.2f} kg "
                f"{dif:>+7.2f} kg {self.formato_clp(costo):>12} {est:>10}"
            )
        if sec == "Plancha":
            print("\n  * Nota: 'Carne de Plancha' se controla separada de 'Posta' (exclusiva de Papas).")
        self.pausar()

    # ---------------- 2. REGISTRAR MOVIMIENTO + BALANZA ----------------
    def menu_registrar_movimiento(self):
        self.encabezado("REGISTRAR MOVIMIENTO DE INVENTARIO")
        sec = self.elegir_seccion("Paso 1: Selecciona la sección")
        if not sec:
            return
        item = self.elegir_ingrediente(sec)
        if not item:
            return

        print(f"\nIngrediente: {item['nombre']} ({sec}) | Stock actual: {item['stock_actual']:.2f} kg")
        print("Tipo de movimiento:")
        print("  1. SALIDA  (Uso normal en cocina: descuenta stock)")
        print("  2. MERMA   (Pérdida/desperdicio directo: descuenta stock)")
        print("  3. ENTRADA (Compra/reposición: suma stock)")
        t_op = self.elegir_opcion(1, 3)
        tipo = {1: "SALIDA", 2: "MERMA", 3: "ENTRADA"}[t_op]

        print("\nModo de ingreso de peso:")
        print("  1. Ingreso manual por teclado (kg)")
        print("  2. Leer desde Balanza Digital (Simulador)")
        m_op = self.elegir_opcion(1, 2)
        if m_op == 2:
            cantidad = round(random.uniform(0.25, 1.85), 2)
            print(f"  [Balanza Digital] Peso detectado: {cantidad:.2f} kg")
        else:
            cantidad = self.leer_float("  Cantidad en kg (ej: 0.75): ")

        op_signo = "+" if tipo == "ENTRADA" else "-"
        nuevo = item["stock_actual"] + cantidad if tipo == "ENTRADA" else item["stock_actual"] - cantidad
        print(f"\n  Fórmula en vivo: {item['stock_actual']:.2f} {op_signo} {cantidad:.2f} = {nuevo:.2f} kg")

        obs = input("  Observación (opcional, ENTER para omitir): ").strip() or "Registro desde terminal cocina"
        conf = input("  ¿Confirmar movimiento? (s/n): ").strip().lower()
        if conf != "s":
            print("  Operación cancelada.")
            self.pausar()
            return

        try:
            ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            dia, turno = [x.strip() for x in self.turno_actual.split("-")]
            registrar_movimiento(ahora, dia, turno, sec, item["nombre"], tipo, cantidad, self.responsable_actual, obs)
            print(f"\n  [OK] {tipo} de {cantidad:.2f} kg registrada en {item['nombre']}. Nuevo stock: {nuevo:.2f} kg.")
        except ValueError as e:
            print(f"\n  [ERROR] {e}")
        self.pausar()

    # ---------------- 3. CONTEO FÍSICO ----------------
    def menu_conteo_fisico(self):
        self.encabezado("REGISTRAR CONTEO FÍSICO DE CIERRE")
        sec = self.elegir_seccion("Selecciona la sección del conteo")
        if not sec:
            return
        item = self.elegir_ingrediente(sec)
        if not item:
            return

        print(f"\n  Stock esperado actual (S_e): {item['stock_actual']:.2f} kg")
        fisico = self.leer_float("  Ingresa el peso físico real contado (S_r) en kg: ", permitir_cero=True)

        merma = round(item["stock_actual"] - fisico, 2)
        costo = int(round(max(0.0, merma) * item["precio_kg"]))
        print(f"\n  Cálculo inmediato:")
        print(f"    M = S_e - S_r = {item['stock_actual']:.2f} - {fisico:.2f} = {merma:+.2f} kg")
        print(f"    C = M × p     = {max(0.0, merma):.2f} × {self.formato_clp(item['precio_kg'])} = {self.formato_clp(costo)}")

        ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        dia, turno = [x.strip() for x in self.turno_actual.split("-")]
        registrar_movimiento(ahora, dia, turno, sec, item["nombre"], "CONTEO_FISICO", fisico, self.responsable_actual, "Conteo físico terminal")
        print("\n  [OK] Conteo físico guardado y merma actualizada.")
        self.pausar()

    # ---------------- 4. TRASPASO ENTRE SECCIONES ----------------
    def menu_traspaso(self):
        self.encabezado("TRASPASO DE INSUMO ENTRE SECCIONES")
        origen = self.elegir_seccion("Sección de ORIGEN")
        if not origen:
            return
        item = self.elegir_ingrediente(origen)
        if not item:
            return

        destinos = [s for s in SECCIONES if s != origen]
        print("\nSección de DESTINO:")
        for i, d in enumerate(destinos, 1):
            print(f"  {i}. {d}")
        d_op = self.elegir_opcion(1, len(destinos))
        destino = destinos[d_op - 1]

        cantidad = self.leer_float(f"Cantidad de '{item['nombre']}' a traspasar (disponible {item['stock_actual']:.2f} kg): ")
        try:
            ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            dia, turno = [x.strip() for x in self.turno_actual.split("-")]
            traspasar_ingrediente(ahora, dia, turno, origen, destino, item["nombre"], cantidad, self.responsable_actual)
            print(f"\n  [OK] Traspaso registrado: {cantidad:.2f} kg de {item['nombre']} ({origen} -> {destino}).")
        except ValueError as e:
            print(f"\n  [ERROR] {e}")
        self.pausar()

    # ---------------- 5. PANEL DEL JEFE ----------------
    def panel_jefe(self):
        while True:
            vec = calcular_vectores()
            items = get_all_ingredientes()
            rojos = [i for i in items if estado_semaforo(i["stock_actual"], i["stock_minimo"], i["stock_alerta"]) == "ROJO"]
            amarillos = [i for i in items if estado_semaforo(i["stock_actual"], i["stock_minimo"], i["stock_alerta"]) == "AMARILLO"]
            movs = get_movimientos()

            self.encabezado("PANEL DEL JEFE · INDICADORES Y REPORTES")
            print(f"  • Pérdida estimada total (C = M·p): {self.formato_clp(vec['costo_total_clp'])}")
            print(f"  • Merma acumulada total:            {vec['merma_total_kg']:.2f} kg")
            print(f"  • Alertas de stock:                 {len(rojos)} ROJAS  |  {len(amarillos)} AMARILLAS")
            print(f"  • Total movimientos registrados:    {len(movs)}")

            if rojos or amarillos:
                print("\n  ALERTAS ACTIVAS:")
                for x in rojos:
                    print(f"    [ROJO]     {x['nombre']} ({x['seccion']}): {x['stock_actual']:.2f} kg <= mín {x['stock_minimo']:.2f} kg")
                for x in amarillos:
                    print(f"    [AMARILLO] {x['nombre']} ({x['seccion']}): {x['stock_actual']:.2f} kg <= alerta {x['stock_alerta']:.2f} kg")

            print("\n  1. Ver últimos 15 movimientos históricos")
            print("  2. Filtrar movimientos por día de la semana")
            print("  3. Exportar historial completo a CSV (reporte_stockguard.csv)")
            print("  0. Volver al menú principal")
            op = self.elegir_opcion(0, 3)

            if op == 0:
                break
            elif op == 1:
                self._imprimir_movimientos(movs[:15])
                self.pausar()
            elif op == 2:
                dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
                for i, d in enumerate(dias, 1):
                    print(f"  {i}. {d}")
                d_sel = dias[self.elegir_opcion(1, len(dias)) - 1]
                self._imprimir_movimientos(get_movimientos(filtro_dia=d_sel))
                self.pausar()
            elif op == 3:
                ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reporte_stockguard.csv")
                with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
                    w = csv.writer(f, delimiter=";")
                    w.writerow(["Fecha", "Día", "Turno", "Sección", "Ingrediente", "Tipo", "Cantidad (kg)", "Responsable", "Observación"])
                    for m in movs:
                        w.writerow([m["fecha"], m["dia_semana"], m["turno"], m["seccion"], m["ingrediente"], m["tipo"], m["cantidad"], m["responsable"], m["observacion"]])
                print(f"\n  [OK] Reporte exportado en: {ruta}")
                self.pausar()

    def _imprimir_movimientos(self, lista):
        print(f"\n{'Fecha':<16} {'Día':<9} {'Sección':<10} {'Ingrediente':<16} {'Tipo':<13} {'Kg':>6}")
        print("-" * 78)
        for m in lista:
            print(f"{m['fecha']:<16} {m['dia_semana']:<9} {m['seccion']:<10} {m['ingrediente']:<16} {m['tipo']:<13} {m['cantidad']:>6.2f}")

    # ---------------- 6. MOTOR MATEMÁTICO ----------------
    def motor_matematico(self):
        vec = calcular_vectores()
        self.encabezado("MOTOR MATEMÁTICO · VECTORES, MATRIZ Y GRAFO")

        print("1) CÁLCULO VECTORIAL:  S_e = S_i + E - U   |   M = S_e - S_r   |   C = M · p\n")
        print(f"{'Componente':<25} {'S_i':>6} {'E':>6} {'U':>6} {'S_e':>6} {'S_r':>6} {'M':>6} {'C (CLP)':>10}")
        print("-" * 78)
        for i in range(len(vec["etiquetas"])):
            print(
                f"{vec['etiquetas'][i]:<25} {vec['S_i'][i]:>6.2f} {vec['E'][i]:>6.2f} {vec['U'][i]:>6.2f} "
                f"{vec['S_e'][i]:>6.2f} {vec['S_r'][i]:>6.2f} {vec['M'][i]:>+6.2f} {self.formato_clp(vec['C_ind'][i]):>10}"
            )
        print("-" * 78)
        print(f"  PRODUCTO PUNTO TOTAL -> Merma: {vec['merma_total_kg']:.2f} kg  |  C = M · p = {self.formato_clp(vec['costo_total_clp'])}")

        print("\n2) MATRIZ DE STOCK ESPERADO (kg) — PRODUCTOS CLAVE:")
        secciones, nombres, matriz = construir_matriz_stock()
        header = f"{'Sección':<11}" + "".join(f"{n[:10]:>11}" for n in nombres)
        print("  " + header)
        for sec in secciones:
            fila = f"{sec:<11}" + "".join(
                f"{matriz[sec][n]:>11.2f}" if matriz[sec][n] is not None else f"{'-':>11}"
                for n in nombres
            )
            print("  " + fila)

        print("\n3) GRAFO DIRIGIDO DE TRASPASOS REGISTRADOS:")
        aristas = obtener_traspasos_grafo()
        if not aristas:
            print("  Sin traspasos registrados.")
        else:
            for (orig, dest, ing), kg in aristas.items():
                print(f"  [{orig}] --({ing}: {kg:.2f} kg)--> [{dest}]")
        print("  [Papas] (Nodo independiente: Posta exclusiva, sin traspasos entrantes)")
        self.pausar()

    # ---------------- 7. GUÍA DE FÓRMULAS ----------------
    def guia_formulas(self):
        self.encabezado("GUÍA RÁPIDA DE FÓRMULAS")
        print("  1. Stock Esperado (Vector S_e):")
        print("       S_e = S_i + E - U")
        print("       Suma stock inicial + entradas/traspasos y resta usos/mermas.\n")
        print("  2. Merma o Diferencia (Vector M):")
        print("       M = S_e - S_r")
        print("       Compara el stock teórico esperado frente al conteo físico real.\n")
        print("  3. Costo Total de Pérdida (Producto Punto):")
        print("       C = M · p = sum(M_k * p_k)")
        print("       Multiplica cada kg faltante por su precio/kg en CLP y suma el total.\n")
        print("  4. Separación de Insumos:")
        print("       Posta pertenece solo a Papas; Carne de Plancha solo a Plancha.")
        self.pausar()

    # ---------------- 8. CONFIGURACIÓN ----------------
    def menu_configuracion(self):
        self.encabezado("CONFIGURACIÓN Y ADMINISTRACIÓN")
        print("  1. Cambiar turno actual")
        print("  2. Cambiar usuario responsable")
        print("  3. Agregar nuevo ingrediente a una sección")
        print("  4. Reiniciar base de datos con semilla histórica (Lunes a Jueves)")
        print("  0. Volver")
        op = self.elegir_opcion(0, 4)

        if op == 1:
            turnos = ["Viernes - Almuerzo", "Viernes - Tarde", "Viernes - Noche", "Viernes - Cierre"]
            for i, t in enumerate(turnos, 1):
                print(f"  {i}. {t}")
            self.turno_actual = turnos[self.elegir_opcion(1, len(turnos)) - 1]
            print(f"  [OK] Turno cambiado a: {self.turno_actual}")
        elif op == 2:
            nom = input("  Ingresa nombre del responsable: ").strip()
            if nom:
                self.responsable_actual = nom
                print(f"  [OK] Usuario activo: {self.responsable_actual}")
        elif op == 3:
            sec = self.elegir_seccion("¿En qué sección agregar el insumo?")
            if sec:
                nom = input("  Nombre del ingrediente: ").strip()
                if nom:
                    s_ini = self.leer_float("  Stock inicial (kg): ")
                    s_min = self.leer_float("  Stock mínimo alerta ROJA (kg): ")
                    s_ale = self.leer_float("  Stock alerta AMARILLA (kg): ")
                    precio = int(self.leer_float("  Precio por kg (CLP): "))
                    try:
                        agregar_ingrediente(sec, nom, s_ini, s_min, s_ale, precio)
                        print(f"  [OK] '{nom}' agregado a {sec}.")
                    except Exception as e:
                        print(f"  [ERROR] {e}")
        elif op == 4:
            if input("  ¿Seguro que deseas restaurar los datos de Lun-Jue? (s/n): ").strip().lower() == "s":
                cargar_semilla(force_reset=True)
                print("  [OK] Base de datos restaurada con éxito.")
        if op != 0:
            self.pausar()


if __name__ == "__main__":
    StockGuardCLI().ejecutar()
