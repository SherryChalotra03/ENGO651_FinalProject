import osmnx as ox


# Load road network for Calgary
place_name = "Calgary, Alberta, Canada"
G = ox.graph_from_place(place_name, network_type="drive")

# Save the graph to a file
# nx.write_gpickle(G, "./Datasets/Subset/calgary_graph.gpickle")

# print("Graph saved to calgary_graph.gpickle")
# Print basic graph information
print("\nGraph attributes:")
print(f"Number of nodes: {len(G.nodes())}")
print(f"Number of edges: {len(G.edges())}")

# Print node attributes
print("\nNode attributes:")
for key in G.nodes[list(G.nodes())[0]].keys():
    print(f"- {key}")

# Print edge attributes
print("\nEdge attributes:")
first_edge = list(G.edges(data=True))[0]
for key in first_edge[2].keys():
    print(f"- {key}")

# Convert graph to GeoDataFrame
nodes, edges = ox.graph_to_gdfs(G)
edges.drop(columns=['osmid'], inplace=True)
# Convert maxspeed to numeric, replacing invalid values with 50
def convert_maxspeed(speed):
    try:
        # Try to convert to float
        return float(speed)
    except (ValueError, TypeError):
        # Return 50 if conversion fails or speed is None
        return 30.0

edges['maxspeed'] = edges['maxspeed'].apply(convert_maxspeed)

# Print column data types before saving
print("\nEdge columns data types:")
print(edges.dtypes)

# Convert list columns to string representation
for column in edges.columns:
    if edges[column].dtype == 'object' and edges[column].apply(lambda x: isinstance(x, list)).any():
        edges[column] = edges[column].apply(lambda x: str(x) if isinstance(x, list) else x)

# Save to shapefiles
nodes.to_file("./Datasets/Subset/calgary_nodes.shp")
edges.to_file("./Datasets/Subset/calgary_edges.shp")

print("\nGraph exported to shapefiles:")
print("- Nodes saved to calgary_nodes.shp")
print("- Edges saved to calgary_edges.shp")
