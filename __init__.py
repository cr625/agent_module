"""
Agent module for conversation agents.
"""

import os
from typing import Dict, Any, Optional
from flask import Flask

from app.agent_module.adapters.base import LLMServiceAdapterFactory
from app.agent_module.blueprints.agent import create_agent_blueprint
from app.agent_module.blueprints.history import create_history_blueprint
from app.agent_module.interfaces.base import SourceInterface, ContextProviderInterface
from app.agent_module.services.config_service import ConfigService
from app.agent_module.services.database_service import DatabaseService
from app.agent_module.services.conversation_storage_service import ConversationStorageService

# Set version
__version__ = '0.2.0'

def create_agent_module(
    app: Flask, 
    source_interface: SourceInterface,
    context_provider: ContextProviderInterface,
    adapter_factory: Optional[LLMServiceAdapterFactory] = None,
    config_override: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None
) -> None:
    """
    Create and register agent module components with the Flask app.
    
    Args:
        app: Flask application
        source_interface: Interface for source management
        context_provider: Interface for context provisioning
        adapter_factory: Factory for creating LLM service adapters (optional)
        config_override: Configuration overrides (optional)
        db_path: Path to SQLite database file (optional)
    """
    # Create config service
    config_service = ConfigService(config_override)
    
    # Create adapter factory if not provided
    if adapter_factory is None:
        from app.agent_module.adapters.base import DefaultLLMServiceAdapterFactory
        adapter_factory = DefaultLLMServiceAdapterFactory(config_service=config_service)
    
    # Create LLM interface
    from app.agent_module.services.llm_service import LLMService
    llm_service = LLMService(adapter_factory, config_service=config_service)
    
    # Create database service and conversation storage
    db_service = DatabaseService(db_path)
    conversation_storage = ConversationStorageService(db_service)
    
    # Create agent blueprint
    agent_blueprint = create_agent_blueprint(
        source_interface=source_interface,
        context_provider=context_provider,
        llm_interface=llm_service,
        config_service=config_service
    )
    
    # Create history blueprint
    history_blueprint = create_history_blueprint(
        conversation_storage_service=conversation_storage,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates')  # Use absolute path to templates
    )
    
    # Register blueprints
    app.register_blueprint(agent_blueprint)
    app.register_blueprint(history_blueprint)

# For backward compatibility with the existing ProEthica application
def create_proethica_agent_blueprint(
    config: Dict[str, Any] = None, 
    config_override: Dict[str, Any] = None,
    url_prefix: str = None
):
    """
    Create an agent blueprint for the ProEthica application.
    This is maintained for backward compatibility.
    
    Args:
        config: Configuration for the ProEthica adapter
        config_override: Configuration overrides for agent module
        url_prefix: URL prefix for the blueprint
        
    Returns:
        Flask blueprint
    """
    from app.agent_module.adapters.proethica import ProEthicaSourceInterface, ProEthicaContextProvider
    from app.agent_module.services.config_service import ConfigService
    from app.agent_module.adapters.base import DefaultLLMServiceAdapterFactory
    from app.agent_module.services.llm_service import LLMService
    
    # Create interfaces
    source_interface = ProEthicaSourceInterface()
    context_provider = ProEthicaContextProvider()
    
    # Create config service with overrides
    config_service = ConfigService(config_path=None, config_override=config_override)
    
    # Create adapter factory
    adapter_factory = DefaultLLMServiceAdapterFactory(config_service=config_service)
    
    # Create LLM service
    llm_service = LLMService(adapter_factory, config_service=config_service)
    
    # Create and return agent blueprint
    return create_agent_blueprint(
        source_interface=source_interface,
        context_provider=context_provider,
        llm_interface=llm_service,
        config_service=config_service,
        url_prefix=url_prefix
    )

# For backward compatibility with the existing ProEthica application
def create_proethica_history_blueprint(
    db_path: Optional[str] = None,
    url_prefix: str = '/agent/history'
):
    """
    Create a history blueprint for the ProEthica application.
    This is maintained for backward compatibility.
    
    Args:
        db_path: Path to SQLite database file (optional)
        url_prefix: URL prefix for the blueprint
        
    Returns:
        Flask blueprint
    """
    from app.agent_module.services.database_service import DatabaseService
    from app.agent_module.services.conversation_storage_service import ConversationStorageService
    from app.agent_module.blueprints.history import create_history_blueprint
    
    # Create services
    db_service = DatabaseService(db_path)
    conversation_storage = ConversationStorageService(db_service)
    
    # Create and return history blueprint
    return create_history_blueprint(
        conversation_storage_service=conversation_storage,
        url_prefix=url_prefix,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates')  # Use absolute path to templates
    )
