document.addEventListener('DOMContentLoaded', function() {
    // Auto-increment delivery number
    const generateDeliveryNumberBtn = document.getElementById('generateDeliveryNumberBtn');
    const deliveryNumberInput = document.getElementById('delivery_number');
    
    if (generateDeliveryNumberBtn && deliveryNumberInput) {
        generateDeliveryNumberBtn.addEventListener('click', function() {
            // Generate a random delivery number with IR prefix and 6 digits
            const randomNum = Math.floor(100000 + Math.random() * 900000);
            deliveryNumberInput.value = `IR${randomNum}`;
        });
    }
    
    // Add chassis to delivery
    const addChassisForm = document.getElementById('addChassisForm');
    const chassisInput = document.getElementById('chassis_number');
    const chassisList = document.getElementById('chassisList');
    
    if (addChassisForm && chassisInput && chassisList) {
        addChassisForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const chassis = chassisInput.value.trim();
            if (!chassis) {
                alert('Lütfen bir şasi numarası girin');
                return;
            }
            
            // Check if already added
            const items = chassisList.querySelectorAll('li');
            for (let i = 0; i < items.length; i++) {
                if (items[i].dataset.chassis === chassis) {
                    alert('Bu şasi numarası zaten eklenmiş');
                    return;
                }
            }
            
            // Fetch vehicle info
            fetch(`/vehicles/api/vehicle-info?chassis_number=${chassis}`)
                .then(response => response.json())
                .then(data => {
                    let brand = 'Bilinmiyor';
                    let model = 'Bilinmiyor';
                    
                    if (data.status === 'success') {
                        brand = data.vehicle.brand;
                        model = data.vehicle.model;
                    }
                    
                    // Add to the list
                    const li = document.createElement('li');
                    li.className = 'list-group-item d-flex justify-content-between align-items-center';
                    li.dataset.chassis = chassis;
                    li.dataset.brand = brand;
                    li.dataset.model = model;
                    
                    li.innerHTML = `
                        <div>
                            <strong>${chassis}</strong>
                            <span class="text-muted ms-2">${brand} ${model}</span>
                        </div>
                        <button type="button" class="btn btn-sm btn-danger remove-chassis">
                            <i class="bi bi-trash"></i>
                        </button>
                    `;
                    
                    chassisList.appendChild(li);
                    
                    // Add remove button event
                    const removeBtn = li.querySelector('.remove-chassis');
                    removeBtn.addEventListener('click', function() {
                        li.remove();
                    });
                    
                    // Clear input
                    chassisInput.value = '';
                    chassisInput.focus();
                    
                    // Update hidden input with all chassis
                    updateChassisHiddenInput();
                })
                .catch(error => {
                    console.error('Error fetching vehicle info:', error);
                    alert('Araç bilgileri alınırken bir hata oluştu.');
                });
        });
    }
    
    // Update hidden input with all chassis
    function updateChassisHiddenInput() {
        const allChassisInput = document.getElementById('all_chassis');
        const items = chassisList.querySelectorAll('li');
        const chassisArray = [];
        
        items.forEach(item => {
            chassisArray.push({
                chassis: item.dataset.chassis,
                brand: item.dataset.brand,
                model: item.dataset.model
            });
        });
        
        if (allChassisInput) {
            allChassisInput.value = JSON.stringify(chassisArray);
        }
    }
    
    // Remove chassis from list
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-chassis') || e.target.closest('.remove-chassis')) {
            const button = e.target.classList.contains('remove-chassis') ? e.target : e.target.closest('.remove-chassis');
            const listItem = button.closest('li');
            
            if (listItem) {
                listItem.remove();
                updateChassisHiddenInput();
            }
        }
    });
    
    // Date range filter
    const dateFrom = document.getElementById('date_from');
    const dateTo = document.getElementById('date_to');
    
    if (dateFrom && dateTo) {
        [dateFrom, dateTo].forEach(input => {
            input.addEventListener('change', function() {
                const form = this.closest('form');
                if (form) form.submit();
            });
        });
    }
});
