import { useState } from 'react';
import DashboardHeader from './dashboard-header';
import ChatInterface from '../chat/chat-interface/chat-interface';
import SettingsModal from '../settings/settings-modal';
import HelpModel from '../chat/help-model/help-model';
import './dashboard.css';

interface DashboardProps {
  userEmail: string;
  onLogout: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ userEmail, onLogout }) => {
  const [showSettings, setShowSettings] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  const handleSettingsClick = () => {
    setShowSettings(true);
    setShowHelp(false);
  };

  const handleHelpClick = () => {
    setShowHelp(true);
    setShowSettings(false);
  };

  return (
    <div className="dashboard-container">
      <DashboardHeader 
        userEmail={userEmail}
        onLogout={onLogout}
        onSettings={handleSettingsClick}
        onHelp={handleHelpClick}
      />
      
      <div className="dashboard-content">
        {/* Interfaz de chat principal */}
        <ChatInterface />
        
        {/* Panel de configuración condicional */}
        {showSettings && (
          <SettingsModal onClose={() => setShowSettings(false)} />
        )}
        
        {/* Panel de ayuda condicional */}
        {showHelp && (
          <HelpModel onClose={() => setShowHelp(false)} />
        )}
      </div>
    </div>
  );
};

export default Dashboard;