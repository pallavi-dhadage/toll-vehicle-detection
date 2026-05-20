import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Reports from './pages/Reports';
import Heatmap from './pages/Heatmap';
import MultiAngle from './pages/MultiAngle';
import About from './pages/About';
import Admin from './pages/Admin';
import './styles/global.css';

function App() {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      setIsDarkMode(true);
      document.body.classList.add('dark-mode');
    }
  }, []);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    if (!isDarkMode) {
      document.body.classList.add('dark-mode');
      localStorage.setItem('theme', 'dark');
    } else {
      document.body.classList.remove('dark-mode');
      localStorage.setItem('theme', 'light');
    }
  };

  return (
    <Router>
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <Sidebar 
          isCollapsed={isSidebarCollapsed} 
          setIsCollapsed={setIsSidebarCollapsed}
          toggleTheme={toggleTheme}
          isDarkMode={isDarkMode}
        />
        <div style={{ 
          flex: 1, 
          marginLeft: isSidebarCollapsed ? '80px' : '280px',
          transition: 'margin-left 0.3s ease',
          padding: '20px'
        }}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/heatmap" element={<Heatmap />} />
            <Route path="/multi-angle" element={<MultiAngle />} />
            <Route path="/about" element={<About />} />
            <Route path="/admin" element={<Admin />} />
          </Routes>
        </div>
        <Toaster 
          position="top-right"
          toastOptions={{
            style: {
              background: 'linear-gradient(135deg, #667eea, #764ba2)',
              color: '#fff',
              borderRadius: '10px',
            },
          }}
        />
      </div>
    </Router>
  );
}

export default App;
