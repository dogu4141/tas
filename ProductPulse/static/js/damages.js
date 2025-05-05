document.addEventListener('DOMContentLoaded', function() {
    const locationSelectBtn = document.getElementById('locationSelectBtn');
    const saveLocationBtn = document.getElementById('saveLocationBtn');
    const closeLocationModalBtn = document.getElementById('closeLocationModalBtn');
    const carImage = document.getElementById('carImage');
    const markerContainer = document.getElementById('markerContainer');
    const locationX = document.getElementById('location_x');
    const locationY = document.getElementById('location_y');
    const locationPreview = document.getElementById('locationPreview');
    
    let markers = [];
    
    // Initialize from existing data if available
    if (locationX && locationX.value && locationY && locationY.value) {
        try {
            const xValues = JSON.parse(locationX.value);
            const yValues = JSON.parse(locationY.value);
            
            if (Array.isArray(xValues) && Array.isArray(yValues) && xValues.length === yValues.length) {
                for (let i = 0; i < xValues.length; i++) {
                    markers.push({
                        x: xValues[i],
                        y: yValues[i],
                        number: i + 1
                    });
                }
                
                updateLocationPreview();
            }
        } catch (e) {
            console.error('Error parsing location data:', e);
        }
    }
    
    // Show location selection modal
    if (locationSelectBtn) {
        locationSelectBtn.addEventListener('click', function() {
            const locationModal = document.getElementById('locationSelectModal');
            if (locationModal) {
                const modal = new bootstrap.Modal(locationModal);
                modal.show();
                
                // Clear existing markers
                if (markerContainer) {
                    markerContainer.innerHTML = '';
                    
                    // Display existing markers if any
                    if (markers.length > 0) {
                        markers.forEach(function(marker, index) {
                            addMarkerToContainer(marker.x, marker.y, index + 1);
                        });
                    }
                }
            }
        });
    }
    
    // Save location markers
    if (saveLocationBtn) {
        saveLocationBtn.addEventListener('click', function() {
            if (locationX && locationY) {
                locationX.value = JSON.stringify(markers.map(m => m.x));
                locationY.value = JSON.stringify(markers.map(m => m.y));
                
                updateLocationPreview();
                
                const locationModal = document.getElementById('locationSelectModal');
                if (locationModal) {
                    const modal = bootstrap.Modal.getInstance(locationModal);
                    if (modal) modal.hide();
                }
            }
        });
    }
    
    // Close location modal without saving
    if (closeLocationModalBtn) {
        closeLocationModalBtn.addEventListener('click', function() {
            const locationModal = document.getElementById('locationSelectModal');
            if (locationModal) {
                const modal = bootstrap.Modal.getInstance(locationModal);
                if (modal) modal.hide();
            }
        });
    }
    
    // Add markers on image click
    if (carImage) {
        carImage.addEventListener('click', function(e) {
            const rect = carImage.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const markerNumber = markers.length + 1;
            
            // Add marker to the array
            markers.push({
                x: x,
                y: y,
                number: markerNumber
            });
            
            // Add visual marker
            addMarkerToContainer(x, y, markerNumber);
        });
    }
    
    // Function to add marker to the container
    function addMarkerToContainer(x, y, number) {
        if (!markerContainer) return;
        
        const marker = document.createElement('div');
        marker.className = 'marker';
        marker.style.left = `${x - 7.5}px`;
        marker.style.top = `${y - 7.5}px`;
        marker.style.display = 'block';
        marker.innerHTML = `<span class="marker-number">${number}</span>`;
        
        // Add remove functionality
        marker.addEventListener('click', function(e) {
            e.stopPropagation();
            removeMarker(number);
        });
        
        markerContainer.appendChild(marker);
    }
    
    // Function to remove a marker
    function removeMarker(number) {
        // Remove from array
        const index = markers.findIndex(m => m.number === number);
        if (index !== -1) {
            markers.splice(index, 1);
        }
        
        // Rebuild markers with new numbers
        markers = markers.map((m, i) => ({ ...m, number: i + 1 }));
        
        // Clear and rebuild container
        if (markerContainer) {
            markerContainer.innerHTML = '';
            markers.forEach(m => addMarkerToContainer(m.x, m.y, m.number));
        }
    }
    
    // Update location preview text
    function updateLocationPreview() {
        if (locationPreview) {
            if (markers.length === 0) {
                locationPreview.innerHTML = 'Hasar bölgesi seçilmedi';
            } else {
                locationPreview.innerHTML = `${markers.length} hasar bölgesi seçildi`;
            }
        }
    }
    
    // Initialize preview
    updateLocationPreview();
});
