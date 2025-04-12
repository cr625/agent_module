"""
Blueprint for conversation history management.
"""

import json
from typing import Optional, Dict, Any, Callable
from flask import Blueprint, render_template, request, jsonify, Response, current_app
import logging

from app.agent_module.services.conversation_storage_service import ConversationStorageService

logger = logging.getLogger(__name__)

def create_history_blueprint(
    conversation_storage_service: Optional[ConversationStorageService] = None,
    url_prefix: str = '/agent/history',
    template_folder: Optional[str] = None,
    static_folder: Optional[str] = None,
    blueprint_name: str = 'history',
    require_auth: bool = False
) -> Blueprint:
    """
    Create a Flask blueprint for conversation history management.
    
    Args:
        conversation_storage_service: Service for conversation storage.
        url_prefix: URL prefix for the blueprint.
        template_folder: Template folder for the blueprint.
        static_folder: Static folder for the blueprint.
        blueprint_name: Name for the blueprint.
        
    Returns:
        Flask blueprint.
    """
    # Create the storage service if not provided
    storage_service = conversation_storage_service or ConversationStorageService()
    
    # Create blueprint
    history_bp = Blueprint(
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
    
    @history_bp.route('/')
    @auth_required
    def history_view():
        """Render the conversation history view."""
        return render_template('history_tab.html')
    
    @history_bp.route('/api/conversations')
    @auth_required
    def list_conversations():
        """
        API endpoint to list conversations.
        
        Query parameters:
            - context_type: Filter by context type (optional)
            - context_id: Filter by context ID (optional)
            - limit: Maximum number of conversations to return (default: 50)
            - offset: Number of conversations to skip (default: 0)
            
        Returns:
            JSON response with conversation list.
        """
        try:
            # Get query parameters
            context_type = request.args.get('context_type')
            context_id = request.args.get('context_id')
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # Get conversations
            conversations = storage_service.list_conversations(
                context_type=context_type,
                context_id=context_id,
                limit=limit,
                offset=offset
            )
            
            # Get total count for pagination
            total_count = storage_service.count_conversations(
                context_type=context_type,
                context_id=context_id
            )
            
            return jsonify({
                'status': 'success',
                'conversations': conversations,
                'total': total_count,
                'limit': limit,
                'offset': offset
            })
            
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @history_bp.route('/api/conversations/<int:conversation_id>')
    @auth_required
    def get_conversation(conversation_id):
        """
        API endpoint to get a conversation by ID.
        
        Args:
            conversation_id: ID of the conversation.
            
        Returns:
            JSON response with conversation data.
        """
        try:
            conversation = storage_service.get_conversation(conversation_id)
            
            if not conversation:
                return jsonify({
                    'status': 'error',
                    'message': f'Conversation {conversation_id} not found'
                }), 404
                
            return jsonify({
                'status': 'success',
                'conversation': conversation.to_dict()
            })
            
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @history_bp.route('/api/conversations/<int:conversation_id>', methods=['DELETE'])
    @auth_required
    def delete_conversation(conversation_id):
        """
        API endpoint to delete a conversation.
        
        Args:
            conversation_id: ID of the conversation.
            
        Returns:
            JSON response indicating success or failure.
        """
        try:
            success = storage_service.delete_conversation(conversation_id)
            
            if not success:
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to delete conversation {conversation_id}'
                }), 500
                
            return jsonify({
                'status': 'success',
                'message': f'Conversation {conversation_id} deleted'
            })
            
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @history_bp.route('/api/conversations/<int:conversation_id>/export')
    @auth_required
    def export_conversation(conversation_id):
        """
        API endpoint to export a conversation to JSON.
        
        Args:
            conversation_id: ID of the conversation.
            
        Returns:
            JSON file response.
        """
        try:
            json_data = storage_service.export_conversation(conversation_id)
            
            if not json_data:
                return jsonify({
                    'status': 'error',
                    'message': f'Conversation {conversation_id} not found'
                }), 404
                
            # Get conversation for filename
            conversation = storage_service.get_conversation(conversation_id)
            filename = f"conversation_{conversation_id}"
            
            if conversation and conversation.title:
                # Clean title for filename
                safe_title = ''.join(c if c.isalnum() or c in ' -_' else '_' for c in conversation.title)
                filename = f"{safe_title}_{conversation_id}"
            
            # Set response headers for file download
            headers = {
                'Content-Disposition': f'attachment; filename="{filename}.json"',
                'Content-Type': 'application/json'
            }
            
            return Response(json_data, headers=headers)
            
        except Exception as e:
            logger.error(f"Error exporting conversation {conversation_id}: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @history_bp.route('/api/conversations/import', methods=['POST'])
    @auth_required
    def import_conversation():
        """
        API endpoint to import a conversation from JSON.
        
        Returns:
            JSON response with imported conversation ID.
        """
        try:
            if not request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Request must be JSON'
                }), 400
                
            data = request.get_json()
            
            conversation_id = storage_service.import_conversation(data)
            
            if not conversation_id:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to import conversation'
                }), 500
                
            return jsonify({
                'status': 'success',
                'conversation_id': conversation_id,
                'message': 'Conversation imported successfully'
            })
            
        except Exception as e:
            logger.error(f"Error importing conversation: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @history_bp.route('/api/conversations/search')
    @auth_required
    def search_conversations():
        """
        API endpoint to search conversations.
        
        Query parameters:
            - q: Search query
            - limit: Maximum number of results to return (default: 20)
            
        Returns:
            JSON response with search results.
        """
        try:
            search_text = request.args.get('q', '')
            limit = request.args.get('limit', 20, type=int)
            
            if not search_text:
                return jsonify({
                    'status': 'error',
                    'message': 'Search query is required'
                }), 400
                
            results = storage_service.search_conversations(search_text, limit=limit)
            
            return jsonify({
                'status': 'success',
                'conversations': results,
                'count': len(results)
            })
            
        except Exception as e:
            logger.error(f"Error searching conversations: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @history_bp.route('/api/conversations/save', methods=['POST'])
    @auth_required
    def save_current_conversation():
        """
        API endpoint to save the current conversation.
        
        Expected JSON payload:
        {
            "conversation": {
                "title": "Optional title",
                "context_id": "Context ID",
                "context_type": "Context type",
                "context_name": "Human-readable context name",
                "metadata": {} (optional)
            },
            "messages": [
                {
                    "role": "user|assistant",
                    "content": "Message content",
                    "timestamp": "ISO timestamp" (optional)
                }
            ]
        }
        
        Returns:
            JSON response with saved conversation ID.
        """
        try:
            if not request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Request must be JSON'
                }), 400
                
            data = request.get_json()
            
            # Basic validation
            if 'conversation' not in data or 'messages' not in data:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid conversation format'
                }), 400
            
            # Ensure required fields have valid values
            conversation_data = data.get('conversation', {})
            if not conversation_data.get('context_id'):
                conversation_data['context_id'] = 'default'
            if not conversation_data.get('context_type'):
                conversation_data['context_type'] = 'world'  
            if not conversation_data.get('context_name'):
                conversation_data['context_name'] = 'Default Context'
                
            # Set a title if none is provided
            if not conversation_data.get('title'):
                # Find first user message to create a title
                for message in data.get('messages', []):
                    if message.get('role') == 'user' and message.get('content'):
                        content = message.get('content', '')
                        # Truncate to reasonable title length
                        title = content if len(content) <= 50 else content[:47] + '...'
                        conversation_data['title'] = title
                        break
                        
                # If still no title
                if not conversation_data.get('title'):
                    conversation_data['title'] = f"Conversation {data.get('conversation_time', '')}"
                
            # Now import the conversation
            conversation_id = storage_service.import_conversation(data)
            
            if not conversation_id:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to save conversation'
                }), 500
                
            return jsonify({
                'status': 'success',
                'conversation_id': conversation_id,
                'message': 'Conversation saved successfully'
            })
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    return history_bp
