function formatTravelTime(seconds) {
    if (seconds == null || isNaN(seconds)) return "0 sec";
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return minutes === 0 ? `${remainingSeconds} sec` : `${minutes} min ${remainingSeconds} sec`;
}

document.addEventListener('DOMContentLoaded', function () {
    fetch('http://localhost:5000/config')
        .then(response => response.json())
        .then(config => {
            const map = L.map('map').setView([51.0447, -114.0719], 11);

            const greenIcon = L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
                shadowSize: [41, 41]
            });

            const redIcon = L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
                shadowSize: [41, 41]
            });

            let startMarker = null, endMarker = null, pathLayer = null;
            let startPoint = null, endPoint = null;

            const baseMap = L.tileLayer(`https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token=${config.mapboxAccessToken}`, {
                tileSize: 512, zoomOffset: -1, maxZoom: 18
            }).addTo(map);

            const customMap = L.tileLayer(`https://api.mapbox.com/styles/v1/hafsairfan89/cm8ddrp9p00tm01r08ylk88ik/tiles/{z}/{x}/{y}?access_token=${config.mapboxAccessToken}`, {
                tileSize: 512, zoomOffset: -1, minZoom: 12, maxZoom: 22
            });

            const baseMaps = { "Mapbox Streets": baseMap, "Risk & Accident View": customMap };
            const overlayMaps = {};

            Promise.all([
                fetch('http://localhost:5000/road_segments')
                    .then(res => res.json())
                    .then(data => {
                        const layer = L.geoJSON(data, {
                            style: feature => {
                               // const category = feature.properties.risk_categ || 'Unknown';
                                const category = feature.properties.risk_categ || feature.properties.risk_category || 'Unknown';
                                console.log('Risk Category:', category);  // Debugging line

                                let color = 'gray';
                                
                                switch (category) {
                                    case 'Very Low': color = 'green'; break;
                                    case 'Low': color = 'limegreen'; break;
                                    case 'Medium': color = 'orange'; break;
                                    case 'High': color = 'orangered'; break;
                                    case 'Very High': color = 'darkred'; break;
                                    default: color = 'gray';
                                }

                            return { color, weight: 2 };
                        },
                        onEachFeature: (feature, layer) => {
                            const props = feature.properties || {};
                            //const osmid = Array.isArray(props.osmid) ? props.osmid.join(', ') : (props.osmid || 'Unknown');
                            const name = props.name || 'Unnamed';
                            //const category = props.risk_category || 'Unknown';
                            const category = props.risk_categ || props.risk_category || 'Unknown';
                            // Bind a popup to each road segment with details
                            layer.bindPopup(`<b>Name:</b> ${name}<br><b>Risk:</b> ${category}`);
                        }
                    }).addTo(map);
                    overlayMaps["Calgary Roads (Risk)"] = layer; // Add the layer to overlayMaps
                }),
                
                fetch('http://localhost:5000/accidents').then(res => res.json()).then(data => {
                    const layer = L.geoJSON(data, {
                        pointToLayer: (feature, latlng) => {
                            const isHotSpot = feature.properties.hotspot === "Hot Spot"; // Assuming 'hotspot' field exists
                            const zScore = feature.properties.z_score || 0; // Assuming z_score exists and can be used
                            let color = 'yellow'; // Default for non-hotspot
                
                            if (isHotSpot) {
                                color = 'red'; // Hot Spot accidents are red
                            } else if (zScore > 2) {
                                color = 'orange'; // Higher z_score indicates more risk
                            } else {
                                color = 'green'; // Lower risk accidents
                            }
                
                            return L.circleMarker(latlng, {
                                radius: 4, // Adjust size as needed
                                fillColor: color,
                                color: 'darkred',
                                weight: 1,
                                fillOpacity: 0.7
                            });
                        },
                        onEachFeature: (feature, layer) => {
                            const desc = feature.properties.description || "Accident Site";
                            const risk = feature.properties.hotspot === "Hot Spot" ? "High Risk (Hot Spot)" : 
                            feature.properties.z_score > 2 ? "Moderate Risk" : "Low Risk";
                            layer.bindPopup(`<b>Accident:</b> ${desc}<br><b>Risk:</b> ${risk}`);
                        }
                    }).addTo(map);
                    overlayMaps["Accidents"] = layer;
                })
                
            ]).then(() => {
                L.control.layers(baseMaps, overlayMaps).addTo(map);
            });

            const legend = L.control({ position: 'bottomleft' });
            legend.onAdd = function () {
                const div = L.DomUtil.create('div', 'info legend');
                const grades = [
                    { color: 'green', label: 'Very Low' },
                    { color: 'limegreen', label: 'Low' },
                    { color: 'orange', label: 'Medium' },
                    { color: 'orangered', label: 'High' },
                    { color: 'red', label: 'Very High' }
                ];
                
                div.innerHTML += '<b>Risk Levels</b><br>';
                grades.forEach(g => {
                    div.innerHTML += `<i style="background:${g.color}; width: 18px; height: 18px; display:inline-block; margin-right: 8px;"></i> ${g.label}<br>`;
                });
                return div;
            };
            legend.addTo(map);
            const detectBtn = document.getElementById("detectLocationBtn");

        detectBtn.addEventListener("click", () => {
            if (!navigator.geolocation) {
                alert("Geolocation is not supported by your browser.");
                return;
            }

            detectBtn.disabled = true;
            detectBtn.innerText = "Detecting...";

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const { latitude, longitude } = position.coords;
                    document.getElementById("startLat").value = latitude.toFixed(6);
                    document.getElementById("startLon").value = longitude.toFixed(6);

                    map.setView([latitude, longitude], 14); // ✅ map is in scope here
                    if (startMarker) map.removeLayer(startMarker);
                    startMarker = L.marker([latitude, longitude], { icon: greenIcon }).addTo(map).bindPopup("Current Location (Start)").openPopup();
                    // startMarker = L.marker([latitude, longitude], { icon: greenIcon }).addTo(map); // Remove .bindPopup and .openPopup
                    startPoint = [latitude, longitude];

                    detectBtn.innerText = "Use My Current Location";
                    detectBtn.disabled = false;
                },
                (error) => {
                    alert("Failed to get your location: " + error.message);
                    detectBtn.innerText = "Use My Current Location";
                    detectBtn.disabled = false;
                }
            );
        });

            async function geocodeLocation(location) {
                const url = `https://api.geoapify.com/v1/geocode/search?text=${encodeURIComponent(location)}&limit=1&apiKey=${config.geoapifyApiKey}`;
                const res = await fetch(url);
                const data = await res.json();
                return data?.features?.[0]?.geometry?.coordinates?.reverse() || null;
            }

            async function findPath() {
                const loading = document.getElementById('loadingSpinner');
                loading.style.display = 'block';
                const routeSteps = document.getElementById('routeSteps');
                routeSteps.innerHTML = '';

                let start = startPoint, end = endPoint;
                const startLoc = document.getElementById('startLocation').value.trim();
                const endLoc = document.getElementById('endLocation').value.trim();

                if (startLoc && !start) {
                    start = await geocodeLocation(startLoc);
                    if (start) {
                        document.getElementById('startLat').value = start[0].toFixed(6);
                        document.getElementById('startLon').value = start[1].toFixed(6);
                    }
                }
                if (endLoc && !end) {
                    end = await geocodeLocation(endLoc);
                    if (end) {
                        document.getElementById('endLat').value = end[0].toFixed(6);
                        document.getElementById('endLon').value = end[1].toFixed(6);
                    }
                }

                if (!start) {
                    const lat = parseFloat(document.getElementById('startLat').value);
                    const lon = parseFloat(document.getElementById('startLon').value);
                    if (!isNaN(lat) && !isNaN(lon)) start = [lat, lon];
                }

                if (!end) {
                    const lat = parseFloat(document.getElementById('endLat').value);
                    const lon = parseFloat(document.getElementById('endLon').value);
                    if (!isNaN(lat) && !isNaN(lon)) end = [lat, lon];
                }

                if (!start || !end) {
                    alert("Start or End location is missing or invalid.");
                    loading.style.display = 'none';
                    return;
                }

                if (startMarker) map.removeLayer(startMarker);
                if (endMarker) map.removeLayer(endMarker);
                // startMarker = L.marker(start, { icon: greenIcon }).addTo(map).bindPopup('Start').openPopup();
                // endMarker = L.marker(end, { icon: redIcon }).addTo(map).bindPopup('End').openPopup();

                startMarker = L.marker(start, { icon: greenIcon }).addTo(map);
                endMarker = L.marker(end, { icon: redIcon }).addTo(map);

                fetch('http://localhost:5000/find_path', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ start, end })
                })
                    .then(res => res.json())
                    .then(data => {
                        if (pathLayer) map.removeLayer(pathLayer);
                        pathLayer = L.geoJSON(data, {
                            style: { color: 'blue', weight: 3 },
                            onEachFeature: (feature, layer) => {
                                const name = feature.properties.name || 'Unnamed Road';
                                const len = (feature.properties.length / 1000).toFixed(2);
                                const ttime = formatTravelTime(feature.properties.travel_time);
                                layer.bindPopup(`<b>${name}</b><br>${len} km<br>${ttime}`);
                            }
                        }).addTo(map);
                        map.fitBounds(pathLayer.getBounds());

                        const roads = data.features.map(f => ({
                            name: f.properties.name || 'Unnamed Road',
                            length: f.properties.length || 0
                        }));

                        const seen = new Set();
                        const uniqueRoads = roads.filter(r => {
                            if (seen.has(r.name)) return false;
                            seen.add(r.name);
                            return true;
                        });

                        uniqueRoads.forEach((r, i) => {
                            const li = document.createElement('li');
                            li.innerHTML = `Step ${i + 1}: Travel on ${r.name} (${(r.length / 1000).toFixed(2)} km)`;
                            routeSteps.appendChild(li);
                        });

                        const total = document.createElement('li');
                        total.innerHTML = `<b>Total: ${(data.properties.total_length / 1000).toFixed(2)} km, ${formatTravelTime(data.properties.total_travel_time)}</b>`;
                        routeSteps.appendChild(total);
                    })
                    .catch(err => {
                        alert("Error finding path.");
                        console.error(err);
                    })
                    .finally(() => {
                        loading.style.display = 'none';
                    });
                    
            }
            document.getElementById('findPathButton').addEventListener('click', findPath);
            // Reset button
            document.getElementById('resetButton').addEventListener('click', () => {
                if (startMarker) {
                    map.removeLayer(startMarker);
                    startMarker = null; // ✅ Clear marker reference
                }
            
                if (endMarker) {
                    map.removeLayer(endMarker);
                    endMarker = null; // ✅ Clear marker reference
                }
            
                if (pathLayer) {
                    map.removeLayer(pathLayer);
                    pathLayer = null; // ✅ Clear path layer reference
                }
            
                // Clear input fields
                document.getElementById('routeSteps').innerHTML = '';
                document.getElementById('startLocation').value = '';
                document.getElementById('endLocation').value = '';
                document.getElementById('startLat').value = '';
                document.getElementById('startLon').value = '';
                document.getElementById('endLat').value = '';
                document.getElementById('endLon').value = '';
            
                // Clear coordinates
                startPoint = null;
                endPoint = null;
            
                // Reset map view
                map.setView([51.0447, -114.0719], 11);
            });

            // Map click to set start/end
            map.on('click', function (e) {
                if (!startPoint) {
                    startPoint = [e.latlng.lat, e.latlng.lng];
                    startMarker = L.marker(startPoint, { icon: greenIcon }).addTo(map).bindPopup("Start").openPopup();
                    document.getElementById('startLat').value = startPoint[0].toFixed(6); // Add this to update text boxes
                    document.getElementById('startLon').value = startPoint[1].toFixed(6);
                } else if (!endPoint) {
                    endPoint = [e.latlng.lat, e.latlng.lng];
                    endMarker = L.marker(endPoint, { icon: redIcon }).addTo(map).bindPopup("End").openPopup();
                    document.getElementById('endLat').value = endPoint[0].toFixed(6); // Add this to update text boxes
                    document.getElementById('endLon').value = endPoint[1].toFixed(6);
                    findPath(); 
                }
            });

            // ✅ Chatbot logic
            const chatSend = document.getElementById('chatSend');
            const chatInput = document.getElementById('chatInput');
            const chatBody = document.getElementById('chatBody');
            const chatToggle = document.getElementById('chatToggle');
            const chatContainer = document.getElementById('chatContainer');
            let isChatMinimized = false;

            function addChatMessage(message, sender) {
                const msg = document.createElement('div');
                msg.className = `chat-message ${sender}`;
                msg.innerHTML = `<div class="message-content">${message}</div>`;
                chatBody.appendChild(msg);
                chatBody.scrollTop = chatBody.scrollHeight;
            }

            chatSend.addEventListener('click', () => {
                const msg = chatInput.value.trim();
                if (!msg) return;
                addChatMessage(msg, 'user');
                chatInput.value = '';

                fetch('http://localhost:5000/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: msg })
                })
                    .then(res => res.json())
                    .then(data => {
                        if (data.error) addChatMessage(data.error, 'bot');
                        else addChatMessage(data.response, 'bot');

                        if (data.route_geojson && data.start_coords && data.end_coords) {
                            if (startMarker) map.removeLayer(startMarker);
                            if (endMarker) map.removeLayer(endMarker);
                            if (pathLayer) map.removeLayer(pathLayer);

                            startPoint = data.start_coords;
                            endPoint = data.end_coords;

                            // startMarker = L.marker(startPoint, { icon: greenIcon }).addTo(map).bindPopup('Start').openPopup();
                            // endMarker = L.marker(endPoint, { icon: redIcon }).addTo(map).bindPopup('End').openPopup();
                            startMarker = L.marker(startPoint, { icon: greenIcon }).addTo(map); // Remove .bindPopup and .openPopup
                            endMarker = L.marker(endPoint, { icon: redIcon }).addTo(map); // Remove .bindPopup and .openPopup

                            pathLayer = L.geoJSON(data.route_geojson, {
                                style: { color: 'blue', weight: 3 },
                                onEachFeature: (feature, layer) => {
                                    const name = feature.properties.name || 'Unnamed Road';
                                    const len = (feature.properties.length / 1000).toFixed(2);
                                    const ttime = formatTravelTime(feature.properties.travel_time);
                                    layer.bindPopup(`<b>${name}</b><br>${len} km<br>${ttime}`);
                                }
                            }).addTo(map);
                            map.fitBounds(pathLayer.getBounds());

                            const routeSteps = document.getElementById('routeSteps');
                            routeSteps.innerHTML = '';

                            const roads = data.route_geojson.features.map(f => ({
                                name: f.properties.name || 'Unnamed Road',
                                length: f.properties.length || 0
                            }));

                            const seen = new Set();
                            const uniqueRoads = roads.filter(r => {
                                if (seen.has(r.name)) return false;
                                seen.add(r.name);
                                return true;
                            });

                            uniqueRoads.forEach((r, i) => {
                                const li = document.createElement('li');
                                li.innerHTML = `Step ${i + 1}: Travel on ${r.name} (${(r.length / 1000).toFixed(2)} km)`;
                                routeSteps.appendChild(li);
                            });

                            const total = document.createElement('li');
                            total.innerHTML = `<b>Total: ${(data.route_geojson.properties.total_length / 1000).toFixed(2)} km, ${formatTravelTime(data.route_geojson.properties.total_travel_time)}</b>`;
                            routeSteps.appendChild(total);
                        }
                    })
                    .catch(err => {
                        addChatMessage("Chat failed. Try again later.", 'bot');
                        console.error(err);
                    });
            });

            chatInput.addEventListener('keypress', e => {
                if (e.key === 'Enter') chatSend.click();
            });

            chatToggle.addEventListener('click', () => {
                isChatMinimized = !isChatMinimized;
                chatContainer.style.height = isChatMinimized ? '40px' : '400px';
                chatBody.style.display = isChatMinimized ? 'none' : 'block';
                chatInput.parentElement.style.display = isChatMinimized ? 'none' : 'flex';
                chatToggle.textContent = isChatMinimized ? '+' : '−';
            });
        })
        .catch(err => {
            console.error('Failed to load config:', err);
            alert("Config loading failed. Is the backend running?");
        });

  
});

