import { useState } from 'react';
import './dashboard-header.css';

interface DashboardHeaderProps {
  userEmail: string;
  onLogout: () => void;
  onSettings: () => void;
  onHelp: () => void;
  showAdminActions?: boolean;
  activeAdminView?: 'users' | 'reports' | 'create-conv';
  onReportsClick?: () => void;
  onCreateConversationClick?: () => void;
  onUsersAdminClick?: () => void;
}

const DashboardHeader: React.FC<DashboardHeaderProps> = ({
  userEmail,
  onLogout,
  onSettings,
  onHelp,
  showAdminActions,
  activeAdminView,
  onReportsClick,
  onCreateConversationClick,
  onUsersAdminClick
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
          <img src="/FaviconUSS.png" alt="Logo USS" className="header-logo" />
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

        {showAdminActions && (
          <div className="header-quick-actions">
            <button
              className={`cta-button ${activeAdminView === 'users' ? 'active' : ''}`}
              onClick={onUsersAdminClick}
              title="Administración de usuarios"
            >
              Administración de usuarios
            </button>

            <button
              className={`cta-button ${activeAdminView === 'reports' ? 'active' : ''}`}
              onClick={onReportsClick}
              title="Ver reportes"
            >
              Reportes
            </button>
            <button
              className={`cta-button ${activeAdminView === 'create-conv' ? 'active' : ''}`}
              onClick={onCreateConversationClick}
              title="Gestión de IA y Documentos"
            >
              Gestión de IA
            </button>
          </div>
        )}

        <div className="header-actions">
          <button 
            className="header-button help-button"
            onClick={onHelp} 
            aria-label="Ayuda"
            title="Ver ayuda"
          >
            <span className="icon">❓</span>
          </button>
          <button 
            className="header-button settings-button"
            onClick={onSettings} 
            aria-label="Configuración"
            title="Abrir configuración"
          >
            <span className="icon">⚙️</span>
          </button>
          <button 
            className="header-button logout-button"
            onClick={handleLogoutClick} 
            aria-label="Cerrar sesión"
            title="Cerrar sesión"
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
