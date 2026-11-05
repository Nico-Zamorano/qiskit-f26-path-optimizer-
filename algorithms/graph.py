#imports

import numpy as np
import matplotlib.pyplot as plt

# this file is dedicated to initializing the graph we plan to use and optimize a path for, both classically and "quantumly". 
# the graph represents a set of nodes and edges, we can imagine nodes as cities and edges as roads. The goal right now to start is to find the shortest path
# between two given nodes, PURELY on distance, later constraints can be added if permitted.

# no qiskit needed

class node:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y

class edge:
    def __init__(self, node1, node2):
        self.node1 = node1
        self.node2 = node2
        self.distance = np.sqrt((node1.x - node2.x)**2 + (node1.y - node2.y)**2)

class map:
    def __init__(self):
        self.nodes = []
        self.edges = []

    def add_node(self, name, x, y):
        new_node = node(name, x, y)
        self.nodes.append(new_node)

    def add_edge(self, node1_name, node2_name):
        node1 = next((node for node in self.nodes if node.name == node1_name), None)
        node2 = next((node for node in self.nodes if node.name == node2_name), None)
        if node1 and node2:
            new_edge = edge(node1, node2)
            self.edges.append(new_edge)

# make an example map to test the graph class
example_map = map()

# nodes
example_map.add_node("A", 0, 0)
example_map.add_node("B", 1, 5)
example_map.add_node("C", 3, 2)
example_map.add_node("D", 5, 10)
example_map.add_node("E", 5, 10)
example_map.add_node("F", 12, 9)
example_map.add_node("G", 13, 2)
example_map.add_node("H", 34, 23)

# edges
example_map.add_edge("A", "B")
example_map.add_edge("B", "C")
example_map.add_edge("A", "C")
example_map.add_edge("C", "D")
example_map.add_edge("D", "E")
example_map.add_edge("H", "B")
example_map.add_edge("B", "F")
example_map.add_edge("A", "G")
example_map.add_edge("G", "H")

# plotting the graph
plot_x = [node.x for node in example_map.nodes]
plot_y = [node.y for node in example_map.nodes]
plt.scatter(plot_x, plot_y)

for edge in example_map.edges:
    plt.plot([edge.node1.x, edge.node2.x], [edge.node1.y, edge.node2.y], 'k-')

plt.title("Example Map")
plt.xlabel("X Coordinate")
plt.ylabel("Y Coordinate")
plt.grid()