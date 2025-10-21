CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id VARCHAR(50) UNIQUE NOT NULL,
    employee_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    redmine_url VARCHAR(500) NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    default_project_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_telegram_id ON users(telegram_id);

CREATE INDEX idx_employee_id ON users(employee_id);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();







-- CREATE TABLE IF NOT EXISTS activity_log (
--     id SERIAL PRIMARY KEY,
--     telegram_id VARCHAR(50) NOT NULL,
--     action VARCHAR(100) NOT NULL,
--     details JSONB,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
-- );

-- CREATE INDEX idx_activity_telegram_id ON activity_log(telegram_id);
-- CREATE INDEX idx_activity_created_at ON activity_log(created_at);
