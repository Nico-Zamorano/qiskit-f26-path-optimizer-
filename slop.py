"""
Quantum shortest path with Qiskit (QAOA)
=========================================

Finds the cheapest path between two nodes of a weighted graph by:
  1. Writing shortest-path as a binary optimization problem
     (one qubit per directed edge: 1 = "edge is used in the path").
  2. Converting it to a QUBO / Ising Hamiltonian.
  3. Solving it with QAOA on a simulator.
  4. Checking the answer against classical Dijkstra and drawing the
     graph with the optimal path highlighted.

Requirements:
    pip install qiskit qiskit-optimization qiskit-algorithms networkx matplotlib
"""

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

from qiskit.primitives import StatevectorSampler
from qiskit_algorithms import QAOA, NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import COBYLA
from qiskit_algorithms.utils import algorithm_globals
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_optimization.converters import QuadraticProgramToQubo

algorithm_globals.random_seed = 7
np.random.seed(7)

# ----------------------------------------------------------------------
# 1. Toy problem: weighted undirected graph, find cheapest path A -> F
# ----------------------------------------------------------------------
SOURCE, TARGET = "A", "F"

edges = [
    ("A", "B", 4), ("A", "C", 2),
    ("B", "C", 1), ("B", "D", 5),
    ("C", "D", 8), ("C", "E", 10),
    ("D", "E", 2), ("D", "F", 6),
    ("E", "F", 3),
]

G = nx.Graph()
G.add_weighted_edges_from(edges)

# ----------------------------------------------------------------------
# 2. Build the optimization model
#    Variable x_u_v = 1 if the path travels u -> v.
#    Edges into the source / out of the target are never useful,
#    so we drop them to save qubits.
# ----------------------------------------------------------------------
arcs = []
for u, v, w in edges:
    for a, b in [(u, v), (v, u)]:
        if b == SOURCE or a == TARGET:
            continue
        arcs.append((a, b, w))

qp = QuadraticProgram("shortest_path")
var = {}
for a, b, w in arcs:
    name = f"x_{a}_{b}"
    qp.binary_var(name)
    var[(a, b)] = name

# Objective: minimise total weight of selected arcs
qp.minimize(linear={var[(a, b)]: w for a, b, w in arcs})

# Flow conservation: out - in = +1 at source, -1 at target, 0 elsewhere
for node in G.nodes:
    coeffs = {}
    for (a, b), name in var.items():
        if a == node:
            coeffs[name] = coeffs.get(name, 0) + 1
        if b == node:
            coeffs[name] = coeffs.get(name, 0) - 1
    rhs = 1 if node == SOURCE else -1 if node == TARGET else 0
    qp.linear_constraint(linear=coeffs, sense="==", rhs=rhs, name=f"flow_{node}")

# Convert constraints into penalty terms -> unconstrained QUBO
qubo = QuadraticProgramToQubo(penalty=sum(w for *_, w in edges)).convert(qp)
print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
print(f"QUBO uses {qubo.get_num_vars()} qubits\n")

# ----------------------------------------------------------------------
# 3. Solve with QAOA (quantum) and with an exact eigensolver (check)
# ----------------------------------------------------------------------
def decode(result):
    """Turn a solution vector into an ordered list of nodes."""
    chosen = {a: b for (a, b), name in var.items() if result.variables_dict[name] > 0.5}
    path, node = [SOURCE], SOURCE
    while node in chosen and node != TARGET and len(path) <= len(G):
        node = chosen[node]
        path.append(node)
    return path


def path_cost(path):
    return sum(G[u][v]["weight"] for u, v in zip(path, path[1:]))


qaoa = QAOA(sampler=StatevectorSampler(seed=7), optimizer=COBYLA(maxiter=300), reps=3)
qaoa_result = MinimumEigenOptimizer(qaoa).solve(qp)
qaoa_path = decode(qaoa_result)

exact_result = MinimumEigenOptimizer(NumPyMinimumEigensolver()).solve(qp)
exact_path = decode(exact_result)

dijkstra_path = nx.dijkstra_path(G, SOURCE, TARGET)

print(f"QAOA path      : {' -> '.join(qaoa_path)}   cost = {path_cost(qaoa_path)}")
print(f"Exact (QUBO)   : {' -> '.join(exact_path)}   cost = {path_cost(exact_path)}")
print(f"Dijkstra check : {' -> '.join(dijkstra_path)}   cost = {path_cost(dijkstra_path)}")
print("QAOA found the optimal path!" if path_cost(qaoa_path) == path_cost(dijkstra_path)
      else "QAOA did not reach the optimum (try more reps / iterations).")

# ----------------------------------------------------------------------
# 4. Draw the graph with the QAOA path highlighted
# ----------------------------------------------------------------------
pos = {"A": (0, 1), "B": (1.2, 2), "C": (1.2, 0), "D": (2.6, 2), "E": (2.6, 0), "F": (3.8, 1)}
path_edges = set(zip(qaoa_path, qaoa_path[1:])) | set(zip(qaoa_path[1:], qaoa_path))
on_path = [(u, v) for u, v in G.edges if (u, v) in path_edges]
off_path = [(u, v) for u, v in G.edges if (u, v) not in path_edges]

fig, ax = plt.subplots(figsize=(9, 5.5))
nx.draw_networkx_edges(G, pos, edgelist=off_path, width=2, edge_color="#c4c4c4", ax=ax)
nx.draw_networkx_edges(G, pos, edgelist=on_path, width=6, edge_color="#e4572e", ax=ax)

node_colors = ["#2e86ab" if n in (SOURCE, TARGET) else
               "#f3a712" if n in qaoa_path else "#e8e8e8" for n in G.nodes]
nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1300,
                       edgecolors="#333333", linewidths=1.5, ax=ax)
nx.draw_networkx_labels(G, pos, font_size=15, font_weight="bold", ax=ax)
nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "weight"),
                             font_size=12, rotate=False, ax=ax,
                             bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))

ax.set_title(f"Shortest path {SOURCE} → {TARGET} found by QAOA: "
             f"{' → '.join(qaoa_path)}  (total cost {path_cost(qaoa_path)})",
             fontsize=13)
ax.axis("off")
plt.tight_layout()
plt.savefig("shortest_path_qaoa.png", dpi=150)
print("\nSaved figure to shortest_path_qaoa.png")
plt.show()
