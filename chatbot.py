# chatbot.py
import re
import requests
import json

def parse_user_input(user_input):
    """
    Parse the user's input to extract start and end locations.
    Returns a tuple (start_location, end_location).
    """
    # Simple rule-based parsing: look for "from" and "to"
    #user_input = user_input.lower().strip()
    
    user_input = user_input.strip()
    user_input_lower = user_input.lower()
    
    # Patterns to match "from X to Y" or similar phrases
    # pattern = r"(?:from|starting at)\s+(.+?)\s+(?:to|ending at)\s+(.+?)(?:\s|$)"
    # match = re.search(pattern, user_input)
    
    pattern = r"(?:from|starting at)\s+(.+?)\s+(?:to|ending at)\s+(.+)$"
    match = re.search(pattern, user_input_lower, re.IGNORECASE)
    
    if match:
        start_location = match.group(1).strip()
        end_location = match.group(2).strip()
        
        # Restore the original case from the user input
        start_idx = user_input_lower.find(start_location)
        end_idx = user_input_lower.find(end_location)
        start_location = user_input[start_idx:start_idx + len(start_location)]
        end_location = user_input[end_idx:end_idx + len(end_location)]
        
        return start_location, end_location
    
    # Fallback: split by " to " if the pattern doesn't match
    if " to " in user_input:
        parts = user_input.split(" to ", 1)  # Split only on the first " to "
        if len(parts) == 2:
            start_location = parts[0].replace("from ", "", 1).strip()
            end_location = parts[1].strip()
            return start_location, end_location
    
    # If parsing fails, return None
    return None, None

def geocode_location(location, geoapify_api_key):
    """
    Geocode a location name to coordinates using the Geoapify API.
    Returns a tuple (latitude, longitude) or None if geocoding fails.
    """
    url = f"https://api.geoapify.com/v1/geocode/search?text={location}&limit=1&apiKey={geoapify_api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data['features'] and len(data['features']) > 0:
            coords = data['features'][0]['geometry']['coordinates']
            return coords[1], coords[0]  # [lat, lon]
        return None
    except requests.exceptions.RequestException as e:
        print(f"Geocoding failed for {location}: {str(e)}")
        return None

def find_route(start_coords, end_coords):
    """
    Find a route between start_coords and end_coords using the /find_path endpoint.
    Returns the route GeoJSON or None if the request fails.
    """
    url = "http://localhost:5000/find_path"
    payload = {
        "start": start_coords,
        "end": end_coords
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Pathfinding failed: {str(e)}")
        return None

def format_route_response(route_geojson, start_location, end_location):
    """
    Format the route GeoJSON into a conversational response.
    Returns a string with the route plan , formatted as an HTML list.
    """
    if not route_geojson or 'features' not in route_geojson or not route_geojson['features']:
        return "I couldn't find a route between those locations. Please try different points or check if they are within Calgary."

    # Extract road names and length from the route
    roads = []
    total_length = route_geojson.get('properties', {}).get('total_length', 0)
    for feature in route_geojson['features']:
        road_name = feature['properties'].get('name', 'Unnamed Road')
        length = feature['properties'].get('length', 0)
        roads.append({
            "name": road_name,
            "length": length
        })
    
    # Remove duplicates while preserving order
    seen = set()
    unique_roads = [road for road in roads if not (road['name'] in seen or seen.add(road['name']))]

    if not unique_roads:
        return "I found a route, but I couldn't identify the road names."

    # Format the response
    response = f"Here’s your route from {start_location} to {end_location}:\n"
    for i, road in enumerate(unique_roads, 1):
        response += f"<li>Step {i}: Travel on {road['name']} ({(road['length'] / 1000):.2f} km)</li>"
    response += f"</ul><br><b>Total Distance: {(total_length / 1000):.2f} km</b>"
    
    return response

def process_chat_message(user_input, geoapify_api_key):
    """
    Process the user's chat message and return a response.
    """
    # Step 1: Parse the user input
    start_location, end_location = parse_user_input(user_input)
    if not start_location or not end_location:
        return "I couldn't understand your request. Please use a format like 'Find a route from Calgary Tower to University Station, Calgary'."

    # Step 2: Geocode the locations
    # Append ", Calgary, AB" if "Calgary" is not in the location name
    if "calgary" not in start_location.lower():
        start_location = f"{start_location}, Calgary, AB"
    if "calgary" not in end_location.lower():
        end_location = f"{end_location}, Calgary, AB"
        
    print(f"Geocoding start location: {start_location}")
    print(f"Geocoding end location: {end_location}")

    start_coords = geocode_location(start_location, geoapify_api_key)
    if not start_coords:
        return f"I couldn't find the location '{start_location}'. Please try a more specific address."

    end_coords = geocode_location(end_location, geoapify_api_key)
    if not end_coords:
        return f"I couldn't find the location '{end_location}'. Please try a more specific address."

    print(f"Start coordinates: {start_coords}")
    print(f"End coordinates: {end_coords}")
    
    # Step 3: Find the route
    route_geojson = find_route(start_coords, end_coords)
    if not route_geojson:
        return "I couldn't find a route between those locations. Please try different points or check if they are within Calgary."

    # Step 4: Format the response
    response = format_route_response(route_geojson, start_location, end_location)
    return {"success": True, "response": response, "route_geojson": route_geojson, "start_coords": start_coords, "end_coords": end_coords}