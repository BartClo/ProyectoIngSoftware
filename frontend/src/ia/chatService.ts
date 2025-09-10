// frontend/src/IA/chatService.ts

export interface ChatResponse {
  answer: string;
  sources?: string[];
  error?: string;
}

/**
 * Envia un mensaje al backend FastAPI que está corriendo RAG
 * (solo responde en base a los documentos precargados).
 */
export const sendToGemini = async (message: string): Promise<string> => {
  try {
    const res = await fetch("http://127.0.0.1:8000/chat/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    if (!res.ok) {
      throw new Error(`Error HTTP ${res.status}`);
    }

    const data: ChatResponse = await res.json();

    if (data.answer) {
      const sourcesText =
        data.sources && data.sources.length > 0
          ? `\n\n📚 Fuentes: ${data.sources.join(", ")}`
          : "";
      return data.answer + sourcesText;
    }

    if (data.error) {
      return `❌ Error: ${data.error}`;
    }

    return "⚠️ No se encontró una respuesta en el contexto.";
  } catch (error) {
    console.error("Error llamando al backend:", error);
    return "🚨 Error al conectar con la IA.";
  }
};

