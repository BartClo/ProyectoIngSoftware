import React, { useState } from 'react';
import '../dashboard/dashboard.css';
import DashboardHeader from '../dashboard/dashboard-header';
import UsersTable from './users-table';
import ReportsTable from './reports-table';
import CreateConversation from './create-conversation';
import SettingsModal from '../settings/settings-modal';
import AdminHelpModel from './help-model/help-model';
import { AdminDataProvider, useAdminData } from './admin-data-context';

interface AdminDashboardProps {
  userEmail: string;
  onLogout: () => void;
}

const AdminDashboard: React.FC<AdminDashboardProps> = ({ userEmail, onLogout }) => {
  const [showSettings, setShowSettings] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [view, setView] = useState<'users' | 'reports' | 'create-conv'>('users');

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
        showAdminActions
        activeAdminView={view}
        onUsersAdminClick={() => setView('users')}
        onReportsClick={() => setView('reports')}
        onCreateConversationClick={() => setView('create-conv')}
      />

      <AdminDataProvider>
        <div className="dashboard-content" style={{ backgroundColor: '#f5f7fb' }}>
          <AdminInner view={view} />
          
          {showSettings && (
            <SettingsModal onClose={() => setShowSettings(false)} />
          )}

          {showHelp && (
            <AdminHelpModel onClose={() => setShowHelp(false)} />
          )}
        </div>
      </AdminDataProvider>
    </div>
  );
};

export default AdminDashboard;

// Componente interno para consumir el contexto y refrescar usuarios cuando se muestra la vista 'users'
const AdminInner: React.FC<{ view: 'users' | 'reports' | 'create-conv' }> = ({ view }) => {
  const { refreshUsers } = useAdminData();
  React.useEffect(() => {
    if (view === 'users') {
      refreshUsers().catch(() => {});
    }
  }, [view, refreshUsers]);

  return (
    <>
      {view === 'users' && <UsersTable />}
      {view === 'reports' && <ReportsTable />}
      {view === 'create-conv' && <CreateConversation />}
    </>
  );
};
