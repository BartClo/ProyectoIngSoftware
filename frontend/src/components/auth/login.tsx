import { useState } from 'react';
import logoUSS from '../../assets/style/LogoUSS.svg';
import fondoUSS from '../../assets/style/FondoUSS.svg';
import './login.css';

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

interface LoginProps {
  onLogin: (email: string) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [emailError, setEmailError] = useState('');
  
  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setEmail(value);
    
    // Validar que el correo termine con @docente.uss.cl solo cuando el usuario ha escrito algo
    if (value && value.includes('@') && !value.endsWith('@docente.uss.cl')) {
      setEmailError('Debe usar su correo institucional');
    } else {
      setEmailError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (emailError) return;

    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const res = await fetch(`${API_BASE_URL}/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });

      if (!res.ok) {
        setEmailError('Credenciales inválidas');
        return;
      }

      const data = await res.json();
      const token = data?.access_token as string | undefined;
      if (!token) {
        setEmailError('Respuesta inválida del servidor');
        return;
      }

      // Guardar token para siguientes peticiones
      localStorage.setItem('authToken', token);
      // Avisar al componente padre
      onLogin(email);
    } catch (err) {
      console.error('Error en login:', err);
      setEmailError('No se pudo conectar con el servidor');
    }
  };

  return (
    <div className="login-container" style={{ backgroundImage: `url(${fondoUSS})` }}>
      <div className="login-form-container">
        <div className="login-logo">
          <img src={logoUSS} alt="Logo USS" />
        </div>
        <h1 className="login-title">Asistente IA</h1>
        <p className="login-subtitle">Inicie sesión con su cuenta institucional</p>
        
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Correo Electrónico</label>
            <input
              type="text"
              id="email"
              value={email}
              onChange={handleEmailChange}
              placeholder="usuario@docente.uss.cl"
              autoComplete="email"
              required
              className={`form-control ${emailError ? 'error' : ''}`}
            />
            <span className="error-message">{emailError}</span>
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Contraseña</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Ingrese su contraseña"
              autoComplete="current-password"
              required
              className="form-control"
            />
            <span className="error-message"></span>
          </div>
          
          <button type="submit" className="login-button">
            Iniciar Sesión
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
