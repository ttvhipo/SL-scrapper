from flask import Flask, render_template_string, jsonify
import requests
import folium
from google.transit import gtfs_realtime_pb2
from folium.plugins import MarkerCluster
import json

app = Flask(__name__)

def fetch_bus_data():
    """Fetch and process bus data, returning both HTML and raw position data"""
    url = 'https://opendata.samtrafiken.se/gtfs-rt-sweden/sl/VehiclePositionsSweden.pb?key=55d7e64ffaff42acafaedfdee46c3788'
    response = requests.get(url)
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    # Create base map
    map_center = [59.3293, 18.0686]
    map_object = folium.Map(location=map_center, zoom_start=12)
    
    # Process bus positions
    bus_positions = []
    for entity in feed.entity:
        if entity.HasField('vehicle'):
            vehicle = entity.vehicle
            if hasattr(vehicle.position, 'latitude') and hasattr(vehicle.position, 'longitude'):
                vehicle_info = {
                    'lat': vehicle.position.latitude,
                    'lng': vehicle.position.longitude,
                    'id': getattr(vehicle, 'id', 'No ID available'),
                    'route_id': getattr(vehicle.trip, 'route_id', 'Unknown Route'),
                    'trip_id': getattr(vehicle.trip, 'trip_id', 'Unknown Trip'),
                    'direction_id': getattr(vehicle.trip, 'direction_id', None),
                    'speed': getattr(vehicle.position, 'speed', 0),
                    'bearing': getattr(vehicle.position, 'bearing', 0),
                    'vehicle_label': getattr(vehicle.vehicle, 'label', 'Unknown Vehicle'),
                    'timestamp': getattr(vehicle, 'timestamp', 0)
                }
                bus_positions.append(vehicle_info)

    return map_object._repr_html_(), bus_positions

@app.route('/')
def index():
    base_map_html, initial_positions = fetch_bus_data()

    final_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vehicle Positions Map</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.css" />
        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/leaflet.markercluster.js"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.css" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.Default.css" />
        <style>
            #map {{
                height: 800px;
                width: 100%;
            }}
            .bus-popup {{
                font-family: Arial, sans-serif;
            }}
            .bus-popup h3 {{
                margin: 0 0 5px 0;
                color: #2c3e50;
            }}
            .bus-info {{
                margin: 2px 0;
                color: #34495e;
            }}
        </style>
        <script>
            let map;
            let markers = L.markerClusterGroup();
            
            function initMap() {{
                map = L.map('map').setView([59.3293, 18.0686], 12);
                
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '© OpenStreetMap contributors'
                }}).addTo(map);
                
                map.addLayer(markers);
                
                updateMarkers({json.dumps(initial_positions)});
                
                setInterval(updateBusPositions, 4000);
            }}

            function createPopupContent(bus) {{
                const timestamp = new Date(bus.timestamp * 1000).toLocaleTimeString();
                const speed = bus.speed ? Math.round(bus.speed * 3.6) : 0;
                
                return `
                    <div class="bus-popup">
                        <h3>Route ${{bus.route_id}}</h3>
                        <div class="bus-info">Vehicle: ${{bus.vehicle_label}}</div>
                        <div class="bus-info">Direction: ${{bus.direction_id === 0 ? 'Outbound' : 'Inbound'}}</div>
                        <div class="bus-info">Speed: ${{speed}} km/h</div>
                        <div class="bus-info">Last Update: ${{timestamp}}</div>
                        <div class="bus-info">Trip ID: ${{bus.trip_id}}</div>
                        <div class="bus-info">Vehicle ID: ${{bus.id}}</div>
                    </div>
                `;
            }}

            function updateMarkers(positions) {{
                markers.clearLayers();
                
                positions.forEach(pos => {{
                    const marker = L.marker([pos.lat, pos.lng], {{
                        rotationAngle: pos.bearing
                    }});
                    marker.bindPopup(createPopupContent(pos));
                    markers.addLayer(marker);
                }});
            }}

            function updateBusPositions() {{
                fetch('/update_map')
                    .then(response => response.json())
                    .then(data => {{
                        updateMarkers(data.positions);
                    }})
                    .catch(error => {{
                        console.error('Error updating bus positions:', error);
                    }});
            }}

            function getUserLocation() {{
                if (navigator.geolocation) {{
                    navigator.geolocation.getCurrentPosition(function(position) {{
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        map.setView([lat, lon], 12);
                    }}, function(error) {{
                        console.error("Error getting location:", error);
                    }});
                }} else {{
                    console.log("Geolocation is not supported by this browser.");
                }}
            }}

            window.onload = initMap;
        </script>
    </head>
    <body>
        <h1>Vehicle Positions Map</h1>
        <button onclick="getUserLocation()">Get My Location</button>
        <div id="map"></div>
    </body>
    </html>
    """
    return render_template_string(final_html)

@app.route('/update_map')
def update_map():
    _, positions = fetch_bus_data()
    return jsonify({"positions": positions})

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)