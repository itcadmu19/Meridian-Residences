import api from "./api";

export async function chat({ message, conversationId }) {
  const response = await api.post("/assistant/chat", {
    message,
    conversation_id: conversationId ?? undefined,
  });
  return response.data.data; // { answer, sources, conversation_id }
}
