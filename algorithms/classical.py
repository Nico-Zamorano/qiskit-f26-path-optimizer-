# this file is the classical implementation of the shortest path problem, using Dijkstra's algorithm.
# this was researched instead of developed from scratch, as it is a well known and well documented algorithm.
# it used to test the graph.py file and to compare to our quantum implementation of the shortest path problem.

import itertools

import graph
import matplotlib.pyplot as plt

from qubo import decode_path

class Dijkstra:
    def __init__(self, map_object):
        self.map = map_object

    def find_shortest_path(self, start_node_name, end_node_name):
        node_names = {node.name for node in self.map.nodes}
        if start_node_name not in node_names or end_node_name not in node_names:
            raise ValueError("Start and end nodes must exist in the map.")

        distances = {name: float("inf") for name in node_names}
        previous_nodes = {name: None for name in node_names}
        distances[start_node_name] = 0
        unvisited_nodes = set(node_names)

        while unvisited_nodes:
            current_node_name = min(
                unvisited_nodes, key=lambda node_name: distances[node_name]
            )
            unvisited_nodes.remove(current_node_name)

            if current_node_name == end_node_name:
                break
            if distances[current_node_name] == float("inf"):
                break

            for edge in self.map.edges:
                if edge.node1.name == current_node_name or edge.node2.name == current_node_name:
                    neighbor_node = edge.node2 if edge.node1.name == current_node_name else edge.node1
                    new_distance = distances[current_node_name] + edge.distance
                    if new_distance < distances[neighbor_node.name]:
                        distances[neighbor_node.name] = new_distance
                        previous_nodes[neighbor_node.name] = current_node_name

        if distances[end_node_name] == float("inf"):
            raise ValueError(
                f"No path exists from {start_node_name} to {end_node_name}."
            )
        return self._reconstruct_path(previous_nodes, end_node_name)

    @staticmethod
    def _reconstruct_path(previous_nodes, end_node_name):
        path = []
        current_node_name = end_node_name
        while current_node_name is not None:
            path.append(current_node_name)
            current_node_name = previous_nodes[current_node_name]
        path.reverse()
        return path

def dijkstra(map_object, start_node_name=None, end_node_name=None):
    """Find and display a map's shortest path, defaulting to its first and last nodes."""
    if not map_object.nodes:
        raise ValueError("The map must contain at least one node.")
    if start_node_name is None:
        start_node_name = map_object.nodes[0].name
    if end_node_name is None:
        end_node_name = map_object.nodes[-1].name
    shortest_path = Dijkstra(map_object).find_shortest_path(
        start_node_name, end_node_name
    )
    graph._plot_graph(map_object, shortest_path)
    return shortest_path

# plot an example using example map from graph.py, and find the shortest path between its first and last nodes A and H
start_node = graph.example_map.nodes[0].name
end_node = graph.example_map.nodes[-1].name
shortest_path = dijkstra(graph.example_map, start_node, end_node)

print("Graph nodes:", [node.name for node in graph.example_map.nodes])
print(
    "Graph edges:",
    [
        (edge.node1.name, edge.node2.name)
        for edge in graph.example_map.edges
    ],
)
print(
    f"Shortest path from {start_node} to {end_node}:",
    " -> ".join(shortest_path), 
)


# brute force method to find the shortest path
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