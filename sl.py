from flask import Flask, render_template_string, jsonify
import requests
import folium
from google.transit import gtfs_realtime_pb2
from folium.plugins import MarkerCluster, HeatMap
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

def fetch_bus_data():
    """Fetch and process bus data, returning both HTML and raw position data"""
    api_key = os.getenv('SAMTRAFIKEN_API_KEY', '55d7e64ffaff42acafaedfdee46c3788')
    url = f'https://opendata.samtrafiken.se/gtfs-rt-sweden/sl/VehiclePositionsSweden.pb?key={api_key}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)

        map_center = [59.3293, 18.0686]
        map_object = folium.Map(location=map_center, zoom_start=12)
        
        bus_positions = []
        for entity in feed.entity:
            if entity.HasField('vehicle'):
                vehicle = entity.vehicle
                # Debug print
                print("Vehicle data:", vehicle)
                print("Trip data:", vehicle.trip)
                
                if hasattr(vehicle.position, 'latitude') and hasattr(vehicle.position, 'longitude'):
                    # Get route information from trip
                    route_id = vehicle.trip.route_id if vehicle.trip.HasField('route_id') else 'Unknown Route'
                    
                    vehicle_info = {
                        'lat': float(vehicle.position.latitude),
                        'lng': float(vehicle.position.longitude),
                        'id': getattr(vehicle.vehicle, 'id', 'No ID available'),
                        'route_id': route_id,  # Store the route ID
                        'trip_id': getattr(vehicle.trip, 'trip_id', 'Unknown Trip'),
                        'direction_id': getattr(vehicle.trip, 'direction_id', None),
                        'speed': float(getattr(vehicle.position, 'speed', 0)),
                        'bearing': float(getattr(vehicle.position, 'bearing', 0)),
                        'vehicle_label': getattr(vehicle.vehicle, 'label', 'Unknown Vehicle'),
                        'timestamp': int(getattr(vehicle, 'timestamp', 0))
                    }
                    bus_positions.append(vehicle_info)

        # Debug print first few positions
        print("First few bus positions:", bus_positions[:3])
        
        return map_object._repr_html_(), bus_positions

    except requests.exceptions.RequestException as e:
        print(f"Error fetching bus data: {e}")
        return None, []

