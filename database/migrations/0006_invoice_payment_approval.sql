-- Resident dummy payment submissions remain pending until staff approval.
ALTER TABLE recurring_invoices DROP CONSTRAINT IF EXISTS recurring_invoices_payment_status_check;
ALTER TABLE recurring_invoices DROP CONSTRAINT IF EXISTS ck_recurring_invoices_payment_status;
ALTER TABLE recurring_invoices ADD CONSTRAINT ck_recurring_invoices_payment_status
    CHECK (payment_status IN ('pending', 'payment_submitted', 'paid', 'overdue', 'cancelled'));