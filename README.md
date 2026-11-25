# SG StockGuard — Control de Inventario y Registro de Mermas

**Proyecto ABPro · Física Mecánica — INACAP**  
**Integrantes:** Diego Xavier Flórez Fernández · Javier Josias Oyarzun Rojas · Jean Carlo Yauri Pasten  
**Especialidad:** Analista Programador

## 1. Problemática y Contexto
En un local de comida (pub) dividido en **cuatro secciones de cocina** (*Frío, Plancha, Meriendas y Papas*), el inventario se realiza diariamente de forma manual en cuadernos separados por área. Esta dinámica genera tres problemas críticos:

1. **Cruce de insumos sin trazabilidad:** Áreas como *Plancha* y *Frío* comparten productos clave (camarones y pollo), dificultando saber qué sección consumió cada kilogramo.
2. **Error humano y fatiga laboral:** Al cierre de turnos extensos, el cansancio reduce la precisión del pesaje y provoca omisiones en el cuaderno (posta, machas y bolsas de papas).
3. **Fugas silenciosas acumulativas:** Los datos dejan de cuadrar entre el lunes y el jueves, generando compras innecesarias y pérdidas económicas invisibles para la administración.

## 2. Solución Propuesta
**StockGuard** es una aplicación de escritorio ejecutable en **Python** con persistencia local en **SQLite**, diseñada para operar en pantalla de cocina y entregar al encargado control en tiempo real sobre:

* Registro táctil de **entradas, salidas y mermas** (con simulador de balanza digital).
* Registro de **traspasos entre secciones** con actualización automática del grafo dirigido.
* Comparación entre **stock esperado y conteo físico real** al cierre del turno.
* **Alertas tipo semáforo** (Verde, Amarillo y Rojo) y **exportación a CSV** desde el Panel del Jefe.
* **Historial precargado de 4 días (Lunes a Jueves)** para simular operación real desde el primer uso.

## 3. Modelo Matemático Aplicado
StockGuard modela el inventario del pub mediante **álgebra lineal (vectores y matrices)** y **teoría de grafos**:

* **Vector de Stock Esperado:** $\vec{S}_e = \vec{S}_i + \vec{E} - \vec{U}$
* **Vector de Merma / Diferencia:** $\vec{M} = \vec{S}_e - \vec{S}_r$
* **Costo Total de Pérdida (Producto Punto):** $C = \vec{M} \cdot \vec{p} = \sum_{k=1}^{n} M_k \cdot p_k$
* **Grafo Dirigido:** Cada sección representa un vértice ($A$: Frío, $B$: Plancha, $C$: Meriendas, $D$: Papas) y cada flecha representa un traspaso trazable de insumos. *Posta* se mantiene exclusiva de *Papas* y *Carne de Plancha* exclusiva de *Plancha*.

## 4. Requisitos y Ejecución
No requiere instalar paquetes externos (`pip install` no es necesario), ya que utiliza únicamente la biblioteca estándar de **Python 3** (`tkinter`, `sqlite3`, `csv`).

1. Descomprime la carpeta `StockGuard_Python`.
2. Abre una terminal dentro de la carpeta del proyecto.
3. Ejecuta:
   ```bash
   python main.py
