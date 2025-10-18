import React, { useState, useEffect } from 'react';
import { listUserChatbots } from '../../../lib/api';
import './chatbot-selector.css';

interface Chatbot {
  id: number;
  name: string;
  description: string;
  created_at: string;
}

interface ChatbotSelectorProps {
  selectedChatbotId: number | null;
  onSelectChatbot: (chatbotId: number | null) => void;
}

const ChatbotSelector: React.FC<ChatbotSelectorProps> = ({ selectedChatbotId, onSelectChatbot }) => {
  const [chatbots, setChatbots] = useState<Chatbot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchChatbots = async () => {
      try {
        setLoading(true);
        const userChatbots = await listUserChatbots();
        setChatbots(userChatbots);
        setError(null);
      } catch (err) {
        console.error('Error fetching user chatbots:', err);
        setError('Error al cargar los chatbots disponibles');
      } finally {
        setLoading(false);
      }
    };

    fetchChatbots();
  }, []);

  if (loading) {
    return (
      <div className="chatbot-selector">
        <div className="chatbot-selector-header">
          <h3>Seleccionar Chatbot</h3>
        </div>
        <div className="chatbot-loading">
          <div className="spinner"></div>
          <span>Cargando chatbots...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="chatbot-selector">
        <div className="chatbot-selector-header">
          <h3>Seleccionar Chatbot</h3>
        </div>
        <div className="chatbot-error">
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (chatbots.length === 0) {
    return (
      <div className="chatbot-selector">
        <div className="chatbot-selector-header">
          <h3>Chatbots Disponibles</h3>
        </div>
        <div className="chatbot-empty">
          <p>No tienes acceso a ningún chatbot personalizado.</p>
          <p>Puedes usar el chatbot general seleccionando "Chatbot General".</p>
        </div>
        <div className="chatbot-list">
          <div 
            className={`chatbot-item ${selectedChatbotId === null ? 'selected' : ''}`}
            onClick={() => onSelectChatbot(null)}
          >
            <div className="chatbot-icon general">🤖</div>
            <div className="chatbot-info">
              <h4>Chatbot General</h4>
              <p>Asistente de IA general sin contexto especializado</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="chatbot-selector">
      <div className="chatbot-selector-header">
        <h3>Seleccionar Chatbot</h3>
        <span className="chatbot-count">{chatbots.length} disponibles</span>
      </div>
      
      <div className="chatbot-list">
        {/* Opción de chatbot general */}
        <div 
          className={`chatbot-item ${selectedChatbotId === null ? 'selected' : ''}`}
          onClick={() => onSelectChatbot(null)}
        >
          <div className="chatbot-icon general">🤖</div>
          <div className="chatbot-info">
            <h4>Chatbot General</h4>
            <p>Asistente de IA general sin contexto especializado</p>
          </div>
          {selectedChatbotId === null && <div className="selection-indicator">✓</div>}
        </div>

        {/* Chatbots personalizados */}
        {chatbots.map((chatbot) => (
          <div 
            key={chatbot.id}
            className={`chatbot-item ${selectedChatbotId === chatbot.id ? 'selected' : ''}`}
            onClick={() => onSelectChatbot(chatbot.id)}
          >
            <div className="chatbot-icon custom">📚</div>
            <div className="chatbot-info">
              <h4>{chatbot.name}</h4>
              <p>{chatbot.description}</p>
              <div className="chatbot-meta">
                Creado: {new Date(chatbot.created_at).toLocaleDateString()}
              </div>
            </div>
            {selectedChatbotId === chatbot.id && <div className="selection-indicator">✓</div>}
          </div>
        ))}
      </div>

      {selectedChatbotId && (
        <div className="selected-chatbot-info">
          <p>
            <strong>Chatbot seleccionado:</strong> {' '}
            {chatbots.find(c => c.id === selectedChatbotId)?.name || 'Chatbot General'}
          </p>
        </div>
      )}
    </div>
  );
};

export default ChatbotSelector;