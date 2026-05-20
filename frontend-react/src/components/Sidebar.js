import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FaTachometerAlt, FaFileAlt, FaFire, FaLayerGroup,
  FaInfoCircle, FaCrown, FaChevronLeft, FaChevronRight,
  FaMoon, FaSun, FaCar
} from 'react-icons/fa';

const Sidebar = ({ isCollapsed, setIsCollapsed, toggleTheme, isDarkMode }) => {
  const menuItems = [
    { path: '/dashboard', icon: <FaTachometerAlt />, label: 'Dashboard' },
    { path: '/reports', icon: <FaFileAlt />, label: 'Reports' },
    { path: '/heatmap', icon: <FaFire />, label: 'Heatmap' },
    { path: '/multi-angle', icon: <FaLayerGroup />, label: 'Multi-Angle' },
    { path: '/about', icon: <FaInfoCircle />, label: 'About' },
    { path: '/admin', icon: <FaCrown />, label: 'Admin' },
  ];

  return (
    <motion.div
      initial={{ x: -280 }}
      animate={{ x: 0 }}
      transition={{ duration: 0.5 }}
      style={{
        position: 'fixed',
        left: 0,
        top: 0,
        height: '100vh',
        width: isCollapsed ? '80px' : '280px',
        background: 'linear-gradient(180deg, rgba(15, 12, 41, 0.95) 0%, rgba(36, 36, 62, 0.95) 100%)',
        backdropFilter: 'blur(10px)',
        borderRight: '1px solid rgba(102, 126, 234, 0.3)',
        transition: 'width 0.3s ease',
        zIndex: 1000,
        overflowY: 'auto',
        boxShadow: '5px 0 30px rgba(0, 0, 0, 0.3)',
      }}
    >
      <div style={{ padding: '30px 20px', textAlign: 'center', borderBottom: '1px solid rgba(102, 126, 234, 0.3)', marginBottom: '20px' }}>
        <motion.div whileHover={{ scale: 1.05 }} style={{ cursor: 'pointer' }}>
          <FaCar size={isCollapsed ? 30 : 40} style={{ color: '#667eea', marginBottom: '10px' }} />
          {!isCollapsed && (
            <motion.h3 initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{ background: 'linear-gradient(135deg, #667eea, #764ba2)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontSize: '18px', marginTop: '10px' }}>
              TollPlaza AI
            </motion.h3>
          )}
        </motion.div>
      </div>

      <nav style={{ padding: '0 15px' }}>
        {menuItems.map((item, index) => (
          <NavLink
            key={index}
            to={item.path}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '15px',
              padding: '12px 15px',
              margin: '8px 0',
              borderRadius: '12px',
              textDecoration: 'none',
              color: isActive ? '#fff' : 'rgba(255, 255, 255, 0.7)',
              background: isActive ? 'linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2))' : 'transparent',
              border: isActive ? '1px solid rgba(102, 126, 234, 0.5)' : '1px solid transparent',
              transition: 'all 0.3s ease',
              justifyContent: isCollapsed ? 'center' : 'flex-start',
            })}
          >
            <span style={{ fontSize: '20px' }}>{item.icon}</span>
            {!isCollapsed && <span style={{ fontSize: '14px', fontWeight: 500 }}>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <div style={{ position: 'absolute', bottom: '20px', left: isCollapsed ? '10px' : '20px', right: isCollapsed ? '10px' : '20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={toggleTheme} style={{ display: 'flex', alignItems: 'center', justifyContent: isCollapsed ? 'center' : 'flex-start', gap: '15px', padding: '10px 15px', background: 'linear-gradient(135deg, #667eea, #764ba2)', border: 'none', borderRadius: '10px', color: '#fff', cursor: 'pointer', fontSize: '16px' }}>
          {isDarkMode ? <FaSun /> : <FaMoon />}
          {!isCollapsed && <span>{isDarkMode ? 'Light Mode' : 'Dark Mode'}</span>}
        </motion.button>
        <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={() => setIsCollapsed(!isCollapsed)} style={{ display: 'flex', alignItems: 'center', justifyContent: isCollapsed ? 'center' : 'flex-start', gap: '15px', padding: '10px 15px', background: 'rgba(255, 255, 255, 0.1)', border: '1px solid rgba(255, 255, 255, 0.2)', borderRadius: '10px', color: '#fff', cursor: 'pointer', fontSize: '16px' }}>
          {isCollapsed ? <FaChevronRight /> : <FaChevronLeft />}
          {!isCollapsed && <span>Collapse</span>}
        </motion.button>
      </div>
    </motion.div>
  );
};

export default Sidebar;
