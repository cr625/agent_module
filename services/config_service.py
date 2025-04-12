"""
Configuration service for agent module adapters.
"""

import os
import json
from typing import Dict, Any, Optional, Union, TypeVar, Generic

# Generic type for default value
T = TypeVar('T')

class ConfigService:
    """
    Service for managing adapter configurations.
    
    This service loads default configurations and allows overriding
    from user-provided configuration files or direct overrides.
    """
    
    def __init__(self, 
                 config_path: Optional[str] = None, 
                 config_override: Optional[Dict[str, Any]] = None):
        """
        Initialize the ConfigService.
        
        Args:
            config_path: Path to custom configuration file (optional)
            config_override: Direct configuration override dictionary (optional)
        """
        self.config_path = config_path
        self.config_override = config_override or {}
        
        # Load configurations
        self.default_config = self._load_default_config()
        self.user_config = self._load_user_config() if config_path else {}
        
    def _load_default_config(self) -> Dict[str, Any]:
        """
        Load default configuration from package files.
        
        Returns:
            Default configuration dictionary
        """
        result = {
            "adapter_defaults": {},
            "prompt_templates": {},
            "settings": {
                "default_llm_service": "claude"
            }
        }
        
        try:
            # Get the directory of this file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Load adapter defaults
            defaults_path = os.path.join(base_dir, "config", "defaults", "adapter_defaults.json")
            if os.path.exists(defaults_path):
                with open(defaults_path, 'r') as f:
                    result["adapter_defaults"] = json.load(f)
            
            # Load prompt templates
            templates_path = os.path.join(base_dir, "config", "defaults", "prompt_templates.json")
            if os.path.exists(templates_path):
                with open(templates_path, 'r') as f:
                    result["prompt_templates"] = json.load(f)
                    
        except Exception as e:
            print(f"Error loading default configuration: {str(e)}")
        
        return result
    
    def _load_user_config(self) -> Dict[str, Any]:
        """
        Load user configuration from provided path.
        
        Returns:
            User configuration dictionary
        """
        if not self.config_path or not os.path.exists(self.config_path):
            return {}
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading user configuration from {self.config_path}: {str(e)}")
            return {}
    
    def _deep_merge(self, source: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries, with override values taking precedence.
        
        Args:
            source: Source dictionary
            override: Override dictionary
            
        Returns:
            Merged dictionary
        """
        result = source.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge(result[key], value)
            else:
                # Override or add value
                result[key] = value
                
        return result
    
    def get_value(self, key: str, default: T = None) -> Union[Any, T]:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key to retrieve
            default: Default value if key is not found
            
        Returns:
            Configuration value or default if not found
        """
        # Check direct overrides first
        if key in self.config_override:
            return self.config_override[key]
        
        # Check settings in the user config
        if "settings" in self.user_config and key in self.user_config["settings"]:
            return self.user_config["settings"][key]
        
        # Check settings in default config
        if "settings" in self.default_config and key in self.default_config["settings"]:
            return self.default_config["settings"][key]
        
        # Return default if not found
        return default
    
    def get_adapter_config(self, adapter_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific adapter with all overrides applied.
        
        Args:
            adapter_name: Name of the adapter
            
        Returns:
            Merged configuration dictionary
        """
        # Start with default configuration
        adapter_defaults = self.default_config.get("adapter_defaults", {})
        config = adapter_defaults.get("default", {}).copy()
        
        # Apply adapter-specific defaults if they exist
        if adapter_name in adapter_defaults:
            config = self._deep_merge(config, adapter_defaults[adapter_name])
        
        # Apply user configuration if it exists
        if "adapter_defaults" in self.user_config:
            user_defaults = self.user_config["adapter_defaults"]
            if "default" in user_defaults:
                config = self._deep_merge(config, user_defaults["default"])
            if adapter_name in user_defaults:
                config = self._deep_merge(config, user_defaults[adapter_name])
        
        # Apply direct overrides if they exist
        if self.config_override:
            if "adapter_defaults" in self.config_override:
                override_defaults = self.config_override["adapter_defaults"]
                if "default" in override_defaults:
                    config = self._deep_merge(config, override_defaults["default"])
                if adapter_name in override_defaults:
                    config = self._deep_merge(config, override_defaults[adapter_name])
        
        return config
    
    def get_prompt_template(self, template_name: str, adapter_name: Optional[str] = None) -> str:
        """
        Get a prompt template with all overrides applied.
        
        Args:
            template_name: Name of the template
            adapter_name: Optional adapter name for adapter-specific templates
            
        Returns:
            Template string
        """
        # Get prompt templates
        templates = self.default_config.get("prompt_templates", {})
        
        # Start with default template
        if "default" in templates and template_name in templates["default"]:
            template = templates["default"][template_name]
        else:
            # If no default template found, return empty string
            template = ""
        
        # Apply adapter-specific template if available
        if adapter_name and adapter_name in templates and template_name in templates[adapter_name]:
            template = templates[adapter_name][template_name]
        
        # Apply user configuration if it exists
        if "prompt_templates" in self.user_config:
            user_templates = self.user_config["prompt_templates"]
            if "default" in user_templates and template_name in user_templates["default"]:
                template = user_templates["default"][template_name]
            if adapter_name and adapter_name in user_templates and template_name in user_templates[adapter_name]:
                template = user_templates[adapter_name][template_name]
        
        # Apply direct overrides if they exist
        if self.config_override and "prompt_templates" in self.config_override:
            override_templates = self.config_override["prompt_templates"]
            if "default" in override_templates and template_name in override_templates["default"]:
                template = override_templates["default"][template_name]
            if adapter_name and adapter_name in override_templates and template_name in override_templates[adapter_name]:
                template = override_templates[adapter_name][template_name]
        
        return template
    
    def format_template(self, template_name: str, adapter_name: Optional[str] = None, **kwargs) -> str:
        """
        Format a prompt template with provided values.
        
        Args:
            template_name: Name of the template
            adapter_name: Optional adapter name for adapter-specific templates
            **kwargs: Keyword arguments for template formatting
            
        Returns:
            Formatted template string
        """
        template = self.get_prompt_template(template_name, adapter_name)
        
        # Format template with provided values
        try:
            return template.format(**kwargs)
        except KeyError as e:
            print(f"Error formatting template '{template_name}': missing key {str(e)}")
            return template
        except Exception as e:
            print(f"Error formatting template '{template_name}': {str(e)}")
            return template
