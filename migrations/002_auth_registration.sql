-- Migration 002: registration & password reset support

-- Unique phone index for login-by-phone
CREATE UNIQUE INDEX IF NOT EXISTS idx_employees_phone ON employees(phone)
    WHERE phone IS NOT NULL;

-- 6-digit password reset codes
CREATE TABLE IF NOT EXISTS password_reset_codes (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    code VARCHAR(10) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reset_codes_employee ON password_reset_codes(employee_id, expires_at);
