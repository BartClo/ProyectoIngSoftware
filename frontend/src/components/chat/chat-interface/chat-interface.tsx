import React, { useState, useEffect, useRef } from 'react';
import ChatSidebar from '../chat-sidebar/chat-sidebar';
import ChatNoConversation from '../chat-no-conversation/chat-no-conversation';
import './chat-interface.css';

// Interfaces
interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

interface ChatConversation {
  id: string;
  title: string;
  createdAt: Date;
  messages: ChatMessage[];
}

const ChatInterface: React.FC = () => {
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Record<string, ChatConversation>>({});
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Al montar, cargar conversaciones del localStorage
  useEffect(() => {
    const savedConversations = localStorage.getItem('chatConversations');
    
    if (savedConversations) {
      try {
        const parsed = JSON.parse(savedConversations);
        
        // Convertir strings de fecha a objetos Date
        const parsedWithDates: Record<string, ChatConversation> = {};
        
        Object.entries(parsed).forEach(([id, conv]: [string, any]) => {
          parsedWithDates[id] = {
            ...conv,
            createdAt: new Date(conv.createdAt),
            messages: conv.messages.map((msg: any) => ({
              ...msg,
              timestamp: new Date(msg.timestamp)
            }))
          };
        });
        
        setConversations(parsedWithDates);
        
        // Si hay conversaciones cargadas, seleccionar la primera
        const conversationIds = Object.keys(parsedWithDates);
        if (conversationIds.length > 0) {
          // Intentar recuperar la última conversación activa
          const lastActiveId = localStorage.getItem('activeConversationId');
          if (lastActiveId && parsedWithDates[lastActiveId]) {
            setActiveConversationId(lastActiveId);
          } else {
            // Si no existe, usar la primera
            setActiveConversationId(conversationIds[0]);
          }
        }
      } catch (error) {
        console.error('Error parsing saved conversations:', error);
        localStorage.removeItem('chatConversations');
      }
    }
  }, []);
  
  // Guardar conversaciones en localStorage cuando cambien
  useEffect(() => {
    if (Object.keys(conversations).length > 0) {
      localStorage.setItem('chatConversations', JSON.stringify(conversations));
    } else {
      localStorage.removeItem('chatConversations');
      localStorage.removeItem('activeConversationId');
    }
  }, [conversations]);
  
  // Guardar ID de conversación activa
  useEffect(() => {
    if (activeConversationId) {
      localStorage.setItem('activeConversationId', activeConversationId);
    } else {
      localStorage.removeItem('activeConversationId');
    }
  }, [activeConversationId]);
  
  // Manejar la selección de una conversación
  const handleSelectConversation = (conversationId: string) => {
    setActiveConversationId(conversationId);
  };
  
  // Crear una nueva conversación
  const handleNewConversation = () => {
    console.log("Creando nueva conversación");
    
    // Generar un ID único para la nueva conversación
    const newConversationId = `conv_${Date.now()}`;
    
    // Mensaje de bienvenida del asistente
    const welcomeMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      text: "¡Hola! Soy tu asistente de IA USS. ¿Cómo puedo ayudarte hoy?",
      sender: 'ai',
      timestamp: new Date()
    };
    
    // Crear la nueva conversación con el mensaje de bienvenida
    const newConversation: ChatConversation = {
      id: newConversationId,
      title: `Nueva conversación`,
      createdAt: new Date(),
      messages: [welcomeMessage] // Incluimos el mensaje de bienvenida
    };
    
    // Actualizar el estado para añadir la nueva conversación
    const updatedConversations = {
      [newConversationId]: newConversation,
      ...conversations
    };
    
    console.log("Conversaciones actualizadas:", updatedConversations);
    setConversations(updatedConversations);
    
    // Establecer la nueva conversación como activa
    setActiveConversationId(newConversationId);
    console.log("Nueva conversación activa:", newConversationId);
  };
  
  // Eliminar conversación
  const handleDeleteConversation = (conversationId: string) => {
    setConversations(prevConversations => {
      const { [conversationId]: deleted, ...remaining } = prevConversations;
      
      // Si eliminamos la conversación activa, seleccionar otra si hay disponibles
      if (conversationId === activeConversationId) {
        const remainingIds = Object.keys(remaining);
        if (remainingIds.length > 0) {
          setActiveConversationId(remainingIds[0]);
        } else {
          setActiveConversationId(null);  // No hay más conversaciones
        }
      }
      
      return remaining;
    });
  };
  
  // Renombrar conversación
  const handleRenameConversation = (conversationId: string, newTitle: string) => {
    setConversations(prevConversations => ({
      ...prevConversations,
      [conversationId]: {
        ...prevConversations[conversationId],
        title: newTitle
      }
    }));
  };
  
  // Enviar un mensaje
  const handleSendMessage = () => {
    if (!inputValue.trim() || !activeConversationId) return;
    
    const newMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      text: inputValue,
      sender: 'user',
      timestamp: new Date()
    };
    
    // Actualizar la conversación activa con el nuevo mensaje
    const updatedConversations = { ...conversations };
    const updatedConversation = { 
      ...updatedConversations[activeConversationId],
      messages: [
        ...updatedConversations[activeConversationId].messages,
        newMessage
      ]
    };
    
    // Eliminar la conversación actual para reordenarla
    delete updatedConversations[activeConversationId];
    
    // Añadir la conversación actualizada al principio
    setConversations({
      [activeConversationId]: updatedConversation,
      ...updatedConversations
    });
    
    // Limpiar el input
    setInputValue('');
    
    // Simular respuesta del asistente
    setTimeout(() => {
      const aiResponse: ChatMessage = {
        id: `msg_${Date.now()}`,
        text: `Esta es una respuesta de ejemplo a: "${newMessage.text}"`,
        sender: 'ai',
        timestamp: new Date()
      };
      
      setConversations(prevState => {
        const updatedConversation = {
          ...prevState[activeConversationId],
          messages: [
            ...prevState[activeConversationId].messages,
            aiResponse
          ]
        };
        
        // Eliminar la conversación actual para reordenarla
        const { [activeConversationId]: _, ...restConversations } = prevState;
        
        // Añadir la conversación actualizada al principio
        return {
          [activeConversationId]: updatedConversation,
          ...restConversations
        };
      });
    }, 1000);
  };
  
  // Ordenar las conversaciones para el sidebar
  const sortedConversations = Object.values(conversations);
  
  // Verificar si hay conversaciones
  const hasConversations = sortedConversations.length > 0;
  
  // Para depuración - mostrar en consola cada vez que el estado cambia
  useEffect(() => {
    console.log("Estado actualizado:");
    console.log("Conversaciones:", conversations);
    console.log("Conversación activa:", activeConversationId);
    console.log("¿Hay conversaciones?", hasConversations);
  }, [conversations, activeConversationId, hasConversations]);
  
  // Función para hacer autoscroll al final de los mensajes
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  // Hacer autoscroll cuando cambian los mensajes
  useEffect(() => {
    if (activeConversationId && conversations[activeConversationId]) {
      scrollToBottom();
    }
  }, [conversations, activeConversationId]);
  
  return (
    <div className="chat-interface">
      <div className="chat-sidebar-container open">
        <ChatSidebar 
          conversations={sortedConversations}
          activeConversationId={activeConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onDeleteConversation={handleDeleteConversation}
          onRenameConversation={handleRenameConversation}
        />
      </div>
      
      <div className="chat-main-container">
        {hasConversations && activeConversationId ? (
          // Si hay conversaciones y una está activa, mostrar el chat
          <div className="chat-content">
            <div className="chat-header">
              <h2>{conversations[activeConversationId]?.title || 'Chat'}</h2>
            </div>
            
            <div className="messages-container">
              {conversations[activeConversationId]?.messages.map(message => (
                <div 
                  key={message.id} 
                  className={`message ${message.sender === 'user' ? 'user-message' : 'ai-message'}`}
                >
                  <div className="message-content">{message.text}</div>
                  <div className="message-timestamp">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              ))}
              {/* Espacio adicional para asegurar que los mensajes se vean bien al hacer scroll */}
              <div style={{ paddingBottom: "20px" }} ref={messagesEndRef}></div>
            </div>
            
            <div className="message-input-container">
              <input
                type="text"
                value={inputValue}
                onChange={e => setInputValue(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
                placeholder="Escribe un mensaje..."
                className="message-input"
              />
              <button 
                onClick={handleSendMessage} 
                className="send-button"
                disabled={!inputValue.trim()}
              >
                Enviar
              </button>
            </div>
          </div>
        ) : (
          // Si no hay conversaciones o ninguna está activa, mostrar el componente sin conversaciones
          <ChatNoConversation onNewConversation={handleNewConversation} />
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