@app.route('/')
def index():
    base_map_html, initial_positions = fetch_bus_data()
    
    if base_map_html is None:
        return "Error fetching bus data", 500

    final_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stockholm Bus Tracker</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.css" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.css" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.Default.css" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" />
        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/leaflet.markercluster.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.heat/0.2.0/leaflet-heat.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}

            body {{
                background-color: #f5f5f5;
            }}

            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }}

            .header {{
                background-color: #2c3e50;
                color: white;
                padding: 1rem;
                margin-bottom: 1rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}

            .header h1 {{
                font-size: 1.8rem;
                margin-bottom: 0.5rem;
            }}

            .controls {{
                display: flex;
                gap: 1rem;
                margin-bottom: 1rem;
                flex-wrap: wrap;
            }}

            .control-panel {{
                background: white;
                padding: 1rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 1rem;
            }}

            .button {{
                background-color: #3498db;
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                transition: background-color 0.3s;
            }}

            .button:hover {{
                background-color: #2980b9;
            }}

            .button i {{
                font-size: 1rem;
            }}

            #map {{
                height: 700px;
                width: 100%;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}

            .bus-popup {{
                font-family: 'Segoe UI', sans-serif;
                padding: 10px;
            }}

            .bus-popup h3 {{
                margin: 0 0 10px 0;
                color: #2c3e50;
                font-size: 1.2rem;
                border-bottom: 2px solid #3498db;
                padding-bottom: 5px;
            }}

            .bus-info {{
                margin: 5px 0;
                color: #34495e;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}

            .bus-info i {{
                width: 20px;
                color: #3498db;
            }}

            .stats-panel {{
                background: white;
                padding: 1rem;
                border-radius: 8px;
                margin-top: 1rem;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1rem;
            }}

            .stat-item {{
                text-align: center;
                padding: 1rem;
                background: #f8f9fa;
                border-radius: 4px;
            }}

            .stat-value {{
                font-size: 1.5rem;
                font-weight: bold;
                color: #2c3e50;
            }}

            .stat-label {{
                color: #7f8c8d;
                margin-top: 0.5rem;
            }}

            .filter-panel {{
                display: flex;
                gap: 1rem;
                align-items: center;
                margin-bottom: 1rem;
            }}

            .search-input {{
                padding: 0.5rem;
                border: 1px solid #ddd;
                border-radius: 4px;
                width: 200px;
            }}

            .legend {{
                position: absolute;
                bottom: 20px;
                right: 20px;
                background: white;
                padding: 10px;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                z-index: 1000;
            }}

            @media (max-width: 768px) {{
                .controls {{
                    flex-direction: column;
                }}
                
                .stat-item {{
                    padding: 0.5rem;
                }}
                
                #map {{
                    height: 500px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1><i class="fas fa-bus"></i> Stockholm Bus Tracker</h1>
                <p>Real-time tracking of public transportation</p>
            </div>

            <div class="control-panel">
                <div class="filter-panel">
                    <input type="text" id="routeFilter" class="search-input" placeholder="Search by route number...">
                    <button class="button" onclick="clearFilters()">
                        <i class="fas fa-times"></i> Clear Filters
                    </button>
                    <button class="button" onclick="getUserLocation()">
                        <i class="fas fa-location-arrow"></i> My Location
                    </button>
                    <button class="button" onclick="toggleHeatmap()">
                        <i class="fas fa-fire"></i> Toggle Heatmap
                    </button>
                    <button class="button" onclick="refreshData()">
                        <i class="fas fa-sync"></i> Refresh Data
                    </button>
                </div>
            </div>

            <div id="map"></div>

            <div class="stats-panel">
                <div class="stat-item">
                    <div class="stat-value" id="activeBuses">0</div>
                    <div class="stat-label">Active Buses</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="averageSpeed">0</div>
                    <div class="stat-label">Avg. Speed (km/h)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="activeRoutes">0</div>
                    <div class="stat-label">Active Routes</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="lastUpdate">-</div>
                    <div class="stat-label">Last Update</div>
                </div>
            </div>
        </div>

        <script>
            let map;
            let markers = L.markerClusterGroup();
            let busPositions = {json.dumps(initial_positions)};
            let activeHeatmapLayer = null;
            let refreshInterval;

            function initMap() {{
                map = L.map('map').setView([59.3293, 18.0686], 12);

                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '© OpenStreetMap contributors'
                }}).addTo(map);
                
                map.addLayer(markers);
                updateStats();
                addBusMarkers();

                refreshInterval = setInterval(refreshData, 3000);
            }}

            function addBusMarkers() {{
                markers.clearLayers();
                busPositions.forEach(bus => {{
                    const marker = L.marker([bus.lat, bus.lng], {{
                        icon: L.divIcon({{
                            html: '<i class="fas fa-bus" style="color: #3498db; font-size: 20px;"></i>',
                            className: 'bus-marker',
                            iconSize: [20, 20],
                            iconAnchor: [10, 10]
                        }})
                    }}).bindPopup(`
                        <div class="bus-popup">
                            <h3>${{bus.vehicle_label}}</h3>
                            <div class="bus-info"><i class="fas fa-bus"></i> ID: ${{bus.id}}</div>
                            <div class="bus-info"><i class="fas fa-route"></i> Route: ${{bus.route_id}}</div>
                            <div class="bus-info"><i class="fas fa-clock"></i> Trip: ${{bus.trip_id}}</div>
                            <div class="bus-info"><i class="fas fa-arrow-circle-up"></i> Speed: ${{bus.speed.toFixed(1)}} km/h</div>
                            <div class="bus-info"><i class="fas fa-location-arrow"></i> Bearing: ${{bus.bearing.toFixed(1)}}°</div>
                            <div class="bus-info"><i class="fas fa-calendar-check"></i> Timestamp: ${{new Date(bus.timestamp * 1000).toLocaleString()}}</div>
                        </div>
                    `);
                    markers.addLayer(marker);
                }});
            }}

            function updateStats() {{
                const activeBuses = busPositions.length;
                const totalSpeed = busPositions.reduce((total, bus) => total + bus.speed, 0);
                const averageSpeed = activeBuses > 0 ? totalSpeed / activeBuses : 0;
                const activeRoutes = new Set(busPositions.map(bus => bus.route_id)).size;
                const lastUpdate = busPositions.length > 0 
                    ? new Date(Math.max(...busPositions.map(bus => bus.timestamp * 1000))).toLocaleString()
                    : '-';

                document.getElementById('activeBuses').textContent = activeBuses;
                document.getElementById('averageSpeed').textContent = averageSpeed.toFixed(2);
                document.getElementById('activeRoutes').textContent = activeRoutes;
                document.getElementById('lastUpdate').textContent = lastUpdate;
            }}

            function filterByRoute(routeNumber) {{
                if (!routeNumber) {{
                    clearFilters();
                    return;
                }}
                const filteredBuses = busPositions.filter(bus => 
                    bus.route_id.toString().toLowerCase().includes(routeNumber.toLowerCase())
                );
                addFilteredMarkers(filteredBuses);
                updateFilteredStats(filteredBuses);
            }}

            function addFilteredMarkers(filteredBuses) {{
                markers.clearLayers();
                filteredBuses.forEach(bus => {{
                    const marker = L.marker([bus.lat, bus.lng])
                        .bindPopup(`
                            <div class="bus-popup">
                                <h3>${{bus.vehicle_label}}</h3>
                                <div class="bus-info"><i class="fas fa-bus"></i> ID: ${{bus.id}}</div>
                                <div class="bus-info"><i class="fas fa-route"></i> Route: ${{bus.route_id}}</div>
                                <div class="bus-info"><i class="fas fa-clock"></i> Trip: ${{bus.trip_id}}</div>
                                <div class="bus-info"><i class="fas fa-arrow-circle-up"></i> Speed: ${{bus.speed.toFixed(1)}} km/h</div>
                                <div class="bus-info"><i class="fas fa-location-arrow"></i> Bearing: ${{bus.bearing.toFixed(1)}}°</div>
                                <div class="bus-info"><i class="fas fa-calendar-check"></i> Timestamp: ${{new Date(bus.timestamp * 1000).toLocaleString()}}</div>
                            </div>
                        `);
                    markers.addLayer(marker);
                }});
            }}

            function updateFilteredStats(filteredBuses) {{
                const activeBuses = filteredBuses.length;
                const totalSpeed = filteredBuses.reduce((total, bus) => total + bus.speed, 0);
                const averageSpeed = activeBuses > 0 ? totalSpeed / activeBuses : 0;
                const activeRoutes = new Set(filteredBuses.map(bus => bus.route_id)).size;
                const lastUpdate = filteredBuses.length > 0 
                    ? new Date(Math.max(...filteredBuses.map(bus => bus.timestamp * 1000))).toLocaleString()
                    : '-';

                document.getElementById('activeBuses').textContent = activeBuses;
                document.getElementById('averageSpeed').textContent = averageSpeed.toFixed(2);
                document.getElementById('activeRoutes').textContent = activeRoutes;
                document.getElementById('lastUpdate').textContent = lastUpdate;
            }}

            function clearFilters() {{
                document.getElementById('routeFilter').value = '';
                addBusMarkers();
                updateStats();
            }}

            function getUserLocation() {{
                if (navigator.geolocation) {{
                    navigator.geolocation.getCurrentPosition(function(position) {{
                        map.setView([position.coords.latitude, position.coords.longitude], 14);
                    }});
                }}
            }}

            function toggleHeatmap() {{
                if (activeHeatmapLayer) {{
                    map.removeLayer(activeHeatmapLayer);
                    activeHeatmapLayer = null;
                }} else {{
                    const heatData = busPositions.map(bus => [bus.lat, bus.lng, 1]);
                    activeHeatmapLayer = L.heatLayer(heatData, {{
                        radius: 25,
                        blur: 15,
                        maxZoom: 17,
                        max: 1.0
                    }}).addTo(map);
                }}
            }}

            async function refreshData() {{
                try {{
                    const response = await fetch('/');
                    const text = await response.text();
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(text, 'text/html');
                    const scriptContent = Array.from(doc.scripts)
                        .find(script => script.textContent.includes('busPositions ='))
                        .textContent;
                    
                    const match = scriptContent.match(/busPositions = (.+?);/);
                    if (match) {{
                        busPositions = JSON.parse(match[1]);
                        addBusMarkers();
                        updateStats();
                        
                        if (activeHeatmapLayer) {{
                            toggleHeatmap();
                            toggleHeatmap();
                        }}
                    }}
                }} catch (error) {{
                    console.error('Error refreshing data:', error);
                }}
            }}

            document.getElementById('routeFilter').addEventListener('input', (event) => {{
                filterByRoute(event.target.value);
            }});

            window.addEventListener('beforeunload', () => {{
                if (refreshInterval) {{
                    clearInterval(refreshInterval);
                }}
            }});

            initMap();
        </script>
    </body>
    </html>
    """
    return render_template_string(final_html)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
