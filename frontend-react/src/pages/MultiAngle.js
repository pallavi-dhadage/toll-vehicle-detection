import React from 'react';
import { motion } from 'framer-motion';
import { FaCamera, FaPlus, FaCog } from 'react-icons/fa';

const MultiAngle = () => {
  const angles = [
    { name: 'Front View', icon: <FaCamera />, status: 'Active', color: '#10b981' },
    { name: 'Side View', icon: <FaCamera />, status: 'Inactive', color: '#ef4444' },
    { name: 'Overhead View', icon: <FaCamera />, status: 'Inactive', color: '#ef4444' },
    { name: 'Rear View', icon: <FaCamera />, status: 'Inactive', color: '#ef4444' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div style={{ marginBottom: '30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '32px', fontWeight: '700' }}>Multi-Angle Detection</h1>
          <p style={{ color: 'rgba(255, 255, 255, 0.7)' }}>Monitor vehicles from all angles</p>
        </div>
        <button
          style={{
            padding: '12px 24px',
            background: 'linear-gradient(135deg, #667eea, #764ba2)',
            border: 'none',
            borderRadius: '10px',
            color: '#fff',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <FaPlus /> Add Camera
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
        {angles.map((angle, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: idx * 0.1 }}
            className="glass-card"
            style={{ padding: '20px' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <h3>{angle.name}</h3>
              <span style={{ 
                padding: '4px 12px', 
                background: `${angle.color}20`, 
                color: angle.color,
                borderRadius: '20px',
                fontSize: '12px'
              }}>
                {angle.status}
              </span>
            </div>
            <div style={{ 
              background: 'rgba(0,0,0,0.3)', 
              borderRadius: '10px', 
              height: '250px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '15px'
            }}>
              {angle.icon} Camera Feed
            </div>
            <button
              style={{
                width: '100%',
                padding: '10px',
                background: 'rgba(255,255,255,0.1)',
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '8px',
                color: '#fff',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              <FaCog /> Configure
            </button>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

export default MultiAngle;
