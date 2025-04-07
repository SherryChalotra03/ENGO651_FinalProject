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
- **Precomputed Road Network:** Uses a precomputed NetworkX graph (road_network_processed.pkl) for efficient pathfinding in Calgary.

### 2. IoT Integration for Real-Time Location Tracking
- **MQTT-Based Location Updates:** Retrieves the user’s current location in real-time from an IoT device using the MQTT protocol.
- **Automatic Start Point Setting:** Sets the user’s current location as the start point for route planning, eliminating the need for manual input.
- **Dynamic Updates:** Continuously updates the start point as the user moves, ensuring the route reflects the latest location.
- **Fallback Mechanism:** Allows manual start point selection if IoT location data is unavailable.

### 3. Interactive Map Interface

- **Leaflet Map:** Displays an interactive map of Calgary using Leaflet (leaflet@1.9.4) with Mapbox tiles.
- **Custom Mapbox Style:** Integrates a custom Mapbox Studio style for visualizing:
    - **Road Segments:** Colored by risk category (e.g., green for "Low", yellow for "Medium", red for "High").
   - **Route Visualization:** Displays the calculated route as a blue line on the map, overlaying the styled road segments and accidents.
- **Markers for Start and End Points:**
   - Green marker for the start point.
   - Red marker for the end point.
- **Popups for Interactivity:**
    - Clicking on a road segment shows details like road name and risk category.

### 4. Multiple Input Methods for Route Requests

- **Manual Map Clicks:**
    - Click on the map to set the start point (green marker).
    - Click again to set the end point (red marker).
    - The route is automatically calculated and displayed.
- **Textbox Input:**
    - Enter start and end locations (e.g., "Calgary Tower" and "University Station, Calgary") in the Route Planner pane.
    - Optionally enter coordinates manually (latitude and longitude).
    - Click "Find Path" to calculate the route.
- **Chatbot Interface:**
    - Use natural language to request routes (e.g., "Find a route from Calgary Tower to University Station, Calgary").
    - The chatbot parses the request, geocodes the locations, and displays the route on the map.
- **IoT-Based Start Point:** Automatically uses the user’s current location from IoT data as the start point.

### 5. Chatbot for Natural Language Interaction

- **Natural Language Parsing:** Parses user input to extract start and end locations using regex patterns (e.g., "from X to Y").
- **Geocoding Integration:** Converts location names to coordinates using the Geoapify API.
- **Route Response:** Returns a formatted route plan as an HTML list, including road names, distances, and total travel time.
- **User-Friendly Interface:**
    - Chatbot window with a toggle to minimize/maximize.
    - Styled messages (green for user, blue for bot).
    - Supports Enter key to send messages.

### 6. Geocoding and Location Handling
- **Geoapify API Integration:** Converts location names to coordinates (latitude, longitude) using the Geoapify API.
- **Calgary-Specific Adjustments:** Automatically appends ", Calgary, AB" to location names if "Calgary" is not specified, ensuring accurate geocoding within Calgary.
- **Coordinate Validation:** Ensures start and end points are within Calgary bounds (lat: 50.842 to 51.212, lon: -114.315 to -113.860).

### 7. Route Plan Display
- **Sidebar Route Plan:**
    - Lists each road segment in the route with its name and distance (in kilometers).
    - Removes duplicate road names while preserving order.
    - Displays total distance and total travel time for the route.
- **Travel Time Formatting:** Converts travel time (in seconds) to a human-readable format (e.g., "15 min 30 sec").
- **Dynamic Updates:** Updates the route plan whenever a new route is calculated via map clicks, textboxes, or the chatbot.

