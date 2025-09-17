import React, { useState, useRef, useEffect } from "react";
import ChatSidebar from "./chat-sidebar";
import DashboardHeader from "../dashboard/dashboard-header";
import RobotIcon from "../../assets/Robot.svg";
import UserIcon from "../../assets/Usuario.svg";
import { sendToGemini } from "../../ia/chatService"; // 👈 importamos el servicio IA

interface Message {
  id: string;
  text: string;
  sender: "ia" | "user";
  feedback?: "like" | "dislike";
}

interface ChatInterfaceProps {
  email: string;
  onLogout: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ email, onLogout }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  // Eliminado estado de feedback no utilizado
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Mensaje de bienvenida al iniciar
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: "welcome-message",
          text: "¡Hola! Soy tu asistente de IA. ¿Cómo puedo ayudarte hoy?",
          sender: "ia",
        },
      ]);
    }
  }, []);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    // Agregar mensaje del usuario
    const userMessage: Message = { id: Date.now().toString(), text: input, sender: "user" };
    setMessages((prev) => [...prev, userMessage]);

    const userInput = input;
    setInput("");
    setLoading(true);

    // Llamar al backend (Gemini)
    const aiResponse = await sendToGemini(userInput);

    // Agregar respuesta de la IA
    const iaMessage: Message = { id: (Date.now() + 1).toString(), text: aiResponse, sender: "ia" };
    setMessages((prev) => [...prev, iaMessage]);

    setLoading(false);
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  };

  const handleFeedback = (id: string, feedback: "like" | "dislike") => {
    setMessages((prev) =>
      prev.map((msg) => (msg.id === id ? { ...msg, feedback } : msg))
    );
    // Feedback visual puede añadirse aquí si se requiere
  };

  return (
    <div style={{ display: "flex", width: "100%", height: "100vh" }}>
      {/* Sidebar */}
      <ChatSidebar activeId="" onSelect={() => {}} />

      {/* Contenido */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", height: "100vh" }}>
        {/* Header */}
        <DashboardHeader
          userEmail={email}
          onHelp={() => alert("Ayuda")}
          onSettings={() => alert("Configuración")}
          onLogout={onLogout}
        />

        {/* Chat */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            height: "calc(100vh - 60px)",
            position: "relative",
            background: "#f5f9fc",
          }}
        >
          {/* Mensajes */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "24px 0",
              maxHeight: "calc(100% - 140px)",
            }}
          >
            <div
              style={{
                width: "100%",
                maxWidth: "900px",
                margin: "0 auto",
                display: "flex",
                flexDirection: "column",
                gap: "24px",
              }}
            >
              {messages.map((msg) =>
                msg.sender === "ia" ? (
                  <div key={msg.id} style={{ display: "flex", alignItems: "flex-start", gap: "12px" }}>
                    <div
                      style={{
                        width: "40px",
                        height: "40px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        background: "#1a6ac9",
                        borderRadius: "50%",
                        flexShrink: 0,
                      }}
                    >
                      <img
                        src={RobotIcon}
                        alt="IA"
                        style={{
                          width: "24px",
                          height: "24px",
                          filter: "brightness(0) invert(1)",
                        }}
                      />
                    </div>
                    <div
                      style={{
                        background: "#fff",
                        color: "#333",
                        borderRadius: "8px",
                        padding: "15px 20px",
                        minWidth: "200px",
                        maxWidth: "520px",
                        fontSize: "15px",
                        boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
                      }}
                    >
                      <div>{msg.text}</div>
                      <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
                        <button
                          style={{
                            background: "transparent",
                            border: "none",
                            padding: 0,
                            cursor: "pointer",
                            opacity: msg.feedback === "like" ? 1 : 0.6,
                          }}
                          onClick={() => handleFeedback(msg.id, "like")}
                          title="Bueno"
                        >
                          👍
                        </button>
                        <button
                          style={{
                            background: "transparent",
                            border: "none",
                            padding: 0,
                            cursor: "pointer",
                            opacity: msg.feedback === "dislike" ? 1 : 0.6,
                          }}
                          onClick={() => handleFeedback(msg.id, "dislike")}
                          title="Malo"
                        >
                          👎
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div key={msg.id} style={{ display: "flex", justifyContent: "flex-end" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                      <div
                        style={{
                          background: "#3b98fcff",
                          color: "#fff",
                          borderRadius: "12px",
                          padding: "10px 18px",
                          minWidth: "80px",
                          maxWidth: "320px",
                          fontSize: "16px",
                          boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
                          textAlign: "left",
                        }}
                      >
                        {msg.text}
                      </div>
                      <img
                        src={UserIcon}
                        alt="Usuario"
                        style={{
                          width: "32px",
                          height: "32px",
                          background: "#3b98fcff",
                          borderRadius: "50%",
                          border: "2px solid #b3d4fc",
                          boxShadow: "0 2px 8px rgba(0,87,184,0.10)",
                        }}
                      />
                    </div>
                  </div>
                )
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input */}
          <div
            style={{
              position: "sticky",
              bottom: 0,
              background: "#f5f9fc",
              padding: "10px 0",
              width: "100%",
            }}
          >
            <div
              style={{
                display: "flex",
                flexDirection: "row",
                background: "#f5f9fc",
                padding: "16px 0",
                borderRadius: "0 0 16px 16px",
                width: "100%",
                maxWidth: "900px",
                margin: "0 auto",
                alignItems: "center",
              }}
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleInputKeyDown}
                placeholder="Pregúntame lo que quieras..."
                style={{
                  flex: 1,
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid #b3d4fc",
                  fontSize: "16px",
                  background: "#fff",
                  color: "#222",
                  width: "100%",
                  boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
                  marginRight: "12px",
                }}
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                style={{
                  background: "#1a3a5d",
                  color: "#fff",
                  border: "none",
                  borderRadius: "8px",
                  padding: "12px 32px",
                  fontWeight: 600,
                  fontSize: "18px",
                  cursor: loading || !input.trim() ? "not-allowed" : "pointer",
                  boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
                  minWidth: "90px",
                }}
              >
                Enviar
              </button>
            </div>

            {loading && (
              <div style={{ marginTop: "10px", color: "#888", textAlign: "center" }}>
                Cargando respuesta...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;

