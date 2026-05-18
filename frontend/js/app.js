// Global state
let currentUser = null;
let currentPage = 'dashboard';
let socket = null;
let theme = localStorage.getItem('theme') || 'light';

// Pages configuration
const pages = {
    dashboard: 'Dashboard',
    reports: 'Reports',
    heatmap: 'Heatmap',
    livestreams: 'Live Streams',
    admin: 'Admin Panel'
};

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    checkAuth();
    initWebSocket();
    renderSidebar();
    renderCurrentPage();
    initEventListeners();
});

// Theme Management
function initTheme() {
    document.body.setAttribute('data-bs-theme', theme);
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.innerHTML = theme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    }
}

function toggleTheme() {
    theme = theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', theme);
    document.body.setAttribute('data-bs-theme', theme);
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.innerHTML = theme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    }
    showToast('Theme Changed', `${theme.charAt(0).toUpperCase() + theme.slice(1)} mode activated`, 'info');
}

// Authentication
function checkAuth() {
    const token = localStorage.getItem('token');
    if (token) {
        // Verify token with backend
        fetch('/api/verify', {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(res => res.json())
        .then(data => {
            if (data.valid) {
                currentUser = data.user;
                updateAuthUI(true);
            } else {
                updateAuthUI(false);
            }
        })
        .catch(() => updateAuthUI(false));
    } else {
        updateAuthUI(false);
    }
}

function updateAuthUI(isLoggedIn) {
    const authSection = document.getElementById('authSection');
    if (authSection) {
        if (isLoggedIn && currentUser) {
            authSection.innerHTML = `
                <div class="dropdown">
                    <button class="btn btn-light dropdown-toggle" type="button" data-bs-toggle="dropdown">
                        <i class="fas fa-user-circle"></i> ${currentUser.email}
                    </button>
                    <ul class="dropdown-menu">
                        <li><a class="dropdown-item" href="#" onclick="showProfile()"><i class="fas fa-user"></i> Profile</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item" href="#" onclick="logout()"><i class="fas fa-sign-out-alt"></i> Logout</a></li>
                    </ul>
                </div>
            `;
        } else {
            authSection.innerHTML = `
                <button class="btn btn-light" onclick="showLoginModal()">
                    <i class="fas fa-sign-in-alt"></i> Login / Sign Up
                </button>
            `;
        }
    }
}

function showLoginModal() {
    const modal = new bootstrap.Modal(document.getElementById('loginModal'));
    modal.show();
}

function login() {
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    if (email === 'admin@example.com' && password === 'admin123') {
        localStorage.setItem('token', 'demo-token');
        currentUser = { email: email, role: 'admin' };
        updateAuthUI(true);
        bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
        showToast('Login Successful', 'Welcome back!', 'success');
        renderCurrentPage();
    } else {
        showToast('Login Failed', 'Invalid credentials', 'error');
    }
}

function logout() {
    localStorage.removeItem('token');
    currentUser = null;
    updateAuthUI(false);
    showToast('Logged Out', 'You have been logged out', 'info');
    renderCurrentPage();
}

// WebSocket for real-time alerts
function initWebSocket() {
    socket = io('http://localhost:8000', {
        transports: ['websocket'],
        path: '/ws'
    });
    
    socket.on('connect', () => {
        console.log('WebSocket connected');
    });
    
    socket.on('alert', (data) => {
        showToast('Vehicle Alert', data.message, 'warning');
        playAlertSound();
    });
    
    socket.on('detection', (data) => {
        updateRecentDetections(data);
    });
}

// UI Components
function renderSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    
    const navItems = Object.entries(pages).map(([key, label]) => `
        <li class="nav-item">
            <a class="nav-link ${currentPage === key ? 'active' : ''}" href="#" onclick="navigateTo('${key}')">
                <i class="fas fa-${getIconForPage(key)}"></i>
                <span>${label}</span>
            </a>
        </li>
    `).join('');
    
    sidebar.innerHTML = `
        <div class="sidebar-header p-3">
            <h4><i class="fas fa-car"></i> ${!sidebar.classList.contains('collapsed') ? 'TollPlaza AI' : ''}</h4>
        </div>
        <ul class="nav flex-column">
            ${navItems}
        </ul>
        <div class="sidebar-footer p-3 position-absolute bottom-0">
            <button class="btn btn-light w-100" onclick="toggleSidebar()">
                <i class="fas fa-chevron-${sidebar.classList.contains('collapsed') ? 'right' : 'left'}"></i>
                ${!sidebar.classList.contains('collapsed') ? 'Collapse' : ''}
            </button>
        </div>
    `;
}

function renderCurrentPage() {
    const content = document.getElementById('pageContent');
    if (!content) return;
    
    switch(currentPage) {
        case 'dashboard':
            renderDashboard(content);
            break;
        case 'reports':
            renderReports(content);
            break;
        case 'heatmap':
            renderHeatmap(content);
            break;
        case 'livestreams':
            renderLiveStreams(content);
            break;
        case 'admin':
            renderAdminPanel(content);
            break;
        default:
            renderDashboard(content);
    }
}

// Page Renderers
function renderDashboard(container) {
    container.innerHTML = `
        <div class="page-transition">
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="stat-card">
                        <i class="fas fa-car fa-2x mb-2"></i>
                        <h3 id="totalVehicles">0</h3>
                        <p>Total Vehicles Today</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <i class="fas fa-truck fa-2x mb-2"></i>
                        <h3 id="truckCount">0</h3>
                        <p>Trucks</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <i class="fas fa-bus fa-2x mb-2"></i>
                        <h3 id="busCount">0</h3>
                        <p>Buses</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <i class="fas fa-motorcycle fa-2x mb-2"></i>
                        <h3 id="motorcycleCount">0</h3>
                        <p>Motorcycles</p>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-upload"></i> Upload Images / ZIP</h5>
                        </div>
                        <div class="card-body">
                            <input type="file" id="imageUpload" class="form-control mb-3" accept="image/*,.zip" multiple>
                            <button class="btn btn-primary" onclick="uploadImages()">
                                <i class="fas fa-search"></i> Detect Vehicles
                            </button>
                            <div id="uploadProgress" class="mt-3" style="display:none;">
                                <div class="progress">
                                    <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="card mt-3">
                        <div class="card-header">
                            <h5><i class="fas fa-video"></i> Live Camera</h5>
                        </div>
                        <div class="card-body">
                            <video id="liveCamera" autoplay playsinline style="width:100%; border-radius:10px;"></video>
                            <button class="btn btn-success mt-2" onclick="startCamera()">
                                <i class="fas fa-play"></i> Capture & Detect
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-history"></i> Recent Detections</h5>
                        </div>
                        <div class="card-body" id="recentDetections" style="max-height: 500px; overflow-y: auto;">
                            <div class="text-center text-muted">No detections yet</div>
                        </div>
                        <div class="card-footer">
                            <button class="btn btn-info w-100" onclick="downloadReport()">
                                <i class="fas fa-download"></i> Download Today's Report
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Carousel for detection examples -->
            <div class="row mt-3">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-images"></i> Detection Examples</h5>
                        </div>
                        <div class="card-body">
                            <div id="detectionCarousel" class="carousel slide" data-bs-ride="carousel">
                                <div class="carousel-inner">
                                    <div class="carousel-item active">
                                        <img src="https://via.placeholder.com/800x400/667eea/white?text=Vehicle+Detection+Example" class="d-block w-100" alt="...">
                                    </div>
                                    <div class="carousel-item">
                                        <img src="https://via.placeholder.com/800x400/764ba2/white?text=License+Plate+Recognition" class="d-block w-100" alt="...">
                                    </div>
                                </div>
                                <button class="carousel-control-prev" type="button" data-bs-target="#detectionCarousel" data-bs-slide="prev">
                                    <span class="carousel-control-prev-icon"></span>
                                </button>
                                <button class="carousel-control-next" type="button" data-bs-target="#detectionCarousel" data-bs-slide="next">
                                    <span class="carousel-control-next-icon"></span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    fetchStats();
    setInterval(fetchStats, 5000);
}

function renderReports(container) {
    container.innerHTML = `
        <div class="page-transition">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-file-excel"></i> Daily Reports</h5>
                    <p>Download Excel reports for any date</p>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <label>Select Date</label>
                            <input type="date" id="reportDate" class="form-control" value="${new Date().toISOString().split('T')[0]}">
                        </div>
                        <div class="col-md-6">
                            <label>&nbsp;</label>
                            <button class="btn btn-primary w-100" onclick="downloadCustomReport()">
                                <i class="fas fa-download"></i> Download Report
                            </button>
                        </div>
                    </div>
                    <hr>
                    <div class="text-center">
                        <button class="btn btn-success btn-lg" onclick="downloadTodayReport()">
                            <i class="fas fa-file-excel"></i> Quick Access: Download Today's Report
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Accordion for report history -->
            <div class="card mt-3">
                <div class="card-header">
                    <h5><i class="fas fa-history"></i> Report History</h5>
                </div>
                <div class="card-body">
                    <div class="accordion" id="reportHistoryAccordion">
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseOne">
                                    Last 7 Days Reports
                                </button>
                            </h2>
                            <div id="collapseOne" class="accordion-collapse collapse show" data-bs-parent="#reportHistoryAccordion">
                                <div class="accordion-body" id="weeklyReports">
                                    Loading...
                                </div>
                            </div>
                        </div>
                        <div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseTwo">
                                    Monthly Summary
                                </button>
                            </h2>
                            <div id="collapseTwo" class="accordion-collapse collapse" data-bs-parent="#reportHistoryAccordion">
                                <div class="accordion-body" id="monthlyReports">
                                    Loading...
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderHeatmap(container) {
    container.innerHTML = `
        <div class="page-transition">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-chart-line"></i> Hourly Vehicle Frequency (Heatmap)</h5>
                </div>
                <div class="card-body">
                    <canvas id="heatmapCanvas" width="800" height="400"></canvas>
                </div>
            </div>
            
            <!-- Tooltip example -->
            <div class="card mt-3">
                <div class="card-body text-center">
                    <p>Hover over the chart to see details <i class="fas fa-info-circle" data-bs-toggle="tooltip" title="Data for current month"></i></p>
                    <button class="btn btn-info" onclick="showHeatmapInfo()">
                        <i class="fas fa-chart-simple"></i> View Detailed Analysis
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    renderHeatmapChart();
}

function renderLiveStreams(container) {
    container.innerHTML = `
        <div class="page-transition">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-video"></i> Live Camera Streams</h5>
                    <button class="btn btn-primary" onclick="showAddCameraModal()">
                        <i class="fas fa-plus"></i> Add a new camera
                    </button>
                </div>
                <div class="card-body">
                    <div id="camerasGrid" class="row">
                        <div class="text-center text-muted">No cameras added yet. Click "Add Camera" to start.</div>
                    </div>
                </div>
            </div>
            
            <!-- Offcanvas for camera settings -->
            <div class="offcanvas offcanvas-end" tabindex="-1" id="cameraSettingsOffcanvas">
                <div class="offcanvas-header">
                    <h5 class="offcanvas-title">Camera Settings</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button>
                </div>
                <div class="offcanvas-body">
                    <div id="cameraSettingsContent"></div>
                </div>
            </div>
        </div>
    `;
    
    loadCameras();
}

function renderAdminPanel(container) {
    if (!currentUser || currentUser.role !== 'admin') {
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-lock"></i> Access Denied. Admin privileges required.
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <div class="page-transition">
            <div class="row">
                <div class="col-md-3">
                    <div class="stat-card">
                        <h3 id="totalUsers">0</h3>
                        <p>Total Users</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <h3 id="totalCameras">0</h3>
                        <p>Active Cameras</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <h3 id="storageUsed">0</h3>
                        <p>Storage Used (GB)</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card">
                        <h3 id="apiCalls">0</h3>
                        <p>API Calls Today</p>
                    </div>
                </div>
            </div>
            
            <div class="card mt-3">
                <div class="card-header">
                    <h5><i class="fas fa-users"></i> User Management</h5>
                </div>
                <div class="card-body">
                    <table class="table" id="usersTable">
                        <thead>
                            <tr><th>ID</th><th>Email</th><th>Role</th><th>Status</th><th>Actions</th></tr>
                        </thead>
                        <tbody>
                            <tr><td colspan="5" class="text-center">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="card mt-3">
                <div class="card-header">
                    <h5><i class="fas fa-chart-bar"></i> System Metrics</h5>
                </div>
                <div class="card-body">
                    <canvas id="systemMetricsChart"></canvas>
                </div>
            </div>
        </div>
    `;
    
    loadAdminData();
}

// Helper Functions
function getIconForPage(page) {
    const icons = {
        dashboard: 'tachometer-alt',
        reports: 'file-alt',
        heatmap: 'fire',
        livestreams: 'video',
        admin: 'crown'
    };
    return icons[page] || 'circle';
}

function navigateTo(page) {
    currentPage = page;
    renderSidebar();
    renderCurrentPage();
    
    // Update URL without reload
    history.pushState({ page }, '', `#${page}`);
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    sidebar.classList.toggle('collapsed');
    mainContent.classList.toggle('expanded');
    renderSidebar();
}

function showToast(title, message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    const toastId = 'toast-' + Date.now();
    
    const bgColor = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : type === 'warning' ? 'bg-warning' : 'bg-info';
    
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgColor} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong><br>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

function playAlertSound() {
    // Optional: Add sound notification
    const audio = new Audio('data:audio/wav;base64,U3RlYWx0aCBzb3VuZA==');
    audio.play().catch(e => console.log('Audio not supported'));
}

// API Calls
async function fetchStats() {
    try {
        const response = await fetch('http://localhost:8000/stats/camera1');
        const data = await response.json();
        
        const total = Object.values(data.counters).reduce((a,b) => a+b, 0);
        document.getElementById('totalVehicles') && (document.getElementById('totalVehicles').innerText = total);
        document.getElementById('truckCount') && (document.getElementById('truckCount').innerText = data.counters.truck || 0);
        document.getElementById('busCount') && (document.getElementById('busCount').innerText = data.counters.bus || 0);
        document.getElementById('motorcycleCount') && (document.getElementById('motorcycleCount').innerText = data.counters.motorcycle || 0);
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

async function uploadImages() {
    const files = document.getElementById('imageUpload').files;
    if (files.length === 0) {
        showToast('No Files', 'Please select images to upload', 'warning');
        return;
    }
    
    const progressDiv = document.getElementById('uploadProgress');
    progressDiv.style.display = 'block';
    const progressBar = progressDiv.querySelector('.progress-bar');
    
    for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append('file', files[i]);
        
        progressBar.style.width = `${((i+1)/files.length)*100}%`;
        
        try {
            const response = await fetch('http://localhost:8000/detect', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (data.success) {
                showToast('Detection Complete', `Found ${data.count} vehicles in ${files[i].name}`, 'success');
                updateRecentDetections(data.detections);
            }
        } catch (error) {
            showToast('Error', `Failed to process ${files[i].name}`, 'error');
        }
    }
    
    setTimeout(() => {
        progressDiv.style.display = 'none';
        progressBar.style.width = '0%';
    }, 1000);
}

function updateRecentDetections(detections) {
    const container = document.getElementById('recentDetections');
    if (!container) return;
    
    const now = new Date();
    const timeStr = now.toLocaleString();
    
    let html = '<table class="table table-sm">';
    html += '<thead><tr><th>Time</th><th>Vehicle Type</th><th>Confidence</th><th>License Plate</th></tr></thead><tbody>';
    
    if (Array.isArray(detections)) {
        detections.slice(0, 5).forEach(d => {
            html += `
                <tr>
                    <td>${timeStr}</td>
                    <td><i class="fas fa-${d.type === 'car' ? 'car' : d.type === 'truck' ? 'truck' : 'bus'}"></i> ${d.type}</td>
                    <td>${Math.round(d.confidence * 100)}%</td>
                    <td>${d.license_plate || '—'}</td>
                </tr>
            `;
        });
    }
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

async function startCamera() {
    const video = document.getElementById('liveCamera');
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        
        // Capture frame every 2 seconds
        setInterval(async () => {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            
            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('file', blob, 'webcam.jpg');
                
                try {
                    const response = await fetch('http://localhost:8000/detect', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();
                    if (data.success && data.detections) {
                        updateRecentDetections(data.detections);
                        showToast('Detection', `Found ${data.count} vehicles`, 'info');
                    }
                } catch (e) {}
            }, 'image/jpeg');
        }, 3000);
        
        showToast('Camera Started', 'Live detection is now active', 'success');
    } catch (error) {
        showToast('Camera Error', 'Unable to access camera', 'error');
    }
}

async function downloadReport() {
    window.open('http://localhost:8000/generate-report', '_blank');
    showToast('Report Generated', 'Your report is being downloaded', 'success');
}

function renderHeatmapChart() {
    const ctx = document.getElementById('heatmapCanvas');
    if (!ctx) return;
    
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Array.from({length: 24}, (_, i) => `${i}:00`),
            datasets: [{
                label: 'Vehicle Count',
                data: Array.from({length: 24}, () => Math.floor(Math.random() * 100)),
                backgroundColor: 'rgba(102, 126, 234, 0.6)',
                borderColor: 'rgb(102, 126, 234)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Vehicles: ${context.raw}`;
                        }
                    }
                }
            }
        }
    });
}

