# this file is the classical implementation of the shortest path problem, using Dijkstra's algorithm.
# this was researched instead of developed from scratch, as it is a well known and well documented algorithm.
# it used to test the graph.py file and to compare to our quantum implementation of the shortest path problem.

import graph

class Dijkstra:
    def __init__(self, graph):
        self.graph = graph
        self.distances = {node.name: float('inf') for node in graph.nodes}
        self.previous_nodes = {node.name: None for node in graph.nodes}
        self.distances[graph.nodes[0].name] = 0  # Start from the first node

    def find_shortest_path(self, start_node_name, end_node_name):
        unvisited_nodes = set(node.name for node in self.graph.nodes)

        while unvisited_nodes:
            current_node_name = min(unvisited_nodes, key=lambda node_name: self.distances[node_name])
            unvisited_nodes.remove(current_node_name)

            if current_node_name == end_node_name:
                break

            current_node = next(node for node in self.graph.nodes if node.name == current_node_name)
            for edge in self.graph.edges:
                if edge.node1.name == current_node_name or edge.node2.name == current_node_name:
                    neighbor_node = edge.node2 if edge.node1.name == current_node_name else edge.node1
                    new_distance = self.distances[current_node_name] + edge.distance
                    if new_distance < self.distances[neighbor_node.name]:
                        self.distances[neighbor_node.name] = new_distance
                        self.previous_nodes[neighbor_node.name] = current_node_name

        return self._reconstruct_path(start_node_name, end_node_name)

    def _reconstruct_path(self, start_node_name, end_node_name):
        path = []
        current_node_name = end_node_name
        while current_node_name is not None:
            path.append(current_node_name)
            current_node_name = self.previous_nodes[current_node_name]
        path.reverse()
        return path

