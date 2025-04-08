from flask import Flask, request, jsonify, send_from_directory
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
from find_path import find_nearest_node, adjust_risk_score, astar_path
from datetime import datetime
from dateutil.parser import parse as parse_datetime
from pyproj import Transformer
import pickle

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})

print("Loading precomputed graph...")
G = pickle.load(open(os.path.join(os.path.dirname(__file__), "road_network_processed.pkl"), "rb"))
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
    start_coords = (start_lon, start_lat)
    end_coords = (end_lon, end_lat)

    print(f"Received: start={start_lat},{start_lon}, end={end_lat},{end_lon}")

    calgary_bounds = {
        'min_lat': 50.842, 'max_lat': 51.212,
        'min_lon': -114.315, 'max_lon': -113.860
    }
    if not (calgary_bounds['min_lat'] <= start_lat <= calgary_bounds['max_lat'] and
            calgary_bounds['min_lon'] <= start_lon <= calgary_bounds['max_lon']):
        return jsonify({"error": "Start point is outside Calgary bounds"}), 400

    if not (calgary_bounds['min_lat'] <= end_lat <= calgary_bounds['max_lat'] and
            calgary_bounds['min_lon'] <= end_lon <= calgary_bounds['max_lon']):
        return jsonify({"error": "End point is outside Calgary bounds"}), 400

    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32611", always_xy=True)
    start_coords_utm = transformer.transform(start_coords[0], start_coords[1])
    end_coords_utm = transformer.transform(end_coords[0], end_coords[1])

    start_node = find_nearest_node(G, start_coords_utm)
    end_node = find_nearest_node(G, end_coords_utm)

    print(f"Nearest nodes: start={start_node}, end={end_node}")

    if start_node not in G.nodes or end_node not in G.nodes:
        return jsonify({"error": "One or both points are outside the Calgary road network"}), 400

    try:
        time_str = data.get('time')
        if time_str:
           current_time = parse_datetime(time_str)
        else:
           current_time = datetime.now()

        path = astar_path(G, start_node, end_node, current_time, alpha=0.1, beta=0.9)
    except nx.NetworkXNoPath as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    if path:
        print(f"Path found with {len(path)} nodes")

        route_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
        print(f"Path found: {len(route_edges)} edges")

        route_gdf = gpd.GeoDataFrame(
            [G[u][v] for u, v in route_edges],
            geometry=[G[u][v]["geometry"] for u, v in route_edges],
            crs='epsg:32611'
        )
        route_gdf_4326 = route_gdf.to_crs('epsg:4326')

        total_length = sum(G[u][v]["length"] for u, v in route_edges)
        total_risk = sum(adjust_risk_score(G[u][v]["risk_score"], current_time) for u, v in route_edges)

        print(f"Total distance: {total_length:.2f} meters")
        print(f"Total adjusted risk: {total_risk:.2f}")

        risk_categories = [G[u][v]["risk_category"] for u, v in route_edges]
        risk_category_counts = {}
        for category in risk_categories:
            risk_category_counts[category] = risk_category_counts.get(category, 0) + 1

        print("Risk category counts:")
        for category, count in risk_category_counts.items():
            print(f"  {category}: {count}")

        total_travel_time = 0
        features = []
        for idx, row in route_gdf_4326.iterrows():
            road_name = row.get('name', None)
            if isinstance(road_name, list):
                road_name = road_name[0] if road_name else 'Unnamed Road'
            if pd.isna(road_name):
                road_name = row.get('ref', None)
            if pd.isna(road_name):
                road_name = row.get('highway', 'Unnamed Road').capitalize()

            total_travel_time += row.get('travel_time', 0)
            total_length += row.get('length', 0)

            features.append({
                "type": "Feature",
                "geometry": row.geometry.__geo_interface__,
                "properties": {
                    "osmid": row.get('road_id', None),
                    "name": road_name,
                    "length": row.get('length', None),
                    "travel_time": row.get('travel_time', None),
                    "total_risk": row.get('total_risk', None),
                    "risk_category": row.get('risk_categ', None)
                }
            })
    else:
        return None

    path_geojson = {
        "type": "FeatureCollection",
        "features": features,
        "properties": {
            "total_length": total_length,
            "total_travel_time": total_travel_time,
            "total_risk": total_risk,
            "risk_category_counts": risk_category_counts,
        }
    }
    return jsonify(path_geojson)
#-----

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_input = data.get('message', '')
        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        geoapify_api_key = os.getenv('GEOAPIFY_API_KEY')
        if not geoapify_api_key:
            return jsonify({"error": "Geoapify API key not configured"}), 500

        result = process_chat_message(user_input, geoapify_api_key)
        if isinstance(result, dict):
            return jsonify(result)
        else:
            return jsonify({"response": result})
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route('/road_segments')
def serve_road_segments():
    return send_from_directory('static', 'road_segments.geojson')

@app.route('/accidents')
def serve_accidents():
    return send_from_directory('static', 'accidents.geojson')

@app.route('/config.js')
def serve_config_js():
    return send_from_directory('static', 'config.js')

@app.route('/chatbot.js')
def serve_chatbot_js():
    return send_from_directory('static', 'chatbot.js')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
