from flask import Flask, request, jsonify
from flask_cors import CORS
import osmnx as ox
import networkx as nx
import geopandas as gpd
import json
import pandas as pd
from dotenv import load_dotenv
import requests
import os
import math
from alternate_pathfinding import find_alternate_paths
from chatbot import *
from find_path import find_nearest_node, dijkstra_path, adjust_risk_score, astar_path
from datetime import datetime
from pyproj import Transformer
import pickle


# Print NetworkX version for debugging 
# print("NetworkX version in server.py:", nx.__version__)
# print("k_shortest_paths available in server.py:", hasattr(nx, 'k_shortest_paths'))

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
#CORS(app, resources={r"/find_path": {"origins": "http://localhost:8000"}})
#CORS(app, resources={r"/find_path": {"origins": "http://localhost:8000"}, r"/geocode": {"origins": "http://localhost:8000"}})
#CORS(app, resources={r"/find_path": {"origins": "http://localhost:8000"}, r"/geocode": {"origins": "http://localhost:8000"}, r"/config": {"origins": "http://localhost:8000"}})
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})

# Allow all origins for all endpoints (temporary for debugging)
#CORS(app)


# #Load road network for Calgary
# G = ox.graph_from_place("Calgary, Alberta, Canada", network_type="drive")
# print("Road network loaded")
# nodes, edges = ox.graph_to_gdfs(G)

# Load the precomputed graph
# print("Loading precomputed graph...")
# try:
#     G = ox.load_graphml("calgary_roads.graphml")
#     print("Graph loaded successfully")
# except Exception as e:
#     print(f"Error loading graph: {str(e)}")
#     raise

# nodes, edges = ox.graph_to_gdfs(G)
# print("Nodes and edges converted to GeoDataFrames")

# Load the precomputed graph
print("Loading precomputed graph...")
G = pickle.load(open("./road_network_processed.pkl", "rb")) 
print("Graph Loaded.")


@app.route('/')
def test():
    return "Backend is running!"

@app.route('/config', methods=['GET'])
def get_config():
    return jsonify({
        "mapboxAccessToken": os.getenv('MAPBOX_ACCESS_TOKEN'),
        "geoapifyApiKey": os.getenv('GEOAPIFY_API_KEY')
    })

# Geocoding endpoint using Geoapify API
@app.route('/geocode', methods=['POST'])
def geocode():
    geoapify_api_key = os.getenv('GEOAPIFY_API_KEY')
    if not geoapify_api_key:
        return jsonify({"error": "Geoapify API key not configured"}), 500
    data = request.get_json()
    location = data['location']
    url = f"https://api.geoapify.com/v1/geocode/search?text={location}&limit=1&apiKey={geoapify_api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Geocoding failed: {str(e)}"}), 500

