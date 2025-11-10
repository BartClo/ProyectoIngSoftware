import React, { useState, useEffect, useRef, useMemo } from 'react';
import './chat-interface.css';
import ChatSidebar from '../chat-sidebar/chat-sidebar';
import ChatNoConversation from '../chat-no-conversation/chat-no-conversation';
import { listConversations, sendMessage, createConversation, listUserChatbots } from '../../../lib/api';
import type { ChatbotInfo, ChatResponseDTO } from '../../../lib/api';

interface ChatMessage {
  id: number;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  sources?: string[];
}

interface ChatConversation {
  id: string; // Cambiado a string para compatibilidad con sidebar
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messages: ChatMessage[];
  chatbotId?: number; // ID del chatbot asociado
  chatbotName?: string; // Nombre del chatbot asociado
}

interface ChatInterfaceProps {
  userEmail: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ userEmail: _userEmail }) => {
  // Estados principales
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messagesByConv, setMessagesByConv] = useState<Record<string, ChatMessage[]>>({});
  const [inputValue, setInputValue] = useState('');
  const [sending, setSending] = useState(false);
  
  // Estados para chatbots
  const [availableChatbots, setAvailableChatbots] = useState<ChatbotInfo[]>([]);
  const [selectedChatbot, setSelectedChatbot] = useState<ChatbotInfo | null>(null);
  
  // Estado para modal de selección de chatbot
  const [showChatbotSelector, setShowChatbotSelector] = useState(false);
  
  // Ref para autoscroll
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Cargar conversaciones y chatbots al montar
  useEffect(() => {
    const loadData = async () => {
      await loadChatbots();
      await loadConversations();
    };
    loadData();
  }, []);

  // Cuando cambian los chatbots disponibles, revaluar la conversación activa
  useEffect(() => {
    if (activeConversationId && availableChatbots.length > 0) {
      const activeConv = conversations.find(c => c.id === activeConversationId);
      if (activeConv && activeConv.chatbotId) {
        const associatedChatbot = availableChatbots.find(c => c.id === activeConv.chatbotId);
        if (associatedChatbot) {
          setSelectedChatbot(associatedChatbot);
        }
      }
    }
  }, [availableChatbots, activeConversationId, conversations]);

  // Cargar conversaciones desde el backend
  const loadConversations = async () => {
    try {
      const convs = await listConversations();
      const conversationsWithMessages: ChatConversation[] = convs.map((conv: any) => ({
        id: String(conv.id), // Convertir a string
        title: conv.title,
        createdAt: new Date(conv.created_at),
        updatedAt: new Date(conv.updated_at || conv.created_at),
        messages: [],
        chatbotId: conv.chatbot_id,
        chatbotName: conv.chatbot_name
      }));
      
      setConversations(conversationsWithMessages);
      
      // Seleccionar la primera conversación si existe
      if (conversationsWithMessages.length > 0) {
        setActiveConversationId(conversationsWithMessages[0].id);
        // Si la conversación tiene un chatbot asociado, seleccionarlo
        if (conversationsWithMessages[0].chatbotId) {
          const associatedChatbot = availableChatbots.find(c => c.id === conversationsWithMessages[0].chatbotId);
          if (associatedChatbot) {
            setSelectedChatbot(associatedChatbot);
          }
        }
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  };

  // Cargar chatbots disponibles
  const loadChatbots = async () => {
    try {
      const chatbots = await listUserChatbots();
      setAvailableChatbots(Array.isArray(chatbots) ? chatbots : []);
    } catch (error) {
      console.error('Error loading chatbots:', error);
    }
  };

  // Manejar selección de conversación
  const handleSelectConversation = (conversationId: string) => {
    setActiveConversationId(conversationId);
    
    // Buscar la conversación seleccionada y su chatbot asociado
    const selectedConversation = conversations.find(c => c.id === conversationId);
    if (selectedConversation && selectedConversation.chatbotId) {
      const associatedChatbot = availableChatbots.find(c => c.id === selectedConversation.chatbotId);
      if (associatedChatbot) {
        setSelectedChatbot(associatedChatbot);
      }
    } else {
      // Si no hay chatbot asociado, limpiar selección
      setSelectedChatbot(null);
    }
  };

  // Crear nueva conversación con chatbot específico
  const handleNewConversation = () => {
    if (availableChatbots.length === 0) {
      alert('No tienes acceso a ningún chatbot. Contacta al administrador.');
      return;
    }
    
    if (availableChatbots.length === 1) {
      // Si solo hay un chatbot disponible, crearlo directamente
      createConversationWithChatbot(availableChatbots[0]);
    } else {
      // Si hay múltiples chatbots, mostrar selector
      setShowChatbotSelector(true);
    }
  };

  // Crear conversación con chatbot específico
  const createConversationWithChatbot = async (chatbot: ChatbotInfo) => {
    try {
      const newConv = await createConversation({ 
        title: `Chat con ${chatbot.title}`,
        chatbot_id: chatbot.id 
      });
      const conversation: ChatConversation = {
        id: String(newConv.id),
        title: newConv.title,
        createdAt: new Date(newConv.created_at),
        updatedAt: new Date(newConv.updated_at || newConv.created_at),
        messages: [],
        chatbotId: chatbot.id,
        chatbotName: chatbot.title
      };
      
      setConversations(prev => [conversation, ...prev]);
      setActiveConversationId(conversation.id);
      setSelectedChatbot(chatbot);
      setShowChatbotSelector(false);
    } catch (error) {
      console.error('Error creating conversation:', error);
      alert('No se pudo crear la conversación');
    }
  };

  // FUNCIONES DE ELIMINAR Y RENOMBRAR REMOVIDAS
  // Los usuarios/docentes NO pueden eliminar ni renombrar conversaciones
  // Solo los administradores tienen estos permisos

  // Enviar mensaje
  const handleSendMessage = async () => {
    if (!inputValue.trim() || !activeConversationId) return;
    
    const text = inputValue;
    const convId = activeConversationId;

    // Mensaje del usuario (optimista)
    const userMsg: ChatMessage = {
      id: Date.now(),
      text,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessagesByConv(prev => ({
      ...prev,
      [convId]: [...(prev[convId] || []), userMsg],
    }));
    setInputValue('');
    setSending(true);

    try {
      const resp: ChatResponseDTO = await sendMessage(Number(convId), text, selectedChatbot?.id);
      const aiMsg: ChatMessage = {
        id: Date.now() + 1,
        text: resp.response || 'No pude generar una respuesta',
        sender: 'ai',
        timestamp: new Date(),
        sources: resp.sources || [],
      };
      
      setMessagesByConv(prev => ({
        ...prev,
        [convId]: [...(prev[convId] || []), aiMsg],
      }));

      // Reordenar conversación al tope
      setConversations(prev => {
        const updated = prev.map(c => (c.id === convId ? { ...c, updatedAt: new Date() } : c));
        return updated.sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
      });
    } catch (error) {
      console.error('Error sending message:', error);
      const errMsg: ChatMessage = {
        id: Date.now() + 1,
        text: 'Error al obtener respuesta del asistente.',
        sender: 'ai',
        timestamp: new Date(),
      };
      setMessagesByConv(prev => ({
        ...prev,
        [convId]: [...(prev[convId] || []), errMsg],
      }));
    } finally {
      setSending(false);
    }
  };

  // Manejar Enter para enviar mensaje
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Ordenar conversaciones por fecha de actualización
  const sortedConversations: ChatConversation[] = useMemo(() => {
    return [...conversations].sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
  }, [conversations]);

  const hasConversations = sortedConversations.length > 0;
  const activeMessages: ChatMessage[] = activeConversationId ? (messagesByConv[activeConversationId] || []) : [];

  // Autoscroll al final cuando cambian los mensajes
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    if (activeConversationId) scrollToBottom();
  }, [activeMessages]);

  return (
    <div className="chat-interface">
      {/* Sidebar - Vista de USUARIO (sin funciones de editar/eliminar) */}
      <ChatSidebar
        conversations={sortedConversations}
        activeConversationId={activeConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        isAdminView={false} // Usuario/Docente NO puede eliminar ni renombrar
        // onDeleteConversation y onRenameConversation NO se pasan
      />

      {/* Área principal */}
      <div className="chat-main">
        {/* Header con selección de chatbot */}
        <div className="chat-header">
          <div className="chatbot-selector">
            <label htmlFor="chatbot-select">Chatbot: </label>
            <select
              id="chatbot-select"
              value={selectedChatbot?.id || ''}
              onChange={(e) => {
                const chatbotId = Number(e.target.value);
                const chatbot = availableChatbots.find(c => c.id === chatbotId);
                setSelectedChatbot(chatbot || null);
              }}
              disabled={!activeConversationId || Boolean(conversations.find(c => c.id === activeConversationId)?.chatbotId)}
            >
              <option value="">Sin chatbot específico</option>
              {availableChatbots.map(chatbot => (
                <option key={chatbot.id} value={chatbot.id}>
                  {chatbot.title} {chatbot.is_owner ? '(Tuyo)' : ''}
                </option>
              ))}
            </select>
          </div>
          {selectedChatbot && (
            <div className="chatbot-info">
              <span className="chatbot-description">
                {selectedChatbot.description}
                {conversations.find(c => c.id === activeConversationId)?.chatbotId && (
                  <em> (Chatbot predefinido para esta conversación)</em>
                )}
              </span>
            </div>
          )}
        </div>

        {/* Área de conversación */}
        {!hasConversations ? (
          <ChatNoConversation onNewConversation={handleNewConversation} />
        ) : (
          <div className="conversation-area">
            {/* Mensajes */}
            <div className="messages-container">
              {activeConversationId ? (
                activeMessages.map((msg) => (
                  <div key={msg.id} className={`message ${msg.sender}`}>
                    <div className="message-content">
                      <div className="message-text">{msg.text}</div>
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="message-sources">
                          <strong>Fuentes:</strong> {msg.sources.join(', ')}
                        </div>
                      )}
                      <div className="message-timestamp">
                        {msg.timestamp.toLocaleTimeString('es-CL', { 
                          hour: '2-digit', 
                          minute: '2-digit',
                          hour12: false 
                        })}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-active-conversation">
                  <p>Selecciona una conversación para comenzar a chatear</p>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input - solo mostrar si hay conversación activa */}
            {activeConversationId && (
              <div className="input-container">
                <div className="input-wrapper">
                  <textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder={selectedChatbot ? `Pregunta a ${selectedChatbot.title}...` : "Escribe tu mensaje..."}
                    rows={1}
                    disabled={sending}
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputValue.trim() || sending}
                    className="send-button"
                  >
                    {sending ? 'Procesando...' : 'Enviar'}
                  </button>
                </div>
                {selectedChatbot && (
                  <div className="selected-chatbot-indicator">
                    Usando: {selectedChatbot.title}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal de selección de chatbot */}
      {showChatbotSelector && (
        <div className="chatbot-selector-modal">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Selecciona un Chatbot</h3>
              <button 
                className="close-button"
                onClick={() => setShowChatbotSelector(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <p>Elige el chatbot con el que quieres iniciar una conversación:</p>
              <div className="chatbots-grid">
                {availableChatbots.map(chatbot => (
                  <div 
                    key={chatbot.id}
                    className="chatbot-card"
                    onClick={() => createConversationWithChatbot(chatbot)}
                  >
                    <div className="chatbot-card-header">
                      <h4>{chatbot.title}</h4>
                      {chatbot.is_owner && (
                        <span className="owner-badge">Tuyo</span>
                      )}
                    </div>
                    <p className="chatbot-description">
                      {chatbot.description || 'Sin descripción disponible'}
                    </p>
                    <div className="chatbot-info">
                      <span className="document-count">
                        📄 Chatbot disponible
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div 
            className="modal-backdrop"
            onClick={() => setShowChatbotSelector(false)}
          />
        </div>
      )}
    </div>
  );
};

export default ChatInterface;