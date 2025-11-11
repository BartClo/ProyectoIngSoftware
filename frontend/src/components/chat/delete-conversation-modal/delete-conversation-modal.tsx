import React, { useState } from 'react';
import './delete-conversation-modal.css';

interface DeleteConversationModalProps {
  conversationTitle: string;
  onConfirm: () => void;
  onCancel: () => void;
}

const DeleteConversationModal: React.FC<DeleteConversationModalProps> = ({
  conversationTitle,
  onConfirm,
  onCancel
}) => {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleConfirm = async () => {
    setIsDeleting(true);
    try {
      await onConfirm();
    } catch (error) {
      console.error('Error al eliminar:', error);
      setIsDeleting(false);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !isDeleting) {
      onCancel();
    }
  };

  return (
    <div 
      className="delete-conversation-modal-overlay" 
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-modal-title"
    >
      <div className="delete-conversation-modal">
        <div className="modal-header">
          <div className="modal-icon-warning">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
              <path 
                d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <h2 id="delete-modal-title">Confirmar eliminación</h2>
          <button
            className="modal-close-button"
            onClick={onCancel}
            disabled={isDeleting}
            aria-label="Cerrar modal"
          >
            ✕
          </button>
        </div>

        <div className="modal-body">
          <p className="modal-warning-text">
            ¿Está seguro de que desea eliminar esta conversación?
          </p>
          <div className="modal-conversation-info">
            <span className="conversation-label">Conversación:</span>
            <span className="conversation-name">"{conversationTitle}"</span>
          </div>
          <div className="modal-alert">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path 
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
                stroke="currentColor" 
                strokeWidth="2" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
            </svg>
            <span>Esta acción no se puede deshacer. Todos los mensajes de esta conversación se perderán permanentemente.</span>
          </div>
        </div>

        <div className="modal-footer">
          <button
            className="modal-button button-cancel"
            onClick={onCancel}
            disabled={isDeleting}
          >
            Cancelar
          </button>
          <button
            className="modal-button button-delete"
            onClick={handleConfirm}
            disabled={isDeleting}
          >
            {isDeleting ? (
              <>
                <span className="spinner"></span>
                Eliminando...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path 
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round"
                  />
                </svg>
                Eliminar conversación
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteConversationModal;
