// Global değişkenler
let records = [];
let drivers = [];
let models = [];
let logs = [];
let editHistory = {};
let selectedRecord = null;
let sortDirection = {};
let filteredRecords = [];
let damageChart = null;
let markers = []; // Birden fazla marker için global dizi

// Sayfalama için değişkenler
let currentDriverPage = 1;
let currentModelPage = 1;
let currentLogPage = 1; // Yeni: Geçmiş için sayfalama
let driversPerPage = 10;
let modelsPerPage = 10;
let logsPerPage = 10; // Yeni: Geçmiş için varsayılan gösterim adedi
// Mock veritabanı
const mockDatabase = {
    'W0VEDYHP9SN512197': { brand: 'OPEL', model: 'COMBO' }
};

// DOM yüklendiğinde
document.addEventListener('DOMContentLoaded', () => {
    // Elementleri tanımla
    const elements = {
        dashboardBtn: document.getElementById('dashboardBtn'),
        addRecordBtn: document.getElementById('addRecordBtn'),
        manageDriversBtn: document.getElementById('manageDriversBtn'),
        manageModelsBtn: document.getElementById('manageModelsBtn'),
        historyBtn: document.getElementById('historyBtn'),
        analyticsBtn: document.getElementById('analyticsBtn'),
        exportExcelBtn: document.getElementById('exportExcelBtn'),
        exportCsvBtn: document.getElementById('exportCsvBtn'),
        clearRangeBtn: document.getElementById('clearRangeBtn'),
        backupBtn: document.getElementById('backupBtn'),
        restoreBtn: document.getElementById('restoreBtn'),
        toggleThemeBtn: document.getElementById('toggleThemeBtn'),
        refreshBtn: document.getElementById('refreshBtn'),
        printBtn: document.getElementById('printBtn'),
        mainTitle: document.getElementById('mainTitle'),
        recordForm: document.getElementById('recordForm'),
        updateRecordBtn: document.getElementById('updateRecordBtn'),
        copyRecordBtn: document.getElementById('copyRecordBtn'),
        clearInputsBtn: document.getElementById('clearInputsBtn'),
        showAddDriverModalBtn: document.getElementById('showAddDriverModalBtn'),
        showDeleteDriverModalBtn: document.getElementById('showDeleteDriverModalBtn'),
        showAddModelModalBtn: document.getElementById('showAddModelModalBtn'),
        saveDriverBtn: document.getElementById('saveDriverBtn'),
        closeAddDriverModalBtn: document.getElementById('closeAddDriverModalBtn'),
        deleteDriverBtn: document.getElementById('deleteDriverBtn'),
        closeDeleteDriverModalBtn: document.getElementById('closeDeleteDriverModalBtn'),
        saveModelBtn: document.getElementById('saveModelBtn'),
        closeAddModelModalBtn: document.getElementById('closeAddModelModalBtn'),
        closeRecordDetailModalBtn: document.getElementById('closeRecordDetailModalBtn'),
        confirmClearRangeBtn: document.getElementById('confirmClearRangeBtn'),
        closeClearRangeModalBtn: document.getElementById('closeClearRangeModalBtn'),
        closeEditHistoryModalBtn: document.getElementById('closeEditHistoryModalBtn'),
        restoreFileInput: document.getElementById('restoreFileInput'),
        quickSearch: document.getElementById('quickSearch'),
        txtFilterChassis: document.getElementById('txtFilterChassis'),
        txtFilterDateStart: document.getElementById('txtFilterDateStart'),
        txtFilterDateEnd: document.getElementById('txtFilterDateEnd'),
        cmbFilterModel: document.getElementById('cmbFilterModel'),
        cmbFilterDriver: document.getElementById('cmbFilterDriver'),
        filterPeriod: document.getElementById('filterPeriod'),
        bulkDeleteBtn: document.getElementById('bulkDeleteBtn'),
        selectAllRecords: document.getElementById('selectAllRecords'),
        dashboardSection: document.getElementById('dashboardSection'),
        addRecordSection: document.getElementById('addRecordSection'),
        manageDriversSection: document.getElementById('manageDriversSection'),
        manageModelsSection: document.getElementById('manageModelsSection'),
        historySection: document.getElementById('historySection'),
        analyticsSection: document.getElementById('analyticsSection'),
        txtChassis: document.getElementById('txtChassis'),
        analyticsType: document.getElementById('analyticsType'),
        analyticsPeriod: document.getElementById('analyticsPeriod'),
        selectLocationBtn: document.getElementById('selectLocationBtn'),
        saveLocationBtn: document.getElementById('saveLocationBtn'),
        closeLocationModalBtn: document.getElementById('closeLocationModalBtn'),
        locationX: document.getElementById('locationX'),
        locationY: document.getElementById('locationY'),
        driversPerPage: document.getElementById('driversPerPage'),
        modelsPerPage: document.getElementById('modelsPerPage')
    };

    // Başlangıç işlemleri
    loadData();
    updateTable();
    updateDriverList();
    updateModelList();
    updateManagementLists();
    updateDashboardStats();
    updateHistoryTable();
    if (document.getElementById('quickSearch')) document.getElementById('quickSearch').focus();
    startAutoBackup();
	    if (elements.logsPerPage) elements.logsPerPage.addEventListener('change', () => {
        logsPerPage = elements.logsPerPage.value === 'all' ? Infinity : parseInt(elements.logsPerPage.value);
        currentLogPage = 1;
        updateHistoryTable();
    });

    // Sidebar navigasyon
    if (elements.dashboardBtn) elements.dashboardBtn.addEventListener('click', () => setActiveSection(elements, 'dashboardSection', 'Gösterge Paneli', updateDashboardStats));
    if (elements.addRecordBtn) elements.addRecordBtn.addEventListener('click', () => setActiveSection(elements, 'addRecordSection', 'Kayıt Ekle'));
    if (elements.manageDriversBtn) elements.manageDriversBtn.addEventListener('click', () => setActiveSection(elements, 'manageDriversSection', 'Şoför Yönetimi', updateManagementLists));
    if (elements.manageModelsBtn) elements.manageModelsBtn.addEventListener('click', () => setActiveSection(elements, 'manageModelsSection', 'Model Yönetimi', updateManagementLists));
    if (elements.historyBtn) elements.historyBtn.addEventListener('click', () => setActiveSection(elements, 'historySection', 'Geçmiş İşlemler', updateHistoryTable));
    if (elements.analyticsBtn) elements.analyticsBtn.addEventListener('click', () => setActiveSection(elements, 'analyticsSection', 'Hasar Analizi', updateDamageChart));
    if (elements.exportExcelBtn) elements.exportExcelBtn.addEventListener('click', exportToExcel);
    if (elements.exportCsvBtn) elements.exportCsvBtn.addEventListener('click', exportToCsv);
    if (elements.clearRangeBtn) elements.clearRangeBtn.addEventListener('click', showClearRangeModal);
    if (elements.backupBtn) elements.backupBtn.addEventListener('click', backupData);
    if (elements.restoreBtn) elements.restoreBtn.addEventListener('click', () => elements.restoreFileInput.click());
    if (elements.toggleThemeBtn) elements.toggleThemeBtn.addEventListener('click', toggleTheme);
    if (elements.refreshBtn) elements.refreshBtn.addEventListener('click', refresh);
    if (elements.printBtn) elements.printBtn.addEventListener('click', showPrintPreview);

    // Form olayları
    if (elements.recordForm) elements.recordForm.addEventListener('submit', addRecord);
    if (elements.updateRecordBtn) elements.updateRecordBtn.addEventListener('click', updateRecord);
    if (elements.copyRecordBtn) elements.copyRecordBtn.addEventListener('click', copyRecord);
    if (elements.clearInputsBtn) elements.clearInputsBtn.addEventListener('click', clearInputs);
    if (elements.txtChassis) elements.txtChassis.addEventListener('input', () => {
        const chassis = elements.txtChassis.value.trim();
        const vehicle = mockDatabase[chassis] || { model: '' };
        document.getElementById('cmbModel').value = vehicle.model;
    });

    // Yer seçimi popup olayları
    if (elements.selectLocationBtn) elements.selectLocationBtn.addEventListener('click', () => {
        showModal('locationSelectModal');
        const carImage = document.getElementById('carImage');
        const markerContainer = document.getElementById('markerContainer');
        markerContainer.innerHTML = '';
        markers = [];

        const handleClick = (e) => {
            const rect = carImage.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const markerNumber = markers.length + 1;

            const marker = document.createElement('div');
            marker.className = 'marker';
            marker.style.left = `${x - 7.5}px`;
            marker.style.top = `${y - 7.5}px`;
            marker.style.display = 'block';
            marker.innerHTML = `<span class="marker-number">${markerNumber}</span>`;
            markerContainer.appendChild(marker);

            markers.push({ x, y, number: markerNumber });
            elements.locationX.value = JSON.stringify(markers.map(m => m.x));
            elements.locationY.value = JSON.stringify(markers.map(m => m.y));
            document.getElementById('locationPreview').innerHTML = `<span>${markers.length} hasar yeri seçildi</span>`;
        };

        carImage.removeEventListener('click', handleClick);
        carImage.addEventListener('click', handleClick);
    });

    if (elements.saveLocationBtn) elements.saveLocationBtn.addEventListener('click', () => {
        closeModal('locationSelectModal');
        showMessage("Hasar yerleri kaydedildi!", "success");
    });

    if (elements.closeLocationModalBtn) elements.closeLocationModalBtn.addEventListener('click', () => {
        closeModal('locationSelectModal');
        document.getElementById('markerContainer').innerHTML = '';
    });

    // Modal olayları
    if (elements.showAddDriverModalBtn) elements.showAddDriverModalBtn.addEventListener('click', showAddDriverModal);
    if (elements.showDeleteDriverModalBtn) elements.showDeleteDriverModalBtn.addEventListener('click', showDeleteDriverModal);
    if (elements.showAddModelModalBtn) elements.showAddModelModalBtn.addEventListener('click', showAddModelModal);
    if (elements.saveDriverBtn) elements.saveDriverBtn.addEventListener('click', saveDriver);
    if (elements.closeAddDriverModalBtn) elements.closeAddDriverModalBtn.addEventListener('click', () => closeModal('addDriverModal'));
    if (elements.deleteDriverBtn) elements.deleteDriverBtn.addEventListener('click', deleteDriver);
    if (elements.closeDeleteDriverModalBtn) elements.closeDeleteDriverModalBtn.addEventListener('click', () => closeModal('deleteDriverModal'));
    if (elements.saveModelBtn) elements.saveModelBtn.addEventListener('click', saveModel);
    if (elements.closeAddModelModalBtn) elements.closeAddModelModalBtn.addEventListener('click', () => closeModal('addModelModal'));
    if (elements.closeRecordDetailModalBtn) elements.closeRecordDetailModalBtn.addEventListener('click', () => closeModal('recordDetailModal'));
    if (elements.confirmClearRangeBtn) elements.confirmClearRangeBtn.addEventListener('click', clearRange);
    if (elements.closeClearRangeModalBtn) elements.closeClearRangeModalBtn.addEventListener('click', () => closeModal('clearRangeModal'));
    if (elements.closeEditHistoryModalBtn) elements.closeEditHistoryModalBtn.addEventListener('click', () => closeModal('editHistoryModal'));
    if (elements.restoreFileInput) elements.restoreFileInput.addEventListener('change', restoreData);

    // Filtreleme olayları
    const resetOtherFilters = (currentElement) => {
        ['quickSearch', 'txtFilterChassis', 'txtFilterDateStart', 'txtFilterDateEnd', 'cmbFilterModel', 'cmbFilterDriver', 'filterPeriod'].forEach(id => {
            if (elements[id] !== currentElement) elements[id].value = '';
        });
    };

    if (elements.quickSearch) elements.quickSearch.addEventListener('input', () => { resetOtherFilters(elements.quickSearch); filterRecords(); });
    if (elements.txtFilterChassis) elements.txtFilterChassis.addEventListener('input', () => { resetOtherFilters(elements.txtFilterChassis); filterRecords(); });
    if (elements.txtFilterDateStart) elements.txtFilterDateStart.addEventListener('change', () => { resetOtherFilters(elements.txtFilterDateStart); filterRecords(); });
    if (elements.txtFilterDateEnd) elements.txtFilterDateEnd.addEventListener('change', () => { resetOtherFilters(elements.txtFilterDateEnd); filterRecords(); });
    if (elements.cmbFilterModel) elements.cmbFilterModel.addEventListener('change', () => { resetOtherFilters(elements.cmbFilterModel); filterRecords(); });
    if (elements.cmbFilterDriver) elements.cmbFilterDriver.addEventListener('change', () => { resetOtherFilters(elements.cmbFilterDriver); filterRecords(); });

    if (elements.filterPeriod) elements.filterPeriod.addEventListener('change', () => {
        const period = elements.filterPeriod.value;
        resetOtherFilters(elements.filterPeriod);
        const today = new Date();
        switch (period) {
            case 'today':
                elements.txtFilterDateStart.value = elements.txtFilterDateEnd.value = today.toISOString().split('T')[0];
                break;
            case 'yesterday':
                const yesterday = new Date(today);
                yesterday.setDate(today.getDate() - 1);
                elements.txtFilterDateStart.value = elements.txtFilterDateEnd.value = yesterday.toISOString().split('T')[0];
                break;
            case 'last7days':
                const last7Days = new Date(today);
                last7Days.setDate(today.getDate() - 7);
                elements.txtFilterDateStart.value = last7Days.toISOString().split('T')[0];
                elements.txtFilterDateEnd.value = today.toISOString().split('T')[0];
                break;
            case 'thismonth':
                const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
                elements.txtFilterDateStart.value = firstDay.toISOString().split('T')[0];
                elements.txtFilterDateEnd.value = today.toISOString().split('T')[0];
                break;
        }
        filterRecords();
    });

    if (elements.bulkDeleteBtn) elements.bulkDeleteBtn.addEventListener('click', bulkDeleteRecords);
    if (elements.selectAllRecords) elements.selectAllRecords.addEventListener('change', (e) => {
        document.querySelectorAll('.record-checkbox').forEach(cb => cb.checked = e.target.checked);
    });

    document.querySelectorAll('#recordsTable th[data-sort]').forEach(header => {
        header.addEventListener('click', () => sortTable(header.getAttribute('data-sort')));
    });

    if (elements.analyticsType) elements.analyticsType.addEventListener('change', updateDamageChart);
    if (elements.analyticsPeriod) elements.analyticsPeriod.addEventListener('change', updateDamageChart);

    if (elements.driversPerPage) elements.driversPerPage.addEventListener('change', () => {
        driversPerPage = elements.driversPerPage.value === 'all' ? Infinity : parseInt(elements.driversPerPage.value);
        currentDriverPage = 1;
        updateDriverManagementList();
    });

    if (elements.modelsPerPage) elements.modelsPerPage.addEventListener('change', () => {
        modelsPerPage = elements.modelsPerPage.value === 'all' ? Infinity : parseInt(elements.modelsPerPage.value);
        currentModelPage = 1;
        updateModelManagementList();
    });

    // Sidebar toggle (mobil için)
    const sidebar = document.querySelector('.sidebar');
    const header = document.querySelector('.main-header');
    if (header) header.addEventListener('click', (e) => {
        if (window.innerWidth <= 480 && e.target.closest('.main-header')) sidebar.classList.toggle('active');
    });

    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 480 && !sidebar.contains(e.target) && !header.contains(e.target)) sidebar.classList.remove('active');
    });

    // Modal ESC dinleyicileri
    ['addDriverModal', 'addModelModal', 'clearRangeModal', 'locationSelectModal', 'printPreviewModal'].forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (modal) modal.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (modalId === 'addDriverModal') elements.saveDriverBtn.click();
                else if (modalId === 'addModelModal') elements.saveModelBtn.click();
                else if (modalId === 'clearRangeModal') elements.confirmClearRangeBtn.click();
                else if (modalId === 'locationSelectModal') elements.saveLocationBtn.click();
                else if (modalId === 'printPreviewModal') elements.printBtn.click();
            } else if (e.key === 'Escape') closeModal(modalId);
        });
    });
});

