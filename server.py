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

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
#CORS(app, resources={r"/find_path": {"origins": "http://localhost:8000"}})
#CORS(app, resources={r"/find_path": {"origins": "http://localhost:8000"}, r"/geocode": {"origins": "http://localhost:8000"}})
#CORS(app, resources={r"/find_path": {"origins": "http://localhost:8000"}, r"/geocode": {"origins": "http://localhost:8000"}, r"/config": {"origins": "http://localhost:8000"}})

# Allow all origins for all endpoints (temporary for debugging)
CORS(app)


#Load road network for Calgary
G = ox.graph_from_place("Calgary, Alberta, Canada", network_type="drive")
print("Road network loaded")
nodes, edges = ox.graph_to_gdfs(G)

# # Load the pre-saved graph from GraphML
# G = ox.load_graphml(filepath="calgary_roads.graphml")
# print("Road network loaded from calgary_roads.graphml")
# nodes, edges = ox.graph_to_gdfs(G)

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
    data = request.get_json()
    start_lat, start_lon = data['start']
    end_lat, end_lon = data['end']
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
    
    start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
    end_node = ox.distance.nearest_nodes(G, end_lon, end_lat)
    print(f"Nearest nodes: start={start_node}, end={end_node}")

    if start_node not in G.nodes or end_node not in G.nodes:
        print("One or both nodes are not in the Calgary road network")
        return jsonify({"error": "One or both points are outside the Calgary road network"}), 400

    try:
        path = nx.shortest_path(G, start_node, end_node, weight='length')
        print(f"Path found with {len(path)} nodes")
    except nx.NetworkXNoPath as e:
        print(f"Unexpected pathfinding error: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    features = []
    for u, v in zip(path[:-1], path[1:]):
        try:
            edge_data = G.get_edge_data(u, v)[0]
            edge_key = (u, v, 0)
            edge_gdf = edges.loc[edge_key]
            geom = edge_gdf.geometry
            # Try multiple attributes for road name
            road_name = edge_gdf.get('name', None)

            if isinstance(road_name, list):
                road_name = road_name[0] if road_name else 'Unnamed Road'
            if pd.isna(road_name):
                road_name = edge_gdf.get('ref', None)
            if pd.isna(road_name):
                road_name = edge_gdf.get('highway', 'Unnamed Road').capitalize()
            print(f"Edge {edge_key}: name={road_name}")
            features.append({
                "type": "Feature",
                "geometry": geom.__geo_interface__,
                "properties": {
                    "osmid": edge_gdf['osmid'],
                    "name": road_name if not pd.isna(road_name) else 'Unnamed Road'  # Nest name under properties
                    # Add other properties as needed (e.g., highway, length)
                }
            })
        except KeyError:
            print(f"Edge {edge_key} not found")
            continue
        except NameError:
            import pandas as pd  # Ensure pandas is imported if not already
            road_name = edge_gdf.get('name', None)
            if pd.isna(road_name):
                road_name = edge_gdf.get('ref', None)
            if pd.isna(road_name):
                road_name = edge_gdf.get('highway', 'Unnamed Road').capitalize()
            if isinstance(road_name, list):
                road_name = road_name[0] if road_name else 'Unnamed Road'
            print(f"Edge {edge_key}: name={road_name}")
            features.append({
                "type": "Feature",
                "geometry": geom.__geo_interface__,
                "properties": {
                    "osmid": edge_gdf['osmid'],
                    "name": road_name if not pd.isna(road_name) else 'Unnamed Road'
                }
            })

    path_geojson = {"type": "FeatureCollection", "features": features}
    print(f"Returning JSON: {json.dumps(path_geojson)}")  # Debug the exact JSON string
    return jsonify(path_geojson)

if __name__ == '__main__':
    app.run(debug=True, port=5000)