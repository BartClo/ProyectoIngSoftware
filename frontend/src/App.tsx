import { useState } from 'react';
import Login from './components/auth/login';
import ChatInterface from './components/chat/chat-interface';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userEmail, setUserEmail] = useState("");

  const handleLoginSuccess = (email: string) => {
    setUserEmail(email);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUserEmail("");
  };

  return (
    <div style={{ minHeight: "100vh", width: "100vw", display: "flex", flexDirection: "column", background: "#f5f9fc" }}>
      {isAuthenticated ? (
        <ChatInterface email={userEmail} onLogout={handleLogout} />
      ) : (
        <Login onLoginSuccess={handleLoginSuccess} />
      )}
    </div>
  );
}

export default App;
