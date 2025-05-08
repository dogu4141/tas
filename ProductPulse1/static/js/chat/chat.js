// Chat functionality
document.addEventListener('DOMContentLoaded', function() {
    // Location sharing
    const locationButtons = document.querySelectorAll('.share-location-btn');
    
    if (locationButtons.length > 0) {
        locationButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Check if geolocation is supported
                if (navigator.geolocation) {
                    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Konum alınıyor...';
                    button.disabled = true;
                    
                    navigator.geolocation.getCurrentPosition(
                        // Success
                        function(position) {
                            const lat = position.coords.latitude;
                            const lng = position.coords.longitude;
                            
                            // Set hidden input values
                            document.getElementById('location_lat').value = lat;
                            document.getElementById('location_lng').value = lng;
                            
                            // Update button to indicate success
                            button.innerHTML = '<i class="fas fa-map-marker-alt"></i> Konum eklendi';
                            button.classList.remove('btn-outline-secondary');
                            button.classList.add('btn-success');
                            button.disabled = false;
                            
                            // Add message to inform user
                            const messageInput = document.getElementById('content');
                            if (messageInput && !messageInput.value.trim()) {
                                messageInput.value = 'Konum paylaşıyorum.';
                            }
                        },
                        // Error
                        function(error) {
                            console.error("Geolocation error:", error);
                            button.innerHTML = '<i class="fas fa-map-marker-alt"></i> Konum alınamadı';
                            button.classList.remove('btn-outline-secondary');
                            button.classList.add('btn-danger');
                            button.disabled = false;
                            
                            setTimeout(() => {
                                button.innerHTML = '<i class="fas fa-map-marker-alt"></i> Konum paylaş';
                                button.classList.remove('btn-danger');
                                button.classList.add('btn-outline-secondary');
                            }, 3000);
                        },
                        // Options
                        {
                            enableHighAccuracy: true,
                            timeout: 10000,
                            maximumAge: 0
                        }
                    );
                } else {
                    console.error("Geolocation is not supported by this browser.");
                    alert('Konumunuzu paylaşmak için bu tarayıcıda konum hizmetlerini etkinleştirmeniz gerekiyor.');
                }
            });
        });
    }
    
    // Real-time message display
    const messageForm = document.getElementById('messageForm');
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitButton = messageForm.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            
            fetch('/chat/send-message', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Clear the input fields
                    document.getElementById('content').value = '';
                    document.getElementById('attachment').value = '';
                    document.getElementById('location_lat').value = '';
                    document.getElementById('location_lng').value = '';
                    
                    // Reset location button if it exists
                    const locationButton = document.querySelector('.share-location-btn');
                    if (locationButton) {
                        locationButton.innerHTML = '<i class="fas fa-map-marker-alt"></i> Konum paylaş';
                        locationButton.classList.remove('btn-success');
                        locationButton.classList.add('btn-outline-secondary');
                    }
                    
                    // Reload messages or add the new message to the UI
                    // This could be enhanced to dynamically add the message without reloading
                    window.location.reload();
                } else {
                    console.error('Error sending message:', data.errors);
                    alert('Mesaj gönderilirken bir hata oluştu. Lütfen tekrar deneyin.');
                }
                
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fas fa-paper-plane"></i> Gönder';
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Mesaj gönderilirken bir hata oluştu. Lütfen tekrar deneyin.');
                
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fas fa-paper-plane"></i> Gönder';
            });
        });
    }
    
    // Initialize maps for location messages
    const mapContainers = document.querySelectorAll('.location-map');
    if (mapContainers.length > 0) {
        mapContainers.forEach(container => {
            const lat = parseFloat(container.dataset.lat);
            const lng = parseFloat(container.dataset.lng);
            
            if (!isNaN(lat) && !isNaN(lng)) {
                const map = L.map(container).setView([lat, lng], 13);
                
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }).addTo(map);
                
                L.marker([lat, lng]).addTo(map)
                    .bindPopup('Paylaşılan konum')
                    .openPopup();
            }
        });
    }
    
    // Message polling for real-time updates
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        let lastUpdate = new Date().toISOString();
        
        function checkForNewMessages() {
            fetch(`/chat/get-updates?last_update=${encodeURIComponent(lastUpdate)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.new_messages) {
                        // Update timestamp for next check
                        lastUpdate = new Date().toISOString();
                        
                        // Check if we need to refresh the page
                        if (data.direct_messages.length > 0 || data.group_messages.length > 0) {
                            // For simplicity, just reload the page
                            // This could be enhanced to dynamically add messages
                            window.location.reload();
                        }
                    }
                })
                .catch(error => console.error('Error checking for new messages:', error));
        }
        
        // Check for new messages every 15 seconds
        setInterval(checkForNewMessages, 15000);
    }
});