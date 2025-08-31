import { useState } from 'react';
import './App.css';
import Login from './components/Login';
import Chatbot from './components/Chatbot';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  return isLoggedIn ? (
    <Chatbot />
  ) : (
    <Login onLogin={() => setIsLoggedIn(true)} />
  );
}

export default App;
