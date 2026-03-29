-- Migration 004: learning modules catalog + per-user progress

CREATE TABLE IF NOT EXISTS learning_modules (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    icon VARCHAR(50) NOT NULL DEFAULT 'book.fill',
    module_type VARCHAR(10) NOT NULL CHECK (module_type IN ('lesson', 'video', 'test')),
    duration_minutes INTEGER NOT NULL DEFAULT 15,
    points INTEGER NOT NULL DEFAULT 50,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_locked_default BOOLEAN NOT NULL DEFAULT FALSE
);

-- Per-user progress: 0.0 (not started) → 1.0 (completed)
CREATE TABLE IF NOT EXISTS user_module_progress (
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    module_id VARCHAR(36) NOT NULL REFERENCES learning_modules(id) ON DELETE CASCADE,
    progress DECIMAL(5,4) NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 1),
    completed_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (employee_id, module_id)
);

CREATE INDEX IF NOT EXISTS idx_module_progress_employee ON user_module_progress(employee_id);
