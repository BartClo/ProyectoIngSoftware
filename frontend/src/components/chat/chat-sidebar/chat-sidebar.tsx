import React, { useState } from 'react';
import './chat-sidebar.css';
import ReportModal from '../reporte-model/report-modal';

interface ChatConversation {
  id: string;
  title: string;
  createdAt: Date;
  messages: any[];
}

interface ChatSidebarProps {
  conversations: ChatConversation[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
  onRenameConversation: (id: string, newTitle: string) => void;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onRenameConversation
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [showConfirmDelete, setShowConfirmDelete] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showReportModal, setShowReportModal] = useState<string | null>(null);
  
  const handleStartEdit = (conversation: ChatConversation) => {
    setEditingId(conversation.id);
    setEditTitle(conversation.title);
  };
  
  const handleSaveEdit = () => {
    if (editingId && editTitle.trim()) {
      onRenameConversation(editingId, editTitle.trim());
      setEditingId(null);
    }
  };
  
  const handleCancelEdit = () => {
    setEditingId(null);
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSaveEdit();
    } else if (e.key === 'Escape') {
      handleCancelEdit();
    }
  };
  
  const handleClickDelete = (id: string) => {
    setShowConfirmDelete(id);
  };
  
  const handleConfirmDelete = (id: string) => {
    onDeleteConversation(id);
    setShowConfirmDelete(null);
  };
  
  const handleCancelDelete = () => {
    setShowConfirmDelete(null);
  };
  
  const handleReportClick = (conversationId: string) => {
    setShowReportModal(conversationId);
  };
  
  const handleReportClose = () => {
    setShowReportModal(null);
  };
  
  const handleReportSubmit = (reportData: any) => {
    console.log('Reporte enviado:', reportData);
    // Aquí puedes implementar la lógica para enviar el reporte al backend
    alert('Reporte enviado correctamente');
    setShowReportModal(null);
  };
  
  const formatDate = (date: Date) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const messageDate = new Date(date);
    messageDate.setHours(0, 0, 0, 0);
    
    if (messageDate.getTime() === today.getTime()) {
      return 'Hoy';
    }
    
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (messageDate.getTime() === yesterday.getTime()) {
      return 'Ayer';
    }
    
    return date.toLocaleDateString();
  };
  
  return (
    <div className="chat-sidebar">
      <div className="sidebar-header">
        <h2>Conversaciones</h2>
        <button 
          className="new-conversation-button" 
          onClick={onNewConversation}
        >
          <span className="icon">💬</span> Nueva conversación
        </button>
      </div>
      
      <div className="search-container">
        <input
          type="text"
          placeholder="Buscar conversaciones..."
          className="search-input"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>
      
      <div className="conversations-list">
        {conversations.length === 0 ? (
          <div className="no-conversations-message">
            No se encontraron conversaciones
          </div>
        ) : (
          // Filtramos las conversaciones según el término de búsqueda
          conversations.filter(conv => 
            searchTerm === '' || conv.title.toLowerCase().includes(searchTerm.toLowerCase())
          ).map(conversation => {
            const isActive = activeConversationId === conversation.id;
            
            return (
              <div 
                key={conversation.id}
                className={`conversation-item ${isActive ? 'active' : ''}`}
                onClick={() => onSelectConversation(conversation.id)}
                title={conversation.title}
              >
                {editingId === conversation.id ? (
                  <div className="edit-conversation-container" onClick={(e) => e.stopPropagation()}>

                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={handleKeyDown}
                      autoFocus
                      className="edit-conversation-input"
                      placeholder="Nuevo nombre..."
                    />
                    <div className="confirm-buttons">
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSaveEdit();
                        }}
                        className="confirm-delete"
                        title="Guardar"
                      >
                        Sí
                      </button>
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCancelEdit();
                        }}
                        className="cancel-delete"
                        title="Cancelar"
                      >
                        No
                      </button>
                    </div>
                  </div>
                ) : showConfirmDelete === conversation.id ? (
                  <div className="delete-confirm-container" onClick={(e) => e.stopPropagation()}>
                    <p>¿Eliminar esta conversación?</p>
                    <div className="confirm-buttons">
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleConfirmDelete(conversation.id);
                        }}
                        className="confirm-delete"
                      >
                        Sí
                      </button>
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCancelDelete();
                        }}
                        className="cancel-delete"
                      >
                        No
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="conversation-info">
                      <div className="conversation-icon">
                        💬
                      </div>
                      <div className="conversation-details">
                        <div className="conversation-title">{conversation.title}</div>
                        <div className="conversation-date">
                          {formatDate(conversation.createdAt)}
                        </div>
                      </div>
                    </div>
                    
                    <div className="conversation-actions">
                      <button
                        className="action-button more-options"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleReportClick(conversation.id);
                        }}
                        title="Reportar problema"
                      >
                        ⋮
                      </button>
                      <button
                        className="action-button edit"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStartEdit(conversation);
                        }}
                        title="Renombrar"
                      >
                        ✎
                      </button>
                      <button
                        className="action-button delete"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleClickDelete(conversation.id);
                        }}
                        title="Eliminar"
                      >
                        🗑️
                      </button>
                    </div>
                  </>
                )}
              </div>
            );
          })
        )}
        {searchTerm && conversations.filter(conv => 
          conv.title.toLowerCase().includes(searchTerm.toLowerCase())
        ).length === 0 && (
          <div className="no-conversations-message">
            No se encontraron resultados para "{searchTerm}"
          </div>
        )}
      </div>
      
      {showReportModal && (
        <ReportModal
          conversationId={showReportModal}
          conversationTitle={conversations.find(conv => conv.id === showReportModal)?.title || 'Conversación'}
          onClose={handleReportClose}
          onSubmit={handleReportSubmit}
        />
      )}
    </div>
  );
};

export default ChatSidebar;
