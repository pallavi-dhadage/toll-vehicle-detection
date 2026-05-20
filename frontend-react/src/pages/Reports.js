import React, { useState } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { FaDownload, FaCalendar } from 'react-icons/fa';

const Reports = () => {
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);

  const downloadReport = () => {
    window.open('http://localhost:8000/generate-report', '_blank');
    toast.success('Downloading report...');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700' }}>Reports</h1>
        <p style={{ color: 'rgba(255, 255, 255, 0.7)' }}>Download vehicle detection reports</p>
      </div>

      <div className="glass-card" style={{ padding: '30px', maxWidth: '500px' }}>
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '10px' }}>
            <FaCalendar style={{ marginRight: '8px' }} /> Select Date
          </label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '10px',
              color: '#fff',
              fontSize: '16px'
            }}
          />
        </div>
        <button
          onClick={downloadReport}
          style={{
            width: '100%',
            padding: '14px',
            background: 'linear-gradient(135deg, #667eea, #764ba2)',
            border: 'none',
            borderRadius: '10px',
            color: '#fff',
            fontSize: '16px',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px'
          }}
        >
          <FaDownload /> Download Excel Report
        </button>
      </div>
    </motion.div>
  );
};

export default Reports;
