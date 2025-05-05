/**
 * Hasar Yönetim Sistemi JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elementleri
    const chassisNumberInput = document.getElementById('chassis_number');
    const locationXInput = document.getElementById('location_x');
    const locationYInput = document.getElementById('location_y');
    const carImage = document.querySelector('.car-image');
    const markerContainer = document.getElementById('markerContainer');
    const damageForm = document.querySelector('form[id$="DamageForm"]');

    // Globals
    let markers = [];
    let markerCount = 0;
    
    // Hasar yerlerini işaretlemek için
    function setupDamageMarking() {
        if (!carImage || !markerContainer) return;
        
        // Eğer lokasyon koordinatları zaten varsa (düzenleme modu), onları yükle
        if (locationXInput && locationYInput && locationXInput.value && locationYInput.value) {
            try {
                const xCoords = JSON.parse(locationXInput.value);
                const yCoords = JSON.parse(locationYInput.value);
                
                if (Array.isArray(xCoords) && Array.isArray(yCoords) && xCoords.length === yCoords.length) {
                    for (let i = 0; i < xCoords.length; i++) {
                        addMarker(xCoords[i], yCoords[i]);
                    }
                }
            } catch (e) {
                console.error('Koordinat ayrıştırma hatası:', e);
            }
        }
        
        // Araç görseline tıklama
        carImage.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;
            
            addMarker(x, y);
            updateCoordinates();
        });
    }
    
    // Hasar işaretleyici ekle
    function addMarker(x, y) {
        markerCount++;
        
        const marker = document.createElement('div');
        marker.className = 'marker';
        marker.style.left = `${x}%`;
        marker.style.top = `${y}%`;
        marker.setAttribute('data-index', markerCount);
        
        const markerNumber = document.createElement('span');
        markerNumber.className = 'marker-number';
        markerNumber.textContent = markerCount;
        
        marker.appendChild(markerNumber);
        markerContainer.appendChild(marker);
        
        markers.push({ element: marker, x: x, y: y, index: markerCount });
        
        // İşaretleyici silme
        marker.addEventListener('click', function(e) {
            e.stopPropagation();
            removeMarker(this.getAttribute('data-index'));
        });
    }
    
    // Hasar işaretleyici kaldır
    function removeMarker(index) {
        const markerToRemove = markers.find(m => m.index == index);
        if (markerToRemove) {
            markerToRemove.element.remove();
            markers = markers.filter(m => m.index != index);
            updateCoordinates();
        }
    }
    
    // Koordinatları güncelle
    function updateCoordinates() {
        if (!locationXInput || !locationYInput) return;
        
        const xCoords = markers.map(m => m.x);
        const yCoords = markers.map(m => m.y);
        
        locationXInput.value = JSON.stringify(xCoords);
        locationYInput.value = JSON.stringify(yCoords);
    }
    
    // Şasi numarasına göre araç bilgilerini getir
    function setupChassisNumberLookup() {
        if (!chassisNumberInput) return;
        
        chassisNumberInput.addEventListener('blur', function() {
            const chassisNumber = this.value.trim();
            if (chassisNumber) {
                fetch(`/vehicles/api/vehicle-info?chassis_number=${chassisNumber}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            console.log('Araç bulundu:', data.vehicle);
                            // İlgili form alanlarını doldur
                            const vehicleIdInput = document.getElementById('vehicle_id');
                            if (vehicleIdInput) vehicleIdInput.value = data.vehicle.id;
                        } else {
                            console.log('Araç bulunamadı:', data.message);
                            // Hata mesajı göster
                            showAlert('Araç bulunamadı. Lütfen geçerli bir şasi numarası girin.', 'danger');
                        }
                    })
                    .catch(error => {
                        console.error('Araç verisi getirme hatası:', error);
                        showAlert('Araç bilgileri getirilirken bir hata oluştu.', 'danger');
                    });
            }
        });
    }
    
    // Hasar durum değiştirme
    function setupStatusChange() {
        const statusSelect = document.getElementById('status');
        if (!statusSelect) return;
        
        statusSelect.addEventListener('change', function() {
            const statusForm = this.closest('form');
            if (statusForm) {
                statusForm.submit();
            }
        });
    }
    
    // İrsaliye yazdırma önizleme
    function setupDeliveryPrint() {
        const printPreviewButtons = document.querySelectorAll('.print-preview-btn');
        if (printPreviewButtons.length === 0) return;
        
        printPreviewButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const deliveryId = this.getAttribute('data-id');
                
                // Yazdırma önizleme modalını aç
                fetch(`/deliveries/print-preview/${deliveryId}`)
                    .then(response => response.text())
                    .then(html => {
                        const printModal = document.getElementById('printPreviewModal');
                        const printContent = document.getElementById('printPreviewContent');
                        
                        if (printModal && printContent) {
                            printContent.innerHTML = html;
                            // Bootstrap modal'ı aç
                            const modal = new bootstrap.Modal(printModal);
                            modal.show();
                            
                            // Yazdır butonu
                            const printButton = document.getElementById('printButton');
                            if (printButton) {
                                printButton.addEventListener('click', function() {
                                    window.print();
                                });
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Yazdırma önizleme hatası:', error);
                        showAlert('Yazdırma önizleme yüklenirken bir hata oluştu.', 'danger');
                    });
            });
        });
    }
    
    // Uyarı mesajı göster
    function showAlert(message, type = 'info') {
        const alertPlaceholder = document.getElementById('alertPlaceholder');
        if (!alertPlaceholder) return;
        
        const wrapper = document.createElement('div');
        wrapper.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        alertPlaceholder.appendChild(wrapper);
        
        // 5 saniye sonra otomatik kapat
        setTimeout(() => {
            const alert = wrapper.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }
    
    // Hasar analizi grafiği
    function setupDamageAnalytics() {
        const damageChartCanvas = document.getElementById('damageChart');
        if (!damageChartCanvas) return;
        
        fetch('/damages/api/analytics')
            .then(response => response.json())
            .then(data => {
                const ctx = damageChartCanvas.getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Hasar Sayısı',
                            data: data.values,
                            backgroundColor: 'rgba(54, 162, 235, 0.5)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 1
                                }
                            }
                        }
                    }
                });
            })
            .catch(error => {
                console.error('Analiz verisi getirme hatası:', error);
            });
    }
    
    // Tüm sistemi başlat
    function initDamageSystem() {
        setupDamageMarking();
        setupChassisNumberLookup();
        setupStatusChange();
        setupDeliveryPrint();
        setupDamageAnalytics();
    }
    
    // Sistemi başlat
    initDamageSystem();
});