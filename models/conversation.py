"""
Conversation model for conversation storage.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.agent_module.models.message import Message

@dataclass
class Conversation:
    """
    Represents a conversation with metadata and messages.
    """
    id: Optional[int] = None
    title: Optional[str] = None
    context_id: Optional[str] = None
    context_type: Optional[str] = None
    context_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    messages: List[Message] = field(default_factory=list)
    
    def __post_init__(self):
        """Handle initialization with string metadata and timestamps."""
        # Handle metadata
        if isinstance(self.metadata, str):
            try:
                self.metadata = json.loads(self.metadata)
            except (json.JSONDecodeError, TypeError):
                self.metadata = {}
        
        # Handle timestamps
        if self.created_at is None:
            self.created_at = datetime.now()
        elif isinstance(self.created_at, str):
            try:
                self.created_at = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                self.created_at = datetime.now()
                
        if self.updated_at is None:
            self.updated_at = self.created_at
        elif isinstance(self.updated_at, str):
            try:
                self.updated_at = datetime.fromisoformat(self.updated_at.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                self.updated_at = self.created_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the conversation to a dictionary.
        
        Returns:
            Dictionary representation of the conversation.
        """
        result = {
            "metadata": self.metadata,
            "messages": [msg.to_dict() for msg in self.messages]
        }
        
        # Add optional fields if they exist
        if self.id is not None:
            result["id"] = self.id
            
        if self.title is not None:
            result["title"] = self.title
            
        if self.context_id is not None:
            result["context_id"] = self.context_id
            
        if self.context_type is not None:
            result["context_type"] = self.context_type
            
        if self.context_name is not None:
            result["context_name"] = self.context_name
            
        if self.created_at is not None:
            result["created_at"] = self.created_at.isoformat()
            
        if self.updated_at is not None:
            result["updated_at"] = self.updated_at.isoformat()
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """
        Create a conversation from a dictionary.
        
        Args:
            data: Dictionary representation of a conversation.
            
        Returns:
            New Conversation instance.
        """
        if data is None:
            return cls()
            
        # Extract basic conversation metadata
        conversation_id = data.get('id')
        title = data.get('title')
        context_id = data.get('context_id')
        context_type = data.get('context_type')
        context_name = data.get('context_name')
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')
        metadata = data.get('metadata', {})
        
        # Create the conversation without messages first
        conversation = cls(
            id=conversation_id,
            title=title,
            context_id=context_id,
            context_type=context_type,
            context_name=context_name,
            created_at=created_at,
            updated_at=updated_at,
            metadata=metadata
        )
        
        # Add messages if they exist
        if 'messages' in data and isinstance(data['messages'], list):
            for msg_data in data['messages']:
                # Skip invalid message data
                if not isinstance(msg_data, dict):
                    continue
                    
                # Create message and ensure conversation_id is set
                message = Message.from_dict(msg_data)
                if conversation_id is not None:
                    message.conversation_id = conversation_id
                    
                conversation.messages.append(message)
        
        return conversation
    
    def add_message(self, message: Message) -> None:
        """
        Add a message to the conversation.
        
        Args:
            message: Message to add.
        """
        # Set the conversation ID on the message
        if self.id is not None:
            message.conversation_id = self.id
            
        # Add the message to the list
        self.messages.append(message)
        
        # Update the updated_at timestamp
        self.updated_at = datetime.now()
    
    def to_db_dict(self) -> Dict[str, Any]:
        """
        Convert to a dictionary suitable for database storage.
        
        Returns:
            Dictionary with fields prepared for database storage.
        """
        return {
            "title": self.title or "Untitled Conversation",
            "context_id": self.context_id or "",
            "context_type": self.context_type or "",
            "context_name": self.context_name or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": json.dumps(self.metadata)
        }
    
    def generate_default_title(self) -> str:
        """
        Generate a default title for the conversation based on context and time.
        
        Returns:
            A default title.
        """
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if self.context_name:
            return f"{self.context_name} - {time_str}"
        elif self.context_type and self.context_id:
            return f"{self.context_type.capitalize()} {self.context_id} - {time_str}"
        else:
            return f"Conversation - {time_str}"
