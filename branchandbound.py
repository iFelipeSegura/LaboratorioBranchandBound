import json
import heapq
import math
from copy import deepcopy

INF = math.inf
CITIES = ['A', 'B', 'C', 'D', 'E']
N = len(CITIES)

ORIGINAL_MATRIX = [
    [INF, 14,  4, 10, 20],
    [14, INF,  7,  8, 12],
    [4,   5, INF, 16,  3],
    [11,  7,  16, INF,  2],
    [18, 10,   4,  2, INF],
]

def copy_matrix(m):
    return [row[:] for row in m]

def reduce_matrix(matrix):
    """Aplica la reducción de filas y columnas a la matriz."""
    m = copy_matrix(matrix)
    n = len(m)
    total_reduction = 0
    
    # Reducción de filas
    for i in range(n):
        finite_vals = [m[i][j] for j in range(n) if m[i][j] != INF]
        if not finite_vals:
            continue
        row_min = min(finite_vals)
        if row_min > 0:
            total_reduction += row_min
            for j in range(n):
                if m[i][j] != INF:
                    m[i][j] -= row_min
                    
    # Reducción de columnas
    for j in range(n):
        finite_vals = [m[i][j] for i in range(n) if m[i][j] != INF]
        if not finite_vals:
            continue
        col_min = min(finite_vals)
        if col_min > 0:
            total_reduction += col_min
            for i in range(n):
                if m[i][j] != INF:
                    m[i][j] -= col_min
                    
    return m, total_reduction

def get_child_matrix(matrix, from_c, to_c):
    """Invalida fila y columna correspondientes para evitar ciclos."""
    m = copy_matrix(matrix)
    n = len(m)
    for j in range(n):
        m[from_c][j] = INF
    for i in range(n):
        m[i][to_c] = INF
        
    # Previene regresar al inicio prematuramente
    m[to_c][0] = INF  
    return m

def naive_bound_val(matrix):
    """Cota ingenua: suma de los valores mínimos de las filas (sin actualizar columnas)."""
    total = 0
    for i in range(N):
        finite_vals = [matrix[i][j] for j in range(N) if matrix[i][j] != INF]
        if finite_vals:
            total += min(finite_vals)
    return total

class TSPSolver:
    """Clase para encapsular la lógica del algoritmo Branch & Bound para TSP."""
    def __init__(self, cost_matrix, strategy='best_first', use_naive=False):
        self.original_matrix = cost_matrix
        self.strategy = strategy
        self.use_naive = use_naive
        self.node_id_counter = 0
        self.nodes_list = []
        self.node_map = {}
        self.best_cost = INF
        self.best_path = None
        self.heap = []
        self.stack = []

    def make_node(self, path, matrix, cost, parent_id):
        nid = self.node_id_counter
        self.node_id_counter += 1
        path_str = ' → '.join(CITIES[c] for c in path)
        
        node = {
            'id': nid,
            'parent_id': parent_id,
            'path': path[:],
            'path_str': path_str,
            'cost': cost,
            'matrix': matrix,
            'status': 'pending',
            'children': [],
            'level': len(path) - 1,
        }
        self.nodes_list.append(node)
        self.node_map[nid] = node
        return node

    def enqueue(self, node):
        if self.strategy == 'best_first':
            heapq.heappush(self.heap, (node['cost'], node['id']))
        else:
            self.stack.append(node['id'])

    def get_next(self):
        if self.strategy == 'best_first':
            while self.heap:
                _, nid = heapq.heappop(self.heap)
                n = self.node_map[nid]
                if n['status'] == 'pending':
                    return n
        else:
            while self.stack:
                nid = self.stack.pop()
                n = self.node_map[nid]
                if n['status'] == 'pending':
                    return n
        return None

    def solve(self):
        root_matrix, root_cost = reduce_matrix(self.original_matrix)
        root = self.make_node([0], root_matrix, root_cost, None)
        self.enqueue(root)

        while True:
            current = self.get_next()
            if current is None:
                break

            path = current['path']
            matrix = current['matrix']
            cost = current['cost']

            if cost >= self.best_cost:
                current['status'] = 'pruned_cost'
                continue

            # Evaluar si es un camino completo
            if len(path) == N:
                last_city = path[-1]
                actual_ret = matrix[last_city][0]
                
                if actual_ret == INF:
                    if self.original_matrix[last_city][0] == INF:
                        current['status'] = 'pruned_infeasible'
                        continue
                    actual_ret = 0 

                total = cost + (actual_ret if actual_ret != INF else 0)
                if total < self.best_cost:
                    self.best_cost = total
                    self.best_path = path + [0]
                    current['status'] = 'solution'
                    current['final_cost'] = total
                else:
                    current['status'] = 'pruned_cost'
                continue

            current['status'] = 'expanded'
            current_city = path[-1]
            visited = set(path)

            for next_city in range(N):
                if next_city in visited or matrix[current_city][next_city] == INF:
                    continue

                edge_cost = matrix[current_city][next_city]
                child_matrix_raw = get_child_matrix(matrix, current_city, next_city)

                if self.use_naive:
                    child_matrix = child_matrix_raw
                    reduction_cost = naive_bound_val(child_matrix_raw)
                else:
                    child_matrix, reduction_cost = reduce_matrix(child_matrix_raw)

                child_cost = cost + edge_cost + reduction_cost
                child_path = path + [next_city]
                child = self.make_node(child_path, child_matrix, child_cost, current['id'])
                current['children'].append(child['id'])

                if child_cost < self.best_cost:
                    self.enqueue(child)
                else:
                    child['status'] = 'pruned_cost'

        # Limpiar nodos residuales
        for n in self.nodes_list:
            if n['status'] == 'pending':
                n['status'] = 'pruned_cost'

        return self.nodes_list, self.best_cost, self.best_path

