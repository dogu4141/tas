document.addEventListener('DOMContentLoaded', function() {
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
