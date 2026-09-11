import { User, Sparkles } from "lucide-react";

/**
 * Renders a single turn in the lease/policy conversation.
 *
 * message: {
 *   role: "user" | "assistant",
 *   content: string,
 *   sources?: [{ document_id, title, chunk_id }],
 *   isError?: boolean
 * }
 */
export default function ChatMessage({ message }) {
  const isUser = message.role === "user";

  return (
    <div
      style={{
        display: "flex",
        flexDirection: isUser ? "row-reverse" : "row",
        gap: "10px",
        alignItems: "flex-start",
        marginBottom: "16px"
      }}
    >
      <div
        aria-hidden="true"
        style={{
          flexShrink: 0,
          width: "32px",
          height: "32px",
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: isUser ? "#16324F" : "#3C7A89",
          color: "#FFFFFF"
        }}
      >
        {isUser ? <User size={16} /> : <Sparkles size={16} />}
      </div>

      <div style={{ maxWidth: "70%" }}>
        <div
          style={{
            background: isUser
              ? "#16324F"
              : message.isError
              ? "#FBEAEA"
              : "#FFFFFF",
            color: isUser ? "#FFFFFF" : "#1F2933",
            border: isUser
              ? "none"
              : `1px solid ${message.isError ? "#C94C4C" : "#E4E7EC"}`,
            borderRadius: "12px",
            padding: "12px 16px",
            fontSize: "14px",
            lineHeight: 1.5,
            whiteSpace: "pre-wrap"
          }}
        >
          {message.content}
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <div style={{ marginTop: "8px" }}>
            <div
              style={{
                fontSize: "12px",
                color: "#667085",
                marginBottom: "4px"
              }}
            >
              Sources
            </div>
            <ul style={{ margin: 0, paddingLeft: "18px" }}>
              {message.sources.map((source) => (
                <li
                  key={source.chunk_id}
                  style={{
                    fontSize: "13px",
                    color: "#3C7A89",
                    marginBottom: "2px"
                  }}
                >
                  {source.title}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}