// Verileri yükleme
function loadData() {
    records = JSON.parse(localStorage.getItem('records')) || [];
    drivers = JSON.parse(localStorage.getItem('drivers')) || [];
    models = JSON.parse(localStorage.getItem('models')) || [];
    logs = JSON.parse(localStorage.getItem('logs')) || [];
    editHistory = JSON.parse(localStorage.getItem('editHistory')) || {};
    const theme = localStorage.getItem('theme');
    if (theme === 'dark') document.body.classList.add('dark-theme');
}

// Verileri kaydetme
function saveData() {
    localStorage.setItem('records', JSON.stringify(records));
    localStorage.setItem('drivers', JSON.stringify(drivers));
    localStorage.setItem('models', JSON.stringify(models));
    localStorage.setItem('logs', JSON.stringify(logs));
    localStorage.setItem('editHistory', JSON.stringify(editHistory));
}

// Log kaydı
function addLog(action, detail) {
    logs.push({ date: new Date().toLocaleString('tr-TR'), action, detail });
    if (logs.length > 50) logs.shift();
    saveData();
    updateHistoryTable();
}

// Edit geçmişi ekleme
function addEditHistory(chassisNumber, oldRecord) {
    if (!editHistory[chassisNumber]) editHistory[chassisNumber] = [];
    editHistory[chassisNumber].push({
        date: new Date().toLocaleString('tr-TR'),
        oldData: { ...oldRecord }
    });
    saveData();
}