@app.route('/find_path', methods=['POST'])
def find_path():
     
    """
    Find the shortest path between two coordinates using A* (or Dijkstra) algorithm.      
    """

    data = request.get_json()
    start_lat, start_lon = data['start'] # [lat, lon]
    end_lat, end_lon = data['end']       # [lat, lon]
    start_coords = (start_lon, start_lat)
    end_coords = (end_lon, end_lat)

    print(f"Received: start={start_lat},{start_lon}, end={end_lat},{end_lon}")
 
     # Validate coordinates are within Calgary bounds (approx)
    calgary_bounds = {
         'min_lat': 50.842, 'max_lat': 51.212,
         'min_lon': -114.315, 'max_lon': -113.860
    }
    if not (calgary_bounds['min_lat'] <= start_lat <= calgary_bounds['max_lat'] and
            calgary_bounds['min_lon'] <= start_lon <= calgary_bounds['max_lon']):
        print("Start point is outside Calgary bounds")
        return jsonify({"error": "Start point is outside Calgary bounds"}), 400
    
    if not (calgary_bounds['min_lat'] <= end_lat <= calgary_bounds['max_lat'] and
             calgary_bounds['min_lon'] <= end_lon <= calgary_bounds['max_lon']):
        print("End point is outside Calgary bounds")
        return jsonify({"error": "End point is outside Calgary bounds"}), 400

    # Convert coordinates from WGS84 to UTM Zone 11N
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32611", always_xy=True)
    start_coords_utm = transformer.transform(start_coords[0], start_coords[1])
    end_coords_utm = transformer.transform(end_coords[0], end_coords[1])
   
    start_node = find_nearest_node(G, start_coords_utm)
    end_node = find_nearest_node(G, end_coords_utm)
    
    print(f"Nearest nodes: start={start_node}, end={end_node}")

    if start_node not in G.nodes or end_node not in G.nodes:
        print("One or both nodes are not in the Calgary road network")
        return jsonify({"error": "One or both points are outside the Calgary road network"}), 400

    # Find the shortest path using Dijkstra's algorithm
    try:
        #path = nx.shortest_path(G, start_node, end_node, weight='length')
        #path = nx.shortest_path(G, start_node, end_node, weight='travel_time')
        
        current_time = datetime(2025, 4, 2, 17, 0)  #TODO: Get current time from request or use a default value
        # current_time =datetime.now()  # Get the current time
        
        path = astar_path(G, start_node, end_node, current_time, alpha=10.0, beta=10.0)
        #path = dijkstra_path(G, start_node, end_node, current_time, alpha=1.0, beta=1.0)

        print(f"Path found with {len(path)} nodes")
    except nx.NetworkXNoPath as e:
        print(f"Unexpected pathfinding error: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    # Extract and visualize the route
    if path:
        route_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
        route_gdf = gpd.GeoDataFrame(
            [G[u][v] for u, v in route_edges],
            geometry=[G[u][v]["geometry"] for u, v in route_edges],
            crs='epsg:32611'
        )
        route_gdf_4326 = route_gdf.to_crs('epsg:4326')

        # route_gdf.plot()
        # plt.show()

        # Calculate total distance and risk
        total_length = sum(G[u][v]["length"] for u, v in route_edges)
        total_risk = sum(adjust_risk_score(G[u][v]["risk_score"], current_time)
                        for u, v in route_edges)
        


        # Count risk categories along the path
        risk_categories = [G[u][v]["risk_category"] for u, v in route_edges]
        risk_category_counts = {}
        for category in risk_categories:
            risk_category_counts[category] = risk_category_counts.get(category, 0) + 1
        
        print(f"Path found: {len(path)} nodes")
        print(f"Total distance: {total_length:.2f} meters") 
        print(f"Total adjusted risk: {total_risk:.2f}")
        print(f"Risk category counts:")

        for category, count in risk_category_counts.items():
            print(f"  {category}: {count}")
        total_travel_time = 0  # In ?
        total_length = 0  # In meters

        # Convert route_gdf_4326 to GeoJSON features
        features = []
        for idx, row in route_gdf_4326.iterrows():
            # Get the road name from the attributes
            # Try multiple attributes for road name
            road_name = row.get('name', None)
            if isinstance(road_name, list):
                road_name = road_name[0] if road_name else 'Unnamed Road'
            if pd.isna(road_name):
                road_name = row.get('ref', None)
            if pd.isna(road_name):
                road_name = row.get('highway', 'Unnamed Road').capitalize()

            # Accumulate travel time and distance
            total_travel_time += row.get('travel_time', 0)
            total_length += row.get('length', 0)

            features.append({
                "type": "Feature",
                "geometry": row.geometry.__geo_interface__,
                "properties": {
                    "osmid": row.get('road_id', None),
                    "name": road_name if not pd.isna(road_name) else 'Unnamed Road',
                    "length": row.get('length', None),
                    "travel_time": row.get('travel_time', None),
                    "total_risk": row.get('total_risk', None),
                    "risk_category": row.get('risk_category', None)
                }
            })
    else:
        print("No path found.")
        return None

    path_geojson = {"type": "FeatureCollection", "features": features}
    path_geojson = {
        "type": "FeatureCollection",
        "features": features,
        "properties": {
            "total_length": total_length,  # Add total length to the GeoJSON
            "total_travel_time": total_travel_time,  # Include total travel time
            "total_risk": total_risk,  # Include total risk
            "risk_category_counts": risk_category_counts,  # Include risk category counts
        }
    }
    # print(f"Returning JSON: {json.dumps(path_geojson)}")  # Debug the exact JSON string
    return jsonify(path_geojson)

    

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle chatbot requests.
    """
    try:
        data = request.get_json()
        user_input = data.get('message', '')
        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        geoapify_api_key = os.getenv('GEOAPIFY_API_KEY')
        if not geoapify_api_key:
            return jsonify({"error": "Geoapify API key not configured"}), 500

        # Process the chat message
        result = process_chat_message(user_input, geoapify_api_key)
        if isinstance(result, dict):
            return jsonify(result)
        else:
            return jsonify({"response": result})
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)