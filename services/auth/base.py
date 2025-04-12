"""
Base authentication implementations for the agent module.
"""

from typing import Optional, Any, Callable
from functools import wraps

from app.agent_module.interfaces.base import AuthInterface


class FlaskLoginAuthAdapter(AuthInterface):
    """
    Adapter for Flask-Login authentication.
    Uses the Flask-Login extension for authentication services.
    """
    
    def __init__(self):
        """Initialize the Flask-Login adapter."""
        # Import here to avoid circular imports
        from flask_login import login_required as flask_login_required
        from flask_login import current_user
        
        self._login_required = flask_login_required
        self._current_user = current_user
    
    def login_required(self, func: Callable) -> Callable:
        """
        Decorator to require authentication for a route.
        
        Args:
            func: Route function to protect
            
        Returns:
            Decorated function
        """
        return self._login_required(func)
    
    def get_current_user(self) -> Optional[Any]:
        """
        Get the current authenticated user.
        
        Returns:
            Current user object or None if not authenticated
        """
        return self._current_user if self.is_authenticated() else None
    
    def is_authenticated(self) -> bool:
        """
        Check if the current user is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self._current_user.is_authenticated if self._current_user else False


class DefaultAuthProvider(AuthInterface):
    """
    Default authentication provider that does not enforce authentication.
    Used when authentication is not required.
    """
    
    def login_required(self, func: Callable) -> Callable:
        """
        Pass-through decorator that doesn't enforce authentication.
        
        Args:
            func: Route function
            
        Returns:
            Original function (unmodified)
        """
        @wraps(func)
        def decorated_function(*args, **kwargs):
            return func(*args, **kwargs)
        return decorated_function
    
    def get_current_user(self) -> Optional[Any]:
        """
        Get the current authenticated user.
        
        Returns:
            None since authentication is not enforced
        """
        return None
    
    def is_authenticated(self) -> bool:
        """
        Check if the current user is authenticated.
        
        Returns:
            Always False since authentication is not enforced
        """
        return False
