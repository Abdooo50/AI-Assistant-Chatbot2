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

CREATE INDEX idx_chat_messages_thread_id ON chat_messages(thread_id)

-- SQL script to update chat_messages table with new columns for ChatGPT-like features

-- Add message_type column to chat_messages table
ALTER TABLE chat_messages 
ADD COLUMN IF NOT EXISTS message_type VARCHAR(50) DEFAULT 'text';

-- Add metadata column to chat_messages table (as JSONB for flexibility)
ALTER TABLE chat_messages 
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT NULL;

-- Update existing records to have default message_type
UPDATE chat_messages 
SET message_type = 'text' 
WHERE message_type IS NULL;

-- Create index on message_type for faster queries
CREATE INDEX IF NOT EXISTS idx_chat_messages_message_type ON chat_messages(message_type);

-- Add comment to explain the purpose of these columns
COMMENT ON COLUMN chat_messages.message_type IS 'Type of message (text, code, error, suggestion, greeting, etc.)';
COMMENT ON COLUMN chat_messages.metadata IS 'Additional metadata for the message in JSON format';
