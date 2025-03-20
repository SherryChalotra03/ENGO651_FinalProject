# ENGO651_FinalProject:

## Overview of final project: 

## Project Structure

- `server.py`: Flask backend for route calculation and API key serving.
- `index.html`: Main HTML file for the frontend.
- `script.js`: JavaScript file handling map interactions, geocoding, and route display.
- `styles.css`: CSS for styling the map and sidebar.
- `calgary_roads.geojson`: GeoJSON file containing Calgary’s road network.
- `.env`: Environment file for storing API keys.
- `calgary_roads_geojson.ipynb`: Jupyter Notebook to generate `calgary_roads.geojson` (optional).
- 
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

 - **View the Route:**
    - The calculated route will be displayed in blue on the map.
    - A step-by-step route plan will appear in the sidebar, listing the roads to travel on.

- **Reset the Map:**
    - Click the "Reset" button or press the R key to clear the markers and route, resetting the map to its initial state.
