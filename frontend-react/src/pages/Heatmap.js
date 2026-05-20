import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Heatmap = () => {
  const data = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    vehicles: Math.floor(Math.random() * 100)
  }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700' }}>Traffic Heatmap</h1>
        <p style={{ color: 'rgba(255, 255, 255, 0.7)' }}>Hourly vehicle frequency</p>
      </div>

      <div className="glass-card" style={{ padding: '30px' }}>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey="hour" stroke="rgba(255,255,255,0.5)" />
            <YAxis stroke="rgba(255,255,255,0.5)" />
            <Tooltip 
              contentStyle={{ 
                background: 'rgba(0,0,0,0.8)', 
                border: 'none', 
                borderRadius: '10px',
                color: '#fff'
              }} 
            />
            <Bar dataKey="vehicles" fill="url(#gradient)" radius={[10, 10, 0, 0]} />
            <defs>
              <linearGradient id="gradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#667eea" />
                <stop offset="100%" stopColor="#764ba2" />
              </linearGradient>
            </defs>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
};

export default Heatmap;
