-- Sber Dealer Database Schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2.1 employees
CREATE TABLE IF NOT EXISTS employees (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::varchar,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    position VARCHAR(200) NOT NULL,
    dealership VARCHAR(200) NOT NULL,
    dealership_code VARCHAR(20) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(200),
    avatar_url TEXT,
    program_join_date DATE NOT NULL DEFAULT CURRENT_DATE,
    region VARCHAR(100) NOT NULL DEFAULT 'Москва',
    employee_code VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(200),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 2.2 rating_plans
CREATE TABLE IF NOT EXISTS rating_plans (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    month DATE NOT NULL,
    volume_plan DECIMAL(10,2) NOT NULL DEFAULT 10.0,
    deals_plan INTEGER NOT NULL DEFAULT 10,
    bank_share_target DECIMAL(5,2) NOT NULL DEFAULT 50.0,
    volume_max_index INTEGER NOT NULL DEFAULT 120,
    UNIQUE(employee_id, month)
);

-- 2.3 daily_results
CREATE TABLE IF NOT EXISTS daily_results (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::varchar,
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    deals_closed INTEGER NOT NULL DEFAULT 0,
    loan_volume DECIMAL(10,2) NOT NULL DEFAULT 0,
    additional_products INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(employee_id, date)
);

-- 2.4 monthly_tasks
CREATE TABLE IF NOT EXISTS monthly_tasks (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::varchar,
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    month DATE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    target DECIMAL(10,2) NOT NULL,
    current DECIMAL(10,2) NOT NULL DEFAULT 0,
    unit VARCHAR(20) NOT NULL DEFAULT 'шт.',
    category VARCHAR(20) NOT NULL DEFAULT 'sales',
    deadline DATE,
    reward_points INTEGER NOT NULL DEFAULT 10
);

-- 2.5 privileges
CREATE TABLE IF NOT EXISTS privileges (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::varchar,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(20) NOT NULL DEFAULT 'other',
    available_from VARCHAR(10) NOT NULL DEFAULT 'silver',
    financial_effect INTEGER,
    detail_text TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0
);

-- 2.6 support_messages
CREATE TABLE IF NOT EXISTS support_messages (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::varchar,
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    sender VARCHAR(10) NOT NULL DEFAULT 'employee',
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    is_read BOOLEAN NOT NULL DEFAULT FALSE
);

-- 2.7 personal_managers
CREATE TABLE IF NOT EXISTS personal_managers (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::varchar,
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    position VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(200),
    avatar_url TEXT
);

-- 2.8 news
CREATE TABLE IF NOT EXISTS news (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::varchar,
    title VARCHAR(300) NOT NULL,
    summary TEXT NOT NULL,
    body TEXT,
    image_url TEXT,
    category VARCHAR(20) NOT NULL DEFAULT 'company',
    published_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 2.9 news_read_status
CREATE TABLE IF NOT EXISTS news_read_status (
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    news_id VARCHAR(36) NOT NULL REFERENCES news(id) ON DELETE CASCADE,
    read_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (employee_id, news_id)
);

-- refresh tokens
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(36) NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    token VARCHAR(512) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_daily_results_employee_date ON daily_results(employee_id, date);
CREATE INDEX IF NOT EXISTS idx_monthly_tasks_employee_month ON monthly_tasks(employee_id, month);
CREATE INDEX IF NOT EXISTS idx_support_messages_employee ON support_messages(employee_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_news_published ON news(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_rating_plans_employee_month ON rating_plans(employee_id, month);
