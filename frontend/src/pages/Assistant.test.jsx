import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import Assistant from "./Assistant";
import assistantService from "../services/assistantService";

vi.mock("../services/assistantService");

function askQuestion(text) {
  const input = screen.getByPlaceholderText("Ask about your lease or building...");
  fireEvent.change(input, { target: { value: text } });
  fireEvent.click(screen.getByLabelText("Send message"));
}

describe("Assistant page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a grounded answer with its sources", async () => {
    assistantService.chat.mockResolvedValue({
      answer: "Parking is included for one vehicle per apartment.",
      sources: [
        { document_id: "doc-1", title: "Building Parking Policy", chunk_id: "chunk-1" }
      ],
      conversation_id: "conv-1"
    });

    render(<Assistant />);
    askQuestion("Is parking included?");

    expect(await screen.findByText(/Parking is included/)).toBeInTheDocument();
    expect(screen.getByText("Building Parking Policy")).toBeInTheDocument();
  });

  it("shows the assistant's own unavailable-answer message rather than inventing one", async () => {
    assistantService.chat.mockResolvedValue({
      answer: "I can't find that in the lease or building policy documents.",
      sources: [],
      conversation_id: "conv-1"
    });

    render(<Assistant />);
    askQuestion("Do you allow pet elephants?");

    expect(
      await screen.findByText(/can't find that in the lease or building policy documents/)
    ).toBeInTheDocument();
  });

  it("handles a validation error (empty question) without crashing", async () => {
    assistantService.chat.mockRejectedValue({
      status: 422,
      errorCode: "VALIDATION_ERROR",
      message: "Question is required"
    });

    render(<Assistant />);
    askQuestion("anything");

    expect(
      await screen.findByText("Please enter a question before sending.")
    ).toBeInTheDocument();
  });

  it("does not send an empty question", () => {
    render(<Assistant />);
    const button = screen.getByLabelText("Send message");
    expect(button).toBeDisabled();
    expect(assistantService.chat).not.toHaveBeenCalled();
  });
});