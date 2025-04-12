"""
Schema definitions for the conversation storage SQLite database.
"""

# Current schema version, increment this when schema changes
SCHEMA_VERSION = 1

# SQLite schema definition
SCHEMA_SQL = """
-- Schema Version Tracking
CREATE TABLE IF NOT EXISTS schema_info (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Main Conversation Table
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    context_id TEXT NOT NULL,          -- ID of related context (world_id, persona_id, etc.)
    context_type TEXT NOT NULL,        -- Type of context ("world", "persona", "problem")
    context_name TEXT NOT NULL,        -- Name of the context for display
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT DEFAULT '{}'         -- JSON field for flexible storage
);

-- Message Storage
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL,                -- "user" or "assistant"
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT DEFAULT '{}',        -- JSON field for flexible storage
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- Vector Embeddings Cache
CREATE TABLE IF NOT EXISTS message_embeddings (
    message_id INTEGER PRIMARY KEY,
    embedding BLOB NOT NULL,           -- Binary representation of vector
    model_version TEXT NOT NULL,       -- Embedding model identifier
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_conversation_context ON conversations(context_type, context_id);
CREATE INDEX IF NOT EXISTS idx_message_conversation ON messages(conversation_id);
"""