// Aktif bölüm değiştirme
function setActiveSection(elements, sectionId, title, callback) {
    ['dashboardSection', 'addRecordSection', 'manageDriversSection', 'manageModelsSection', 'historySection', 'analyticsSection'].forEach(id => {
        elements[id].style.display = id === sectionId ? 'block' : 'none';
    });
    ['dashboardBtn', 'addRecordBtn', 'manageDriversBtn', 'manageModelsBtn', 'historyBtn', 'analyticsBtn'].forEach(btn => {
        elements[btn].classList.toggle('active', btn === `${sectionId.replace('Section', 'Btn')}`);
    });
    elements.mainTitle.textContent = title;
    if (callback) callback();
}

// Kayıt ekleme
function addRecord(e) {
    e.preventDefault();
    if (!validateInputs()) return;

    const chassis = document.getElementById('txtChassis').value.trim();
    if (records.some(r => r.chassisNumber === chassis && !selectedRecord)) {
        showMessage("Bu şasi numarası zaten kayıtlı!", "error");
        return;
    }

    const record = {
        date: formatDate(document.getElementById('txtDate').value),
        chassisNumber: chassis,
        model: document.getElementById('cmbModel').value,
        driverInfo: document.getElementById('cmbDriver').value,
        group: document.getElementById('groupList').options[document.getElementById('groupList').selectedIndex].text,
        description: document.getElementById('descriptionList').options[document.getElementById('descriptionList').selectedIndex].text,
        level: document.getElementById('levelList').options[document.getElementById('levelList').selectedIndex].text,
        explanation: document.getElementById('txtExplanation').value.trim(),
        notes: document.getElementById('txtNotes').value.trim(),
        locations: document.getElementById('locationX').value ? 
            markers.map(m => ({ x: m.x, y: m.y, number: m.number })) : []
    };

    records.push(record);
    saveData();
    addLog("Kayıt Ekle", `Şasi No: ${record.chassisNumber}`);
    showMessage("Kayıt başarıyla eklendi!", "success");
    clearInputs();
    updateTable();
    updateManagementLists();
    updateDashboardStats();
    updateDamageChart();
}

// Kayıt güncelleme
function updateRecord() {
    if (!selectedRecord) {
        showMessage("Lütfen bir kayıt seçin!", "warning");
        return;
    }
    if (!validateInputs()) return;

    const chassis = document.getElementById('txtChassis').value.trim();
    if (selectedRecord.chassisNumber !== chassis) {
        showMessage("Şasi numarası değiştirilemez!", "error");
        return;
    }

    const index = records.findIndex(r => r.chassisNumber === chassis);
    const oldRecord = { ...records[index] };
    records[index] = {
        date: formatDate(document.getElementById('txtDate').value),
        chassisNumber: chassis,
        model: document.getElementById('cmbModel').value,
        driverInfo: document.getElementById('cmbDriver').value,
        group: document.getElementById('groupList').options[document.getElementById('groupList').selectedIndex].text,
        description: document.getElementById('descriptionList').options[document.getElementById('descriptionList').selectedIndex].text,
        level: document.getElementById('levelList').options[document.getElementById('levelList').selectedIndex].text,
        explanation: document.getElementById('txtExplanation').value.trim(),
        notes: document.getElementById('txtNotes').value.trim(),
        locations: document.getElementById('locationX').value ? 
            markers.map(m => ({ x: m.x, y: m.y, number: m.number })) : []
    };

    addEditHistory(chassis, oldRecord);
    saveData();
    addLog("Kayıt Güncelle", `Şasi No: ${chassis}`);
    showMessage("Kayıt güncellendi!", "success");
    clearInputs();
    updateTable();
    updateManagementLists();
    updateDashboardStats();
    updateDamageChart();
}

// Kayıt kopyalama
function copyRecord() {
    if (!selectedRecord) {
        showMessage("Lütfen bir kayıt seçin!", "warning");
        return;
    }

    const popup = document.createElement('div');
    popup.className = 'modal show';
    popup.innerHTML = `
        <div class="modal-content">
            <h3>Yeni Şasi Numarası Girin</h3>
            <div class="form-group">
                <label for="newChassisInput">Yeni Şasi Numarası</label>
                <input type="text" id="newChassisInput" placeholder="Yeni Şasi Numarası" />
            </div>
            <div class="modal-actions">
                <button type="button" class="btn btn-primary" onclick="confirmCopyRecord()">Kaydet</button>
                <button type="button" class="btn btn-neutral" onclick="this.closest('.modal').remove()">Kapat</button>
            </div>
        </div>
    `;
    document.body.appendChild(popup);
    document.getElementById('newChassisInput').focus();
}

function confirmCopyRecord() {
    const newChassis = document.getElementById('newChassisInput').value.trim();
    if (!newChassis) {
        showMessage("Şasi numarası zorunludur!", "error");
        return;
    }

    if (records.some(r => r.chassisNumber === newChassis)) {
        showMessage("Bu şasi numarası zaten kayıtlı!", "error");
        return;
    }

    const newRecord = { ...selectedRecord, chassisNumber: newChassis };
    records.push(newRecord);
    saveData();
    addLog("Kayıt Kopyala", `Yeni Şasi No: ${newChassis}`);
    showMessage("Kayıt kopyalandı!", "success");
    clearInputs();
    updateTable();
    updateManagementLists();
    updateDashboardStats();
    updateDamageChart();
    document.querySelector('.modal').remove();
}

// Giriş doğrulama
function validateInputs() {
    const inputs = [
        { id: 'txtDate', message: "Tarih zorunludur!" },
        { id: 'txtChassis', message: "Şasi No zorunludur!" },
        { id: 'cmbModel', message: "Model zorunludur!" },
        { id: 'groupList', message: "Grup zorunludur!" },
        { id: 'descriptionList', message: "Tanım zorunludur!" },
        { id: 'levelList', message: "Seviye zorunludur!" }
    ];

    for (let input of inputs) {
        const element = document.getElementById(input.id);
        if (!element || !element.value.trim()) {
            showMessage(input.message, "error");
            return false;
        }
    }
    return true;
}

// Girişleri temizleme
function clearInputs() {
    ['txtDate', 'txtChassis', 'cmbModel', 'cmbDriver', 'groupList', 'descriptionList', 'levelList', 'txtExplanation', 'txtNotes', 'locationX', 'locationY'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.value = '';
            if (id === 'txtChassis') element.readOnly = false;
        }
    });
    document.getElementById('locationPreview').innerHTML = '';
    selectedRecord = null;
    markers = [];
    document.getElementById('updateRecordBtn').style.display = 'none';
}

