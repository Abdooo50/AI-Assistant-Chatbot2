DROP TABLE IF EXISTS chat_messages;
DROP TABLE IF EXISTS chat_threads;

CREATE TABLE chat_threads (
    thread_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    chat_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_threads_user_id ON chat_threads(user_id);

CREATE TABLE chat_messages (
    message_id SERIAL PRIMARY KEY,
    thread_id VARCHAR(255) REFERENCES chat_threads(thread_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_messages_thread_id ON chat_messages(thread_id);