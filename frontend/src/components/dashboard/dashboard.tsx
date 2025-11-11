import { useState } from 'react';
import DashboardHeader from './dashboard-header';
import ChatInterface from '../chat/chat-interface/chat-interface';
import HelpModel from '../chat/help-model/help-model';
import './dashboard.css';

interface DashboardProps {
  userEmail: string;
  onLogout: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ userEmail, onLogout }) => {
  const [showHelp, setShowHelp] = useState(false);

  const handleHelpClick = () => {
    setShowHelp(true);
  };

  return (
    <div className="dashboard-container">
      <DashboardHeader 
        userEmail={userEmail}
        onLogout={onLogout}
        onHelp={handleHelpClick}
      />
      
      <div className="dashboard-content">
        {/* Interfaz de chat principal */}
        <ChatInterface userEmail={userEmail} />
        
        {/* Panel de ayuda condicional */}
        {showHelp && (
          <HelpModel onClose={() => setShowHelp(false)} />
        )}
      </div>
    </div>
  );
};

export default Dashboard;