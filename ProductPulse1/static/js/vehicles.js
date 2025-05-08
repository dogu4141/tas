function deleteVehicle(vehicleId) {
    if (confirm('Bu aracı silmek istediğinize emin misiniz?')) {
        fetch(`/vehicles/delete/${vehicleId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(response => {
            if (response.ok) {
                window.location.reload();
            } else {
                alert('Silme işlemi başarısız oldu.');
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Model modal elements
    const addModelBtn = document.getElementById('addModelBtn');
    const modelAddModal = document.getElementById('modelAddModal');
    const closeModelBtn = document.getElementById('closeModelModal');
    const saveModelBtn = document.getElementById('saveModelBtn');
    const modelNameInput = document.getElementById('modelName');
    
    // Initialize modal
    const modelModal = new bootstrap.Modal(modelAddModal, {
        backdrop: 'static',
        keyboard: false
    });
    
    // Show modal
    if (addModelBtn) {
        addModelBtn.addEventListener('click', () => {
            modelNameInput.value = '';
            modelModal.show();
        });
    }
    
    // Close modal
    if (closeModelBtn) {
        closeModelBtn.addEventListener('click', () => {
            modelModal.hide();
        });
    }
    
    // Save model
    if (saveModelBtn) {
        saveModelBtn.addEventListener('click', async () => {
            const modelName = modelNameInput.value.trim();
            
            if (!modelName) {
                alert('Model adı boş olamaz!');
                return;
            }
            
            try {
                const response = await fetch('/vehicles/api/add-model', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ model_name: modelName })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Refresh model dropdown
                    const modelSelect = document.getElementById('model');
                    if (modelSelect) {
                        const option = new Option(modelName, modelName);
                        modelSelect.add(option);
                    }
                    alert('Model başarıyla eklendi!');
                } else {
                    alert(data.message || 'Model eklenirken bir hata oluştu!');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Model eklenirken bir hata oluştu!');
            }
        });
    }
    // Vehicle search by chassis number
    const chassisSearchInput = document.getElementById('chassisSearch');
    const chassisSearchForm = document.getElementById('chassisSearchForm');
    
    if (chassisSearchInput && chassisSearchForm) {
        chassisSearchInput.addEventListener('keypress', function(e) {
            // Submit on Enter key
            if (e.key === 'Enter') {
                e.preventDefault();
                chassisSearchForm.submit();
            }
        });
    }
    
    // Auto-populate vehicle fields when chassis number is entered
    const chassisInput = document.getElementById('chassis_number');
    const brandInput = document.getElementById('brand');
    const modelInput = document.getElementById('model');
    const vehicleIdInput = document.getElementById('vehicle_id');
    
    if (chassisInput) {
        chassisInput.addEventListener('blur', function() {
            const chassisNumber = this.value.trim();
            if (chassisNumber) {
                fetch(`/vehicles/api/vehicle-info?chassis_number=${chassisNumber}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            const vehicle = data.vehicle;
                            
                            if (brandInput) brandInput.value = vehicle.brand;
                            if (modelInput) modelInput.value = vehicle.model;
                            if (vehicleIdInput) vehicleIdInput.value = vehicle.id;
                        } else {
                            // Clear the fields if vehicle not found
                            if (brandInput) brandInput.value = '';
                            if (modelInput) modelInput.value = '';
                            if (vehicleIdInput) vehicleIdInput.value = '';
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching vehicle info:', error);
                    });
            }
        });
    }
    
    // Vehicle status filter
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            const form = this.closest('form');
            if (form) form.submit();
        });
    }
    
    // Batch operations on vehicles
    const selectAllCheckbox = document.getElementById('selectAll');
    const vehicleCheckboxes = document.querySelectorAll('.vehicle-checkbox');
    const batchActionBtn = document.getElementById('batchActionBtn');
    const batchActionSelect = document.getElementById('batchAction');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            vehicleCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBatchActionButton();
        });
    }
    
    if (vehicleCheckboxes.length > 0) {
        vehicleCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                updateBatchActionButton();
                
                // Update selectAll checkbox state
                const allChecked = Array.from(vehicleCheckboxes).every(cb => cb.checked);
                const someChecked = Array.from(vehicleCheckboxes).some(cb => cb.checked);
                
                if (selectAllCheckbox) {
                    selectAllCheckbox.checked = allChecked;
                    selectAllCheckbox.indeterminate = someChecked && !allChecked;
                }
            });
        });
    }
    
    // Enable/disable batch action button based on selections
    function updateBatchActionButton() {
        if (batchActionBtn) {
            const anyChecked = Array.from(vehicleCheckboxes).some(cb => cb.checked);
            batchActionBtn.disabled = !anyChecked;
        }
    }
    
    // Handle batch action form submission
    const batchActionForm = document.getElementById('batchActionForm');
    if (batchActionForm && batchActionBtn) {
        batchActionBtn.addEventListener('click', function() {
            if (batchActionSelect && batchActionSelect.value) {
                if (confirm('Seçilen araçlar üzerinde bu işlemi gerçekleştirmek istediğinizden emin misiniz?')) {
                    batchActionForm.submit();
                }
            } else {
                alert('Lütfen bir işlem seçin');
            }
        });
    }
    
    // Initialize batch action button state
    updateBatchActionButton();
});
