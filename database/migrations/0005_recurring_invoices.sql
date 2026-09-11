-- Member 2 story: View & Generate Recurring Invoices (Design Contract §5.4).
CREATE TABLE IF NOT EXISTS recurring_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lease_id UUID NOT NULL REFERENCES lease_agreements (id),
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,
    amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    due_date DATE NOT NULL,
    payment_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (payment_status IN ('pending', 'paid', 'overdue', 'cancelled')),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_at TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_recurring_invoices_lease_period
        UNIQUE (lease_id, billing_period_start, billing_period_end)
);

CREATE INDEX IF NOT EXISTS ix_recurring_invoices_lease_id ON recurring_invoices (lease_id);
CREATE INDEX IF NOT EXISTS ix_recurring_invoices_payment_status ON recurring_invoices (payment_status);
CREATE INDEX IF NOT EXISTS ix_recurring_invoices_due_date ON recurring_invoices (due_date);

DROP TRIGGER IF EXISTS trg_recurring_invoices_updated_at ON recurring_invoices;
CREATE TRIGGER trg_recurring_invoices_updated_at
    BEFORE UPDATE ON recurring_invoices
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();