// Hasar yeri gösterme (Güncellendi)
function showDamageLocation(locations) {
    // locations parametresinin bir dizi olduğundan emin ol
    if (!Array.isArray(locations) || locations.length === 0) {
        showMessage("Hasar yeri bilgisi bulunamadı!", "warning");
        return;
    }

    // Mevcut bir popup varsa kaldır
    const existingPopup = document.getElementById('damageLocationModal');
    if (existingPopup) existingPopup.remove();

    // Yeni popup oluştur
    const popup = document.createElement('div');
    popup.className = 'modal show';
    popup.id = 'damageLocationModal';
    popup.innerHTML = `
        <div class="modal-content">
            <h3>Hasar Yerleri</h3>
            <div class="car-image-container" style="position: relative;">
                <img id="damageCarImage" src="https://ares.rsservis.com.tr/css/otoekspertiz/img/kaporta_svg/9.svg" alt="Car Image" style="width: 100%; height: auto;" />
                <div id="damageMarkerContainer" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></div>
            </div>
            <div class="modal-actions">
                <button type="button" class="btn btn-neutral" id="closeDamageLocationModalBtn">Kapat</button>
            </div>
        </div>
    `;
    document.body.appendChild(popup);

    // Marker'ları yerleştir
    const markerContainer = document.getElementById('damageMarkerContainer');
    locations.forEach(loc => {
        if (loc.x !== undefined && loc.y !== undefined && loc.number !== undefined) {
            const marker = document.createElement('div');
            marker.className = 'marker';
            marker.style.left = `${loc.x - 7.5}px`; // Marker'ın merkezini ayarlamak için
            marker.style.top = `${loc.y - 7.5}px`;
            marker.style.display = 'block';
            marker.innerHTML = `<span class="marker-number">${loc.number}</span>`;
            markerContainer.appendChild(marker);
        }
    });

    // Kapat butonuna tıklama olayı
    document.getElementById('closeDamageLocationModalBtn').addEventListener('click', () => {
        popup.remove();
    });

    // ESC tuşu ile kapatma
    popup.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            popup.remove();
        }
    });

    // Popup açıldığında odaklanmasını sağla
    popup.focus();
}

// Yazdır Ön İzleme Gösterme
function showPrintPreview() {
    if (!filteredRecords.length) {
        showMessage("Yazdırılacak kayıt bulunamadı!", "error");
        return;
    }

    const printPreview = document.getElementById('printPreview');
    printPreview.innerHTML = `
        <div class="print-header">
            <h2>Hasar Kayıtları</h2>
            <p>Taşdanlar Otomotiv - ${new Date().toLocaleDateString('tr-TR')}</p>
        </div>
        <table id="printTable">
            <thead>
                <tr>
                    <th>Tarih</th>
                    <th>Şasi No</th>
                    <th>Model</th>
                    <th>Şoför</th>
                    <th>Grup</th>
                    <th>Tanım</th>
                    <th>Seviye</th>
                    <th>Açıklama</th>
                    <th>Notlar</th>
                </tr>
            </thead>
            <tbody>
                ${filteredRecords.map(record => `
                    <tr>
                        <td>${record.date}</td>
                        <td>${record.chassisNumber}</td>
                        <td>${record.model}</td>
                        <td>${record.driverInfo || '-'}</td>
                        <td>${record.group}</td>
                        <td>${record.description}</td>
                        <td>${record.level}</td>
                        <td>${record.explanation || '-'}</td>
                        <td>${record.notes || '-'}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
        <div class="print-footer">
            <p>Toplam Kayıt: ${filteredRecords.length}</p>
        </div>
    `;
    showModal('printPreviewModal');
}

// Kayıtları Yazdır
function printRecords() {
    const printContent = document.getElementById('printPreview').innerHTML;
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
            <head>
                <title>Hasar Kayıtları - Taşdanlar Otomotiv</title>
                <style>
                    body {
                        margin: 0;
                        font-family: 'Inter', sans-serif;
                        font-size: 8px;
                        color: #333;
                    }
                    .print-container {
                        width: 210mm;
                        height: 297mm;
                        padding: 10mm;
                        box-sizing: border-box;
                        position: relative;
                        background: #fff;
                        border: 2px solid #2563eb;
                        /* Dört kenarda "Taşdanlar" yazısı için çerçeve */
                        background-image:
                            repeating-linear-gradient(0deg, transparent, transparent 20px, #2563eb 20px, #2563eb 22px),
                            repeating-linear-gradient(90deg, transparent, transparent 20px, #2563eb 20px, #2563eb 22px),
                            repeating-linear-gradient(180deg, transparent, transparent 20px, #2563eb 20px, #2563eb 22px),
                            repeating-linear-gradient(270deg, transparent, transparent 20px, #2563eb 20px, #2563eb 22px);
                        background-size: 2px 100%, 100% 2px, 2px 100%, 100% 2px;
                        background-position: 0 0, 0 0, 100% 0, 0 100%;
                        background-repeat: repeat;
                    }
                    .print-container::before {
                        content: "Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar";
                        position: absolute;
                        top: -8px;
                        left: 0;
                        width: 100%;
                        font-size: 6px;
                        color: #2563eb;
                        letter-spacing: 5px;
                        white-space: nowrap;
                        overflow: hidden;
                    }
                    .print-container::after {
                        content: "Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar";
                        position: absolute;
                        bottom: -8px;
                        left: 0;
                        width: 100%;
                        font-size: 6px;
                        color: #2563eb;
                        letter-spacing: 5px;
                        white-space: nowrap;
                        overflow: hidden;
                    }
                    .print-container::before,
                    .print-container::after {
                        transform-origin: center;
                    }
                    .print-container .left-border,
                    .print-container .right-border {
                        position: absolute;
                        top: 0;
                        height: 100%;
                        width: 10px;
                        font-size: 6px;
                        color: #2563eb;
                        writing-mode: vertical-rl;
                        text-align: center;
                        letter-spacing: 5px;
                    }
                    .print-container .left-border {
                        left: -8px;
                        content: "Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar";
                    }
                    .print-container .right-border {
                        right: -8px;
                        content: "Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar";
                    }
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        font-size: 8px;
                        margin-bottom: 20px;
                    }
                    th, td {
                        border: 1px solid #ddd;
                        padding: 6px;
                        text-align: left;
                    }
                    th {
                        background: #f0f0f0;
                        font-weight: 600;
                    }
                    .signature-section {
                        margin-top: 20px;
                        display: flex;
                        justify-content: space-between;
                        border-top: 1px solid #ddd;
                        padding-top: 10px;
                    }
                    .signature-box {
                        width: 30%;
                        text-align: center;
                    }
                    .signature-box p {
                        margin: 5px 0;
                        border-top: 1px solid #000;
                        padding-top: 10px;
                        font-size: 8px;
                    }
                    .print-footer {
                        position: absolute;
                        bottom: 5mm;
                        width: calc(100% - 20mm);
                        text-align: center;
                        font-size: 8px;
                        color: #666;
                        border-top: 1px solid #ddd;
                        padding-top: 3px;
                    }
                    .print-footer p {
                        margin: 2px 0;
                    }
                </style>
            </head>
            <body>
                <div class="print-container">
                    <div class="left-border">Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar</div>
                    <div class="right-border">Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar Taşdanlar</div>
                    ${printContent}
                    <div class="signature-section">
                        <div class="signature-box">
                            <p>Yetkili İmza</p>
                        </div>
                        <div class="signature-box">
                            <p>Şoför İmza</p>
                        </div>
                        <div class="signature-box">
                            <p>Kontrol Eden</p>
                        </div>
                    </div>
                    <div class="print-footer">
                        <p><strong>Taşdanlar Otomotiv</strong> - © ${new Date().getFullYear()}</p>
                        <p>Adres: [Adres Bilgisi] | Telefon: [Telefon Numarası] | E-posta: [E-posta Adresi]</p>
                        <p>Toplam Kayıt: ${filteredRecords.length}</p>
                    </div>
                </div>
            </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
    printWindow.close();
    closeModal('printPreviewModal');
}
// Tablo güncelleme (Tooltip'ler zaten ekliydi, CSS ile iyileştirildi)
function updateTable(data = records) {
    filteredRecords = data;
    const tbody = document.getElementById('recordsTableBody');
    if (!tbody) return;

    tbody.innerHTML = filteredRecords.map((record, index) => {
        const truncateText = (text, maxLength = 20) => {
            if (!text || text === '-') return text;
            return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;
        };

        const levelClass = record.level && typeof record.level === 'string' 
            ? `level-${record.level.split(' ')[0]}` 
            : 'level-default';

        // "Seçildi" linkinin güncellenmiş hali
        const locationLink = record.locations && Array.isArray(record.locations) && record.locations.length > 0
            ? `<a href="#" class="location-link" data-locations='${JSON.stringify(record.locations)}'>Seçildi (${record.locations.length} yer)</a>`
            : 'Seçilmedi';

        return `
            <tr class="${levelClass}">
                <td><input type="checkbox" class="record-checkbox" data-chassis="${record.chassisNumber}"></td>
                <td>${record.date || '-'}</td>
                <td>${record.chassisNumber || '-'}</td>
                <td>${record.model || '-'}</td>
                <td data-tooltip="${record.driverInfo || '-'}">${truncateText(record.driverInfo || '-')}</td>
                <td data-tooltip="${record.group || '-'}">${truncateText(record.group || '-')}</td>
                <td data-tooltip="${record.description || '-'}">${truncateText(record.description || '-')}</td>
                <td data-tooltip="${record.level || '-'}">${truncateText(record.level || '-')}</td>
                <td data-tooltip="${record.explanation || '-'}">${truncateText(record.explanation || '-')}</td>
                <td data-tooltip="${record.notes || '-'}">${truncateText(record.notes || '-')}</td>
                <td>${locationLink}</td>
                <td>
                    <div class="table-actions">
                        <button class="table-btn view" onclick="viewRecord('${record.chassisNumber}')">Görüntüle</button>
                        <button class="table-btn edit" onclick="editRecord('${record.chassisNumber}')">Düzenle</button>
                        <button class="table-btn delete" onclick="deleteRecord('${record.chassisNumber}')">Sil</button>
                        <button class="table-btn history" onclick="viewEditHistory('${record.chassisNumber}')">Geçmiş</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');

    // "Seçildi" linklerine tıklama olayını ekle
    document.querySelectorAll('.location-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const locations = JSON.parse(link.getAttribute('data-locations'));
            showDamageLocation(locations);
        });
    });

    updateDashboardStats();
}
// Dashboard istatistikleri
function updateDashboardStats() {
    const totalRecords = document.getElementById('totalRecords');
    const totalDrivers = document.getElementById('totalDrivers');
    const totalModels = document.getElementById('totalModels');
    const filteredRecordsElement = document.getElementById('filteredRecords');
    const mostDamagedModel = document.getElementById('mostDamagedModel');
    const mostDamagedDriver = document.getElementById('mostDamagedDriver');

    if (totalRecords) totalRecords.textContent = records.length;
    if (totalDrivers) totalDrivers.textContent = drivers.length;
    if (totalModels) totalModels.textContent = models.length;
    if (filteredRecordsElement) filteredRecordsElement.textContent = filteredRecords.length;

    const modelDamageCounts = models.map(m => ({
        model: m.model,
        count: records.filter(r => r.model === m.model).length
    })).sort((a, b) => b.count - a.count);
    if (mostDamagedModel) {
        mostDamagedModel.textContent = modelDamageCounts[0]?.count > 0 
            ? `${modelDamageCounts[0].model} (${modelDamageCounts[0].count})` 
            : '-';
    }

    const driverDamageCounts = drivers.map(d => ({
        driver: d.displayText,
        count: records.filter(r => r.driverInfo === d.displayText).length
    })).sort((a, b) => b.count - a.count);
    if (mostDamagedDriver) {
        mostDamagedDriver.textContent = driverDamageCounts[0]?.count > 0 
            ? `${driverDamageCounts[0].driver} (${driverDamageCounts[0].count})` 
            : '-';
    }
}

