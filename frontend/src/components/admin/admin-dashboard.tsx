import { useState } from 'react';
import '../dashboard/dashboard.css';
import DashboardHeader from '../dashboard/dashboard-header';
import UsersTable from './users-table';
import SettingsModal from '../settings/settings-modal';
import HelpModel from '../chat/help-model/help-model';

interface AdminDashboardProps {
  userEmail: string;
  onLogout: () => void;
}

const AdminDashboard: React.FC<AdminDashboardProps> = ({ userEmail, onLogout }) => {
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

      <div className="dashboard-content" style={{ backgroundColor: '#f5f7fb' }}>
        <UsersTable />

        {showSettings && (
          <SettingsModal onClose={() => setShowSettings(false)} />
        )}

        {showHelp && (
          <HelpModel onClose={() => setShowHelp(false)} />
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
