-- Demo staff login for local development: staff@meridian.com / StaffPass123!
INSERT INTO guests (id, name, email, phone, loyalty_tier)
VALUES ('12121212-1212-1212-1212-121212121212', 'Meridian Staff', 'staff@meridian.com', NULL, NULL)
ON CONFLICT (id) DO NOTHING;

INSERT INTO resident_credentials (id, guest_id, unit_id, email, password_hash, role)
VALUES (
    '55555555-5555-5555-5555-555555555555',
    '12121212-1212-1212-1212-121212121212',
    '33333333-3333-3333-3333-333333333333',
    'staff@meridian.com',
    '$2b$12$TtkR6oUXWjCjgQdzLGNlv.T/WCTtJhg3buJq45PSvoGJd/iH8V27S',
    'staff'
)
ON CONFLICT (id) DO NOTHING;
