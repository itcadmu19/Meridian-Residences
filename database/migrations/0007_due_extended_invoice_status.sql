-- Staff due-date extensions are visible to both staff and residents.
ALTER TABLE recurring_invoices DROP CONSTRAINT IF EXISTS recurring_invoices_payment_status_check;
ALTER TABLE recurring_invoices DROP CONSTRAINT IF EXISTS ck_recurring_invoices_payment_status;
ALTER TABLE recurring_invoices ADD CONSTRAINT ck_recurring_invoices_payment_status
    CHECK (payment_status IN ('pending', 'payment_submitted', 'paid', 'overdue', 'due_extended', 'cancelled'));