// Kayıt görüntüleme (Tek "Kapat" butonu)
function viewRecord(chassisNumber) {
    const record = records.find(r => r.chassisNumber === chassisNumber);
    if (!record) {
        alert('Kayıt bulunamadı.');
        return;
    }

    const content = document.getElementById('recordDetailContent');
    if (!content) return;

    // "Seçildi" linkini data-locations özniteliği ile oluştur
    const locationLink = record.locations && Array.isArray(record.locations) && record.locations.length > 0
        ? `<a href="#" class="location-link-modal" data-locations='${JSON.stringify(record.locations)}'>Seçildi (${record.locations.length} yer)</a>`
        : 'Seçilmedi';

    content.innerHTML = `
        <div class="record-detail">
            <p><strong>Tarih:</strong> ${record.date || '-'}</p>
            <p><strong>Şasi No:</strong> ${record.chassisNumber || '-'}</p>
            <p><strong>Model:</strong> ${record.model || '-'}</p>
            <p><strong>Şoför:</strong> ${record.driverInfo || '-'}</p>
            <p><strong>Grup:</strong> ${record.group || '-'}</p>
            <p><strong>Tanım:</strong> ${record.description || '-'}</p>
            <p><strong>Seviye:</strong> ${record.level || '-'}</p>
            <p><strong>Açıklama:</strong> ${record.explanation || '-'}</p>
            <p><strong>Notlar:</strong> ${record.notes || '-'}</p>
            <p><strong>Hasar Yeri:</strong> ${locationLink}</p>
        </div>
        <div class="modal-actions">
            <button class="btn btn-primary" onclick="printDamageReport('${record.chassisNumber}')">
                <i class="fas fa-print"></i> Yazdır
            </button>
            <!-- "Kapat" butonu kaldırıldı, çünkü index.html'de zaten mevcut -->
        </div>
    `;
    showModal('recordDetailModal');

    // "Seçildi" linkine tıklama olayı ekle
    const locationLinkElement = content.querySelector('.location-link-modal');
    if (locationLinkElement) {
        locationLinkElement.addEventListener('click', (e) => {
            e.preventDefault();
            const locations = JSON.parse(locationLinkElement.getAttribute('data-locations'));
            showDamageLocation(locations);
        });
    }
}
// Kayıt düzenleme
function editRecord(chassisNumber) {
    const record = records.find(r => r.chassisNumber === chassisNumber);
    if (!record) {
        showMessage('Kayıt bulunamadı!', 'error');
        return;
    }

    selectedRecord = record;
    const dateParts = record.date.split('.');
    const formattedDate = `${dateParts[2]}-${dateParts[1].padStart(2, '0')}-${dateParts[0].padStart(2, '0')}`;
    
    document.getElementById('txtDate').value = formattedDate;
    document.getElementById('txtChassis').value = record.chassisNumber;
    document.getElementById('txtChassis').readOnly = true;
    document.getElementById('cmbModel').value = record.model || '';
    document.getElementById('cmbDriver').value = record.driverInfo || '';
    document.getElementById('groupList').value = Array.from(document.getElementById('groupList').options)
        .find(opt => opt.text === record.group)?.value || '';
    document.getElementById('descriptionList').value = Array.from(document.getElementById('descriptionList').options)
        .find(opt => opt.text === record.description)?.value || '';
    document.getElementById('levelList').value = Array.from(document.getElementById('levelList').options)
        .find(opt => opt.text === record.level)?.value || '';
    document.getElementById('txtExplanation').value = record.explanation || '';
    document.getElementById('txtNotes').value = record.notes || '';

    if (record.locations && record.locations.length > 0) {
        markers = record.locations.map(loc => ({ x: loc.x, y: loc.y, number: loc.number }));
        document.getElementById('locationX').value = JSON.stringify(markers.map(m => m.x));
        document.getElementById('locationY').value = JSON.stringify(markers.map(m => m.y));
        document.getElementById('locationPreview').innerHTML = `<span>${markers.length} hasar yeri seçildi</span>`;
    } else {
        markers = [];
        document.getElementById('locationX').value = '';
        document.getElementById('locationY').value = '';
        document.getElementById('locationPreview').innerHTML = '';
    }

    document.getElementById('updateRecordBtn').style.display = 'inline-block';
    setActiveSection({ addRecordSection: document.getElementById('addRecordSection'), mainTitle: document.getElementById('mainTitle') }, 'addRecordSection', 'Kayıt Düzenle');
}

// Düzenleme geçmişi görüntüleme
function viewEditHistory(chassisNumber) {
    const history = editHistory[chassisNumber] || [];
    const content = document.getElementById('editHistoryContent');
    if (!content) return;

    content.innerHTML = history.length > 0 ? 
        history.map(h => `<p>${h.date}: Düzenleme yapıldı</p>`).join('') : 
        '<p>Bu kayıt için düzenleme geçmişi bulunamadı.</p>';
    showModal('editHistoryModal');
}

// Kayıt silme
function deleteRecord(chassisNumber) {
    if (!confirm('Bu kaydı silmek istediğinize emin misiniz?')) return;
    records = records.filter(r => r.chassisNumber !== chassisNumber);
    localStorage.setItem('records', JSON.stringify(records));
    updateTable();
    addLog('Kayıt Silindi', `Şasi No: ${chassisNumber}`);
}