function showAddCameraModal() {
    const modalHTML = `
        <div class="modal fade" id="addCameraModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Add New Camera</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <label>Camera ID (unique)</label>
                        <input type="text" id="cameraId" class="form-control mb-3" placeholder="e.g., camera_1">
                        <label>RTSP/HTTP URL</label>
                        <input type="text" id="cameraUrl" class="form-control mb-3" placeholder="rtsp://username:password@ip:port/stream">
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button class="btn btn-primary" onclick="addCamera()">Add Camera</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    const modal = new bootstrap.Modal(document.getElementById('addCameraModal'));
    modal.show();
    
    document.getElementById('addCameraModal').addEventListener('hidden.bs.modal', () => {
        document.getElementById('addCameraModal').remove();
    });
}

async function addCamera() {
    const cameraId = document.getElementById('cameraId').value;
    const cameraUrl = document.getElementById('cameraUrl').value;
    
    if (!cameraId || !cameraUrl) {
        showToast('Invalid Input', 'Please fill all fields', 'warning');
        return;
    }
    
    try {
        const response = await fetch('http://localhost:8000/add-camera', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ camera_id: cameraId, url: cameraUrl })
        });
        
        if (response.ok) {
            showToast('Camera Added', `Camera ${cameraId} has been added`, 'success');
            bootstrap.Modal.getInstance(document.getElementById('addCameraModal')).hide();
            loadCameras();
        }
    } catch (error) {
        showToast('Error', 'Failed to add camera', 'error');
    }
}

async function loadCameras() {
    // Placeholder for camera loading logic
    const grid = document.getElementById('camerasGrid');
    if (grid) {
        grid.innerHTML = `
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-body">
                        <h5>Camera 1 (Main Gate)</h5>
                        <video autoplay playsinline style="width:100%; border-radius:10px;"></video>
                        <div class="mt-2">
                            <button class="btn btn-sm btn-info" onclick="showCameraSettings('camera1')">
                                <i class="fas fa-cog"></i> Settings
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

function showProfile() {
    showToast('Profile', 'Profile feature coming soon', 'info');
}

function downloadCustomReport() {
    const date = document.getElementById('reportDate').value;
    if (date) {
        window.open(`http://localhost:8000/generate-report?date=${date}`, '_blank');
        showToast('Report', `Generating report for ${date}`, 'success');
    }
}

function downloadTodayReport() {
    downloadReport();
}

function showHeatmapInfo() {
    showToast('Heatmap Info', 'Showing vehicle frequency patterns throughout the day', 'info');
}

function showCameraSettings(cameraId) {
    const offcanvas = new bootstrap.Offcanvas(document.getElementById('cameraSettingsOffcanvas'));
    document.getElementById('cameraSettingsContent').innerHTML = `
        <h6>Camera: ${cameraId}</h6>
        <label>Detection Sensitivity</label>
        <input type="range" class="form-range" min="0" max="100" value="75">
        <label class="mt-3">Alert Threshold</label>
        <input type="number" class="form-control" value="3">
        <button class="btn btn-primary mt-3 w-100" onclick="saveCameraSettings()">Save Settings</button>
    `;
    offcanvas.show();
}

function saveCameraSettings() {
    showToast('Settings Saved', 'Camera settings updated successfully', 'success');
    bootstrap.Offcanvas.getInstance(document.getElementById('cameraSettingsOffcanvas')).hide();
}

function loadAdminData() {
    // Populate admin data
    document.getElementById('totalUsers') && (document.getElementById('totalUsers').innerText = '1');
    document.getElementById('totalCameras') && (document.getElementById('totalCameras').innerText = '0');
    document.getElementById('storageUsed') && (document.getElementById('storageUsed').innerText = '2.4');
    document.getElementById('apiCalls') && (document.getElementById('apiCalls').innerText = '156');
    
    const usersTable = document.getElementById('usersTable');
    if (usersTable) {
        usersTable.innerHTML = `
            <thead><tr><th>ID</th><th>Email</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
                <tr><td>1</td><td>admin@example.com</td><td>Admin</td><td><span class="badge bg-success">Active</span></td>
                <td><button class="btn btn-sm btn-danger"><i class="fas fa-trash"></i></button></td></tr>
            </tbody>
        `;
    }
    
    // System metrics chart
    const ctx = document.getElementById('systemMetricsChart');
    if (ctx) {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'API Calls',
                    data: [65, 78, 89, 92, 105, 98, 112],
                    borderColor: 'rgb(102, 126, 234)',
                    tension: 0.1
                }]
            }
        });
    }
}

// Initialize event listeners
function initEventListeners() {
    window.addEventListener('popstate', (event) => {
        if (event.state && event.state.page) {
            currentPage = event.state.page;
            renderSidebar();
            renderCurrentPage();
        }
    });
    
    // Initialize tooltips globally
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Expose functions globally
window.navigateTo = navigateTo;
window.toggleTheme = toggleTheme;
window.showLoginModal = showLoginModal;
window.login = login;
window.logout = logout;
window.uploadImages = uploadImages;
window.startCamera = startCamera;
window.downloadReport = downloadReport;
window.downloadCustomReport = downloadCustomReport;
window.downloadTodayReport = downloadTodayReport;
window.showAddCameraModal = showAddCameraModal;
window.addCamera = addCamera;
window.showCameraSettings = showCameraSettings;
window.saveCameraSettings = saveCameraSettings;
window.showHeatmapInfo = showHeatmapInfo;
window.showProfile = showProfile;

console.log('TollPlaza AI Application Loaded');