# --- Funciones de Exportación ---

def nodes_to_json_export(nodes):
    return [{
        'id': n['id'],
        'parent_id': n['parent_id'],
        'path_str': n['path_str'],
        'cost': n['cost'] if n['cost'] != INF else 9999,
        'status': n['status'],
        'level': n['level'],
        'children': n['children'],
        'final_cost': n.get('final_cost', None),
    } for n in nodes]

def nodes_to_dot(nodes, label):
    color_map = {
        'expanded': 'blue',
        'pruned_cost': 'red',
        'pruned_infeasible': 'orange',
        'solution': 'green',
        'pending': 'gray',
    }
    status_labels = {
        'expanded': 'Expandido',
        'pruned_cost': 'Podado por Cota',
        'pruned_infeasible': 'Podado por Inviabilidad',
        'solution': 'Solución Completa',
        'pending': 'Pendiente',
    }
    
    lines = [f'digraph TSP_{label} {{', '  node [shape=box, fontname="Arial"];']
    
    for n in nodes:
        color = color_map.get(n['status'], 'gray')
        sl = status_labels.get(n['status'], n['status'])
        cost_val = n['cost'] if n['cost'] != INF else '∞'
        extra = f"\\nCosto Final: {n.get('final_cost','')}" if n.get('final_cost') else ''
        lines.append(f'  Node{n["id"]} [label="ID: {n["id"]}\\nCamino: [{n["path_str"]}]\\nCota: {cost_val}\\nEstado: {sl}{extra}", color={color}];')
        
    for n in nodes:
        for cid in n['children']:
            lines.append(f'  Node{n["id"]} -> Node{cid};')
            
    lines.append('}')
    return '\n'.join(lines)


if __name__ == '__main__':
    print("=== Ejecutando Branch & Bound TSP ===\n")

    # 1. Escenario LIFO
    solver_lifo = TSPSolver(ORIGINAL_MATRIX, strategy='lifo')
    nodes_lifo, best_lifo, path_lifo = solver_lifo.solve()
    print(f"LIFO: Óptimo={best_lifo}, Camino={[CITIES[c] for c in path_lifo] if path_lifo else None}, Nodos Totales={len(nodes_lifo)}")

    # 2. Escenario Best First
    solver_bf = TSPSolver(ORIGINAL_MATRIX, strategy='best_first')
    nodes_bf, best_bf, path_bf = solver_bf.solve()
    print(f"BestFirst: Óptimo={best_bf}, Camino={[CITIES[c] for c in path_bf] if path_bf else None}, Nodos Totales={len(nodes_bf)}")

    # 3. Escenario Cota Ingenua
    solver_naive = TSPSolver(ORIGINAL_MATRIX, strategy='best_first', use_naive=True)
    nodes_naive, best_naive, path_naive = solver_naive.solve()
    print(f"Ingenua: Óptimo={best_naive}, Camino={[CITIES[c] for c in path_naive] if path_naive else None}, Nodos Totales={len(nodes_naive)}")

    # 4. Escenario Modificado (Efecto Espejismo)
    MOD_MATRIX = copy_matrix(ORIGINAL_MATRIX)
    MOD_MATRIX[2][4] = 99
    solver_mod = TSPSolver(MOD_MATRIX, strategy='best_first')
    nodes_mod, best_mod, path_mod = solver_mod.solve()
    print(f"Modificado(C->E=99): Óptimo={best_mod}, Camino={[CITIES[c] for c in path_mod] if path_mod else None}, Nodos Totales={len(nodes_mod)}")

    # Guardar archivos localmente (en la misma carpeta donde se ejecute el script)
    archivos_json = [
        ('arbollifo.json', nodes_to_json_export(nodes_lifo)),
        ('arbolbestfirst.json', nodes_to_json_export(nodes_bf)),
        ('arbolnaive.json', nodes_to_json_export(nodes_naive)),
        ('arbolmodified.json', nodes_to_json_export(nodes_mod)),
    ]
    for fname, data in archivos_json:
        with open(fname, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    archivos_dot = [
        ('arbollifo.dot', nodes_to_dot(nodes_lifo, 'LIFO')),
        ('arbolbestfirst.dot', nodes_to_dot(nodes_bf, 'BestFirst')),
        ('arbolnaive.dot', nodes_to_dot(nodes_naive, 'Naive')),
        ('arbolmodified.dot', nodes_to_dot(nodes_mod, 'Modified')),
    ]
    for fname, content in archivos_dot:
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(content)

    print("\nArchivos exportados exitosamente en el directorio actual (.json y .dot).")