// Toplu silme
function bulkDeleteRecords() {
    const selected = Array.from(document.querySelectorAll('.record-checkbox:checked')).map(cb => cb.dataset.chassis);
    if (!selected.length) {
        showMessage("Lütfen silmek için en az bir kayıt seçin!", "warning");
        return;
    }
    if (confirm(`${selected.length} kaydı silmek istediğinize emin misiniz?`)) {
        records = records.filter(r => !selected.includes(r.chassisNumber));
        selected.forEach(chassis => delete editHistory[chassis]);
        saveData();
        addLog("Toplu Kayıt Sil", `Silinen Kayıt Sayısı: ${selected.length}`);
        updateTable();
        updateManagementLists();
        updateDashboardStats();
        updateDamageChart();
        showMessage(`${selected.length} kayıt silindi!`, "success");
        document.getElementById('selectAllRecords').checked = false;
    }
}

// Excel'e aktarma
function exportToExcel() {
    if (!filteredRecords.length) {
        showMessage("Dışa aktarılacak kayıt bulunamadı!", "error");
        return;
    }

    const wb = XLSX.utils.book_new();
    const wsRecords = XLSX.utils.json_to_sheet(filteredRecords, { 
        header: ["date", "chassisNumber", "model", "driverInfo", "group", "description", "level", "explanation", "notes"] 
    });
    XLSX.utils.sheet_add_aoa(wsRecords, [["Tarih", "Şasi No", "Model", "Şoför", "Grup", "Tanım", "Seviye", "Açıklama", "Notlar"]], { origin: "A1" });
    XLSX.utils.book_append_sheet(wb, wsRecords, "Hasar Kayıtları");

    const driverStats = drivers.map(driver => ({
        licensePlate: driver.licensePlate,
        fullName: driver.fullName,
        damageCount: records.filter(r => r.driverInfo === driver.displayText).length
    }));
    const wsDrivers = XLSX.utils.json_to_sheet(driverStats, { header: ["licensePlate", "fullName", "damageCount"] });
    XLSX.utils.sheet_add_aoa(wsDrivers, [["Plaka", "İsim Soyisim", "Hasarlı Araç Sayısı"]], { origin: "A1" });
    XLSX.utils.book_append_sheet(wb, wsDrivers, "Şoför Bilgileri");

    const modelStats = models.map(model => ({
        model: model.model,
        damageCount: records.filter(r => r.model === model.model).length
    }));
    const wsModels = XLSX.utils.json_to_sheet(modelStats, { header: ["model", "damageCount"] });
    XLSX.utils.sheet_add_aoa(wsModels, [["Model", "Hasar Sayısı"]], { origin: "A1" });
    XLSX.utils.book_append_sheet(wb, wsModels, "Model Bilgileri");

    XLSX.writeFile(wb, `Hasar_Kayitlari_${new Date().toISOString().split('T')[0]}.xlsx`);
    addLog("Excel'e Aktar", `Kayıt Sayısı: ${filteredRecords.length}`);
    showMessage("Veriler Excel'e aktarıldı!", "success");
}

// CSV'ye aktarma
function exportToCsv() {
    if (!filteredRecords.length) {
        showMessage("Dışa aktarılacak kayıt bulunamadı!", "error");
        return;
    }

    const headers = ["Tarih", "Şasi No", "Model", "Şoför", "Grup", "Tanım", "Seviye", "Açıklama", "Notlar"];
    const rows = filteredRecords.map(r => [
        r.date, r.chassisNumber, r.model, r.driverInfo || '-', r.group, r.description, r.level, r.explanation || '-', r.notes || '-'
    ]);
    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Hasar_Kayitlari_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    addLog("CSV'ye Aktar", `Kayıt Sayısı: ${filteredRecords.length}`);
    showMessage("Veriler CSV'ye aktarıldı!", "success");
}

// Şoför listesi güncelleme
function updateDriverList() {
    const driverSelect = document.getElementById('cmbDriver');
    const filterDriverSelect = document.getElementById('cmbFilterDriver');
    const deleteDriverSelect = document.getElementById('cmbDeleteDriver');
    if (driverSelect) driverSelect.innerHTML = '<option value="">Şoför Seçiniz</option>' + drivers.map(d => `<option value="${d.displayText}">${d.displayText}</option>`).join('');
    if (filterDriverSelect) filterDriverSelect.innerHTML = '<option value="">Tümü</option>' + drivers.map(d => `<option value="${d.displayText}">${d.displayText}</option>`).join('');
    if (deleteDriverSelect) deleteDriverSelect.innerHTML = drivers.map(d => `<option value="${d.displayText}">${d.displayText}</option>`).join('');
}

// Model listesi güncelleme
function updateModelList() {
    const modelSelect = document.getElementById('cmbModel');
    const filterModelSelect = document.getElementById('cmbFilterModel');
    if (modelSelect) modelSelect.innerHTML = '<option value="">Model Seçiniz</option>' + models.map(m => `<option value="${m.model}">${m.model}</option>`).join('');
    if (filterModelSelect) filterModelSelect.innerHTML = '<option value="">Tümü</option>' + models.map(m => `<option value="${m.model}">${m.model}</option>`).join('');
}

// Şoför ekleme
function showAddDriverModal() {
    document.getElementById('txtPlate').value = '';
    document.getElementById('txtFullName').value = '';
    showModal('addDriverModal');
    document.getElementById('txtPlate').focus();
}

function saveDriver() {
    const plate = document.getElementById('txtPlate').value.trim().toUpperCase();
    const fullName = document.getElementById('txtFullName').value.trim().toUpperCase();
    if (!plate || !fullName) {
        showMessage("Plaka ve isim soyisim zorunludur!", "error");
        return;
    }

    const displayText = `${plate} --> ${fullName}`;
    if (drivers.some(d => d.displayText === displayText)) {
        showMessage("Bu şoför zaten kayıtlı!", "error");
        return;
    }

    drivers.push({ licensePlate: plate, fullName, displayText });
    saveData();
    addLog("Şoför Ekle", displayText);
    updatewhere
    updateDriverList();
    updateManagementLists();
    updateDashboardStats();
    updateDamageChart();
    showMessage("Şoför eklendi!", "success");
    document.getElementById('txtPlate').value = '';
    document.getElementById('txtFullName').value = '';
    document.getElementById('txtPlate').focus();
}

// Şoför silme
function showDeleteDriverModal() {
    if (!drivers.length) {
        showMessage("Silinecek şoför bulunamadı!", "error");
        return;
    }
    showModal('deleteDriverModal');
}

function deleteDriver() {
    const driver = document.getElementById('cmbDeleteDriver').value;
    if (!driver) {
        showMessage("Lütfen bir şoför seçin!", "error");
        return;
    }

    const relatedRecords = records.filter(r => r.driverInfo === driver);
    if (relatedRecords.length > 0) {
        showMessage("Bu şoförün kayıtları mevcut, önce ilgili kayıtları silin!", "error");
        return;
    }

    drivers = drivers.filter(d => d.displayText !== driver);
    saveData();
    addLog("Şoför Sil", driver);
    updateDriverList();
    updateManagementLists();
    updateDashboardStats();
    updateDamageChart();
    showMessage("Şoför silindi!", "success");
    closeModal('deleteDriverModal');
}

// Model ekleme
function showAddModelModal() {
    document.getElementById('txtModel').value = '';
    showModal('addModelModal');
    document.getElementById('txtModel').focus();
}

function saveModel() {
    const model = document.getElementById('txtModel').value.trim().toUpperCase();
    if (!model) {
        showMessage("Model adı zorunludur!", "error");
        return;
    }

    if (models.some(m => m.model === model)) {
        showMessage("Bu model zaten kayıtlı!", "error");
        return;
    }

    models.push({ model });
    saveData();
    addLog("Model Ekle", model);
    updateModelList();
    updateManagementLists();
    updateDashboardStats();
    updateDamageChart();
    showMessage("Model eklendi!", "success");
    document.getElementById('txtModel').value = '';
    document.getElementById('txtModel').focus();
}

// Yönetim listelerini güncelleme
function updateManagementLists() {
    updateDriverManagementList();
    updateModelManagementList();
}

