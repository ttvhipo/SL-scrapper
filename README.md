# Vehicle Positions Map

This project is a Flask-based web application that visualizes real-time bus positions in Stockholm, Sweden, using data from the Samtrafiken GTFS-Realtime API. The application displays the bus positions on an interactive map powered by Folium and Leaflet.js, with additional features like clustering and popups for detailed bus information.

## Features

- **Real-Time Bus Positions**: Fetches and displays real-time bus positions from the Samtrafiken GTFS-Realtime API.
- **Interactive Map**: Built using Folium and Leaflet.js, the map allows users to zoom, pan, and interact with bus markers.
- **Marker Clustering**: Uses Leaflet.markercluster to group nearby bus markers for better visualization.
- **Bus Information Popups**: Clicking on a bus marker displays detailed information such as route ID, vehicle label, speed, direction, and last update timestamp.
- **Auto-Update**: The map automatically updates bus positions every 4 seconds.
- **Geolocation**: Includes a button to center the map on the user's current location.

## How to Use

### Prerequisites

- Python 3.x
- Flask
- Folium
- Requests
- Google Protocol Buffers (`protobuf`)

### Installation

