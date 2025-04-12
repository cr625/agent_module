"""
Adapters for ProEthica's existing services.
"""

from typing import Dict, List, Any, Optional, Union

from flask import current_app
from flask_login import current_user

from app.models.world import World
from app.services.application_context_service import ApplicationContextService
from app.services.claude_service import ClaudeService
from app.services.llm_service import LLMService as ProethicaLLMService
from app.services.llm_service import Conversation as LegacyConversation
from app.services.llm_service import Message

from app.agent_module.adapters.base import LLMServiceAdapter
from app.agent_module.interfaces.base import SourceInterface, ContextProviderInterface
from app.agent_module.services.config_service import ConfigService


class ProEthicaSourceInterface(SourceInterface):
    """
    ProEthica implementation of the SourceInterface.
    Provides access to world guidelines and source materials.
    """
    
    def get_all_sources(self) -> List[Dict[str, Any]]:
        """
        Get all available sources.
        
        Returns:
            List of source objects with metadata
        """
        worlds = World.query.all()
        return [
            {
                'id': str(world.id),
                'name': world.name,
                'description': world.description,
                'type': 'world'
            }
            for world in worlds
        ]
    
    def get_guidelines(self, context_id: str) -> str:
        """
        Get guidelines for a specific world.
        
        Args:
            context_id: ID of the world to get guidelines for
            
        Returns:
            Guidelines text for the world
        """
        try:
            world_id = int(context_id)
            world = World.query.get(world_id)
            if world is None:
                return ""
            
            # Extract guidelines from the world
            if hasattr(world, 'guidelines') and world.guidelines:
                return world.guidelines
            
            # If no direct guidelines attribute, use the world description as a fallback
            if world.description:
                return f"# Guidelines for {world.name}\n\n{world.description}"
            
            return ""
        except (ValueError, TypeError):
            return ""
    
    def get_relevant_sources(self, query: str, context_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get sources relevant to a specific query and world.
        
        Args:
            query: Search query to find relevant sources
            context_id: ID of the world to get sources for
            limit: Maximum number of sources to return
            
        Returns:
            List of source objects with content and metadata
        """
        # This would typically use a search service or similar
        # For now, return an empty list as this requires integration with ProEthica's search
        return []
    
    def get_source_by_id(self, source_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific source by ID.
        
        Args:
            source_id: ID of the source to retrieve
            
        Returns:
            Source object with content and metadata, or None if not found
        """
        try:
            world_id = int(source_id)
            world = World.query.get(world_id)
            if world is None:
                return None
            
            return {
                'id': world.id,
                'name': world.name,
                'description': world.description,
                'ontology_source': world.ontology_source
            }
        except (ValueError, TypeError):
            return None


class ProEthicaContextProvider(ContextProviderInterface):
    """
    ProEthica implementation of the ContextProviderInterface.
    Provides access to contextual data from the ProEthica application.
    """
    
    def __init__(self):
        """Initialize the ProEthicaContextProvider."""
        self.app_context_service = ApplicationContextService.get_instance()
    
    def get_context_name(self, context_id: str, context_type: str) -> Optional[str]:
        """
        Get the human-readable name for a specific context.
        
        Args:
            context_id: ID of the context (e.g., world_id)
            context_type: Type of context (e.g., 'world')
            
        Returns:
            Human-readable name or None if not found
        """
        if context_type == 'world':
            try:
                world_id = int(context_id)
                world = World.query.get(world_id)
                return world.name if world else None
            except (ValueError, TypeError):
                return None
        return None
    
    def get_context_data(self, context_id: str, context_type: str) -> Dict[str, Any]:
        """
        Get additional data about a specific context.
        
        Args:
            context_id: ID of the context (e.g., world_id)
            context_type: Type of context (e.g., 'world')
            
        Returns:
            Dictionary with context data
        """
        if context_type == 'world':
            try:
                world_id = int(context_id)
                context = self.app_context_service.get_full_context(
                    world_id=world_id,
                    scenario_id=None,
                    query=None
                )
                return context
            except (ValueError, TypeError):
                return {}
        return {}
    
    def list_available_contexts(self, context_type: str) -> List[Dict[str, Any]]:
        """
        List all available contexts of a specific type.
        
        Args:
            context_type: Type of context (e.g., 'world')
            
        Returns:
            List of context objects with id, name, and metadata
        """
        if context_type == 'world':
            worlds = World.query.all()
            return [
                {
                    'id': str(world.id),
                    'name': world.name,
                    'description': world.description
                }
                for world in worlds
            ]
        return []
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current user.
        
        Returns:
            Dictionary with user information or None if not authenticated
        """
        if current_user and current_user.is_authenticated:
            return {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email
            }
        return None
        
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
        params = additional_params or {}
        try:
            world_id = int(source_id)
            context = self.app_context_service.get_full_context(
                world_id=world_id,
                scenario_id=params.get('scenario_id'),
                query=query
            )
            return context
        except (ValueError, TypeError):
            return {}
        
    def format_context(self, context: Dict[str, Any], max_tokens: Optional[int] = None) -> str:
        """
        Format context for LLM consumption.
        
        Args:
            context: Context dictionary from get_context
            max_tokens: Maximum number of tokens to include
            
        Returns:
            Formatted context string
        """
        return self.app_context_service.format_context_for_llm(context, max_tokens)
        
    def get_guidelines(self, source_id: str) -> str:
        """
        Get guidelines for a specific source.
        
        Args:
            source_id: ID of the source to get guidelines for
            
        Returns:
            Guidelines text for the source
        """
        try:
            world_id = int(source_id)
            world = World.query.get(world_id)
            if world is None:
                return ""
                
            # Extract guidelines from the world
            if hasattr(world, 'guidelines') and world.guidelines:
                return world.guidelines
            
            # If no direct guidelines attribute, use the world description as a fallback
            if world.description:
                return f"# Guidelines for {world.name}\n\n{world.description}"
                
            return ""
        except (ValueError, TypeError):
            return ""


class ProEthicaAdapter(LLMServiceAdapter):
    """
    Adapter for ProEthica's LLM services (Claude or LangChain).
    Provides a unified interface to both services.
    """
    
    def __init__(self, adapter_type: str, config_service: Optional[ConfigService] = None):
        """
        Initialize the ProEthica adapter.
        
        Args:
            adapter_type: Type of underlying service to use ("claude" or "langchain")
            config_service: Service for accessing configuration values
        """
        self.adapter_type = adapter_type
        self.config_service = config_service
        self.app_context_service = ApplicationContextService.get_instance()
        
        # Store conversation history
        self.conversation_history = []
        
        # Create the appropriate service
        if adapter_type == "claude":
            api_key = current_app.config.get("ANTHROPIC_API_KEY")
            self.service = ClaudeService(api_key=api_key)
        else:
            self.service = ProethicaLLMService()
    
    def send_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a message to the LLM service and get a response.
        
        Args:
            message: The message to send
            context: Optional context information (world, session data, etc.)
            
        Returns:
            Response from the LLM service
        """
        context = context or {}
        
        # Check if this is the new combined context format
        if 'conversation' in context:
            conversation_dict = context.get('conversation', {})
            # Extract the messages if available
            if 'messages' in conversation_dict:
                # Convert each message dict to the expected format for LegacyConversation
                message_list = []
                for msg in conversation_dict.get('messages', []):
                    # Ensure each message has the required 'role' and 'content' fields
                    if isinstance(msg, dict) and 'content' in msg:
                        message_list.append({
                            'role': msg.get('role', 'user'),
                            'content': msg.get('content', '')
                        })
                self.conversation_history = message_list
            
            world_id = context.get('source_id')
            # Get any pre-formatted context
            formatted_context = context.get('formatted_context')
        else:
            # Legacy format - old behavior
            world_id = context.get('world_id')
            formatted_context = None
        
        # Convert each dictionary message to a Message object
        message_objects = []
        for msg in self.conversation_history:
            if isinstance(msg, dict) and 'content' in msg:
                message_objects.append(
                    Message(
                        content=msg.get('content', ''),
                        role=msg.get('role', 'user')
                    )
                )
        
        # Create legacy conversation with Message objects
        legacy_conversation = LegacyConversation(messages=message_objects)
        
        # Get formatted application context if world_id is provided
        app_context = None
        if world_id:
            app_context_data = self.app_context_service.get_full_context(
                world_id=world_id,
                scenario_id=context.get('scenario_id'),
                query=message
            )
            app_context = self.app_context_service.format_context_for_llm(app_context_data)
        
        # Send message to service
        response = self.service.send_message_with_context(
            message=message,
            conversation=legacy_conversation,
            application_context=app_context,
            world_id=world_id
        )
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": response.content})
        
        # Return response
        return {
            "role": "assistant",
            "content": response.content
        }
    
    def generate_options(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate prompt options based on the current context.
        
        Args:
            context: Context information including world data, conversation history, etc.
            
        Returns:
            List of prompt option objects with id and text
        """
        # Check if this is the new combined context format
        if 'conversation' in context:
            conversation_dict = context.get('conversation', {})
            # Extract the messages if available
            if 'messages' in conversation_dict:
                # Convert each message dict to the expected format for LegacyConversation
                message_list = []
                for msg in conversation_dict.get('messages', []):
                    # Ensure each message has the required 'role' and 'content' fields
                    if isinstance(msg, dict) and 'content' in msg:
                        message_list.append({
                            'role': msg.get('role', 'user'),
                            'content': msg.get('content', '')
                        })
                self.conversation_history = message_list
            world_id = context.get('source_id')
        else:
            # Legacy format - old behavior
            world_id = context.get('world_id')
        
        # Convert each dictionary message to a Message object
        message_objects = []
        for msg in self.conversation_history:
            if isinstance(msg, dict) and 'content' in msg:
                message_objects.append(
                    Message(
                        content=msg.get('content', ''),
                        role=msg.get('role', 'user')
                    )
                )
        
        # Create legacy conversation with Message objects
        legacy_conversation = LegacyConversation(messages=message_objects)
        
        # Generate options
        options = self.service.get_prompt_options(
            conversation=legacy_conversation,
            world_id=world_id
        )
        
        # Convert to expected format
        return [{"id": i, "text": option} for i, option in enumerate(options)]
    
    def reset_conversation(self) -> None:
        """Reset the current conversation state."""
        self.conversation_history = []
    
    def get_name(self) -> str:
        """
        Get the name of this LLM service adapter.
        
        Returns:
            Name of the adapter
        """
        return self.adapter_type