function updateDriverManagementList(page = currentDriverPage) {
    currentDriverPage = page;
    const driverList = document.getElementById('driverList');
    if (!driverList) return;

    const totalDrivers = drivers.length;
    const totalPages = Math.ceil(totalDrivers / driversPerPage);
    const startIndex = (currentDriverPage - 1) * driversPerPage;
    const endIndex = Math.min(startIndex + driversPerPage, totalDrivers);
    const paginatedDrivers = drivers.slice(startIndex, endIndex);

    driverList.innerHTML = totalDrivers > 0
        ? paginatedDrivers.map((d, index) => {
            const damageCount = records.filter(r => r.driverInfo === d.displayText).length;
            return `<li>${startIndex + index + 1}. ${d.displayText} <span>(Hasar: ${damageCount})</span></li>`;
          }).join('')
        : '<li>Şoför bulunamadı.</li>';

    const existingPagination = driverList.parentElement.querySelector('.pagination');
    if (existingPagination) existingPagination.remove();
    
    if (totalPages > 1) {
        const pagination = document.createElement('div');
        pagination.className = 'pagination';
        for (let i = 1; i <= totalPages; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.textContent = i;
            pageBtn.className = i === currentDriverPage ? 'active' : '';
            pageBtn.addEventListener('click', () => updateDriverManagementList(i));
            pagination.appendChild(pageBtn);
        }
        driverList.insertAdjacentElement('afterend', pagination);
    }
}

function updateModelManagementList(page = currentModelPage) {
    currentModelPage = page;
    const modelList = document.getElementById('modelList');
    if (!modelList) return;

    const totalModels = models.length;
    const totalPages = Math.ceil(totalModels / modelsPerPage);
    const startIndex = (currentModelPage - 1) * modelsPerPage;
    const endIndex = Math.min(startIndex + modelsPerPage, totalModels);
    const paginatedModels = models.slice(startIndex, endIndex);

    modelList.innerHTML = totalModels > 0
        ? paginatedModels.map((m, index) => {
            const damageCount = records.filter(r => r.model === m.model).length;
            return `<li>${startIndex + index + 1}. ${m.model} <span>(Hasar: ${damageCount})</span></li>`;
          }).join('')
        : '<li>Model bulunamadı.</li>';

    const existingPagination = modelList.parentElement.querySelector('.pagination');
    if (existingPagination) existingPagination.remove();
    
    if (totalPages > 1) {
        const pagination = document.createElement('div');
        pagination.className = 'pagination';
        for (let i = 1; i <= totalPages; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.textContent = i;
            pageBtn.className = i === currentModelPage ? 'active' : '';
            pageBtn.addEventListener('click', () => updateModelManagementList(i));
            pagination.appendChild(pageBtn);
        }
        modelList.insertAdjacentElement('afterend', pagination);
    }
}

// Grafik analizi
function updateDamageChart() {
    const period = document.getElementById('analyticsPeriod')?.value;
    const type = document.getElementById('analyticsType')?.value;
    const canvas = document.getElementById('damageChart');
    if (!canvas || !period || !type) return;

    const ctx = canvas.getContext('2d');
    let data, labels;

    if (type === 'drivers') {
        const driverData = drivers.map(d => ({
            driver: d.displayText,
            count: records.filter(r => r.driverInfo === d.displayText).length
        })).sort((a, b) => a.count - b.count);
        labels = driverData.map(d => d.driver);
        data = driverData.map(d => d.count);
    } else if (type === 'models') {
        const modelData = models.map(m => ({
            model: m.model,
            count: records.filter(r => r.model === m.model).length
        })).sort((a, b) => a.count - b.count);
        labels = modelData.map(m => m.model);
        data = modelData.map(m => m.count);
    } else {
        const groupByPeriod = (records, period) => {
            const grouped = {};
            records.forEach(record => {
                const date = new Date(record.date.split('.').reverse().join('-'));
                let key;
                switch (period) {
                    case 'daily':
                        key = date.toLocaleDateString('tr-TR');
                        break;
                    case 'weekly':
                        const weekStart = new Date(date);
                        weekStart.setDate(date.getDate() - date.getDay());
                        key = weekStart.toLocaleDateString('tr-TR');
                        break;
                    case 'monthly':
                        key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
                        break;
                }
                grouped[key] = (grouped[key] || 0) + 1;
            });
            return grouped;
        };

        const grouped = groupByPeriod(records, period);
        labels = Object.keys(grouped).sort().slice(-30);
        data = labels.map(label => grouped[label]);
    }

    if (damageChart) damageChart.destroy();
    damageChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: type === 'drivers' ? 'Şoför Hasar Sayısı' : type === 'models' ? 'Model Hasar Sayısı' : 'Hasar Sayısı',
                data: data,
                backgroundColor: 'rgba(37, 99, 235, 0.6)',
                borderColor: 'rgba(37, 99, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: { y: { beginAtZero: true } }
        }
    });
}

// Tarih formatlama
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

// Mesaj gösterme
function showMessage(text, type) {
    const message = document.getElementById('message');
    if (!message) return;

    message.textContent = text;
    message.style.background = type === 'success' ? 'rgba(16, 185, 129, 0.1)' : type === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)';
    message.style.color = type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#f59e0b';
    setTimeout(() => message.textContent = '', 3000);
}

// Modal yönetimi
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('show');
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('show');
}

// Tarih aralığı temizleme
function showClearRangeModal() {
    showModal('clearRangeModal');
}

function clearRange() {
    const startDate = document.getElementById('clearStartDate').value;
    const endDate = document.getElementById('clearEndDate').value;
    if (!startDate || !endDate) {
        showMessage("Başlangıç ve bitiş tarihleri zorunludur!", "error");
        return;
    }

    const start = new Date(startDate);
    const end = new Date(endDate);
    const initialLength = records.length;
    records = records.filter(r => {
        const recordDate = new Date(r.date.split('.').reverse().join('-'));
        return recordDate < start || recordDate > end;
    });

    if (records.length < initialLength) {
        saveData();
        addLog("Tarih Aralığı Temizle", `Tarih: ${startDate} - ${endDate}`);
        updateTable();
        updateDashboardStats();
        updateDamageChart();
        showMessage("Seçilen tarih aralığındaki kayıtlar temizlendi!", "success");
    } else {
        showMessage("Seçilen aralıkta silinecek kayıt bulunamadı!", "warning");
    }
    closeModal('clearRangeModal');
}

// Otomatik yedekleme
function startAutoBackup() {
    setInterval(() => backupData(true), 10 * 60 * 1000); // Her 10 dakikada bir
}

function backupData(silent = false) {
    const data = { records, drivers, models, logs, editHistory };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `backup_${new Date().toISOString().split('T')[0]}.json`;
    if (!silent) a.click();
    URL.revokeObjectURL(url);
    if (!silent) showMessage("Veriler yedeklendi!", "success");
}

function restoreData(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target.result);
            records = data.records || [];
            drivers = data.drivers || [];
            models = data.models || [];
            logs = data.logs || [];
            editHistory = data.editHistory || {};
            saveData();
            updateTable();
            updateDriverList();
            updateModelList();
            updateManagementLists();
            updateDashboardStats();
            updateHistoryTable();
            updateDamageChart();
            showMessage("Veriler geri yüklendi!", "success");
        } catch (error) {
            showMessage("Veriler geri yüklenirken bir hata oluştu!", "error");
        }
    };
    reader.readAsText(file);
    event.target.value = '';
}

// Tema değiştirme
function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    const isDark = document.body.classList.contains('dark-theme');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    showMessage(`Tema: ${isDark ? 'Koyu' : 'Açık'}`, "success");
}

// Yenileme
function refresh() {
    updateTable();
    updateDriverList();
    updateModelList();
    updateManagementLists();
    updateDashboardStats();
    updateHistoryTable();
    updateDamageChart();
    showMessage("Sayfa yenilendi!", "success");
}

// Filtreleme
function filterRecords() {
    const quickSearch = document.getElementById('quickSearch').value.toLowerCase();
    const chassisFilter = document.getElementById('txtFilterChassis').value.toLowerCase();
    const startDate = document.getElementById('txtFilterDateStart').value;
    const endDate = document.getElementById('txtFilterDateEnd').value;
    const modelFilter = document.getElementById('cmbFilterModel').value;
    const driverFilter = document.getElementById('cmbFilterDriver').value;

    filteredRecords = records.filter(record => {
        const recordDate = new Date(record.date.split('.').reverse().join('-'));
        const matchesQuickSearch = quickSearch === '' || 
            Object.values(record).some(val => val && val.toString().toLowerCase().includes(quickSearch));
        const matchesChassis = chassisFilter === '' || 
            (record.chassisNumber && record.chassisNumber.toLowerCase().includes(chassisFilter));
        const matchesDate = (!startDate || recordDate >= new Date(startDate)) && 
                            (!endDate || recordDate <= new Date(endDate));
        const matchesModel = modelFilter === '' || record.model === modelFilter;
        const matchesDriver = driverFilter === '' || record.driverInfo === driverFilter;

        return matchesQuickSearch && matchesChassis && matchesDate && matchesModel && matchesDriver;
    });

    updateTable(filteredRecords);
}

