// script.js

// Function to get the user's current location
function getUserLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            console.log("Your location:", lat, lon);
        }, function(error) {
            console.error("Error getting location:", error);
        });
    } else {
        console.log("Geolocation is not supported by this browser.");
    }
}

// Function to update the map every 4 seconds
function updateMap() {
    fetch('/update_map')
        .then(response => response.json())
        .then(data => {
            // Update the map content with the new HTML
            document.getElementById('map').innerHTML = data.map_html;
        })
        .catch(error => {
            console.error('Error updating map:', error);
        });
}

// Set an interval to update the map every 4 seconds
setInterval(updateMap, 4000);

// Call the location function once the page loads
window.onload = getUserLocation;
