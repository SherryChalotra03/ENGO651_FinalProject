
# Calgary Safe Way – Risk-Aware Navigation API

Calgary Safe Way introduces a novel, risk-aware approach to urban navigation by integrating accident risk data, dynamic temporal adjustments, and real-time geolocation into its routing engine. This README provides documentation for the backend RESTful API developed with Flask.

---

## 🚀 Server Configuration

- **Backend Server:** `http://localhost:5000`
- **Frontend Origin:** `http://localhost:8000`
- **Data Format:** All responses are in JSON; routing data uses GeoJSON.
- **CORS:** Handled using Flask-CORS.

---

## 6.4 API Description and Documentation

### 6.4.1 `GET /config`

**Description:**  
Retrieves configuration settings including API keys for Mapbox and Geoapify.

**Response:**
```json
{
  "mapboxAccessToken": "your_mapbox_token",
  "geoapifyApiKey": "your_geoapify_key"
}
```

---

### 6.4.2 `POST /find_path`

**Description:**  
Computes a risk-aware route using a customized A* algorithm that balances distance and contextual risk.

**Request:**
```json
{
  "start": [51.048615, -114.063245],
  "end": [51.080836, -114.125186]
}
```

**Success Response:**
```json
{
  "route": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "LineString",
          "coordinates": [[51.048615, -114.063245], [51.080836, -114.125186]]
        },
        "properties": {
          "road_name": "9 Ave SE",
          "distance": 120.5,
          "travel_time": 180,
          "risk_category": "Low"
        }
      }
    ]
  },
  "total_distance": 5200.0,
  "total_travel_time": 765,
  "total_risk": 6.10,
  "risk_categories": {
    "Low": 15,
    "Medium": 15,
    "High": 42,
    "Very High": 78
  }
}
```

**Errors:**
- `400 Bad Request`: Invalid coordinates
- `500 Internal Server Error`: Route computation failed

---

### 6.4.3 `POST /geocode`

**Description:**  
Geocodes a location name into coordinates using Geoapify, with Calgary-specific formatting.

**Request:**
```json
{
  "location": "Calgary Tower"
}
```

**Success Response:**
```json
{
  "location": "Calgary Tower, Calgary, AB",
  "coordinates": [51.048615, -114.063245]
}
```

**Errors:**
- `400 Bad Request`: Location not found
- `500 Internal Server Error`: Geocoding failed

---

### 6.4.4 `POST /chat`

**Description:**  
Processes a natural language message and returns a route plan.

**Request:**
```json
{
  "message": "Find a route from Calgary Tower to University Station, Calgary"
}
```

**Success Response:**
```json
{
  "route_plan": "<ul><li>9 Ave SE: 120.5m</li><li>Centre St S: 150.0m</li></ul>",
  "total_distance": 5200.0,
  "total_travel_time": "12 min 45 sec",
  "total_risk": 6.10,
  "route_geojson": {
    "type": "FeatureCollection",
    "features": [...]
  }
}
```

**Errors:**
- `400 Bad Request`: Unable to parse locations
- `500 Internal Server Error`: Chatbot failed

---

## 6.5 Data Models and JSON Encodings

### 6.5.1 Road Segments

GeoJSON representing Calgary roads with safety metadata.

**Example:**
```json
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [[-114.063245, 51.048615], [-114.063300, 51.048700]]
  },
  "properties": {
    "road_id": 123,
    "name": "16 Ave NW",
    "risk_score": 0.42,
    "risk_category": "Medium"
  }
}
```

---

### 6.5.2 Accident Hotspots

GeoJSON layer showing accident-prone locations in Calgary.

**Example:**
```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [-114.06, 51.05]
  },
  "properties": {
    "description": "Crash at intersection",
    "hotspot": "Hot Spot",
    "z_score": 3.2
  }
}
```

---

## 🛠️ Technologies

- Flask + Flask-CORS
- Leaflet + Mapbox Studio
- Geoapify API
- Python `datetime` for dynamic temporal routing
