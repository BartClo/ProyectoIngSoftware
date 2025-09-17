import React, { useState } from 'react';
import ussLogo from '../assets/uss-logo.png';

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

interface LoginProps {
  onLogin: () => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const emailRegex = /^[a-zA-Z0-9._%+-]+@docente\.uss\.cl$/;
    if (!emailRegex.test(email)) {
      setError('El correo debe tener el formato xxx@docente.uss.cl');
      return;
    }
    if (!password) {
      setError('La contraseña es obligatoria');
      return;
    }
    setError('');

    const body = new URLSearchParams();
    body.append('username', email); // El backend espera un 'username'
    body.append('password', password);

    try {
      const response = await fetch(`${API_BASE_URL}/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: body.toString(),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        onLogin(); // Llama a la función solo si el login es exitoso
      } else {
        // El backend envió un error (ej. 401 Unauthorized)
        setError('Credenciales inválidas');
      }
    } catch (err) {
      setError('No se pudo conectar con el servidor.');
    }
  };

  return (
    <>
      <style>{`
        html, body {
          background: #fff !important;
          margin: 0;
          padding: 0;
          height: 100%;
        }
        input[type="email"], input[type="password"] {
          background: #fff !important;
          color: #222 !important;
        }
      `}</style>
      <div style={{
        background: '#fff',
        borderRadius: 16,
        boxShadow: '0 4px 24px rgba(0,0,0,0.10)',
        padding: '2.5rem 2.2rem 2rem 2.2rem',
        minWidth: 340,
        maxWidth: 410,
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}>
        <img src={ussLogo} alt="USS Logo" style={{ width: 170, height: 'auto', marginBottom: 18 }} />
        <h2 style={{ color: '#003057', marginBottom: 6, fontWeight: 700, fontSize: 23, width: '100%', textAlign: 'left' }}>Chatbot USS</h2>
        <p style={{ color: '#555', margin: 0, marginBottom: 18, fontSize: 15, width: '100%', textAlign: 'left' }}>Inicia sesión para continuar con tu asistente</p>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.1rem', width: '100%' }}>
          <div style={{ width: '100%' }}>
            <label style={{ color: '#222', fontWeight: 600, fontSize: 14, marginBottom: 4, display: 'block' }}>Correo institucional</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="usuario@docente.uss.cl"
              required
              style={{ width: '100%', padding: '0.7rem', borderRadius: 7, border: '1px solid #e0e0e0', marginTop: 2, fontSize: 15, background: '#fff', color: '#222' }}
            />
          </div>
          <div style={{ width: '100%' }}>
            <label style={{ color: '#222', fontWeight: 600, fontSize: 14, marginBottom: 4, display: 'block' }}>Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              style={{ width: '100%', padding: '0.7rem', borderRadius: 7, border: '1px solid #e0e0e0', marginTop: 2, fontSize: 15, background: '#fff', color: '#222' }}
            />
          </div>
          {error && <div style={{ color: '#d32f2f', background: '#ffeaea', borderRadius: 4, fontWeight: 500, textAlign: 'center', fontSize: 15, padding: '0.3rem 0.5rem' }}>{error}</div>}
          <button type="submit" style={{ padding: '0.8rem', background: '#0057b8', color: 'white', border: 'none', borderRadius: 7, fontWeight: 600, fontSize: 16, marginTop: 8, cursor: 'pointer', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
            Iniciar sesión
          </button>
        </form>
        <p style={{ color: '#888', fontSize: 12, marginTop: 18, textAlign: 'center' }}>
          Al continuar aceptas nuestros{' '}
          <a href="#" style={{ color: '#0057b8', textDecoration: 'underline', fontWeight: 500 }}>Términos y Política de Privacidad</a>.
        </p>
      </div>
    </>
  );
};

export default Login;
