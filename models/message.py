"""
Message model for conversation storage.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class Message:
    """
    Represents a message in a conversation.
    """
    content: str
    role: str  # 'user' or 'assistant'
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[int] = None
    conversation_id: Optional[int] = None
    
    def __post_init__(self):
        """Handle initialization with string metadata and timestamps."""
        # Handle metadata
        if isinstance(self.metadata, str):
            try:
                self.metadata = json.loads(self.metadata)
            except (json.JSONDecodeError, TypeError):
                self.metadata = {}
        
        # Handle timestamp
        if self.timestamp is None:
            self.timestamp = datetime.now()
        elif isinstance(self.timestamp, str):
            try:
                self.timestamp = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the message to a dictionary.
        
        Returns:
            Dictionary representation of the message.
        """
        result = {
            "content": self.content,
            "role": self.role,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.metadata
        }
        
        if self.id is not None:
            result["id"] = self.id
            
        if self.conversation_id is not None:
            result["conversation_id"] = self.conversation_id
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        Create a message from a dictionary.
        
        Args:
            data: Dictionary representation of a message.
            
        Returns:
            New Message instance.
        """
        # Extract relevant fields with defaults
        content = data.get('content', '')
        role = data.get('role', 'assistant')
        timestamp = data.get('timestamp')
        metadata = data.get('metadata', {})
        msg_id = data.get('id')
        conversation_id = data.get('conversation_id')
        
        return cls(
            content=content,
            role=role,
            timestamp=timestamp,
            metadata=metadata,
            id=msg_id,
            conversation_id=conversation_id
        )
    
    def to_db_dict(self) -> Dict[str, Any]:
        """
        Convert to a dictionary suitable for database storage.
        
        Returns:
            Dictionary with fields prepared for database storage.
        """
        return {
            "content": self.content,
            "role": self.role,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": json.dumps(self.metadata),
            "conversation_id": self.conversation_id
        }
