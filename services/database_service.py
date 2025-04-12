"""
Service for managing the SQLite database for conversation storage.
"""

import os
import sqlite3
import json
from typing import Optional, Dict, Any, List, Tuple
import logging

from app.agent_module.database.schema import SCHEMA_VERSION, SCHEMA_SQL

logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Service for managing the SQLite database for conversation storage.
    Handles database initialization, connections, and schema management.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database service.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses default path.
        """
        self.db_path = db_path or self._get_default_db_path()
        self._ensure_directory_exists()
        self._init_database()
    
    def _get_default_db_path(self) -> str:
        """
        Get the default path for the SQLite database file.
        
        Returns:
            Path to the default SQLite database file.
        """
        # Use the agent_module directory as the base
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(base_dir, 'data')
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        return os.path.join(data_dir, 'conversations.db')
    
    def _ensure_directory_exists(self) -> None:
        """Ensure the directory for the database file exists."""
        directory = os.path.dirname(self.db_path)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    def _init_database(self) -> None:
        """Initialize the database with the schema if it doesn't exist."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Execute schema SQL
            cursor.executescript(SCHEMA_SQL)
            
            # Check if schema_info has been populated
            cursor.execute("SELECT version FROM schema_info")
            versions = cursor.fetchall()
            
            if not versions:
                # Initialize schema version
                cursor.execute(
                    "INSERT INTO schema_info (version) VALUES (?)",
                    (SCHEMA_VERSION,)
                )
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
            
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a connection to the SQLite database.
        
        Returns:
            sqlite3.Connection: Connection to the SQLite database.
        """
        try:
            # Enable foreign key support
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Configure connection
            conn.row_factory = sqlite3.Row
            
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    # Connection for transaction support
    _transaction_connection = None
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a query and return the results as a list of dictionaries.
        
        Args:
            query: SQL query to execute.
            params: Parameters for the query.
            
        Returns:
            List of dictionaries representing rows.
        """
        # Handle transaction control statements
        if query.strip().upper() == "BEGIN TRANSACTION":
            if self._transaction_connection is not None:
                logger.warning("Transaction already in progress, ignoring BEGIN TRANSACTION")
                return []
                
            self._transaction_connection = self.get_connection()
            cursor = self._transaction_connection.cursor()
            cursor.execute(query)
            return []
            
        elif query.strip().upper() == "COMMIT":
            if self._transaction_connection is None:
                logger.warning("No transaction in progress, ignoring COMMIT")
                return []
                
            try:
                self._transaction_connection.commit()
                return []
            except sqlite3.Error as e:
                logger.error(f"Error executing COMMIT: {e}")
                raise
            finally:
                if self._transaction_connection:
                    self._transaction_connection.close()
                    self._transaction_connection = None
                    
        elif query.strip().upper() == "ROLLBACK":
            if self._transaction_connection is None:
                logger.warning("No transaction in progress, ignoring ROLLBACK")
                return []
                
            try:
                self._transaction_connection.rollback()
                return []
            except sqlite3.Error as e:
                logger.error(f"Error executing ROLLBACK: {e}")
                raise
            finally:
                if self._transaction_connection:
                    self._transaction_connection.close()
                    self._transaction_connection = None
                
        # Use transaction connection if in a transaction, or create a new one
        conn = self._transaction_connection or self.get_connection()
        conn_is_temporary = self._transaction_connection is None
        
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            # If this is a SELECT query, return results
            if query.strip().upper().startswith("SELECT"):
                results = [dict(row) for row in cursor.fetchall()]
                return results
            
            # For INSERT, UPDATE, DELETE operations, commit immediately if not in a transaction
            if conn_is_temporary:
                conn.commit()
                
            return []
            
        except sqlite3.Error as e:
            # Only rollback if not in a transaction
            if conn_is_temporary:
                try:
                    conn.rollback()
                except sqlite3.Error:
                    pass
                    
            logger.error(f"Error executing query: {e}")
            raise
        finally:
            # Only close connection if it's temporary
            if conn_is_temporary and conn:
                conn.close()
    
    def execute_transaction(self, queries: List[Tuple[str, tuple]]) -> None:
        """
        Execute multiple queries in a transaction.
        
        Args:
            queries: List of (query, params) tuples.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            for query, params in queries:
                cursor.execute(query, params)
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Error executing transaction: {e}")
            raise
        finally:
            conn.close()
    
    def get_schema_version(self) -> int:
        """
        Get the current schema version.
        
        Returns:
            Current schema version.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(version) FROM schema_info")
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else 0
        except sqlite3.Error as e:
            logger.error(f"Error getting schema version: {e}")
            raise
        finally:
            conn.close()
