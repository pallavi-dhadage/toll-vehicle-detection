import React from 'react';
import { motion } from 'framer-motion';
import { FaInfoCircle, FaGavel, FaMoneyBill, FaPhone } from 'react-icons/fa';

const About = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700' }}>About Toll Plaza</h1>
        <p style={{ color: 'rgba(255, 255, 255, 0.7)' }}>Information and regulations</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div className="glass-card" style={{ padding: '25px' }}>
          <h3><FaInfoCircle /> About</h3>
          <div style={{ marginTop: '15px' }}>
            <p><strong>Location:</strong> NH-48, Gurugram, India</p>
            <p><strong>Established:</strong> 2015</p>
            <p><strong>Daily Traffic:</strong> ~50,000 vehicles</p>
            <p><strong>Lanes:</strong> 12 (6 each direction)</p>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '25px' }}>
          <h3><FaGavel /> Rules & Regulations</h3>
          <div style={{ marginTop: '15px' }}>
            <p>✓ Speed limit: 40 km/h</p>
            <p>✓ FASTag mandatory</p>
            <p>✓ No overtaking near booths</p>
            <p>✓ Emergency: 1033</p>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '25px' }}>
          <h3><FaMoneyBill /> Toll Rates</h3>
          <div style={{ marginTop: '15px' }}>
            <p>Car/Jeep/Van: ₹85</p>
            <p>Light Commercial: ₹135</p>
            <p>Bus/Truck: ₹290</p>
            <p>Heavy Vehicle: ₹450</p>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '25px' }}>
          <h3><FaPhone /> Contact</h3>
          <div style={{ marginTop: '15px' }}>
            <p>Email: support@tollplaza.ai</p>
            <p>Phone: +91-124-4567890</p>
            <p>Helpline: 1033</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default About;
