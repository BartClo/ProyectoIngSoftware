import { useState } from 'react';
import './App.css';
import Login from './components/auth/login';
import Dashboard from './components/dashboard/dashboard';
import { ThemeProvider } from './components/theme/theme-context';
import './components/theme/theme.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  
  const handleLogin = (email: string) => {
    setUserEmail(email);
    setIsAuthenticated(true);
  };
  
  const handleLogout = () => {
    setIsAuthenticated(false);
    setUserEmail('');
  };
  
  return (
    <ThemeProvider>
      <div className="app-container">
        {!isAuthenticated ? (
          <Login onLogin={handleLogin} />
        ) : (
          <Dashboard userEmail={userEmail} onLogout={handleLogout} />
        )}
      </div>
    </ThemeProvider>);
}

export default App
