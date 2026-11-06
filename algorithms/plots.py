import graph
import matplotlib.pyplot as plt

from qubo import build_qubo
from classical import brute_force
import numpy as np
from graph import example_map
from graph import _plot_graph

# plot example map
_plot_graph(example_map, highlighted_path=[])

# brute -force test of the QUBO formulation
start, end = graph.example_map.nodes[0].name, graph.example_map.nodes[-1].name
qp, arcs = build_qubo(graph.example_map, start, end)
print(qp.prettyprint())
x, cost, path = brute_force(qp, arcs, start, end)
print("Brute-force best path:", " -> ".join(path), "| normalized cost:", round(cost, 4))

# Dijkstra's algorithm test of the shortest path
from classical import dijkstra

dijkstra_path = dijkstra(example_map, start, end)
print("Dijkstra's algorithm best path:", " -> ".join(dijkstra_path))