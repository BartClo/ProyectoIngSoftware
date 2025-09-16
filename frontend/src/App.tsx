import { useState } from 'react';
import './App.css';
<<<<<<< Updated upstream
import Login from './components/Login';
import Chatbot from './components/Chatbot';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  return isLoggedIn ? (
    <Chatbot />
  ) : (
    <Login onLogin={() => setIsLoggedIn(true)} />
  );
=======
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
>>>>>>> Stashed changes
}

export default App
