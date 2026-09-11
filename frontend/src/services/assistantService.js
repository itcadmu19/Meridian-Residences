import api from "./api";

// DEMO-ONLY fallback used when VITE_MOCK_ASSISTANT=true and the real
// FastAPI backend isn't running yet. This lets the page be previewed
// end-to-end before Member 4's backend/RAG service exists. It never
// runs in production — delete this block (and the .env flag) once the
// real /api/v1/assistant/chat endpoint is up.
const MOCK_KB = [
  {
    match: /parking/i,
    answer:
      "According to your building policy, parking is included for one vehicle per apartment. Additional vehicles may require prior approval and an additional fee.",
    sources: [{ document_id: "doc-parking", title: "Building Parking Policy", chunk_id: "chunk-1" }]
  },
  {
    match: /early termination|terminat/i,
    answer:
      "Early termination requires 60 days' written notice and forfeiture of one month's security deposit, as outlined in your lease agreement.",
    sources: [{ document_id: "doc-lease", title: "Lease Terms — Section 8", chunk_id: "chunk-2" }]
  }
];

function mockChat({ message, conversationId }) {
  const hit = MOCK_KB.find((entry) => entry.match.test(message));
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(
        hit
          ? { answer: hit.answer, sources: hit.sources, conversation_id: conversationId ?? "mock-conversation" }
          : {
              answer:
                "I can't find this in the lease or building policy documents. Please contact the resident office for more detail.",
              sources: [],
              conversation_id: conversationId ?? "mock-conversation"
            }
      );
    }, 500);
  });
}

/**
 * POST /api/v1/assistant/chat
 * Request:  { message, conversation_id? }
 * Response: { success, data: { answer, sources[], conversation_id }, message, meta }
 */
async function chat({ message, conversationId }) {
  if (import.meta.env.VITE_MOCK_ASSISTANT === "true") {
    return mockChat({ message, conversationId });
  }

  const response = await api.post("/assistant/chat", {
    message,
    conversation_id: conversationId ?? undefined
  });
  return response.data.data; // { answer, sources, conversation_id }
}

/**
 * POST /api/v1/assistant/reindex
 * Admin/internal — not called from the resident-facing chat UI.
 */
async function reindex(documentMetadata) {
  const response = await api.post("/assistant/reindex", documentMetadata);
  return response.data.data;
}

const assistantService = { chat, reindex };
export default assistantService;
