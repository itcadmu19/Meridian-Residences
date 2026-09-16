import React, { useEffect, useRef, useState } from "react";
import { Bot, Send, Sparkles, User } from "lucide-react";
import { chat } from "../services/assistantService";
import Toast from "../components/Toast";

const SUGGESTED_QUESTIONS = [
  "Is parking included in my lease?",
  "What is the early termination policy?",
  "How much notice do I need to give before moving out?",
  "What happens if my rent payment is late?",
];

export default function AiAssistant() {
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toast, setToast] = useState(null);

  const scrollAnchorRef = useRef(null);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSubmitting]);

  async function sendMessage(text) {
    const trimmed = text.trim();
    if (!trimmed || isSubmitting) return;

    setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
    setMessageInput("");
    setIsSubmitting(true);

    try {
      const result = await chat({ message: trimmed, conversationId });
      setConversationId(result.conversation_id);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.answer, sources: result.sources },
      ]);
    } catch (err) {
      const isValidationError = err?.response?.data?.error_code === "VALIDATION_ERROR";
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: isValidationError
            ? "Please enter a question before sending."
            : "I couldn't reach the assistant service just now. Please try again.",
          isError: true,
        },
      ]);
      setToast({ title: "Assistant unavailable", message: "Could not get a response. Please try again." });
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    sendMessage(messageInput);
  }

  return (
    <div className="staff-page">
      <section className="page-heading lease-heading">
        <div>
          <span className="section-kicker">RESIDENT SERVICES</span>
          <h1>AI Assistant</h1>
          <p>Ask questions about your lease and building policies.</p>
        </div>
      </section>

      <section className="content-card chat-card">
        <div className="chat-thread">
          {messages.length === 0 && (
            <div className="chat-suggestions">
              <div className="chat-suggestions-heading">
                <Sparkles size={16} />
                Ask me anything about your lease or building policies
              </div>
              <div className="chat-suggestions-list">
                {SUGGESTED_QUESTIONS.map((question) => (
                  <button key={question} className="chat-suggestion" onClick={() => sendMessage(question)}>
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message, index) => {
            const isUser = message.role === "user";
            return (
              <div key={index} className={`chat-bubble-row ${isUser ? "chat-bubble-row--user" : ""}`}>
                <span className="chat-avatar" aria-hidden="true">
                  {isUser ? <User size={16} /> : <Bot size={16} />}
                </span>
                <div className="chat-bubble-group">
                  <div
                    className={`chat-bubble ${isUser ? "chat-bubble--user" : "chat-bubble--assistant"} ${
                      message.isError ? "chat-bubble--error" : ""
                    }`}
                  >
                    {message.content}
                  </div>
                  {!isUser && message.sources && message.sources.length > 0 && (
                    <div className="chat-sources">
                      <span>Sources</span>
                      <ul>
                        {message.sources.map((source) => (
                          <li key={source.chunk_id}>{source.title}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {isSubmitting && <div className="chat-loading">Looking through your documents…</div>}

          <div ref={scrollAnchorRef} />
        </div>

        <form className="chat-input-row" onSubmit={handleSubmit}>
          <input
            type="text"
            value={messageInput}
            onChange={(event) => setMessageInput(event.target.value)}
            placeholder="Ask about your lease or building…"
            disabled={isSubmitting}
          />
          <button
            type="submit"
            className="primary-button chat-send-button"
            disabled={isSubmitting || !messageInput.trim()}
            aria-label="Send message"
          >
            <Send size={16} />
          </button>
        </form>
      </section>

      <Toast open={Boolean(toast)} onClose={() => setToast(null)} title={toast?.title} message={toast?.message} />
    </div>
  );
}
