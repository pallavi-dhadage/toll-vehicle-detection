"""
Main FastAPI Application - Fixed for JSON serialization
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from detection import detector
import json
from datetime import datetime

app = FastAPI(title="Vehicle Detection System", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTML Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Vehicle Detection System</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f5f5f5; }
        .navbar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; border-radius: 15px; padding: 20px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .stat-value { font-size: 2em; font-weight: bold; color: #667eea; }
        .upload-section { background: white; border-radius: 15px; padding: 20px; margin-bottom: 30px; }
        .upload-area { border: 2px dashed #667eea; border-radius: 10px; padding: 30px; text-align: center; cursor: pointer; background: #f8f9fa; }
        .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; margin-top: 10px; }
        .chart-card { background: white; border-radius: 15px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .chart-container { height: 400px; }
        .preview-img { max-width: 100%; max-height: 200px; border-radius: 10px; margin-top: 10px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .tab { padding: 10px 20px; cursor: pointer; background: white; border-radius: 8px; transition: all 0.3s; }
        .tab.active { background: #667eea; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .loading { display: none; text-align: center; padding: 20px; }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .result-item { background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #28a745; }
        .log-table { width: 100%; border-collapse: collapse; }
        .log-table th, .log-table td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        .log-table th { background: #667eea; color: white; }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="container">
            <h1>🚗 Vehicle Detection & Analytics System</h1>
            <p>Real-time detection with 92%+ confidence | Logging | Heatmaps | Analytics</p>
        </div>
    </div>
    
    <div class="container">
        <div class="upload-section">
            <h3>📸 Upload Image for Detection</h3>
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                Click to upload vehicle image<br>
                <small>Supports: JPG, PNG, JPEG</small>
                <input type="file" id="fileInput" accept="image/*" style="display:none" onchange="previewImage()">
            </div>
            <div id="preview"></div>
            <button class="btn" onclick="detectVehicle()">🔍 Detect Vehicles (92%+ Confidence)</button>
            <div class="loading" id="loading"><div class="spinner"></div><p>Analyzing...</p></div>
            <div id="detectionResult"></div>
        </div>
        
        <div class="stats-grid" id="statsGrid">
            <div class="stat-card"><div class="stat-value" id="totalDetections">0</div><div>Total Detections</div></div>
            <div class="stat-card"><div class="stat-value" id="todayDetections">0</div><div>Today</div></div>
            <div class="stat-card"><div class="stat-value" id="avgConfidence">0%</div><div>Avg Confidence</div></div>
            <div class="stat-card"><div class="stat-value" id="activeDays">0</div><div>Active Days</div></div>
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="switchTab('analytics')">📊 Analytics</div>
            <div class="tab" onclick="switchTab('logs')">📝 Recent Logs</div>
            <div class="tab" onclick="switchTab('heatmap')">🔥 Heatmap</div>
            <div class="tab" onclick="switchTab('insights')">💡 Insights</div>
        </div>
        
        <div id="analyticsTab" class="tab-content active">
            <div class="chart-card"><h3>Hourly Trends (Last 7 Days)</h3><div class="chart-container" id="hourlyChart"></div></div>
            <div class="chart-card"><h3>Daily Trends (Last 30 Days)</h3><div class="chart-container" id="dailyChart"></div></div>
            <div class="chart-card"><h3>Vehicle Distribution</h3><div class="chart-container" id="distributionChart"></div></div>
        </div>
        
        <div id="logsTab" class="tab-content">
            <div class="chart-card"><h3>Recent Detection Logs</h3><div id="logsTable"></div><button class="btn" onclick="exportData()" style="margin-top: 10px;">📥 Export CSV</button></div>
        </div>
        
        <div id="heatmapTab" class="tab-content">
            <div class="chart-card"><h3>Detection Heatmap (Hour × Day)</h3><div class="chart-container" id="heatmapChart"></div></div>
            <div class="chart-card"><h3>Peak Hours</h3><div class="chart-container" id="peakHoursChart"></div></div>
        </div>
        
        <div id="insightsTab" class="tab-content">
            <div class="chart-card"><h3>AI-Powered Insights</h3><div id="insightsList"></div></div>
        </div>
    </div>
    
    <script>
        let currentFile = null;
        
        function previewImage() {
            const file = document.getElementById('fileInput').files[0];
            if (file) {
                currentFile = file;
                const reader = new FileReader();
                reader.onload = e => document.getElementById('preview').innerHTML = `<img src="${e.target.result}" class="preview-img">`;
                reader.readAsDataURL(file);
            }
        }
        
        async function detectVehicle() {
            if (!currentFile) { alert('Select an image'); return; }
            const formData = new FormData();
            formData.append('file', currentFile);
            document.getElementById('loading').style.display = 'block';
            try {
                const response = await fetch('/detect', { method: 'POST', body: formData });
                const data = await response.json();
                if (data.success) {
                    let html = `<div style="margin-top: 15px; padding: 15px; background: #d4edda; border-radius: 8px;">
                        <strong>✅ Detection Complete!</strong><br>
                        Vehicles Found: ${data.total_vehicles}<br>
                        ${Object.entries(data.vehicle_breakdown || {}).map(([k,v]) => `${k}: ${v}`).join(', ')}
                    </div>`;
                    document.getElementById('detectionResult').innerHTML = html;
                    loadAllData();
                }
            } catch(e) { console.error(e); }
            finally { document.getElementById('loading').style.display = 'none'; }
        }
        
        async function loadAllData() {
            await loadStatistics();
            await loadAnalytics();
            await loadLogs();
            await loadHeatmap();
            await loadInsights();
        }
        
        async function loadStatistics() {
            try {
                const response = await fetch('/api/statistics');
                const stats = await response.json();
                document.getElementById('totalDetections').textContent = stats.total_detections || 0;
                document.getElementById('todayDetections').textContent = stats.today_detections || 0;
                document.getElementById('avgConfidence').innerHTML = `${Math.round((stats.average_confidence || 0) * 100)}%`;
                document.getElementById('activeDays').textContent = stats.active_days || 0;
            } catch(e) { console.error('Stats error:', e); }
        }
        
        async function loadAnalytics() {
            try {
                const response = await fetch('/api/analytics');
                const data = await response.json();
                
                if (data.hourly && data.hourly.length > 0) {
                    const hourlyData = {};
                    data.hourly.forEach(d => {
                        if (!hourlyData[d.hour]) hourlyData[d.hour] = {};
                        hourlyData[d.hour][d.vehicle_type] = d.count;
                    });
                    const hours = [...new Set(data.hourly.map(d => d.hour))].sort();
                    const vehicles = [...new Set(data.hourly.map(d => d.vehicle_type))];
                    const traces = vehicles.map(v => ({
                        name: v.toUpperCase(),
                        x: hours,
                        y: hours.map(h => hourlyData[h]?.[v] || 0),
                        type: 'bar'
                    }));
                    Plotly.newPlot('hourlyChart', traces, { barmode: 'stack', title: 'Vehicles by Hour' });
                }
                
                if (data.daily && data.daily.length > 0) {
                    const dailyData = {};
                    data.daily.forEach(d => {
                        if (!dailyData[d.date]) dailyData[d.date] = {};
                        dailyData[d.date][d.vehicle_type] = d.count;
                    });
                    const dates = [...new Set(data.daily.map(d => d.date))].slice(-30);
                    const vehicles = [...new Set(data.daily.map(d => d.vehicle_type))];
                    const traces = vehicles.map(v => ({
                        name: v.toUpperCase(),
                        x: dates,
                        y: dates.map(date => dailyData[date]?.[v] || 0),
                        type: 'scatter',
                        mode: 'lines+markers'
                    }));
                    Plotly.newPlot('dailyChart', traces, { title: 'Daily Trends' });
                }
                
                if (data.distribution && data.distribution.length > 0) {
                    Plotly.newPlot('distributionChart', [{
                        labels: data.distribution.map(d => d.vehicle_type.toUpperCase()),
                        values: data.distribution.map(d => d.count),
                        type: 'pie',
                        hole: 0.3
                    }], { title: 'Vehicle Distribution' });
                }
            } catch(e) { console.error('Analytics error:', e); }
        }
        
        async function loadLogs() {
            try {
                const response = await fetch('/api/logs?limit=20');
                const logs = await response.json();
                let html = '<table class="log-table"><thead><tr><th>Time</th><th>Vehicle</th><th>Confidence</th></tr></thead><tbody>';
                logs.forEach(log => {
                    html += `<tr><td>${new Date(log.timestamp).toLocaleString()}</td><td>${log.vehicle_type.toUpperCase()}</td><td>${(log.confidence * 100).toFixed(1)}%</td></tr>`;
                });
                html += '</tbody></table>';
                document.getElementById('logsTable').innerHTML = html;
            } catch(e) { console.error('Logs error:', e); }
        }
        
        async function loadHeatmap() {
            try {
                const response = await fetch('/api/analytics');
                const data = await response.json();
                
                if (data.heatmap && data.heatmap.length > 0) {
                    const heatmapData = {};
                    data.heatmap.forEach(d => {
                        if (!heatmapData[d.day_of_week]) heatmapData[d.day_of_week] = {};
                        heatmapData[d.day_of_week][d.hour] = d.count;
                    });
                    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
                    const hours = [...Array(24).keys()];
                    const z = days.map((_, i) => hours.map(h => heatmapData[i]?.[h] || 0));
                    Plotly.newPlot('heatmapChart', [{ z: z, x: hours, y: days, type: 'heatmap', colorscale: 'Viridis' }], { title: 'Detection Heatmap' });
                }
                
                if (data.peak_hours && data.peak_hours.length > 0) {
                    Plotly.newPlot('peakHoursChart', [{
                        x: data.peak_hours.map(p => `${p.hour}:00`),
                        y: data.peak_hours.map(p => p.count),
                        type: 'bar',
                        marker: { color: '#667eea' }
                    }], { title: 'Top 5 Peak Hours' });
                }
            } catch(e) { console.error('Heatmap error:', e); }
        }
        
        async function loadInsights() {
            try {
                const response = await fetch('/api/insights');
                const insights = await response.json();
                let html = '<ul style="list-style: none; padding: 0;">';
                insights.forEach(insight => {
                    html += `<li style="padding: 10px; margin: 10px 0; background: #f8f9fa; border-radius: 8px;">💡 ${insight}</li>`;
                });
                html += '</ul>';
                document.getElementById('insightsList').innerHTML = html;
            } catch(e) { console.error('Insights error:', e); }
        }
        
        async function exportData() {
            window.location.href = '/export/csv';
        }
        
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(`${tabName}Tab`).classList.add('active');
            event.target.classList.add('active');
        }
        
        loadAllData();
        setInterval(loadAllData, 30000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML)

@app.post("/detect")
async def detect_vehicle(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        result = detector.detect(image_bytes)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/statistics")
async def get_statistics():
    return detector.get_statistics()

@app.get("/api/logs")
async def get_logs(limit: int = Query(20, ge=1, le=100)):
    return detector.get_recent_logs(limit)

@app.get("/api/analytics")
async def get_analytics():
    return detector.get_analytics_data()

@app.get("/api/insights")
async def get_insights():
    return detector.get_insights()

@app.get("/export/csv")
async def export_csv():
    csv_path = detector.export_csv()
    return FileResponse(csv_path, media_type='text/csv', filename=csv_path)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model": "YOLOv8x",
        "confidence_threshold": detector.conf_threshold
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚗 VEHICLE DETECTION SYSTEM")
    print("="*60)
    print("📍 Web Interface: http://localhost:8000")
    print("📊 All endpoints ready!")
    print("="*60)
    print("\n✅ Server is running...\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
