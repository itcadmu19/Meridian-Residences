import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Maintenance from "./Maintenance.jsx";
import maintenanceService from "../services/maintenanceService.js";

vi.mock("../services/maintenanceService.js", () => ({
  default: {
    getTickets: vi.fn(),
    createTicket: vi.fn(),
    triageTicket: vi.fn(),
  },
}));

const SAMPLE_TICKET = {
  id: "ticket-1",
  issue_type: "plumbing",
  description: "Kitchen sink is leaking",
  priority: "high",
  status: "open",
  vendor_queue: null,
  escalated: false,
  created_at: "2026-09-01T00:00:00Z",
};

describe("Maintenance page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows a loading state while fetching tickets", () => {
    maintenanceService.getTickets.mockReturnValue(new Promise(() => {}));

    render(<Maintenance />);

    expect(screen.getByText(/loading maintenance requests/i)).toBeInTheDocument();
  });

  it("renders tickets on successful load", async () => {
    maintenanceService.getTickets.mockResolvedValue({ data: [SAMPLE_TICKET] });

    render(<Maintenance />);

    await waitFor(() => {
      expect(screen.getByText(/kitchen sink is leaking/i)).toBeInTheDocument();
    });
  });

  it("shows an error message and retry option when loading fails", async () => {
    maintenanceService.getTickets.mockRejectedValue({ message: "Network error" });

    render(<Maintenance />);

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });

  it("shows an empty state when there are no tickets", async () => {
    maintenanceService.getTickets.mockResolvedValue({ data: [] });

    render(<Maintenance />);

    await waitFor(() => {
      expect(screen.getByText(/no maintenance requests/i)).toBeInTheDocument();
    });
  });

  it("submits a new request and triggers triage", async () => {
    const user = userEvent.setup();
    maintenanceService.getTickets.mockResolvedValue({ data: [] });
    maintenanceService.createTicket.mockResolvedValue({ data: { ...SAMPLE_TICKET, id: "ticket-2" } });
    maintenanceService.triageTicket.mockResolvedValue({
      data: { priority: "urgent", status: "assigned", escalated: true, vendor_queue: "plumbing-emergency" },
    });

    render(<Maintenance />);

    await waitFor(() => expect(screen.getByText(/no maintenance requests/i)).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: /submit request/i }));
    await user.type(screen.getByLabelText(/description/i), "Water leak under sink");
    await user.click(screen.getAllByRole("button", { name: /submit request/i })[1]);

    await waitFor(() => {
      expect(maintenanceService.createTicket).toHaveBeenCalledWith({
        issue_type: "plumbing",
        description: "Water leak under sink",
      });
    });
    expect(maintenanceService.triageTicket).toHaveBeenCalledWith("ticket-2");
  });
});
