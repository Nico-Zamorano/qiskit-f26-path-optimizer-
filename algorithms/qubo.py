# Translates the map from graph.py into a QuadraticProgram (the input Qiskit's QAOA tools expect).
# One binary variable per edge: x_i = 1 means the route uses that edge.
# Cost = total (normalized) distance. Constraints = flow conservation at every node.
# Also contains a brute-force solver to verify the problem BEFORE running any quantum code.

import itertools
from qiskit_optimization import QuadraticProgram


def get_arcs(map_object):
    """Orient each undirected edge toward increasing x. Returns [(from, to, distance), ...]."""
    arcs = []
    for e in map_object.edges:
        a, b = e.node1, e.node2
        if b.x < a.x:
            a, b = b, a
        arcs.append((a.name, b.name, float(e.distance)))
    return arcs


def build_qubo(map_object, start, end, normalize=True):
    """Build the QuadraticProgram. Returns (qp, arcs); arcs[i] matches variable x{i}."""
    arcs = get_arcs(map_object)
    costs = [c for _, _, c in arcs]
    if normalize:  # keeps costs near 0-1 so the QAOA angle landscape is friendlier
        m = max(costs)
        costs = [c / m for c in costs]

    qp = QuadraticProgram("shortest_path")
    for i in range(len(arcs)):
        qp.binary_var(name=f"x{i}")
    qp.minimize(linear=costs)

    # Flow conservation: (edges out) - (edges in) = +1 at start, -1 at end, 0 elsewhere
    for node in map_object.nodes:
        n = node.name
        coeffs = {}
        for i, (u, v, _) in enumerate(arcs):
            if u == n:
                coeffs[f"x{i}"] = coeffs.get(f"x{i}", 0) + 1
            if v == n:
                coeffs[f"x{i}"] = coeffs.get(f"x{i}", 0) - 1
        if not coeffs:
            continue
        rhs = 1 if n == start else (-1 if n == end else 0)
        qp.linear_constraint(linear=coeffs, sense="==", rhs=rhs, name=f"flow_{n}")

    return qp, arcs


def decode_path(x, arcs, start, end):
    """Turn a 0/1 vector into a node list like ['A','B','F','E','H'], or None if not a valid path."""
    nxt = {}
    for i, (u, v, _) in enumerate(arcs):
        if round(x[i]) == 1:
            if u in nxt:  # two edges leaving one node: not a simple path
                return None
            nxt[u] = v
    path, cur = [start], start
    for _ in range(len(arcs) + 1):
        if cur == end:
            return path if len(path) - 1 == sum(round(v) for v in x) else None
        if cur not in nxt:
            return None
        cur = nxt[cur]
        path.append(cur)
    return None


def brute_force(qp, arcs, start, end):
    """Try all 2^E bitstrings. Returns (best_x, best_cost, best_path). Ground truth for the QUBO."""
    best_x, best_cost = None, float("inf")
    for bits in itertools.product([0, 1], repeat=len(arcs)):
        x = list(bits)
        if not qp.get_feasibility_info(x)[0]:
            continue
        cost = qp.objective.evaluate(x)
        if cost < best_cost:
            best_x, best_cost = x, cost
    return best_x, best_cost, decode_path(best_x, arcs, start, end)


if __name__ == "__main__":
    import graph
    start, end = graph.example_map.nodes[0].name, graph.example_map.nodes[-1].name
    qp, arcs = build_qubo(graph.example_map, start, end)
    print(qp.prettyprint())
    x, cost, path = brute_force(qp, arcs, start, end)
    print("Brute-force best path:", " -> ".join(path), "| normalized cost:", round(cost, 4))