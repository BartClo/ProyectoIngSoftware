import React, { useState, useEffect } from 'react';
import './settings-modal.css';
import { useTheme } from '../theme/theme-context';

interface SettingsModalProps {
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ onClose }) => {
  const { theme, fontSize, setTheme, setFontSize } = useTheme();
  const [localTheme, setLocalTheme] = useState(theme);
  const [localFontSize, setLocalFontSize] = useState(fontSize);
  const [hasChanges, setHasChanges] = useState(false);
  
  // Detectar cambios en la configuración
  useEffect(() => {
    if (localTheme !== theme || localFontSize !== fontSize) {
      setHasChanges(true);
    } else {
      setHasChanges(false);
    }
  }, [localTheme, localFontSize, theme, fontSize]);
  
  // Manejar el cambio de tema
  const handleThemeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLocalTheme(e.target.value as 'light' | 'dark' | 'system');
  };
  
  // Manejar el cambio de tamaño de fuente
  const handleFontSizeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setLocalFontSize(e.target.value as 'small' | 'medium' | 'large');
  };
  
  // Guardar los cambios
  const handleSaveChanges = () => {
    setTheme(localTheme as 'light' | 'dark' | 'system');
    setFontSize(localFontSize as 'small' | 'medium' | 'large');
    setHasChanges(false);
    
    // Mostrar notificación de éxito (opcional)
    alert("Configuración guardada con éxito");
  };

  return (
    <div className="settings-modal-overlay">
      <div className="settings-modal-container">
        <div className="settings-modal-header">
          <h2>Configuración</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>
        
        <div className="settings-modal-content">
          <div className="settings-section">
            <h3>Interfaz</h3>
            
            <div className="setting-item">
              <label>Tema</label>
              <select 
                className="setting-input" 
                value={localTheme} 
                onChange={handleThemeChange}
              >
                <option value="light">Claro</option>
                <option value="dark">Oscuro</option>
                <option value="system">Sistema</option>
              </select>
            </div>
            
            <div className="setting-item">
              <label>Tamaño de fuente</label>
              <select 
                className="setting-input"
                value={localFontSize}
                onChange={handleFontSizeChange}
              >
                <option value="small">Pequeño</option>
                <option value="medium">Mediano</option>
                <option value="large">Grande</option>
              </select>
            </div>
          </div>
        </div>
        
        <div className="settings-modal-footer">
          <button className="cancel-button" onClick={onClose}>Cerrar</button>
          <button 
            className="save-button"
            onClick={handleSaveChanges}
            disabled={!hasChanges}
          >
            Guardar cambios
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