// Sıralama
function sortTable(column) {
    const direction = sortDirection[column] = sortDirection[column] === 'asc' ? 'desc' : 'asc';
    filteredRecords.sort((a, b) => {
        const valA = a[column] || '';
        const valB = b[column] || '';
        if (column === 'date') {
            const dateA = new Date(valA.split('.').reverse().join('-'));
            const dateB = new Date(valB.split('.').reverse().join('-'));
            return direction === 'asc' ? dateA - dateB : dateB - dateA;
        }
        return direction === 'asc' 
            ? valA.localeCompare(valB) 
            : valB.localeCompare(valA);
    });
    updateTable(filteredRecords);
}

// Hasar raporu yazdırma (Tek A4'e sığacak şekilde güncellendi)
function printDamageReport(chassisNumber) {
    const record = records.find(r => r.chassisNumber === chassisNumber);
    if (!record) return;

    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
            <head>
                <title>Hasar Tutanağı</title>
                <style>
                    body {
                        margin: 0;
                        font-family: 'Inter', sans-serif;
                        font-size: 8px; /* Küçültülmüş font */
                        color: #333;
                        background: #f5f7fa;
                    }
                    .print-container {
                        width: 210mm;
                        height: 297mm;
                        padding: 5mm; /* Küçültülmüş padding */
                        box-sizing: border-box;
                        position: relative;
                        background: #fff;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        border: 2px solid #2563eb;
                    }
                    .header {
                        text-align: center;
                        background: linear-gradient(135deg, #2563eb, #1a4db3);
                        color: white;
                        padding: 5px; /* Küçültülmüş padding */
                        border-radius: 6px;
                        margin-bottom: 8px; /* Küçültülmüş margin */
                    }
                    .header h1 {
                        margin: 0;
                        font-size: 16px; /* Küçültülmüş font */
                    }
                    .header p {
                        margin: 2px 0; /* Küçültülmüş margin */
                        font-size: 8px; /* Küçültülmüş font */
                    }
                    .details-table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 8px; /* Küçültülmüş margin */
                        border: 1px solid #ddd;
                    }
                    .details-table th, .details-table td {
                        border: 1px solid #ddd;
                        padding: 4px; /* Küçültülmüş padding */
                        text-align: left;
                        font-size: 8px; /* Küçültülmüş font */
                    }
                    .details-table th {
                        background: #f7fafc;
                        font-weight: 600;
                        width: 30%;
                        color: #2563eb;
                    }
                    .car-image-container {
                        position: relative;
                        margin: 8px auto; /* Küçültülmüş margin */
                        text-align: center;
                        width: 100%;
                        max-width: 300px; /* Küçültülmüş genişlik */
                        border: 2px dashed #2563eb;
                        padding: 4px; /* Küçültülmüş padding */
                    }
                    .car-image {
                        width: 100%;
                        height: auto;
                    }
                    .marker {
                        position: absolute;
                        width: 12px; /* Küçültülmüş marker */
                        height: 12px; /* Küçültülmüş marker */
                        background: #ef4444;
                        border-radius: 50%;
                        border: 1px solid white;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-size: 8px; /* Küçültülmüş font */
                        font-weight: bold;
                    }
                    .signature {
                        margin-top: 10px; /* Küçültülmüş margin */
                        display: flex;
                        justify-content: space-between;
                        border-top: 1px solid #ddd;
                        padding-top: 5px; /* Küçültülmüş padding */
                    }
                    .signature div {
                        width: 30%;
                        text-align: center;
                    }
                    .signature div p {
                        margin: 2px 0; /* Küçültülmüş margin */
                        border-top: 1px solid #000;
                        padding-top: 4px; /* Küçültülmüş padding */
                        font-size: 8px; /* Küçültülmüş font */
                    }
                    .footer {
                        position: absolute;
                        bottom: 5mm; /* Küçültülmüş bottom */
                        width: calc(100% - 10mm);
                        border-top: 1px solid #2563eb;
                        padding-top: 3px; /* Küçültülmüş padding */
                        text-align: center;
                        font-size: 8px; /* Küçültülmüş font */
                    }
                    .footer p {
                        margin: 1px 0; /* Küçültülmüş margin */
                    }
                    @media print {
                        body { background: none; }
                        .print-container { border: 2px solid #2563eb; box-shadow: none; }
                    }
                </style>
            </head>
            <body>
                <div class="print-container">
                    <div class="header">
                        <h1>Hasar Tutanağı</h1>
                        <p>Taşdanlar Otomotiv</p>
                        <p>Tarih: ${new Date().toLocaleDateString('tr-TR')} | Şasi No: ${record.chassisNumber}</p>
                    </div>
                    <table class="details-table">
                        <tr><th>Tarih</th><td>${record.date}</td></tr>
                        <tr><th>Şasi No</th><td>${record.chassisNumber}</td></tr>
                        <tr><th>Model</th><td>${record.model}</td></tr>
                        <tr><th>Şoför</th><td>${record.driverInfo || '-'}</td></tr>
                        <tr><th>Hasar Grubu</th><td>${record.group}</td></tr>
                        <tr><th>Hasar Tanımı</th><td>${record.description}</td></tr>
                        <tr><th>Hasar Seviyesi</th><td>${record.level}</td></tr>
                        <tr><th>Açıklama</th><td>${record.explanation || 'Açıklama belirtilmemiştir.'}</td></tr>
                        <tr><th>Notlar</th><td>${record.notes || 'Not belirtilmemiştir.'}</td></tr>
                    </table>
                    <div class="car-image-container">
                        <img class="car-image" src="https://ares.rsservis.com.tr/css/otoekspertiz/img/kaporta_svg/9.svg" alt="Car Image" />
                        <div class="marker-container">
                            ${record.locations?.map(loc => `
                                <div class="marker" style="left: ${loc.x - 6}px; top: ${loc.y - 6}px;">
                                    ${loc.number}
                                </div>
                            `).join('') || ''}
                        </div>
                    </div>
                    <div class="signature">
                        <div><p>Yetkili İmza</p></div>
                        <div><p>Şoför İmza</p></div>
                        <div><p>Kontrol Eden</p></div>
                    </div>
                    <div class="footer">
                        <p><strong>Taşdanlar Otomotiv</strong> - © ${new Date().getFullYear()}</p>
                        <p>Adres: [Adres Bilgisi] | Telefon: [Telefon Numarası] | E-posta: [E-posta Adresi]</p>
                    </div>
                </div>
            </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
    printWindow.close();
    closeModal('recordDetailModal');
}

// Geçmiş tablosu güncelleme
function updateHistoryTable(page = currentLogPage) {
    currentLogPage = page;
    const tbody = document.getElementById('historyTableBody');
    if (!tbody) return;

    // Sayfalama için logları böl
    const totalLogs = logs.length;
    const totalPages = Math.ceil(totalLogs / logsPerPage);
    const startIndex = (currentLogPage - 1) * logsPerPage;
    const endIndex = Math.min(startIndex + logsPerPage, totalLogs);
    const paginatedLogs = logs.slice(startIndex, endIndex);

    // Tabloyu güncelle
    tbody.innerHTML = paginatedLogs.length > 0
        ? paginatedLogs.map((log, index) => `
            <tr>
                <td>${log.date}</td>
                <td>${log.action}</td>
                <td>${log.detail}</td>
            </tr>
        `).join('')
        : '<tr><td colspan="3">Geçmiş kaydı bulunamadı.</td></tr>';

    // Mevcut sayfalama alanını temizle
    const tableWrapper = tbody.closest('.table-wrapper');
    const existingPagination = tableWrapper.querySelector('.pagination');
    if (existingPagination) existingPagination.remove();

    // Sayfalama butonlarını tablonun altına ekle
    if (totalPages > 1) {
        const pagination = document.createElement('div');
        pagination.className = 'pagination';
        for (let i = 1; i <= totalPages; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.textContent = i;
            pageBtn.className = i === currentLogPage ? 'active' : '';
            pageBtn.addEventListener('click', () => updateHistoryTable(i));
            pagination.appendChild(pageBtn);
        }
        tableWrapper.appendChild(pagination);
    }
}