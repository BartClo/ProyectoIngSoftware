import { useState } from 'react';
import './dashboard-header.css';
import faviconUSS from '/FaviconUSS.png';

interface DashboardHeaderProps {
  userEmail: string;
  onLogout: () => void;
  onSettings: () => void;
  onHelp: () => void;
}

const DashboardHeader: React.FC<DashboardHeaderProps> = ({
  userEmail,
  onLogout,
  onSettings,
  onHelp
}) => {
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  
  // Extraer la primera letra del correo para el avatar
  const userInitial = userEmail && userEmail.length > 0 
    ? userEmail.charAt(0).toUpperCase() 
    : 'U';
  
  const handleLogoutClick = () => {
    setShowLogoutConfirm(true);
  };

  const confirmLogout = () => {
    setShowLogoutConfirm(false);
    onLogout();
  };

  const cancelLogout = () => {
    setShowLogoutConfirm(false);
  };

  return (
    <header className="dashboard-header">
      {/* Lado izquierdo - Logo y título */}
      <div className="header-left">
        <div className="header-logo-container">
          <img src={faviconUSS} alt="Logo USS" className="header-logo" />
          <span className="header-logo-text">IA USS</span>
        </div>
        <h1 className="header-title">Asistente IA USS</h1>
      </div>

      {/* Lado derecho - Usuario y acciones */}
      <div className="header-right">
        <div className="header-user-info">
          <span className="header-email">{userEmail}</span>
          <div className="header-avatar">{userInitial}</div>
        </div>

        <div className="header-actions">
          <button 
            className="header-button help-button"
            onClick={onHelp} 
            aria-label="Ayuda"
          >
            <span className="icon">❓</span>
          </button>
          <button 
            className="header-button settings-button"
            onClick={onSettings} 
            aria-label="Configuración"
          >
            <span className="icon">⚙️</span>
          </button>
          <button 
            className="header-button logout-button"
            onClick={handleLogoutClick} 
            aria-label="Cerrar sesión"
          >
            <span className="icon">🚪</span>
          </button>
        </div>
      </div>

      {/* Modal de confirmación para cerrar sesión */}
      {showLogoutConfirm && (
        <div className="logout-confirm-modal">
          <div className="modal-content">
            <h3>Cerrar Sesión</h3>
            <p>¿Está seguro que desea cerrar su sesión?</p>
            <div className="modal-buttons">
              <button 
                className="cancel-button"
                onClick={cancelLogout}
              >
                Cancelar
              </button>
              <button 
                className="confirm-button"
                onClick={confirmLogout}
              >
                Cerrar Sesión
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

export default DashboardHeader;
