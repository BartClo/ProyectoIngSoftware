import React, { useEffect, useMemo, useRef, useState } from 'react';
import ChatSidebar from '../chat-sidebar/chat-sidebar';
import ChatNoConversation from '../chat-no-conversation/chat-no-conversation';
import './chat-interface.css';

import {
  listConversations,
  createConversation as apiCreateConversation,
  renameConversation as apiRenameConversation,
  deleteConversation as apiDeleteConversation,
  listMessages as apiListMessages,
  sendMessage as apiSendMessage,
  ConversationDTO,
  MessageDTO,
} from '../../../lib/api';

// Tipos locales
interface ChatMessage {
  id: number; // id real o temporal negativo
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

interface ChatConversation {
  id: number;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messages: any[]; // no se usa en Sidebar, solo para compatibilidad de tipos
}

function mapConversation(dto: ConversationDTO): ChatConversation {
  return {
    id: dto.id,
    title: dto.title,
    createdAt: new Date(dto.created_at),
    updatedAt: new Date(dto.updated_at),
    messages: [],
  };
}

function mapMessage(dto: MessageDTO): ChatMessage {
  return {
    id: dto.id,
    text: dto.text,
    sender: dto.sender,
    timestamp: new Date(dto.created_at),
  };
}

const ChatInterface: React.FC = () => {
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [messagesByConv, setMessagesByConv] = useState<Record<number, ChatMessage[]>>({});
  const [inputValue, setInputValue] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Cargar conversaciones del backend en el montaje
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const dtos = await listConversations();
        if (!mounted) return;
        const convs = dtos.map(mapConversation);
        setConversations(convs);
        if (convs.length > 0) {
          setActiveConversationId(convs[0].id);
        }
      } catch (e) {
        console.error('Error listando conversaciones', e);
      }
    })();
    return () => { mounted = false; };
  }, []);

  // Cargar mensajes al seleccionar una conversación (si no están ya en memoria)
  useEffect(() => {
    if (!activeConversationId) return;
    if (messagesByConv[activeConversationId]) return;

    let mounted = true;
    (async () => {
      try {
        const msgs = await apiListMessages(activeConversationId);
        if (!mounted) return;
        setMessagesByConv(prev => ({ ...prev, [activeConversationId]: msgs.map(mapMessage) }));
      } catch (e) {
        console.error('Error listando mensajes', e);
        setMessagesByConv(prev => ({ ...prev, [activeConversationId]: [] }));
      }
    })();

    return () => { mounted = false; };
  }, [activeConversationId]);

  const handleSelectConversation = (conversationId: number) => {
    setActiveConversationId(conversationId);
  };

  const handleNewConversation = async () => {
    try {
      const dto = await apiCreateConversation({ with_welcome: true });
      const conv = mapConversation(dto);
      setConversations(prev => [conv, ...prev]);
      setActiveConversationId(conv.id);
      // cargar mensajes (incluye bienvenida si with_welcome=true)
      const msgs = await apiListMessages(conv.id);
      setMessagesByConv(prev => ({ ...prev, [conv.id]: msgs.map(mapMessage) }));
    } catch (e) {
      console.error('Error creando conversación', e);
      alert('No se pudo crear la conversación');
    }
  };

  const handleDeleteConversation = async (conversationId: number) => {
    try {
      await apiDeleteConversation(conversationId);
      setConversations(prev => prev.filter(c => c.id !== conversationId));
      setMessagesByConv(prev => {
        const copy = { ...prev };
        delete copy[conversationId];
        return copy;
      });
      if (activeConversationId === conversationId) {
        const remaining = conversations.filter(c => c.id !== conversationId);
        setActiveConversationId(remaining.length > 0 ? remaining[0].id : null);
      }
    } catch (e) {
      console.error('Error eliminando conversación', e);
      alert('No se pudo eliminar la conversación');
    }
  };

  const handleRenameConversation = async (conversationId: number, newTitle: string) => {
    try {
      const dto = await apiRenameConversation(conversationId, newTitle);
      setConversations(prev => prev.map(c => (c.id === conversationId ? { ...c, title: dto.title, updatedAt: new Date(dto.updated_at) } : c)));
    } catch (e) {
      console.error('Error renombrando conversación', e);
      alert('No se pudo renombrar la conversación');
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !activeConversationId) return;
    const text = inputValue;
    const convId = activeConversationId;

    // Mensaje del usuario (optimista)
    const userMsg: ChatMessage = {
      id: -Date.now(), // id temporal negativo
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
      const resp = await apiSendMessage(convId, text);
      const aiMsg: ChatMessage = {
        id: Date.now(),
        text: resp.response || 'No lo sé con la información disponible',
        sender: 'ai',
        timestamp: new Date(),
      };
      setMessagesByConv(prev => ({
        ...prev,
        [convId]: [...(prev[convId] || []), aiMsg],
      }));

      // Reordenar conversación al tope (updatedAt ahora)
      setConversations(prev => {
        const updated = prev.map(c => (c.id === convId ? { ...c, updatedAt: new Date() } : c));
        return updated.sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
      });
    } catch (e) {
      console.error('Error enviando mensaje', e);
      const errMsg: ChatMessage = {
        id: Date.now(),
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

  // Ordenar para el sidebar por updatedAt desc
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
  }, [activeConversationId, activeMessages]);

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
          <div className="chat-content">
            <div className="chat-header">
              <h2>{conversations.find(c => c.id === activeConversationId)?.title || 'Chat'}</h2>
            </div>

            <div className="messages-container">
              {activeMessages.map((message) => (
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
              <div style={{ paddingBottom: '20px' }} ref={messagesEndRef}></div>
            </div>

            <div className="message-input-container">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !sending && handleSendMessage()}
                placeholder="Escribe un mensaje..."
                className="message-input"
                disabled={!activeConversationId}
              />
              <button
                onClick={handleSendMessage}
                className="send-button"
                disabled={!inputValue.trim() || !activeConversationId || sending}
              >
                {sending ? 'Enviando…' : 'Enviar'}
              </button>
            </div>
          </div>
        ) : (
          <ChatNoConversation onNewConversation={handleNewConversation} />
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
