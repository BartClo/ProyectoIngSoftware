import { useState } from 'react';
import logoUSS from '../../assets/style/LogoUSS.svg';
import fondoUSS from '../../assets/style/FondoUSS.svg';
import './login.css';

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Aquí iría la lógica de autenticación
    if (emailError) {
      return;
    }
    
    // Simulamos autenticación exitosa y pasamos el correo al componente padre
    console.log('Email:', email, 'Password:', password);
    onLogin(email);
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
