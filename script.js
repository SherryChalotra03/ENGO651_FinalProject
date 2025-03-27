// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function () {
    // Fetch the config from the backend
    fetch('http://localhost:5000/config')
        .then(response => response.json())
        .then(config => {
            // Initialize the map with the fetched config
            var map = L.map('map', { zoomControl: true }).setView([51.0447, -114.0719], 11);

            var mapboxLayer = L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
                maxZoom: 18,
                id: 'mapbox/streets-v11',
                tileSize: 512,
                zoomOffset: -1,
                accessToken: config.mapboxAccessToken
            }).addTo(map);

            var roadsLayer = null;
            var startMarker = null, endMarker = null, pathLayer = null;
            var startPoint = null, endPoint = null;
            var info = L.control();

            var greenIcon = L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
                shadowSize: [41, 41]
            });

            var redIcon = L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
                shadowSize: [41, 41]
            });

            fetch('calgary_roads.geojson')
                .then(response => response.json())
                .then(data => {
                    roadsLayer = L.geoJSON(data, {
                        style: { color: "#ff7800", weight: 0.5, opacity: 0.65 },
                        onEachFeature: function (feature, layer) {
                            layer.on('click', function (e) {
                                L.DomEvent.stopPropagation(e);
                                var props = feature.properties || {};
                                var osmidDisplay = Array.isArray(props.osmid) ? props.osmid.join(', ') : (props.osmid || 'Unknown');
                                var popupContent = `<b>Road ID:</b> ${osmidDisplay}<br><b>Incident Risk:</b> Not calculated yet<br><b>Name:</b> ${props.name || 'Unnamed'}`;
                                layer.bindPopup(popupContent).openPopup();
                                console.log('Road clicked:', props);
                            });
                        }
                    }).addTo(map);

                    var baseMaps = { "Mapbox Streets": mapboxLayer };
                    var overlayMaps = { "Calgary Roads": roadsLayer };
                    L.control.layers(baseMaps, overlayMaps).addTo(map);
                });

            // Geocoding function using Geoapify API
            async function geocodeLocation(locationName) {
                if (!locationName) return null;
                const apiKey = config.geoapifyApiKey;
              
                const url = `https://api.geoapify.com/v1/geocode/search?text=${encodeURIComponent(locationName)}&limit=1&apiKey=${apiKey}`;
                
                try {
                    const response = await fetch(url);
                    const data = await response.json();
                    console.log(`Geocoding result for "${locationName}":`, data);
                    if (data.features && data.features.length > 0) {
                        const coords = data.features[0].geometry.coordinates;
                        return [coords[1], coords[0]];
                    } else {
                        console.warn(`No coordinates found for location: ${locationName}`);
                        return null;
                    }
                } catch (error) {
                    console.error('Geocoding failed:', error.message);
                    return null;
                }
            }

            // Point selection via map clicks
            map.on('click', function (e) {
                console.log('Map clicked at:', e.latlng);
                if (!startPoint) {
                    startPoint = [e.latlng.lat, e.latlng.lng];
                    startMarker = L.marker(startPoint, { icon: greenIcon }).addTo(map).bindPopup('Start').openPopup();
                    document.getElementById('startLat').value = startPoint[0];
                    document.getElementById('startLon').value = startPoint[1];
                    document.getElementById('startLocation').value = '';
                    console.log('Start point set:', startPoint);
                } else if (!endPoint) {
                    endPoint = [e.latlng.lat, e.latlng.lng];
                    endMarker = L.marker(endPoint, { icon: redIcon }).addTo(map).bindPopup('End').openPopup();
                    document.getElementById('endLat').value = endPoint[0];
                    document.getElementById('endLon').value = endPoint[1];
                    document.getElementById('endLocation').value = '';
                    console.log('End point set:', endPoint);
                    findPath();
                } else {
                    console.log('Both points already set. Reset to select new points.');
                    info.update({ message: 'Both points already set. Click Reset to select new points.' });
                }
            });

            async function findPath() { //previous findpath() function starts from here
                // Show loading spinner
                document.getElementById('loadingSpinner').style.display = 'block';
                let start = startPoint;
                let end = endPoint;

                const startLocation = document.getElementById('startLocation').value.trim();
                const endLocation = document.getElementById('endLocation').value.trim();

                if (startLocation && !start) {
                    const adjustedStartLocation = startLocation.toLowerCase().includes('calgary') ? startLocation : `${startLocation}, Calgary, AB`;
                    start = await geocodeLocation(adjustedStartLocation);
                    if (start) {
                        if (startMarker) map.removeLayer(startMarker);
                        startMarker = L.marker(start, { icon: greenIcon }).addTo(map).bindPopup('Start').openPopup();
                        startPoint = start;
                        document.getElementById('startLat').value = start[0];
                        document.getElementById('startLon').value = start[1];
                    } else {
                        console.warn('Geocoding failed for start location. Please try a more specific location.');
                        info.update({ message: 'Geocoding failed for start location. Try a more specific location (e.g., "Downtown Calgary, AB").' });
                        return;
                    }
                }
                if (endLocation && !end) {
                    const adjustedEndLocation = endLocation.toLowerCase().includes('calgary') ? endLocation : `${endLocation}, Calgary, AB`;
                    end = await geocodeLocation(adjustedEndLocation);
                    if (end) {
                        if (endMarker) map.removeLayer(endMarker);
                        endMarker = L.marker(end, { icon: redIcon }).addTo(map).bindPopup('End').openPopup();
                        endPoint = end;
                        document.getElementById('endLat').value = end[0];
                        document.getElementById('endLon').value = end[1];
                    } else {
                        console.warn('Geocoding failed for end location. Please try a more specific location.');
                        info.update({ message: 'Geocoding failed for end location. Try a more specific location (e.g., "Calgary Tower, Calgary, AB").' });
                        return;
                    }
                }

                if (!start) {
                    const startLat = parseFloat(document.getElementById('startLat').value);
                    const startLon = parseFloat(document.getElementById('startLon').value);
                    if (!isNaN(startLat) && !isNaN(startLon)) {
                        start = [startLat, startLon];
                        if (startMarker) map.removeLayer(startMarker);
                        startMarker = L.marker(start, { icon: greenIcon }).addTo(map).bindPopup('Start').openPopup();
                        startPoint = start;
                    }
                }
                if (!end) {
                    const endLat = parseFloat(document.getElementById('endLat').value);
                    const endLon = parseFloat(document.getElementById('endLon').value);
                    if (!isNaN(endLat) && !isNaN(endLon)) {
                        end = [endLat, endLon];
                        if (endMarker) map.removeLayer(endMarker);
                        endMarker = L.marker(end, { icon: redIcon }).addTo(map).bindPopup('End').openPopup();
                        endPoint = end;
                    }
                }

                if (!start || !end) {
                    console.warn('Invalid start or end point. Please provide valid locations or coordinates.');
                    info.update({ message: 'Invalid start or end point. Please provide valid locations or coordinates.' });
                    return;
                }

                console.log('Initiating findPath with:', { start: start, end: end });
                fetch('http://localhost:5000/find_path', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ start: start, end: end })
                })
                .then(response => {
                    console.log('Fetch response status:', response.status);
                    console.log('Fetch response headers:', response.headers.get('Content-Type'));
                    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                    return response.text();
                })
                .then(rawText => {
                    console.log('Raw response (as string):', rawText);
                    try {
                        const pathGeojson = JSON.parse(rawText);
                        console.log('Parsed pathGeojson:', pathGeojson);
                        return pathGeojson;
                    } catch (e) {
                        console.error('JSON parsing failed:', e.message, 'Raw text:', rawText);
                        throw new Error('Invalid JSON response from server');
                    }
                })
                .then(pathGeojson => {
                    console.log('Path received:', pathGeojson);
                    if (pathGeojson.error) {
                        console.warn('Backend error:', pathGeojson.error);
                        info.update({ message: pathGeojson.error });
                        document.getElementById('routeSteps').innerHTML = '<li>' + pathGeojson.error + '</li>';
                        return;
                    }
                    if (pathLayer) {
                        map.removeLayer(pathLayer);
                        pathLayer = null;
                    }

                    if (!pathGeojson.features || pathGeojson.features.length === 0) {
                        console.warn('No features in path GeoJSON or invalid response:', pathGeojson);
                        info.update({ message: 'No path found. Try different points.' });
                        document.getElementById('routeSteps').innerHTML = '<li>No route found.</li>';
                        return;
                    }
                    pathLayer = L.geoJSON(pathGeojson, {
                        style: { color: '#0000ff', weight: 2, opacity: 0.8 }
                    }).addTo(map);
                    map.fitBounds(pathLayer.getBounds());
                    console.log('Path layer added with', pathGeojson.features.length, 'features');
                    info.update({ message: `Path found with ${pathGeojson.features.length} segments.` });

                    const routeSteps = document.getElementById('routeSteps');
                    routeSteps.innerHTML = '';
                    const roads = new Set();
                    pathGeojson.features.forEach((feature, index) => {
                        console.log(`Feature ${index}:`, feature);
                        const roadName = feature.properties && feature.properties.name ? feature.properties.name : 'Unnamed Road';
                        console.log(`Feature ${index}: roadName=${roadName}`);
                        roads.add(roadName);
                    });
                    const roadList = Array.from(roads);
                    if (roadList.length === 0) {
                        routeSteps.innerHTML = '<li>No roads identified.</li>';
                    } else {
                        roadList.forEach((road, index) => {
                            const li = document.createElement('li');
                            li.textContent = `Step ${index + 1}: Travel on ${road}`;
                            routeSteps.appendChild(li);
                        });
                    }
                })
                .catch(error => {
                    console.error('Pathfinding failed:', error.message);
                    info.update({ message: 'Pathfinding failed. Check console for details.' });
                    document.getElementById('routeSteps').innerHTML = '<li>Error finding route.</li>';
                })

                .finally(() => {
                    // Hide loading spinner
                    document.getElementById('loadingSpinner').style.display = 'none';
                });
            } //previous findpath() function ends here


            // GUI button event listeners
            document.getElementById('findPathButton').addEventListener('click', function () {
                findPath();
            });

            document.getElementById('resetButton').addEventListener('click', function () {
                console.log('Reset triggered via button');
                if (startMarker) {
                    map.removeLayer(startMarker);
                    startMarker = null;
                }
                if (endMarker) {
                    map.removeLayer(endMarker);
                    endMarker = null;
                }
                if (pathLayer) {
                    map.removeLayer(pathLayer);
                    pathLayer = null;
                }
                startPoint = null;
                endPoint = null;
                document.getElementById('startLocation').value = '';
                document.getElementById('endLocation').value = '';
                document.getElementById('startLat').value = '';
                document.getElementById('startLon').value = '';
                document.getElementById('endLat').value = '';
                document.getElementById('endLon').value = '';
                map.setView([51.0447, -114.0719], 11);
                info.update({ message: 'Map reset. Click to set new points or enter locations.' });
            });

            document.addEventListener('keydown', function (e) {
                if (e.target.tagName === 'INPUT') return;
                console.log('Key pressed:', e.key);
                if (e.key === 'r') {
                    console.log('Reset triggered');
                    if (startMarker) {
                        map.removeLayer(startMarker);
                        startMarker = null;
                    }
                    if (endMarker) {
                        map.removeLayer(endMarker);
                        endMarker = null;
                    }
                    if (pathLayer) {
                        map.removeLayer(pathLayer);
                        pathLayer = null;
                    }
                    startPoint = null;
                    endPoint = null;
                    document.getElementById('startLocation').value = '';
                    document.getElementById('endLocation').value = '';
                    document.getElementById('startLat').value = '';
                    document.getElementById('startLon').value = '';
                    document.getElementById('endLat').value = '';
                    document.getElementById('endLon').value = '';
                    map.setView([51.0447, -114.0719], 11);
                    info.update({ message: 'Map reset. Click to set new points or enter locations.' });
                }
            });

            info.onAdd = function (map) {
                this._div = L.DomUtil.create('div', 'info');
                this.update();
                return this._div;
            };

            info.update = function (props) {
                this._div.innerHTML = '<h4>Calgary Route Info</h4>' + 
                    (props && props.message ? props.message : 'Click a road for details');
            };

            info.addTo(map);

            const chatContainer = document.getElementById('chatContainer');
            const chatBody = document.getElementById('chatBody');
            const chatInput = document.getElementById('chatInput');
            const chatSend = document.getElementById('chatSend');
            const chatToggle = document.getElementById('chatToggle');
            let isChatMinimized = false;

            function addChatMessage(message, sender) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `chat-message ${sender}`;
                const contentDiv = document.createElement('div');
                contentDiv.className = 'message-content';
                contentDiv.textContent = message;
                messageDiv.appendChild(contentDiv);
                chatBody.appendChild(messageDiv);
                chatBody.scrollTop = chatBody.scrollHeight;
            }

            chatSend.addEventListener('click', function () {
                const message = chatInput.value.trim();
                if (!message) return;

                // Add user message to chat
                addChatMessage(message, 'user');
                chatInput.value = '';

                // Send message to backend
                fetch('http://localhost:5000/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        addChatMessage(data.error, 'bot');
                        return;
                    }

                    // Add bot response to chat
                    addChatMessage(data.response, 'bot');

                    // Update the map with the route
                    if (data.route_geojson) {
                        if (startMarker) map.removeLayer(startMarker);
                        if (endMarker) map.removeLayer(endMarker);
                        if (pathLayer) map.removeLayer(pathLayer);

                        startPoint = data.start_coords;
                        endPoint = data.end_coords;
                        startMarker = L.marker(startPoint, { icon: greenIcon }).addTo(map).bindPopup('Start').openPopup();
                        endMarker = L.marker(endPoint, { icon: redIcon }).addTo(map).bindPopup('End').openPopup();

                        pathLayer = L.geoJSON(data.route_geojson, {
                            style: { color: '#0000ff', weight: 2, opacity: 0.8 }
                        }).addTo(map);
                        map.fitBounds(pathLayer.getBounds());

                        // Update the route plan in the sidebar
                        const routeSteps = document.getElementById('routeSteps');
                        routeSteps.innerHTML = '';
                        const roads = new Set();
                        data.route_geojson.features.forEach(feature => {
                            const roadName = feature.properties && feature.properties.name ? feature.properties.name : 'Unnamed Road';
                            roads.add(roadName);
                        });
                        const roadList = Array.from(roads);
                        roadList.forEach((road, index) => {
                            const li = document.createElement('li');
                            li.textContent = `Step ${index + 1}: Travel on ${road}`;
                            routeSteps.appendChild(li);
                        });

                        info.update({ message: `Path found with ${data.route_geojson.features.length} segments.` });
                    }
                })
                .catch(error => {
                    console.error('Chat request failed:', error);
                    addChatMessage('Sorry, something went wrong. Please try again.', 'bot');
                });
            });

            chatInput.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    chatSend.click();
                }
            });

            chatToggle.addEventListener('click', function () {
                if (isChatMinimized) {
                    chatContainer.style.height = '400px';
                    chatBody.style.display = 'block';
                    chatInput.parentElement.style.display = 'flex';
                    chatToggle.textContent = '−';
                    isChatMinimized = false;
                } else {
                    chatContainer.style.height = '40px';
                    chatBody.style.display = 'none';
                    chatInput.parentElement.style.display = 'none';
                    chatToggle.textContent = '+';
                    isChatMinimized = true;
                }
            });




        })
        .catch(error => {
            console.error('Failed to load config from backend:', error);
            alert('Failed to load configuration. Please check if the backend server is running on http://localhost:5000.');
        });


        
});

