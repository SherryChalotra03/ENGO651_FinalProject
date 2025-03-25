// Updated full script.js with multi-route visualization support

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function () {
    fetch('http://localhost:5000/config')
        .then(response => response.json())
        .then(config => {
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

            async function geocodeLocation(locationName) {
                if (!locationName) return null;
                const apiKey = config.geoapifyApiKey;
                const url = `https://api.geoapify.com/v1/geocode/search?text=${encodeURIComponent(locationName)}&limit=1&apiKey=${apiKey}`;
                try {
                    const response = await fetch(url);
                    const data = await response.json();
                    if (data.features && data.features.length > 0) {
                        const coords = data.features[0].geometry.coordinates;
                        return [coords[1], coords[0]];
                    } else {
                        return null;
                    }
                } catch (error) {
                    return null;
                }
            }

            map.on('click', function (e) {
                if (!startPoint) {
                    startPoint = [e.latlng.lat, e.latlng.lng];
                    startMarker = L.marker(startPoint, { icon: greenIcon }).addTo(map).bindPopup('Start').openPopup();
                    document.getElementById('startLat').value = startPoint[0];
                    document.getElementById('startLon').value = startPoint[1];
                    document.getElementById('startLocation').value = '';
                } else if (!endPoint) {
                    endPoint = [e.latlng.lat, e.latlng.lng];
                    endMarker = L.marker(endPoint, { icon: redIcon }).addTo(map).bindPopup('End').openPopup();
                    document.getElementById('endLat').value = endPoint[0];
                    document.getElementById('endLon').value = endPoint[1];
                    document.getElementById('endLocation').value = '';
                    findPath();
                } else {
                    info.update({ message: 'Both points already set. Click Reset to select new points.' });
                }
            });

            async function findPath() {
                let start = startPoint;
                let end = endPoint;
                const startLocation = document.getElementById('startLocation').value.trim();
                const endLocation = document.getElementById('endLocation').value.trim();

                if (startLocation && !start) start = await geocodeLocation(startLocation);
                if (endLocation && !end) end = await geocodeLocation(endLocation);

                if (!start || !end) {
                    info.update({ message: 'Invalid start or end point.' });
                    return;
                }

                fetch('http://localhost:5000/find_path', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ start: start, end: end })
                })
                    .then(response => response.json())
                    .then(pathData => {
                        if (pathLayer) map.removeLayer(pathLayer);

                        if (!pathData.routes || pathData.routes.length === 0) {
                            info.update({ message: 'No routes found.' });
                            document.getElementById('routeSteps').innerHTML = '<li>No route found.</li>';
                            return;
                        }

                        const colors = ['#0000ff', '#008000', '#800080'];
                        let shortestTime = Infinity;
                        let bestRouteLayer = null;
                        let allRoutes = [];

                        const routeSteps = document.getElementById('routeSteps');
                        routeSteps.innerHTML = '';

                        pathData.routes.forEach((route, idx) => {
                            const color = colors[idx % colors.length];
                            const layer = L.geoJSON(route.geojson, {
                                style: { color: color, weight: 4, opacity: 0.6 }
                            }).addTo(map);

                            if (route.time_min < shortestTime) {
                                shortestTime = route.time_min;
                                bestRouteLayer = layer;
                            }

                            allRoutes.push(layer);

                            const li = document.createElement('li');
                            li.innerHTML = `<strong>Route ${idx + 1}:</strong> ${route.distance_km} km, ${route.time_min} min`;
                            routeSteps.appendChild(li);
                        });

                        if (bestRouteLayer) {
                            bestRouteLayer.setStyle({ weight: 5, opacity: 1.0 });
                            map.fitBounds(bestRouteLayer.getBounds());
                            info.update({ message: `Shortest route: ${shortestTime} minutes` });
                        }

                        pathLayer = L.layerGroup(allRoutes);
                    })
                    .catch(error => {
                        console.error('Pathfinding failed:', error.message);
                        info.update({ message: 'Pathfinding failed. Check console for details.' });
                        document.getElementById('routeSteps').innerHTML = '<li>Error finding route.</li>';
                    });
            }

            document.getElementById('findPathButton').addEventListener('click', findPath);

            document.getElementById('resetButton').addEventListener('click', function () {
                if (startMarker) map.removeLayer(startMarker);
                if (endMarker) map.removeLayer(endMarker);
                if (pathLayer) map.removeLayer(pathLayer);
                startMarker = endMarker = pathLayer = null;
                startPoint = endPoint = null;
                document.getElementById('startLocation').value = '';
                document.getElementById('endLocation').value = '';
                document.getElementById('startLat').value = '';
                document.getElementById('startLon').value = '';
                document.getElementById('endLat').value = '';
                document.getElementById('endLon').value = '';
                map.setView([51.0447, -114.0719], 11);
                info.update({ message: 'Map reset. Click to set new points.' });
            });

            document.addEventListener('keydown', function (e) {
                if (e.key === 'r') document.getElementById('resetButton').click();
            });

            info.onAdd = function (map) {
                this._div = L.DomUtil.create('div', 'info');
                this.update();
                return this._div;
            };

            info.update = function (props) {
                this._div.innerHTML = '<h4>Calgary Route Info</h4>' + (props && props.message ? props.message : 'Click a road for details');
            };

            info.addTo(map);
        })
        .catch(error => {
            console.error('Failed to load config from backend:', error);
            alert('Failed to load configuration. Please check if the backend server is running on http://localhost:5000.');
        });
});
