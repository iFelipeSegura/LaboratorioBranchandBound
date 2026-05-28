# # Informe de Laboratorio: Branch & Bound — TSP (5 ciudades)

## Configuración experimental

**Matriz de costos original (asimétrica, 5 ciudades A–E):**

|  | A | B | C | D | E |
|--|---|---|---|---|---|
| A | ∞ | 14 | 4 | 10 | 20 |
| B | 14 | ∞ | 7 | 8 | 12 |
| C | 4 | 5 | ∞ | 16 | 3 |
| D | 11 | 7 | 16 | ∞ | 2 |
| E | 18 | 10 | 4 | 2 | ∞ |

**Función de acotación:** Reducción completa de filas y columnas (Row & Column Reduction). La cota inferior del nodo raíz es **21**.

**Matriz reducida del nodo raíz:**

|  | A | B | C | D | E |
|--|---|---|---|---|---|
| A | ∞ | 8 | 0 | 6 | 16 |
| B | 6 | ∞ | 0 | 1 | 5 |
| C | 0 | 0 | ∞ | 13 | 0 |
| D | 8 | 3 | 14 | ∞ | 0 |
| E | 15 | 6 | 2 | 0 | ∞ |

**Solución óptima:** A → C → E → D → B → A con costo **30**.

---

## Pregunta 4.1 — Anatomía de la poda e incumbente temprana

### Estrategia LIFO (Depth-First)

| Métrica | Valor |
|---------|-------|
| Nodos totales instanciados | 30 |
| Nodos expandidos | 12 |
| Nodos podados | 13 |
| Soluciones completas encontradas | 5 |

**Primera incumbente válida:** El primer nodo de solución completa en LIFO es el **Nodo 10**, con camino `A → E → D → C → B → A` y costo final **57**. Esto ocurre porque LIFO explora en profundidad la rama A→E primero (último encolado), alcanzando hojas antes que estrategias más selectivas.

**Evolución de la incumbente en LIFO:**
- Nodo 10: costo 57 (primera incumbente)
- Nodo 11: costo 40
- Nodo 17: costo 35
- Nodo 18: costo 33
- Nodo 26: costo 30 (óptimo final)

### Estrategia Best-First (Least-Cost)

| Métrica | Valor |
|---------|-------|
| Nodos totales instanciados | 21 |
| Nodos expandidos | 7 |
| Nodos podados | 13 |
| Soluciones completas encontradas | 1 |

**Nodo podado gracias a la incumbente:** En el árbol Best-First, el **Nodo 4** (camino `A → E`, cota = 40) fue creado pero jamás expandido.

**Justificación matemática:**
- La incumbente descubierta en Nodo 20 tiene costo = **30**
- La cota del Nodo 4 es **40**
- Como 40 ≥ 30, se aplica la regla de poda: `cota(N4) ≥ incumbente` → **podado por cota**
- Ningún descendiente de A→E puede superar la solución óptima ya conocida

### Comparación topológica

Best-First reduce el árbol de **30 a 21 nodos** (−30%) y encuentra el óptimo directamente en su única solución completa, mientras que LIFO necesita 5 iteraciones para descender de costo 57 a 30.

---

## Pregunta 4.2 — Sensibilidad ante variaciones de la función de acotación

### Tabla comparativa (Best-First)

| Esquema de acotación | Nodos instanciados | Solución hallada | ¿Óptima? |
|----------------------|-------------------|------------------|----------|
| Cota robusta (reducción completa) | **21** | A→C→E→D→B→A, costo 30 | ✓ Sí |
| Cota ingenua (mínimos independientes) | **29** | A→B→D→E→C→A, costo 36 | ✗ No |

La cota ingenua instancia **38% más nodos** y además falla en encontrar la solución óptima real (costo 30), reportando 36 como su mejor resultado.

### Análisis nivel 3: Nodo A→C→B (id=5 en Best-First)

**Cota robusta:** Al expandir A→C, se elimina fila C y columna B de la matriz reducida, luego se reducen las filas/columnas resultantes. La cota calculada es **30**.

**Cota ingenua:** Se toman los mínimos de cada fila de la matriz residual de forma independiente, sin actualizar columnas: suma de mínimos salientes ≈ **23**. Esta estimación es optimista en exceso porque no penaliza la pérdida de conectividad hamiltoniana.

