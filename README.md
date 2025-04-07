# ENGO651_FinalProject: Calgary Safe Way - Intelligent Route Planning

## Overview: 
Calgary Safe Way is an intelligent route planning application designed for the city of Calgary, Alberta, Canada. It helps users find the safest and most efficient driving routes by considering road risk levels and historical accident data. The application features a web-based interface with a Leaflet map, a chatbot for natural language route requests, and a backend powered by Flask and NetworkX for pathfinding. Road segments and accidents are visualized using custom tilesets created in Mapbox Studio.

## Project Structure

- `server.py`: Flask backend for route calculation and API key serving.
- `index.html`: Main HTML file for the frontend.
- `script.js`: JavaScript file handling map interactions, geocoding, and route display.
- `styles.css`: CSS for styling the map and sidebar.
- `chatbot.css`: Styles for the chatbot interface
- `chatbot.py`: Chatbot logic for processing natural language requests
- `find_path.py`: Pathfinding logic (A* and Dijkstra’s algorithms)
- `calgary_roads.geojson`: GeoJSON file containing Calgary’s road network.
- `calgary_roads_geojson.ipynb`: Jupyter Notebook to generate `calgary_roads.geojson` (optional).
- `.env`: Environment file for storing API keys.
- `road_network_processed.pkl`: Precomputed NetworkX graph of Calgary’s road network
- `road_risk_layer_categorized.shp`: Shapefile for road segments with risk categories
- `requirements.txt`: Python dependencies
- `README.md`: Project documentation
    
## Setup Instructions

### 1. Clone the Repository
         
### 2. Set Up the Backend (Flask)
- Create a Virtual Environment:
    - python -m venv venv
    - source venv/bin/activate  # On Windows: venv\Scripts\activate
 
- Install Dependencies: pip install -r requirements.txt
- Set Up Environment Variables (Create .env file in project root and replace the placeholders with youractual keys)
    - MAPBOX_ACCESS_TOKEN=your_mapbox_access_token_here
    - GEOAPIFY_API_KEY=your_geoapify_api_key_here
 
- Run the Flask Server: python server.py
The server will run on http://localhost:5000. You should see Road network loaded in the terminal.

### 3. Set Up the Frontend
- Navigate to the Project Directory
- Start a Simple HTTP Server: In seperate terminal, start the server using python -m http.server 8000
- Open the Application: Open your browser and go to http://localhost:8000. The map should load, centered on Calgary.

### 4. Required files
- calgary_roads.geojson: Contains the road network data for Calgary. If missing, generate it using the provided calgary_roads_geojson.ipynb notebook (requires Jupyter Notebook and OSMnx).
- index.html, script.js, styles.css: Core frontend files.

### 5. Usage
- **Interact with the Map**
    - **Click on the Map:** Click to set a start point (green marker), then click again to set an end point (red marker). The route will be calculated automatically.
    - **Enter Locations:** Use the sidebar to enter start and end locations (e.g., "Calgary Tower" or "154 SE Rosebrook Rise, Calgary"). Click "Find Path" to calculate the route.
    - **Manual Coordinates:** Enter latitude and longitude manually in the sidebar if preferred.
    - **Chatbot:** Use the Route Assistant (bottom right) to type your request, e.g., "Find a route from Calgary Tower to University Station, Calgary."

 - **View the Route:**
    - The calculated route will be displayed in blue on the map.
    - The Route Plan pane will list the roads to travel on, their distances, and the total distance and travel time.
    - Click on a road segment or accident marker to see more details (e.g., risk category, accident severity).

- **Reset the Map:**
    - Click the "Reset" button or press the R key to clear the markers and route, resetting the map to its initial state.
 
## Features

### 1. Route Planning and Pathfinding

- **Shortest Path Calculation:** Finds the shortest path between two points in Calgary using A* or Dijkstra’s algorithm, balancing distance and risk.
- **Risk-Aware Routing:** Adjusts route risk dynamically based on:
    - **Time of Day:** Higher risk during rush hours (7–9 AM, 4–6 PM) with a configurable rush_hour_factor.
    - **Day of the Week:** Higher risk on weekdays with a weekday_factor.
    - **Season:** Higher risk in winter months (December–February) with a winter_factor.
- **Customizable Cost Function:** Allows tuning the balance between distance (alpha) and risk (beta) in the pathfinding algorithm.
**Precomputed Road Network:** Uses a precomputed NetworkX graph (road_network_processed.pkl) for efficient pathfinding in Calgary.

### 2. 2. Interactive Map Interface

- **Leaflet Map:** Displays an interactive map of Calgary using Leaflet (leaflet@1.9.4) with Mapbox tiles.
- **Custom Mapbox Style:** Integrates a custom Mapbox Studio style for visualizing:
    - **Road Segments:** Colored by risk category (e.g., green for "Low", yellow for "Medium", red for "High").
   - **Route Visualization:** Displays the calculated route as a blue line on the map, overlaying the styled road segments and accidents.
- **Markers for Start and End Points:**
   - Green marker for the start point.
   - Red marker for the end point.
- **Popups for Interactivity:**
    - Clicking on a road segment shows details like road name and risk category.
    
