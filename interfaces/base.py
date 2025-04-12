"""
Base interfaces for agent module integration with parent applications.

These interfaces define the contract between the agent module and
the parent application to allow flexible integration.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Union

class SourceInterface(ABC):
    """
    Interface for source material access.
    
    This interface provides methods to access source materials like
    guidelines, cases, etc. from the parent application.
    """
    
    @abstractmethod
    def get_guidelines(self, context_id: str) -> str:
        """
        Get guidelines text for a specific context.
        
        Args:
            context_id: ID of the context (e.g., world_id, persona_id)
            
        Returns:
            Guidelines text as a string
        """
        pass
    
    @abstractmethod
    def get_relevant_sources(self, query: str, context_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get sources relevant to a specific query and context.
        
        Args:
            query: Search query to find relevant sources
            context_id: ID of the context (e.g., world_id, persona_id)
            limit: Maximum number of sources to return
            
        Returns:
            List of source objects with content and metadata
        """
        pass
    
    @abstractmethod
    def get_source_by_id(self, source_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific source by ID.
        
        Args:
            source_id: ID of the source to retrieve
            
        Returns:
            Source object with content and metadata, or None if not found
        """
        pass
    
    @abstractmethod
    def get_all_sources(self) -> List[Dict[str, Any]]:
        """
        Get all available sources.
        
        Returns:
            List of source objects with metadata
        """
        pass

class ContextProviderInterface(ABC):
    """
    Interface for context data access.
    
    This interface provides methods to access contextual data
    from the parent application, such as user information, current state, etc.
    """
    
    @abstractmethod
    def get_context_name(self, context_id: str, context_type: str) -> Optional[str]:
        """
        Get the human-readable name for a specific context.
        
        Args:
            context_id: ID of the context (e.g., world_id, persona_id)
            context_type: Type of context (e.g., 'world', 'persona')
            
        Returns:
            Human-readable name or None if not found
        """
        pass
    
    @abstractmethod
    def get_context_data(self, context_id: str, context_type: str) -> Dict[str, Any]:
        """
        Get additional data about a specific context.
        
        Args:
            context_id: ID of the context (e.g., world_id, persona_id)
            context_type: Type of context (e.g., 'world', 'persona')
            
        Returns:
            Dictionary with context data
        """
        pass
    
    @abstractmethod
    def list_available_contexts(self, context_type: str) -> List[Dict[str, Any]]:
        """
        List all available contexts of a specific type.
        
        Args:
            context_type: Type of context (e.g., 'world', 'persona')
            
        Returns:
            List of context objects with id, name, and metadata
        """
        pass
    
    @abstractmethod
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current user.
        
        Returns:
            Dictionary with user information or None if not authenticated
        """
        pass
        
    @abstractmethod
    def get_context(self, source_id: str, query: Optional[str] = None, 
                   additional_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get context for a specific source and query.
        
        Args:
            source_id: ID of the source to get context for
            query: Optional query to focus the context
            additional_params: Optional additional parameters for the context
            
        Returns:
            Dictionary containing context information
        """
        pass
        
    @abstractmethod
    def format_context(self, context: Dict[str, Any], max_tokens: Optional[int] = None) -> str:
        """
        Format context for LLM consumption.
        
        Args:
            context: Context dictionary from get_context
            max_tokens: Maximum number of tokens to include
            
        Returns:
            Formatted context string
        """
        pass
        
    @abstractmethod
    def get_guidelines(self, source_id: str) -> str:
        """
        Get guidelines for a specific source.
        
        Args:
            source_id: ID of the source to get guidelines for
            
        Returns:
            Guidelines text for the source
        """
        pass

class LLMInterface(ABC):
    """
    Interface for language model interactions.
    
    This interface provides methods to interact with language models
    for generating responses, suggestions, etc.
    """
    
    @abstractmethod
    def send_message(self, message: str, conversation: Dict[str, Any], 
                     context: Optional[str] = None, source_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a message to the language model.
        
        Args:
            message: User message
            conversation: Conversation dictionary
            context: Optional context information
            source_id: Optional source ID
            
        Returns:
            Message response object
        """
        pass
    
    @abstractmethod
    def get_suggestions(self, conversation: Dict[str, Any], 
                        source_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get suggested prompts based on conversation history.
        
        Args:
            conversation: Conversation dictionary
            source_id: Optional source ID
            
        Returns:
            List of suggestion objects
        """
        pass

class AuthInterface(ABC):
    """
    Interface for authentication and authorization.
    
    This interface provides methods to handle user authentication
    and authorization for protected routes.
    """
    
    @abstractmethod
    def login_required(self, func: Callable) -> Callable:
        """
        Decorator to require authentication for a route.
        
        Args:
            func: Route function to protect
            
        Returns:
            Decorated function
        """
        pass
    
    @abstractmethod
    def get_current_user(self) -> Optional[Any]:
        """
        Get the current authenticated user.
        
        Returns:
            Current user object or None if not authenticated
        """
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        """
        Check if the current user is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        pass

class SessionInterface(ABC):
    """
    Interface for session management.
    
    This interface provides methods to manage session state,
    including conversation history.
    """
    
    @abstractmethod
    def get_conversation(self) -> Optional[Dict[str, Any]]:
        """
        Get the current conversation from session.
        
        Returns:
            Conversation dictionary or None if not present
        """
        pass
    
    @abstractmethod
    def set_conversation(self, conversation: Dict[str, Any]) -> None:
        """
        Set the current conversation in session.
        
        Args:
            conversation: Conversation dictionary
        """
        pass
    
    @abstractmethod
    def reset_conversation(self, source_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Reset the current conversation.
        
        Args:
            source_id: Optional source ID to initialize the conversation with
            
        Returns:
            New conversation dictionary
        """
        pass
