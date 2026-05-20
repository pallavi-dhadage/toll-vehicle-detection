import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import axios from 'axios';
import { FaCar, FaTruck, FaBus, FaMotorcycle, FaUpload, FaChartLine } from 'react-icons/fa';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Dashboard = () => {
  const [stats, setStats] = useState({ total: 0, car: 0, truck: 0, bus: 0 });
  const [detections, setDetections] = useState([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get('http://localhost:8000/stats/camera1');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/detect', formData);
      if (response.data.success) {
        setDetections(response.data.detections);
        toast.success(`✅ Detected ${response.data.count} vehicles!`);
        fetchStats();
      }
    } catch (error) {
      toast.error('Detection failed');
    } finally {
      setUploading(false);
    }
  };

  const statCards = [
    { icon: <FaCar />, label: 'Cars', value: stats.car || 0, color: '#667eea' },
    { icon: <FaTruck />, label: 'Trucks', value: stats.truck || 0, color: '#764ba2' },
    { icon: <FaBus />, label: 'Buses', value: stats.bus || 0, color: '#f093fb' },
    { icon: <FaMotorcycle />, label: 'Total', value: stats.total || 0, color: '#4facfe' },
  ];

  const chartData = [
    { name: 'Mon', vehicles: 65 }, { name: 'Tue', vehicles: 78 }, { name: 'Wed', vehicles: 82 },
    { name: 'Thu', vehicles: 91 }, { name: 'Fri', vehicles: 105 }, { name: 'Sat', vehicles: 98 }, { name: 'Sun', vehicles: 112 },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '10px' }}>Dashboard</h1>
        <p style={{ color: 'rgba(255, 255, 255, 0.7)' }}>Real-time vehicle detection and analytics</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '30px' }}>
        {statCards.map((card, index) => (
          <motion.div key={index} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.1 }} className="glass-card" style={{ padding: '25px', position: 'relative', overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div><p style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '14px' }}>{card.label}</p><h2 style={{ fontSize: '36px', fontWeight: '700', marginTop: '10px' }}>{card.value}</h2></div>
              <div style={{ fontSize: '48px', color: card.color, opacity: 0.8 }}>{card.icon}</div>
            </div>
            <div style={{ position: 'absolute', bottom: '0', left: '0', right: '0', height: '3px', background: `linear-gradient(90deg, ${card.color}, transparent)` }} />
          </motion.div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '30px' }}>
        <div className="glass-card" style={{ padding: '25px' }}>
          <h3 style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}><FaChartLine /> Weekly Traffic Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="name" stroke="rgba(255,255,255,0.5)" />
              <YAxis stroke="rgba(255,255,255,0.5)" />
              <Tooltip contentStyle={{ background: 'rgba(0,0,0,0.8)', border: 'none', borderRadius: '10px', color: '#fff' }} />
              <Line type="monotone" dataKey="vehicles" stroke="#667eea" strokeWidth={2} dot={{ fill: '#764ba2' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="glass-card" style={{ padding: '25px' }}>
          <h3 style={{ marginBottom: '20px' }}><FaUpload /> Vehicle Detection</h3>
          <div style={{ border: '2px dashed rgba(102, 126, 234, 0.5)', borderRadius: '15px', padding: '40px', textAlign: 'center', cursor: 'pointer' }}
            onMouseEnter={(e) => e.currentTarget.style.borderColor = '#667eea'} onMouseLeave={(e) => e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.5)'}>
            <input type="file" accept="image/*" onChange={handleImageUpload} style={{ display: 'none' }} id="image-upload" />
            <label htmlFor="image-upload" style={{ cursor: 'pointer' }}>
              <FaUpload size={48} color="#667eea" />
              <p style={{ marginTop: '15px' }}>{uploading ? 'Processing...' : 'Click or drag to upload image'}</p>
            </label>
          </div>
          {detections.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <h4>Detection Results:</h4>
              {detections.map((det, idx) => (
                <div key={idx} style={{ padding: '10px', margin: '10px 0', background: 'rgba(102, 126, 234, 0.2)', borderRadius: '8px', display: 'flex', justifyContent: 'space-between' }}>
                  <span>{det.type}</span><span>{Math.round(det.confidence * 100)}% confidence</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default Dashboard;
