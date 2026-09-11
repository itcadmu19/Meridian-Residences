import { useEffect, useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";
import PageHeader from "../components/PageHeader";
import Card from "../components/Card";
import ChatMessage from "../components/ChatMessage";
import Loading from "../components/Loading";
import ErrorMessage from "../components/ErrorMessage";
import assistantService from "../services/assistantService";

const SUGGESTED_QUESTIONS = [
  "Is parking included in my lease?",
  "What is the early termination policy?",
  "How much notice do I need to give before moving out?",
  "What happens if my rent payment is late?"
];

export default function Assistant() {
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const scrollAnchorRef = useRef(null);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSubmitting]);

  async function sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed || isSubmitting) return;

    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setMessageInput("");
    setIsSubmitting(true);

    try {
      const result = await assistantService.chat({
        message: trimmed,
        conversationId
      });

      setConversationId(result.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: result.answer,
          sources: result.sources
        }
      ]);
    } catch (err) {
      // 422 (empty question) and general failures both land here.
      // The assistant still answers in its own voice rather than
      // leaving a bare system error in the transcript.
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            err.errorCode === "VALIDATION_ERROR"
              ? "Please enter a question before sending."
              : "I couldn't reach the assistant service just now. Please try again.",
          isError: true
        }
      ]);
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    sendMessage(messageInput);
  }

  return (
    <div style={{ maxWidth: "760px" }}>
      <PageHeader
        title="Lease & Policy Assistant"
        description="Ask questions about your lease and building policies."
      />

      <Card
        style={{
          display: "flex",
          flexDirection: "column",
          height: "560px",
          padding: 0,
          overflow: "hidden"
        }}
      >
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "20px"
          }}
        >
          {messages.length === 0 && (
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  color: "#3C7A89",
                  fontSize: "14px",
                  fontWeight: 600,
                  marginBottom: "12px"
                }}
              >
                <Sparkles size={16} />
                Ask me anything about your lease or building policies
              </div>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "8px"
                }}
              >
                {SUGGESTED_QUESTIONS.map((question) => (
                  <button
                    key={question}
                    onClick={() => sendMessage(question)}
                    style={{
                      textAlign: "left",
                      background: "#F7F5F0",
                      border: "1px solid #E4E7EC",
                      borderRadius: "8px",
                      padding: "10px 14px",
                      fontSize: "13px",
                      color: "#1F2933"
                    }}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))}

          {isSubmitting && <Loading label="Looking through your documents..." />}

          <div ref={scrollAnchorRef} />
        </div>

        {error && (
          <div style={{ padding: "0 20px 12px" }}>
            <ErrorMessage message={error} onRetry={() => setError(null)} />
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          style={{
            display: "flex",
            gap: "8px",
            padding: "16px 20px",
            borderTop: "1px solid #E4E7EC"
          }}
        >
          <input
            type="text"
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            placeholder="Ask about your lease or building..."
            disabled={isSubmitting}
            style={{
              flex: 1,
              border: "1px solid #E4E7EC",
              borderRadius: "8px",
              padding: "10px 14px",
              fontSize: "14px",
              color: "#1F2933"
            }}
          />
          <button
            type="submit"
            disabled={isSubmitting || !messageInput.trim()}
            aria-label="Send message"
            style={{
              background: "#16324F",
              color: "#FFFFFF",
              border: "none",
              borderRadius: "8px",
              width: "40px",
              height: "40px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              opacity: isSubmitting || !messageInput.trim() ? 0.5 : 1
            }}
          >
            <Send size={16} />
          </button>
        </form>
      </Card>
    </div>
  );
}