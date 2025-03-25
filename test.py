# test_networkx.py
import networkx as nx

print("NetworkX version:", nx.__version__)
print("k_shortest_paths available:", hasattr(nx, 'k_shortest_paths'))

# Create a simple MultiDiGraph
G = nx.MultiDiGraph()
G.add_edge(0, 1, 0, weight=1)
G.add_edge(1, 2, 0, weight=1)
try:
    paths = list(nx.k_shortest_paths(G, 0, 2, k=1, weight='weight'))
    print("Test path:", paths)
except AttributeError as e:
    print("Error:", str(e))