### 8. Custom Visualization with Mapbox Studio
- **Road Risk Visualization:** Road segments are styled based on the risk_category property from road_risk_layer_categorized.shp.
- **Example styling:**
    ![image](https://github.com/user-attachments/assets/0eb0d0f9-359e-4410-afc8-9514c1c7e825)

- **Mapbox Studio Integration:**
    - Styled in Mapbox Studio and integrated into Leaflet via a custom Mapbox style URL.

### 8. User Interface Enhancements
- **Loading Spinner:** Displays a loading spinner while the route is being calculated or data is being fetched.
- **Reset Functionality:**
    - Reset the map by clicking the "Reset" button or pressing the R key.
    - Clears markers, route, and input fields, and resets the map view to the default position.
- **Responsive Design:**
    - Sidebar for route planning and route plan display.
    - Chatbot window positioned in the bottom-right corner with a toggle to minimize/maximize.
- **Instructions:** Provides clear instructions on how to use the application (via the map interface).

### 9.Backend Features
- **Flask Server:**
    - Handles API requests for pathfinding (/find_path), geocoding (/geocode), chatbot interactions (/chat), and configuration (/config).
    - Uses Flask-CORS to allow cross-origin requests from the frontend.
- **Dynamic Risk Adjustment:**
    - Adjusts risk scores based on time, day, and season using configurable factors.
    - Caps adjusted risk scores to prevent extreme values.
- **GeoJSON Output:**
    - Returns route data as GeoJSON, including road names, distances, travel times, and risk categories.
    - Includes total distance, total travel time, total risk, and risk category counts in the response.

### 10. Error Handling and Validation
- **Input Validation:**
    - Ensures start and end points are within Calgary bounds.
    - Validates that geocoded locations are valid and within the road network.
- **Error Messages:**
    - Displays user-friendly error messages in the UI (e.g., "Start point is outside Calgary bounds").
    - Logs detailed errors in the console for debugging.
- **Backend Error Handling:**
    - Handles exceptions in pathfinding, geocoding, and file loading.
    - Returns appropriate HTTP status codes and error messages (e.g., 400 for invalid input, 500 for server errors).

### 11. Performance Optimizations
- **Precomputed Graph:** Uses a precomputed NetworkX graph (road_network_processed.pkl) to speed up pathfinding.
- **Efficient Geocoding:** Limits Geoapify API requests to one result per query (limit=1) to reduce latency.
- **Mapbox Vector Tiles:** Leverages Mapbox Studio’s vector tiles for efficient rendering of large datasets (road segments and accidents).

### 12. Extensibility
- **Modular Code Structure:**
    - Pathfinding logic is separated into find_path.py.
    - Chatbot logic is separated into chatbot.py.
    - Frontend logic is modularized in script.js.
- **Configurable Parameters:**
    - Pathfinding weights (alpha for distance, beta for risk) can be adjusted.
    - Risk adjustment factors (rush_hour_factor, weekday_factor, winter_factor) are configurable.
- **Customizable Visualization:**
    - Mapbox Studio allows easy updates to the styling of road segments and accidents.
    - Additional data layers can be added by uploading new tilesets to Mapbox Studio.
### 13. Security and Configuration
- **Environment Variables:** Stores sensitive API keys (Mapbox, Geoapify) in a .env file using python-dotenv.
- **CORS Configuration:** Allows cross-origin requests from the frontend (http://localhost:8000) to the backend (http://localhost:5000).

## Potential Future Features
While not currently implemented, the following features could be added to enhance the project:
- **Real-Time Traffic and Weather Data:** Integrate live traffic data to adjust travel times and risk scores dynamically.
- **Alternate Routes:** Provide multiple route options with different risk/distance trade-offs.
- **User Preferences:** Allow users to prioritize safety, speed, or a balance of both in route planning.
- **Advanced Chatbot Capabilities:** Improve natural language understanding with NLP libraries (e.g., spaCy, Rasa).
- **Mobile Responsiveness:** Optimize the UI for mobile devices.
- **Incident Reporting:** Allow users to report new accidents or road hazards, updating the dataset in real-time.

## Application in Action: Screenshots
- **Map Interface with Route Display**

- **Route Planner Pane**

- **Chatbot Interaction**

- **IoT Location Tracking**

- **Risk Visualization on Map**


## Contributors
- Hafsa Irfan, M.Sc
- Sherry Chalotra, PhD Geomatics Engineering
- Zahra Indrageni - PhD Geomatics Engineering
