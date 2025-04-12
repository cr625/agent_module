"""
Base adapter interfaces and factories for LLM services.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Type

from app.agent_module.services.config_service import ConfigService

class LLMServiceAdapter(ABC):
    """
    Abstract base class for LLM service adapters.
    
    Adapters provide a unified interface to different LLM services
    (like Claude, OpenAI, etc.) to handle prompting, response generation,
    and context management.
    """
    
    @abstractmethod
    def send_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a message to the LLM service and get a response.
        
        Args:
            message: The message to send
            context: Optional context information (world, session data, etc.)
            
        Returns:
            Response from the LLM service
        """
        pass
    
    @abstractmethod
    def generate_options(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate prompt options based on the current context.
        
        Args:
            context: Context information including world data, conversation history, etc.
            
        Returns:
            List of prompt option objects with id and text
        """
        pass
    
    @abstractmethod
    def reset_conversation(self) -> None:
        """Reset the current conversation state."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get the name of this LLM service adapter.
        
        Returns:
            Name of the adapter
        """
        pass

class LLMServiceAdapterFactory(ABC):
    """
    Abstract factory for creating LLM service adapters.
    """
    
    @abstractmethod
    def create_adapter(self, adapter_type: str) -> LLMServiceAdapter:
        """
        Create an LLM service adapter of the specified type.
        
        Args:
            adapter_type: Type of adapter to create (e.g., "claude", "langchain")
            
        Returns:
            An implementation of LLMServiceAdapter
        """
        pass
    
    @abstractmethod
    def list_available_adapters(self) -> List[str]:
        """
        List all available adapter types.
        
        Returns:
            List of adapter type names
        """
        pass

class DefaultLLMServiceAdapterFactory(LLMServiceAdapterFactory):
    """
    Default implementation of LLMServiceAdapterFactory.
    
    This factory creates adapters based on configuration and available
    adapter implementations.
    """
    
    def __init__(self, config_service: Optional[ConfigService] = None):
        """
        Initialize the factory with configuration service.
        
        Args:
            config_service: Service for accessing configuration values
        """
        self.config_service = config_service or ConfigService()
        self._adapters = {}
    
    def register_adapter(self, name: str, adapter_class: Type[LLMServiceAdapter]) -> None:
        """
        Register an adapter class for a given name.
        
        Args:
            name: Name to register the adapter under
            adapter_class: Adapter class to instantiate
        """
        self._adapters[name] = adapter_class
    
    def create_adapter(self, adapter_type: str) -> LLMServiceAdapter:
        """
        Create an LLM service adapter of the specified type.
        
        Args:
            adapter_type: Type of adapter to create (e.g., "claude", "langchain")
            
        Returns:
            An implementation of LLMServiceAdapter
            
        Raises:
            ValueError: If adapter_type is not registered
        """
        # Default to use the existing ProEthica adapter for now
        try:
            from app.agent_module.adapters.proethica import ProEthicaAdapter
            return ProEthicaAdapter(adapter_type, self.config_service)
        except ImportError:
            raise ValueError(f"Adapter type {adapter_type} is not supported")
    
    def list_available_adapters(self) -> List[str]:
        """
        List all available adapter types.
        
        Returns:
            List of adapter type names
        """
        return ["claude", "langchain"]  # Default supported adapters
