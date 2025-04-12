"""
Service for managing and interacting with LLM service adapters.
"""

import logging
from typing import List, Dict, Any, Optional

from app.agent_module.adapters.base import LLMServiceAdapter, LLMServiceAdapterFactory
from app.agent_module.services.config_service import ConfigService

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for managing and interacting with LLM service adapters.
    
    This service provides a unified interface to different LLM backend services
    (like Claude, OpenAI, etc.) through adapters. It handles adapter selection,
    message sending, and context management.
    """
    
    def __init__(
        self, 
        adapter_factory: LLMServiceAdapterFactory,
        config_service: Optional[ConfigService] = None
    ):
        """
        Initialize the LLM service.
        
        Args:
            adapter_factory: Factory for creating LLM service adapters
            config_service: Service for accessing configuration values
        """
        self.adapter_factory = adapter_factory
        self.config_service = config_service or ConfigService()
        self.default_adapter_type = self.config_service.get_value(
            'default_llm_service', 'claude'
        )
        self._active_adapter = None
        
    def get_adapter(self, adapter_type: Optional[str] = None) -> LLMServiceAdapter:
        """
        Get or create an LLM service adapter.
        
        Args:
            adapter_type: Type of adapter to get (e.g., "claude", "langchain")
                          If None, uses the default adapter
                          
        Returns:
            An implementation of LLMServiceAdapter
        """
        adapter_type = adapter_type or self.default_adapter_type
        
        if self._active_adapter is None or self._active_adapter.get_name() != adapter_type:
            self._active_adapter = self.adapter_factory.create_adapter(adapter_type)
            
        return self._active_adapter
    
    def send_message(
        self, 
        message: str,
        conversation: Dict[str, Any], 
        context: Optional[str] = None,
        source_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to the LLM service and get a response.
        
        Args:
            message: The message to send
            conversation: Conversation dictionary
            context: Optional context information
            source_id: Optional source ID
            
        Returns:
            Response from the LLM service
        """
        # Create a combined context from conversation and source_id
        combined_context = {
            "conversation": conversation,
            "source_id": source_id
        }
        
        # Add formatted context if provided
        if context:
            combined_context["formatted_context"] = context
        
        adapter = self.get_adapter()
        return adapter.send_message(message, combined_context)
    
    def generate_options(
        self, 
        context: Dict[str, Any],
        adapter_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate prompt options based on the current context.
        
        Args:
            context: Context information including world data, conversation history, etc.
            adapter_type: Type of adapter to use (if different from current)
            
        Returns:
            List of prompt option objects with id and text
        """
        adapter = self.get_adapter(adapter_type)
        return adapter.generate_options(context)
    
    def reset_conversation(self, adapter_type: Optional[str] = None) -> None:
        """
        Reset the current conversation state.
        
        Args:
            adapter_type: Type of adapter to reset (if different from current)
        """
        adapter = self.get_adapter(adapter_type)
        adapter.reset_conversation()
    
    def list_available_services(self) -> List[str]:
        """
        List all available LLM services.
        
        Returns:
            List of service names
        """
        return self.adapter_factory.list_available_adapters()
    
    def get_suggestions(self, conversation: Dict[str, Any], 
                     source_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Alias for generate_options to maintain compatibility with agent blueprint.
        
        Args:
            conversation: Conversation dictionary
            source_id: Optional source ID
            
        Returns:
            List of suggestion objects
        """
        return self.generate_options(conversation, source_id)
    
    def switch_service(self, adapter_type: str) -> None:
        """
        Switch to a different LLM service.
        
        Args:
            adapter_type: Type of adapter to switch to
        """
        self._active_adapter = None  # Force creation of new adapter
        self.get_adapter(adapter_type)
