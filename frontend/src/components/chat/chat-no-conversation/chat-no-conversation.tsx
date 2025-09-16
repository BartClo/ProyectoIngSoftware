import React from 'react';
import './chat-no-conversation.css';
// Importar la imagen del robot
import RobotIcon from '../../../assets/chat/Robot.svg';

interface ChatNoConversationProps {
  onNewConversation: () => void;
}

const ChatNoConversation: React.FC<ChatNoConversationProps> = ({ onNewConversation }) => {
  return (
    <div className="chat-no-conversation">
      <div className="no-conversation-content">
        <div className="no-conversation-icon">
          {/* Usar la imagen del robot en lugar del SVG */}
          <img src={RobotIcon} alt="Robot asistente" width="80" height="80" />
        </div>
        <h2>No hay conversaciones activas</h2>
        <p>Para comenzar a chatear con el asistente de IA, crea una nueva conversación.</p>
        <button 
          className="start-conversation-button" 
          onClick={onNewConversation}
        >
          Iniciar conversación
        </button>
      </div>
    </div>
  );
};

export default ChatNoConversation;
