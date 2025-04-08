import networkx as nx
import numpy as np
from datetime import time


# Step 3: Dynamic risk adjustment function
def adjust_risk_score(base_risk, current_time, rush_hour_factor=2.0, weekday_factor=1.5, winter_factor=1.5):
    """
    Adjust risk score based on time, day, and month.
    - rush_hour_factor: Multiplier during rush hour.
    - weekday_factor: Multiplier for weekdays.
    - winter_factor: Multiplier for winter months (Dec-Feb).
    """
    rush_hours = [(time(7, 0), time(9, 0)), (time(16, 0), time(18, 0))]
    is_rush_hour = any(start <= current_time.time() <= end for start, end in rush_hours)
    is_weekday = current_time.weekday() < 5  # Monday=0, Sunday=6
    is_winter = current_time.month in [12, 1, 2]

    adjusted_risk = base_risk
    if is_rush_hour:
        adjusted_risk *= rush_hour_factor
    if is_weekday:
        adjusted_risk *= weekday_factor
    if is_winter:
        adjusted_risk *= winter_factor
    
    # return min(adjusted_risk, 1.0)  # Cap at 1.0 (or adjust max as needed)
    return adjusted_risk

# Step 4: A* implementation with dynamic cost
def heuristic(u, v, G):
    """Euclidean distance heuristic for A*."""
    u_x, u_y = G.nodes[u]['pos'][0], G.nodes[u]['pos'][1]
    v_x, v_y = G.nodes[v]['pos'][0], G.nodes[v]['pos'][1]
    return np.sqrt((u_x - v_x) ** 2 + (u_y - v_y) ** 2)

def astar_path(G, start_node, end_node, current_time, alpha=1.0, beta=1.0):
    """
    A* algorithm balancing distance and risk.
    - alpha: Weight for distance.
    - beta: Weight for risk.
    """
    def cost(u, v, d):
        length = float(G[u][v]['length'])
        base_risk = float(G[u][v]['risk_score'])
        adjusted_risk = adjust_risk_score(base_risk, current_time,
                                          rush_hour_factor=2.0, weekday_factor=1.5, winter_factor=1.5)
        # adjusted_risk = base_risk
        return alpha * length + beta * adjusted_risk * length
    
    try:
        path = nx.astar_path(G, start_node, end_node, 
                            heuristic=lambda u, v: heuristic(u, v, G), 
                            weight=cost)
        return path
    except nx.NetworkXNoPath:
        return None

# Step 5: Find nearest nodes to start/end coordinates
def find_nearest_node(G, point):
    #TODO: Implement a more efficient nearest node search, add internal nodes for more accuracy
    coords = [(n, (d['pos'][0], d['pos'][1])) for n, d in G.nodes(data=True)]
    nodes, node_coords = zip(*coords)
    distances = [np.sqrt((x - point[0])**2 + (y - point[1])**2) for x, y in node_coords]
    return nodes[np.argmin(distances)]


# def dijkstra_path(G, start_node, end_node, current_time, alpha=1.0, beta=1.0):
#     """
#     Dijkstra's algorithm implementation balancing distance and risk.
    
#     Parameters:
#     - G: NetworkX graph
#     - start_node: Starting node ID
#     - end_node: Destination node ID
#     - current_time: datetime object for dynamic risk adjustment
#     - alpha: Weight for distance (default: 1.0)
#     - beta: Weight for risk (default: 1.0)
    
#     Returns:
#     - List of nodes representing the shortest path, or None if no path exists
#     """
#     def cost(u, v, d):
#         length = float(G[u][v]['length'])
#         base_risk = float(G[u][v]['risk_score'])
#         adjusted_risk = adjust_risk_score(base_risk, current_time,
#                                           rush_hour_factor=2.0, weekday_factor=1.5, winter_factor=1.5)
#         # adjusted_risk = base_risk
#         # print(f"length: {length}, base_risk: {base_risk}, adjusted_risk: {adjusted_risk}")
#         return alpha * length + beta * adjusted_risk * length
    
#     try:
#         # Using NetworkX's built-in dijkstra_path with our custom cost function
#         path = nx.dijkstra_path(G, start_node, end_node, weight=cost)
#         return path
#     except nx.NetworkXNoPath:
#         return None
