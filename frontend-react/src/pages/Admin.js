import React, { useState } from 'react';
import { motion } from 'framer-motion';
import toast from 'react-hot-toast';
import { FaLock, FaUser, FaKey } from 'react-icons/fa';

const Admin = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = () => {
    if (email === 'admin@example.com' && password === 'admin123') {
      setIsLoggedIn(true);
      toast.success('Login successful!');
    } else {
      toast.error('Invalid credentials');
    }
  };

  if (!isLoggedIn) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card"
        style={{ maxWidth: '400px', margin: '0 auto', padding: '40px' }}
      >
        <h2 style={{ textAlign: 'center', marginBottom: '30px' }}><FaLock /> Admin Login</h2>
        <div style={{ marginBottom: '20px' }}>
          <label><FaUser /> Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@example.com"
            style={{
              width: '100%',
              padding: '12px',
              marginTop: '8px',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '8px',
              color: '#fff'
            }}
          />
        </div>
        <div style={{ marginBottom: '20px' }}>
          <label><FaKey /> Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••"
            style={{
              width: '100%',
              padding: '12px',
              marginTop: '8px',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '8px',
              color: '#fff'
            }}
          />
        </div>
        <button
          onClick={handleLogin}
          style={{
            width: '100%',
            padding: '14px',
            background: 'linear-gradient(135deg, #667eea, #764ba2)',
            border: 'none',
            borderRadius: '8px',
            color: '#fff',
            fontWeight: '600',
            cursor: 'pointer'
          }}
        >
          Login
        </button>
        <p style={{ textAlign: 'center', marginTop: '20px', fontSize: '12px', opacity: 0.7 }}>
          Demo: admin@example.com / admin123
        </p>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <h1>Admin Panel</h1>
      <p>Welcome back, Admin!</p>
    </motion.div>
  );
};

export default Admin;
