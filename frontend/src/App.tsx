import { useState } from 'react';
import './App.css';
import Login from './components/auth/login';
import Dashboard from './components/dashboard/dashboard';
import { ThemeProvider } from './components/theme/theme-context';
import './components/theme/theme.css';
import AdminDashboard from './components/admin/admin-dashboard';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);
  
  const handleLogin = (email: string, asAdmin: boolean) => {
    setUserEmail(email);
    setIsAuthenticated(true);
    setIsAdmin(asAdmin);
  };
  
  const handleLogout = () => {
    setIsAuthenticated(false);
    setUserEmail('');
    setIsAdmin(false);
  };
  
  return (
    <ThemeProvider>
      <div className="app-container">
        {!isAuthenticated && <Login onLogin={handleLogin} />}
        {isAuthenticated && (
          isAdmin ? (
            <AdminDashboard userEmail={userEmail} onLogout={handleLogout} />
          ) : (
            <Dashboard userEmail={userEmail} onLogout={handleLogout} />
          )
        )}
      </div>
    </ThemeProvider>);
}

export default App
