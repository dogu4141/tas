document.addEventListener('DOMContentLoaded', function() {
    // Auto-increment load number
    const generateLoadNumberBtn = document.getElementById('generateLoadNumberBtn');
    const loadNumberInput = document.getElementById('load_number');
    
    if (generateLoadNumberBtn && loadNumberInput) {
        generateLoadNumberBtn.addEventListener('click', function() {
            // Generate a random load number with LD prefix and 6 digits
            const randomNum = Math.floor(100000 + Math.random() * 900000);
            loadNumberInput.value = `LD${randomNum}`;
        });
    }
    
    // Load position visualization
    const loadPositionContainer = document.getElementById('loadPositionContainer');
    const positionSelect = document.getElementById('position');
    
    if (loadPositionContainer) {
        // Create the load visualization grid
        createLoadVisualization();
        
        // Update position selector
        updateAvailablePositions();
    }
    
    // Create load visualization
    function createLoadVisualization() {
        if (!loadPositionContainer) return;
        
        loadPositionContainer.innerHTML = '';
        const loadLayout = document.createElement('div');
        loadLayout.className = 'load-layout';
        
        // Create the truck layout (2 rows of 4 positions each)
        const grid = document.createElement('div');
        grid.className = 'load-grid';
        
        for (let i = 1; i <= 8; i++) {
            const position = document.createElement('div');
            position.className = 'load-position';
            position.id = `load-position-${i}`;
            position.innerHTML = `<span>${i}</span>`;
            position.dataset.position = i;
            
            // Check if this position is already taken
            const isTaken = isPositionTaken(i);
            if (isTaken) {
                position.classList.add('position-taken');
                const vehicleInfo = getVehicleInfoForPosition(i);
                position.setAttribute('data-bs-toggle', 'tooltip');
                position.setAttribute('data-bs-placement', 'top');
                position.setAttribute('title', vehicleInfo);
                
                // Initialize tooltip
                new bootstrap.Tooltip(position);
            }
            
            grid.appendChild(position);
        }
        
        loadLayout.appendChild(grid);
        loadPositionContainer.appendChild(loadLayout);
        
        // Add legend
        const legend = document.createElement('div');
        legend.className = 'load-legend mt-2';
        legend.innerHTML = `
            <div class="d-flex align-items-center me-3">
                <div class="load-position-legend empty"></div>
                <small class="ms-1">Boş</small>
            </div>
            <div class="d-flex align-items-center">
                <div class="load-position-legend taken"></div>
                <small class="ms-1">Dolu</small>
            </div>
        `;
        loadPositionContainer.appendChild(legend);
    }
    
    // Check if a position is taken
    function isPositionTaken(position) {
        // For create page (using items in query params)
        const itemsParam = new URLSearchParams(window.location.search).get('items');
        if (itemsParam) {
            const items = itemsParam.split(',');
            for (const item of items) {
                const parts = item.split('|');
                if (parts.length >= 2 && parseInt(parts[1]) === position) {
                    return true;
                }
            }
        }
        
        // For edit page (using backend-rendered data)
        const positionElements = document.querySelectorAll('.load-item-position');
        for (const element of positionElements) {
            if (parseInt(element.textContent) === position) {
                return true;
            }
        }
        
        return false;
    }
    
    // Get vehicle info for a taken position
    function getVehicleInfoForPosition(position) {
        // For create page
        const itemsParam = new URLSearchParams(window.location.search).get('items');
        if (itemsParam) {
            const items = itemsParam.split(',');
            for (const item of items) {
                const parts = item.split('|');
                if (parts.length >= 2 && parseInt(parts[1]) === position) {
                    // Fetch vehicle info if available
                    const vehicleElements = document.querySelectorAll('.item-vehicle');
                    for (const element of vehicleElements) {
                        if (element.dataset.position === position.toString()) {
                            return element.textContent;
                        }
                    }
                    return `Pozisyon ${position}`;
                }
            }
        }
        
        // For edit page
        const loadItems = document.querySelectorAll('.load-item');
        for (const item of loadItems) {
            const positionElement = item.querySelector('.load-item-position');
            if (positionElement && parseInt(positionElement.textContent) === position) {
                const chassisElement = item.querySelector('.load-item-chassis');
                return chassisElement ? chassisElement.textContent : `Pozisyon ${position}`;
            }
        }
        
        return `Pozisyon ${position}`;
    }
    
    // Update available positions in select dropdown
    function updateAvailablePositions() {
        if (!positionSelect) return;
        
        // Clear existing options
        positionSelect.innerHTML = '';
        
        // Add options for each position
        for (let i = 1; i <= 8; i++) {
            if (!isPositionTaken(i)) {
                const option = document.createElement('option');
                option.value = i;
                option.textContent = i;
                positionSelect.appendChild(option);
            }
        }
        
        // If no positions available
        if (positionSelect.options.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Tüm pozisyonlar dolu';
            option.disabled = true;
            option.selected = true;
            positionSelect.appendChild(option);
        }
    }
    
    // Update visualization when form is submitted
    const addItemForm = document.getElementById('addItemForm');
    if (addItemForm) {
        addItemForm.addEventListener('submit', function() {
            setTimeout(function() {
                createLoadVisualization();
                updateAvailablePositions();
            }, 100);
        });
    }
    
    // Update visualization when an item is removed
    const removeItemBtns = document.querySelectorAll('.remove-item-btn');
    if (removeItemBtns) {
        removeItemBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                setTimeout(function() {
                    createLoadVisualization();
                    updateAvailablePositions();
                }, 100);
            });
        });
    }
    
    // Load status filter
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            const form = this.closest('form');
            if (form) form.submit();
        });
    }
});
