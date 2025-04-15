"""
Custom Claude adapter for a-proxy system.
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional

from anthropic import Anthropic
from agent_module.adapters.base import LLMServiceAdapter
from agent_module.services.config_service import ConfigService

logger = logging.getLogger(__name__)

class AProxyClaudeAdapter(LLMServiceAdapter):
    """
    Adapter for Claude API specifically for a-proxy.
    
    Implements the LLMServiceAdapter interface to provide
    seamless integration between a-proxy and Claude.
    """
    
    def __init__(self, adapter_type: str = "claude", config_service: Optional[ConfigService] = None):
        """
        Initialize the a-proxy Claude adapter.
        
        Args:
            adapter_type: Type of adapter (keeping for interface compatibility)
            config_service: Service for accessing configuration values
        """
        self.adapter_type = adapter_type
        self.config_service = config_service or ConfigService()
        
        # Get API key from config or environment
        self.api_key = self.config_service.get_value('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            logger.error("No Claude API key found in config or environment variables")
            raise ValueError("Anthropic API key is required")
            
        # Primary model to use
        self.model = self.config_service.get_value('CLAUDE_MODEL', 'claude-3-sonnet-20240229')
        
        # Fallback models to try if the primary model isn't available
        self.fallback_models = [
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307',
            'claude-2.1',
            'claude-2.0',
            'claude-instant-1.2'
        ]
        
        self.max_tokens = int(self.config_service.get_value('CLAUDE_MAX_TOKENS', 4096))
        
        # Initialize Anthropic client
        try:
            self.client = Anthropic(api_key=self.api_key)
            logger.info(f"Anthropic client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Anthropic client: {str(e)}")
            raise
            
        # Store conversation history
        self.conversation_history = []
        logger.info(f"AProxyClaudeAdapter initialized with primary model {self.model}")
    
    def send_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send a message to Claude and get a response.
        
        Args:
            message: The message to send
            context: Optional context information
            
        Returns:
            Response from Claude
        """
        context = context or {}
        
        # Process context information
        system_prompt = self._build_system_prompt(context)
        messages = self._prepare_messages(context)
        
        # Add current user message
        user_message = {"role": "user", "content": message}
        formatted_messages = messages + [user_message]
        
        logger.debug(f"Sending request to Claude API with system prompt: {system_prompt[:100]}...")
        
        # Try the primary model first, then fallbacks if needed
        models_to_try = [self.model] + [m for m in self.fallback_models if m != self.model]
        
        last_error = None
        for current_model in models_to_try:
            try:
                # Make request to Claude API using official client
                logger.debug(f"Attempting to use model: {current_model}")
                response = self.client.messages.create(
                    model=current_model,
                    system=system_prompt,
                    messages=formatted_messages,
                    max_tokens=self.max_tokens
                )
                
                # Success! Parse the response
                content = response.content[0].text
                
                # Update conversation history
                self.conversation_history.append(user_message)
                self.conversation_history.append({"role": "assistant", "content": content})
                
                # If this isn't our primary model, update it for future use
                if current_model != self.model:
                    logger.info(f"Switching primary model from {self.model} to {current_model}")
                    self.model = current_model
                
                logger.debug(f"Received response from Claude API: {content[:100]}...")
                return {
                    "role": "assistant",
                    "content": content
                }
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Error with model {current_model}: {error_msg}")
                last_error = error_msg
                
                # Check if this is a model-not-found error
                if "model" in error_msg.lower() and "not found" in error_msg.lower():
                    # Try the next model
                    continue
                elif "status code: 404" in error_msg.lower():
                    # Likely a model-not-found error, try next model
                    continue
                else:
                    # For other errors, we might want to stop trying
                    # But for now, we'll continue with fallbacks
                    pass
        
        # If we get here, all models failed
        logger.error(f"All Claude models failed. Last error: {last_error}")
        return {
            "role": "assistant",
            "content": f"I apologize, but I encountered an error processing your request. My team has been notified and will resolve this issue as soon as possible."
        }
    
    def generate_options(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate conversation suggestions based on the current context.
        
        Args:
            context: Context information
            
        Returns:
            List of suggestion objects with id and text
        """
        # Process context information
        system_prompt = self._build_system_prompt(context, for_suggestions=True)
        messages = self._prepare_messages(context)
        
        suggestion_prompt = "Generate 3 possible user messages that would be natural continuations of this conversation. Make them concise, diverse, and numbered (1-3)."
        
        # Format messages with the suggestion prompt
        formatted_messages = messages + [{"role": "user", "content": suggestion_prompt}]
        
        # Default suggestions in case all models fail
        default_suggestions = [
            {"id": 0, "text": "Tell me more about this topic"},
            {"id": 1, "text": "How does this relate to my current task?"},
            {"id": 2, "text": "Can you provide an example?"}
        ]
        
        # Try the primary model first, then fallbacks if needed
        models_to_try = [self.model] + [m for m in self.fallback_models if m != self.model]
        
        last_error = None
        for current_model in models_to_try:
            try:
                # Make request to Claude API using official client
                logger.debug(f"Attempting to generate suggestions with model: {current_model}")
                response = self.client.messages.create(
                    model=current_model,
                    system=system_prompt,
                    messages=formatted_messages,
                    max_tokens=200
                )
                
                # Success! Parse the response
                content = response.content[0].text
                
                # If this isn't our primary model, update it for future use
                if current_model != self.model:
                    logger.info(f"Switching primary model from {self.model} to {current_model}")
                    self.model = current_model
                
                # Parse suggestions from response
                suggestions = []
                for i, line in enumerate(content.strip().split('\n')):
                    if i >= 3:  # Limit to 3 suggestions
                        break
                    
                    # Clean up the line (remove numbers, etc.)
                    cleaned_line = line
                    if line.startswith(('1. ', '2. ', '3. ')):
                        cleaned_line = line[3:]
                    elif line.startswith(('1) ', '2) ', '3) ')):
                        cleaned_line = line[3:]
                    elif line.startswith(('- ')):
                        cleaned_line = line[2:]
                    
                    if cleaned_line:
                        suggestions.append({
                            "id": i,
                            "text": cleaned_line
                        })
                
                if suggestions:
                    logger.debug(f"Generated {len(suggestions)} suggestions from Claude")
                    return suggestions
                else:
                    # If we couldn't parse any suggestions, use defaults
                    return default_suggestions
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Error generating suggestions with model {current_model}: {error_msg}")
                last_error = error_msg
                
                # Check if this is a model-not-found error
                if "model" in error_msg.lower() and "not found" in error_msg.lower():
                    # Try the next model
                    continue
                elif "status code: 404" in error_msg.lower():
                    # Likely a model-not-found error, try next model
                    continue
                else:
                    # For other errors, we might want to stop trying
                    # But for now, we'll continue with fallbacks
                    pass
        
        # If we get here, all models failed
        logger.error(f"All Claude models failed for generating suggestions. Last error: {last_error}")
        return default_suggestions
    
    def reset_conversation(self) -> None:
        """Reset the current conversation state."""
        logger.debug("Resetting conversation history")
        self.conversation_history = []
    
    def get_name(self) -> str:
        """
        Get the name of this LLM service adapter.
        
        Returns:
            Name of the adapter
        """
        return self.adapter_type
    
    def _build_system_prompt(self, context: Dict[str, Any], for_suggestions: bool = False) -> str:
        """
        Build a system prompt from the context.
        
        Args:
            context: Context dictionary
            for_suggestions: Whether this is for generating suggestions
            
        Returns:
            Formatted system prompt string
        """
        system_prompt_parts = []
        
        # Extract persona context if available
        if 'persona' in context:
            persona = context.get('persona', {})
            if persona:
                persona_prompt = f"""
# Persona Context
Name: {persona.get('name', 'Unknown')}
Description: {persona.get('description', '')}
"""
                if 'traits' in persona and persona['traits']:
                    if isinstance(persona['traits'], list):
                        persona_prompt += f"Traits: {', '.join(persona['traits'])}\n"
                    elif isinstance(persona['traits'], str):
                        persona_prompt += f"Traits: {persona['traits']}\n"
                
                system_prompt_parts.append(persona_prompt)
        
        # Extract journey context if available
        if 'journey' in context:
            journey = context.get('journey', {})
            if journey:
                journey_prompt = f"""
# Journey Context
Name: {journey.get('name', 'Unknown')}
Description: {journey.get('description', '')}
Type: {journey.get('type', 'Unknown')}
"""
                system_prompt_parts.append(journey_prompt)
        
        # Extract waypoints if available
        if 'waypoints' in context:
            waypoints = context.get('waypoints', [])
            if waypoints:
                waypoints_prompt = "# Journey Waypoints\n"
                for i, wp in enumerate(waypoints[:5]):  # Limit to 5 most recent
                    waypoints_prompt += f"- {wp.get('title', 'Waypoint')}: {wp.get('notes', '')}\n"
                system_prompt_parts.append(waypoints_prompt)
        
        # Add conversation guidance
        if for_suggestions:
            system_prompt_parts.append(
                "You are generating suggested user messages to continue the conversation. "
                "Make these suggestions concise, diverse, and appropriate for the context."
            )
        else:
            system_prompt_parts.append(
                "You are a helpful assistant providing information and assistance. "
                "Respond in a natural conversational manner, being concise but thorough."
            )
        
        return "\n\n".join(system_prompt_parts)
    
    def _prepare_messages(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Prepare message history from context.
        
        Args:
            context: Context dictionary
            
        Returns:
            List of message dictionaries
        """
        # Check if this is the new combined context format
        if 'conversation' in context:
            conversation_dict = context.get('conversation', {})
            # Extract the messages if available
            if 'messages' in conversation_dict:
                message_list = conversation_dict.get('messages', [])
                # Validate and format messages
                formatted_messages = []
                for msg in message_list:
                    if isinstance(msg, dict) and 'content' in msg:
                        formatted_messages.append({
                            'role': msg.get('role', 'user'),
                            'content': msg.get('content', '')
                        })
                return formatted_messages
        
        # If we reached here, use the stored conversation history
        return self.conversation_history
