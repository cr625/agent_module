"""
Service for storing and retrieving conversations from the SQLite database.
"""

import json
import logging
from typing import List, Dict, Any, Optional, Union

from app.agent_module.services.database_service import DatabaseService
from app.agent_module.models.conversation import Conversation
from app.agent_module.models.message import Message

logger = logging.getLogger(__name__)

class ConversationStorageService:
    """
    Service for storing and retrieving conversations.
    
    Provides methods for saving, loading, and managing conversation history.
    """
    
    def __init__(self, database_service: Optional[DatabaseService] = None):
        """
        Initialize the conversation storage service.
        
        Args:
            database_service: DatabaseService instance or None to create a new one.
        """
        self.db = database_service or DatabaseService()
    
    def save_conversation(self, conversation: Conversation) -> int:
        """
        Save a conversation to the database.
        
        If the conversation has an ID, it's updated.
        Otherwise, a new conversation is created.
        
        Args:
            conversation: The conversation to save.
            
        Returns:
            The ID of the saved conversation.
        """
        # Generate default title if none is provided
        if not conversation.title:
            conversation.title = conversation.generate_default_title()
        
        # Ensure context values are not None
        conversation_data = conversation.to_db_dict()
        
        if conversation.id is None:
            # Insert new conversation
            query = """
                INSERT INTO conversations 
                (title, context_id, context_type, context_name, created_at, updated_at, metadata)
                VALUES (:title, :context_id, :context_type, :context_name, :created_at, :updated_at, :metadata)
            """
            self.db.execute_query(query, conversation_data)
            
            # Get ID of newly inserted conversation
            query = "SELECT last_insert_rowid() as id"
            result = self.db.execute_query(query)
            conversation.id = result[0]['id'] if result else None
        else:
            # Update existing conversation
            query = """
                UPDATE conversations
                SET title = :title,
                    context_id = :context_id,
                    context_type = :context_type,
                    context_name = :context_name,
                    updated_at = :updated_at,
                    metadata = :metadata
                WHERE id = :id
            """
            params = {**conversation_data, 'id': conversation.id}
            self.db.execute_query(query, params)
        
        # Save messages
        for message in conversation.messages:
            self._save_message(message, conversation.id)
        
        return conversation.id
    
    def _save_message(self, message: Message, conversation_id: int) -> int:
        """
        Save a message to the database.
        
        Args:
            message: The message to save.
            conversation_id: The ID of the conversation.
            
        Returns:
            The ID of the saved message.
        """
        # Set conversation ID on message
        message.conversation_id = conversation_id
        
        message_data = message.to_db_dict()
        
        if message.id is None:
            # Insert new message
            query = """
                INSERT INTO messages
                (conversation_id, role, content, timestamp, metadata)
                VALUES (:conversation_id, :role, :content, :timestamp, :metadata)
            """
            self.db.execute_query(query, message_data)
            
            # Get ID of newly inserted message
            query = "SELECT last_insert_rowid() as id"
            result = self.db.execute_query(query)
            message.id = result[0]['id'] if result else None
        else:
            # Update existing message
            query = """
                UPDATE messages
                SET role = :role,
                    content = :content,
                    timestamp = :timestamp,
                    metadata = :metadata
                WHERE id = :id AND conversation_id = :conversation_id
            """
            params = {**message_data, 'id': message.id}
            self.db.execute_query(query, params)
        
        return message.id
    
    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """
        Get a conversation by its ID.
        
        Args:
            conversation_id: ID of the conversation to retrieve.
            
        Returns:
            The conversation or None if not found.
        """
        # Get conversation metadata
        query = """
            SELECT id, title, context_id, context_type, context_name, created_at, updated_at, metadata
            FROM conversations
            WHERE id = ?
        """
        result = self.db.execute_query(query, (conversation_id,))
        
        if not result:
            return None
        
        conversation_data = result[0]
        
        # Create conversation object
        conversation = Conversation(
            id=conversation_data['id'],
            title=conversation_data['title'],
            context_id=conversation_data['context_id'],
            context_type=conversation_data['context_type'],
            context_name=conversation_data['context_name'],
            created_at=conversation_data['created_at'],
            updated_at=conversation_data['updated_at'],
            metadata=conversation_data['metadata']
        )
        
        # Get messages for this conversation
        query = """
            SELECT id, role, content, timestamp, metadata
            FROM messages
            WHERE conversation_id = ?
            ORDER BY timestamp
        """
        messages_data = self.db.execute_query(query, (conversation_id,))
        
        # Add messages to conversation
        for message_data in messages_data:
            message = Message(
                id=message_data['id'],
                role=message_data['role'],
                content=message_data['content'],
                timestamp=message_data['timestamp'],
                metadata=message_data['metadata'],
                conversation_id=conversation_id
            )
            conversation.messages.append(message)
        
        return conversation
    
    def list_conversations(
        self, 
        context_type: Optional[str] = None, 
        context_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List conversations with optional filtering.
        
        Args:
            context_type: Optional filter by context type.
            context_id: Optional filter by context ID.
            limit: Maximum number of conversations to return.
            offset: Number of conversations to skip.
            
        Returns:
            List of conversation metadata dictionaries.
        """
        query_parts = ["SELECT id, title, context_id, context_type, context_name, created_at, updated_at, metadata FROM conversations"]
        params = {}
        
        # Add filters
        where_clauses = []
        if context_type:
            where_clauses.append("context_type = :context_type")
            params['context_type'] = context_type
            
        if context_id:
            where_clauses.append("context_id = :context_id")
            params['context_id'] = context_id
            
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
        
        # Add ordering and pagination
        query_parts.append("ORDER BY updated_at DESC")
        query_parts.append("LIMIT :limit OFFSET :offset")
        params['limit'] = limit
        params['offset'] = offset
        
        query = " ".join(query_parts)
        return self.db.execute_query(query, params)
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """
        Delete a conversation and all its messages.
        
        Args:
            conversation_id: ID of the conversation to delete.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Cascade will handle message deletion
            query = "DELETE FROM conversations WHERE id = ?"
            self.db.execute_query(query, (conversation_id,))
            return True
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            return False
    
    def export_conversation(self, conversation_id: int) -> Optional[str]:
        """
        Export a conversation to JSON.
        
        Args:
            conversation_id: ID of the conversation to export.
            
        Returns:
            JSON string or None if conversation not found.
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
            
        export_data = {
            "schema_version": 1,
            "conversation": {
                "title": conversation.title,
                "context_id": conversation.context_id,
                "context_type": conversation.context_type,
                "context_name": conversation.context_name,
                "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                "metadata": conversation.metadata
            },
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                    "timestamp": message.timestamp.isoformat() if message.timestamp else None,
                    "metadata": message.metadata
                }
                for message in conversation.messages
            ]
        }
        
        return json.dumps(export_data, indent=2)
    
    def import_conversation(self, json_data: Union[str, Dict]) -> Optional[int]:
        """
        Import a conversation from JSON.
        
        Args:
            json_data: JSON string or dictionary.
            
        Returns:
            ID of the imported conversation or None if import failed.
        """
        try:
            # Parse JSON if string
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
                
            # Validate schema
            if not isinstance(data, dict) or 'conversation' not in data or 'messages' not in data:
                logger.error("Invalid conversation JSON format")
                return None
                
            # Create conversation object
            conversation_data = data['conversation']
            conversation = Conversation(
                title=conversation_data.get('title'),
                context_id=conversation_data.get('context_id'),
                context_type=conversation_data.get('context_type'),
                context_name=conversation_data.get('context_name'),
                created_at=conversation_data.get('created_at'),
                metadata=conversation_data.get('metadata', {})
            )
            
            # Add messages
            for message_data in data['messages']:
                message = Message(
                    role=message_data.get('role', 'assistant'),
                    content=message_data.get('content', ''),
                    timestamp=message_data.get('timestamp'),
                    metadata=message_data.get('metadata', {})
                )
                conversation.add_message(message)
                
            # Save to database
            return self.save_conversation(conversation)
                
        except Exception as e:
            logger.error(f"Error importing conversation: {e}")
            return None
    
    def search_conversations(self, search_text: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search conversations by text content.
        
        Args:
            search_text: Text to search for.
            limit: Maximum number of results to return.
            
        Returns:
            List of conversation metadata dictionaries.
        """
        query = """
            SELECT DISTINCT c.id, c.title, c.context_id, c.context_type, c.context_name, 
                c.created_at, c.updated_at, c.metadata
            FROM conversations c
            JOIN messages m ON c.id = m.conversation_id
            WHERE c.title LIKE :search_text
                OR m.content LIKE :search_text
            ORDER BY c.updated_at DESC
            LIMIT :limit
        """
        params = {
            'search_text': f'%{search_text}%',
            'limit': limit
        }
        return self.db.execute_query(query, params)
    
    def count_conversations(
        self, 
        context_type: Optional[str] = None, 
        context_id: Optional[str] = None
    ) -> int:
        """
        Count the number of conversations with optional filtering.
        
        Args:
            context_type: Optional filter by context type.
            context_id: Optional filter by context ID.
            
        Returns:
            Number of conversations.
        """
        query_parts = ["SELECT COUNT(*) as count FROM conversations"]
        params = {}
        
        # Add filters
        where_clauses = []
        if context_type:
            where_clauses.append("context_type = :context_type")
            params['context_type'] = context_type
            
        if context_id:
            where_clauses.append("context_id = :context_id")
            params['context_id'] = context_id
            
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
        
        query = " ".join(query_parts)
        result = self.db.execute_query(query, params)
        return result[0]['count'] if result else 0
