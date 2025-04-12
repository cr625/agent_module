"""
Base session management implementations for the agent module.
"""

from typing import Optional, Dict, Any

from flask import session

from app.agent_module.interfaces.base import SessionInterface


class FlaskSessionManager(SessionInterface):
    """
    Session manager that uses Flask's session for storage.
    """
    
    def __init__(self, session_key: str = 'agent_conversation'):
        """
        Initialize the Flask session manager.
        
        Args:
            session_key: Key to use for storing conversation in session
        """
        self.session_key = session_key
    
    def get_conversation(self) -> Optional[Dict[str, Any]]:
        """
        Get the current conversation from session.
        
        Returns:
            Conversation dictionary or None if not present
        """
        return session.get(self.session_key)
    
    def set_conversation(self, conversation: Dict[str, Any]) -> None:
        """
        Set the current conversation in session.
        
        Args:
            conversation: Conversation dictionary
        """
        session[self.session_key] = conversation
    
    def reset_conversation(self, source_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Reset the current conversation.
        
        Args:
            source_id: Optional source ID to initialize the conversation with
            
        Returns:
            New conversation dictionary
        """
        # Create a new conversation with metadata including source_id if provided
        metadata = {}
        if source_id:
            metadata['source_id'] = source_id
            
        # New conversation with empty messages and metadata
        new_conversation = {
            'messages': [],
            'metadata': metadata
        }
        
        # Store in session
        self.set_conversation(new_conversation)
        
        return new_conversation
