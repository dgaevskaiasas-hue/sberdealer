-- Migration 003: per-user bank_share and conversion actual values

ALTER TABLE rating_plans
    ADD COLUMN IF NOT EXISTS bank_share_actual DECIMAL(5,2) NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS conversion_actual  DECIMAL(5,2) NOT NULL DEFAULT 0;

-- Seed: copy the existing hardcoded values to current plans so existing users keep their state
UPDATE rating_plans SET bank_share_actual = 40.0, conversion_actual = 45.0
WHERE bank_share_actual = 0;
