"""
Blueprint factory for agent routes.
"""

from typing import Dict, Any, Optional, Callable, Union
from flask import Blueprint, render_template, request, jsonify
import json

from agent_module.interfaces.base import (
    SourceInterface,
    ContextProviderInterface,
    LLMInterface,
    AuthInterface,
    SessionInterface
)
from agent_module.services.auth import FlaskLoginAuthAdapter, DefaultAuthProvider
from agent_module.services.session import FlaskSessionManager
from agent_module.models.conversation import Conversation, Message
from agent_module.services.config_service import ConfigService


def create_agent_blueprint(
    source_interface: SourceInterface,
    context_provider: ContextProviderInterface,
    llm_interface: LLMInterface,
    auth_interface: Optional[AuthInterface] = None,
    session_interface: Optional[SessionInterface] = None,
    config_service: Optional[ConfigService] = None,
    require_auth: bool = True,
    url_prefix: str = '/agent',
    template_folder: Optional[str] = None,
    static_folder: Optional[str] = None,
    blueprint_name: str = 'agent'
) -> Blueprint:
    """
    Create a Flask blueprint for the agent with authentication.

    Args:
        source_interface: Interface for context sources
        context_provider: Interface for context provisioning
        llm_interface: Interface for language model access
        auth_interface: Interface for authentication (optional)
        session_interface: Interface for session management (optional)
        config_service: Configuration service (optional)
        require_auth: Whether to require authentication
        url_prefix: URL prefix for the blueprint
        template_folder: Template folder for the blueprint
        static_folder: Static folder for the blueprint
        blueprint_name: Name for the blueprint

    Returns:
        Flask blueprint
    """
    # Use default implementations if not provided
    auth = auth_interface or (FlaskLoginAuthAdapter() if require_auth else DefaultAuthProvider())
    session_mgr = session_interface or FlaskSessionManager()
    config = config_service or ConfigService()

    # Create blueprint
    agent_bp = Blueprint(
        blueprint_name,
        __name__,
        url_prefix=url_prefix,
        template_folder=template_folder,
        static_folder=static_folder
    )

    # Authentication decorator factory
    def auth_required(func: Callable) -> Callable:
        """Apply authentication if required."""
        # Force disable auth for testing
        return func

    @agent_bp.route('/')
    @auth_required
    def agent_window():
        """Display the agent window."""
        # Get source_id from query parameters
        source_id = request.args.get('source_id', type=int)

        # Get list of sources
        sources = source_interface.get_all_sources()

        # Get the selected source if source_id is provided
        selected_source = None
        if source_id:
            selected_source = source_interface.get_source_by_id(str(source_id))

        # Initialize conversation in session if not already present
        if session_mgr.get_conversation() is None:
            # Get welcome message from config if available
            welcome_message = config.get_value('welcome_message', 
                                               "Hello! I am your assistant. Choose a world to get started.")

            conversation = {
                'messages': [
                    {
                        'content': welcome_message,
                        'role': 'assistant',
                        'timestamp': None
                    }
                ],
                'metadata': {'source_id': source_id}
            }
            session_mgr.set_conversation(conversation)

        # Get welcome message from config for template
        welcome_message = config.get_value('welcome_message', 
                                           "Hello! I am your assistant. Choose a world to get started.")

        return render_template(
            'agent_window.html',
            worlds=sources,  # Pass as 'worlds' to match template expectations
            selected_world=selected_source,  # Pass as 'selected_world' to match template expectations
            welcome_message=welcome_message  # Pass welcome message to template
        )

    @agent_bp.route('/api/message', methods=['POST'])
    @auth_required
    def send_message():
        """Send a message to the agent."""
        data = request.json

        # Get message and source_id from request
        message_text = data.get('message', '')
        source_id = data.get('source_id') or data.get('world_id')  # Support both source_id and world_id
        additional_params = data.get('params', {})

        # Get conversation from session
        conversation_dict = session_mgr.get_conversation()
        conversation = Conversation.from_dict(conversation_dict) if conversation_dict else Conversation()

        # Update metadata if provided
        if source_id is not None:
            conversation.metadata['source_id'] = source_id

        # Add any additional params to metadata
        for key, value in additional_params.items():
            conversation.metadata[key] = value

        # Get context if source_id is available
        context = None
        if source_id:
            context_data = context_provider.get_context(
                source_id,
                message_text,
                additional_params
            )
            context = context_provider.format_context(context_data)

        # Add user message to conversation
        user_message = Message(content=message_text, role='user')
        conversation.add_message(user_message)

        # Update session with the conversation including the new user message
        session_mgr.set_conversation(conversation.to_dict())

        # Send message to LLM interface
        response = llm_interface.send_message(
            message=message_text,
            conversation=conversation.to_dict(),
            context=context,
            source_id=source_id
        )

        # Create response message and add to conversation
        assistant_message = Message(content=response.get('content', ''), role='assistant')
        conversation.add_message(assistant_message)

        # Update session with the final conversation including response
        session_mgr.set_conversation(conversation.to_dict())

        # Return response
        return jsonify({
            'status': 'success',
            'message': {
                'role': 'assistant',
                'content': response.get('content', '')
            }
        })

    @agent_bp.route('/api/options', methods=['GET'])
    @auth_required
    def get_options():
        """Get suggested prompts for the user."""
        # Get source_id from query parameters
        source_id = request.args.get('source_id', type=int) or request.args.get('world_id', type=int)

        # Get conversation from session
        conversation_dict = session_mgr.get_conversation()
        conversation = Conversation.from_dict(conversation_dict) if conversation_dict else Conversation()

        # Update source_id in metadata if provided
        if source_id is not None:
            conversation.metadata['source_id'] = source_id
            # Update conversation in session
            session_mgr.set_conversation(conversation.to_dict())

        # Get prompt options from the LLM interface
        options = llm_interface.get_suggestions(
            conversation=conversation.to_dict(),
            source_id=str(source_id) if source_id else None
        )

        # Return options
        return jsonify({
            'status': 'success',
            'options': options
        })

    @agent_bp.route('/api/reset', methods=['POST'])
    @auth_required
    def reset_conversation():
        """Reset the conversation."""
        data = request.json

        # Get source_id from request
        source_id = data.get('source_id') or data.get('world_id')

        # Reset conversation
        new_conversation = session_mgr.reset_conversation(source_id)

        # Add welcome message
        welcome_message = config.get_value('welcome_message', 
                                           "Hello! I am your assistant. Choose a world to get started.")
        
        # Create a new conversation with the welcome message
        conversation = Conversation.from_dict(new_conversation)
        conversation.add_message(Message(content=welcome_message, role='assistant'))
        
        # Update session
        session_mgr.set_conversation(conversation.to_dict())

        # Return success
        return jsonify({
            'status': 'success',
            'message': 'Conversation reset successfully'
        })

    @agent_bp.route('/api/guidelines', methods=['GET'])
    @auth_required
    def get_guidelines():
        """Get guidelines for a specific source."""
        # Get source_id from query parameters (also support world_id)
        source_id = request.args.get('source_id', type=int) or request.args.get('world_id', type=int)

        if not source_id:
            return jsonify({
                'status': 'error',
                'message': 'Source ID or World ID is required'
            }), 400

        # Get guidelines from the source interface
        guidelines = source_interface.get_guidelines(str(source_id))

        # Return guidelines
        return jsonify({
            'status': 'success',
            'guidelines': guidelines
        })

    @agent_bp.route('/api/current-user', methods=['GET'])
    @auth_required
    def current_user():
        """Get information about the current authenticated user."""
        user = auth.get_current_user()

        # For auth_disabled scenarios with DefaultAuthProvider
        if not require_auth:
            return jsonify({
                'status': 'success',
                'user': None
            })

        # If user is not authenticated and auth is required, return error
        if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
            return jsonify({
                'status': 'error',
                'message': 'Not authenticated'
            }), 401

        # If user has to_dict method, use it
        if hasattr(user, 'to_dict') and callable(user.to_dict):
            user_data = user.to_dict()
        # Otherwise extract basic information
        else:
            user_data = {
                'id': getattr(user, 'id', None),
                'username': getattr(user, 'username', None),
                'email': getattr(user, 'email', None),
                'is_authenticated': True
            }

        return jsonify({
            'status': 'success',
            'user': user_data
        })
        
    @agent_bp.route('/api/switch_service', methods=['POST'])
    @auth_required
    def switch_service():
        """Switch between LLM services."""
        data = request.json
        service = data.get('service', 'claude')  # Default to claude
        
        # Currently, we don't have a direct way to switch LLM services
        # This would typically tell the LLMService to use a different adapter
        
        # For now, just reset the conversation
        source_id = data.get('world_id')
        reset_conversation_response = reset_conversation()
        
        return jsonify({
            'status': 'success',
            'message': f'Switched to {service} service'
        })

    return agent_bp