La diferencia (30 vs 23) en este único nodo ya permite a la cota ingenua explorar ramas que la robusta ya habría descartado.

### Fenómeno de retraso en la poda

Con cota ingenua, los Nodos 9 (`A→C→B→E`, cota=36) y 11 (`A→C→E→D`, cota=35) alcanzan nivel 4 como hojas (Nodos 28 y 27 respectivamente) antes de poder ser podados. En la cota robusta, sus equivalentes ya son podados en nivel 3 por cota ≥ 30.

El camino `A→C→B→E→D` (Nodo 28) se extiende innecesariamente hasta hoja con costo 36. Un análisis combinatorio simple no puede predecir este comportamiento **sin instanciar la matriz reducida** porque:
1. El mínimo saliente de cada ciudad varía según las aristas ya eliminadas
2. La conectividad hamiltoniana impone restricciones cruzadas entre filas y columnas que solo emergen al aplicar la reducción completa
3. La cota ingenua trata cada ciudad como independiente, ignorando que tomar la arista D→X restringe las opciones de X

---

## Pregunta 4.3 — El "Efecto Espejismo" y resiliencia topológica

### Modificación: C→E pasa de 3 a 99

### Comparación primeros 3 niveles

**Nivel 0 — Nodo raíz:**
- Original: cota = 21 (reducción fila C: mín=3, columna E: mín=2)
- Modificado: cota = **20** (la fila C ya tiene mín=4 por arco C→A, columna E tiene mín=2 de D→E)

Los IDs N1, N2, N3, N4 se mantienen con los mismos caminos (A→B, A→C, A→D, A→E) en ambos árboles porque la topología del nivel 1 depende solo de la estructura del grafo, no de los valores internos.

**Nivel 2:**
- N7 (`A→C→E`): pasa de cota=30 (original) a cota=**126** (modificado). El arco C→E=99 suma un penalizador masivo, lo que lo poda inmediatamente.
- N7 (`A→C→E`) en modificado **nunca se expande** (podado por cota), colapsando toda la subestructura bajo C→E.

### Cálculo analítico del nodo raíz modificado

**Matriz modificada antes de reducir:**

|  | A | B | C | D | E |
|--|---|---|---|---|---|
| A | ∞ | 14 | 4 | 10 | 20 |
| B | 14 | ∞ | 7 | 8 | 12 |
| C | 4 | 5 | ∞ | 16 | **99** |
| D | 11 | 7 | 16 | ∞ | 2 |
| E | 18 | 10 | 4 | 2 | ∞ |

**Reducción de filas:**
- Fila A: mín=4 → reducir 4 → [∞,10,0,6,16]
- Fila B: mín=7 → reducir 7 → [7,∞,0,1,5]
- Fila C: mín=4 → reducir 4 → [0,1,∞,12,95]
- Fila D: mín=2 → reducir 2 → [9,5,14,∞,0]
- Fila E: mín=2 → reducir 2 → [16,8,2,0,∞]

Suma filas: 4+7+4+2+2 = **19**

**Reducción de columnas (sobre la matriz fila-reducida):**
- Col A: mín=0 (de C) → no reducir
- Col B: mín=1 (de C) → reducir 1 → [9,∞,0,4,7]
- Col C: mín=0 → no reducir
- Col D: mín=0 → no reducir
- Col E: mín=0 → no reducir

Suma columnas: 0+1+0+0+0 = **1**

**Cota raíz modificada = 19 + 1 = 20** (vs 21 original).

El cambio en C→E de 3 a 99 reduce la cota raíz de 21 a 20 porque la fila C ya no contribuye 3 como mínimo de la columna E — ahora el mínimo de E viene de D→E=2 (sin cambio) y el mínimo de C es su propio arco C→A=4. La naturaleza global de la cota local se evidencia: un cambio en un solo arco afecta la reducción de toda la matriz y, por ende, la cota de todo el espacio de búsqueda.

---

## Archivos entregables

| Archivo | Descripción |
|---------|-------------|
| `bb_tsp.py` | Código fuente Python del algoritmo B&B con instrumentación |
| `lifo_tree.json` | Árbol LIFO completo (30 nodos) |
| `bestfirst_tree.json` | Árbol Best-First (21 nodos) |
| `naive_tree.json` | Árbol con cota ingenua (29 nodos) |
| `modified_tree.json` | Árbol con C→E=99 (21 nodos) |
