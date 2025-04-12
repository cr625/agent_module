# Agent Module

A modular and flexible implementation for conversational AI interfaces, designed to be integrated into any Flask application.

## Features

- **Modular Architecture**: Clean separation of concerns through well-defined interfaces
- **Authentication Support**: Integrated with Flask-Login and configurable auth requirements
- **Session Management**: Handles conversation state persistently 
- **Adapter Pattern**: Easy integration with various data sources and LLM providers
- **Blueprint Factory**: Generate Flask blueprints with customized settings

## Installation

```bash
pip install agent_module
```

Or install from source:

```bash
git clone https://github.com/proethica/agent_module.git
cd agent_module
pip install -e .
```

## Usage

### Basic Integration

```python
from flask import Flask
from agent_module import create_proethica_agent_blueprint

app = Flask(__name__)

# Create agent blueprint
agent_bp = create_proethica_agent_blueprint(
    config={
        'require_auth': True,  # Enable authentication
        'api_key': 'your-llm-api-key',
        'use_claude': True     # Use Claude as LLM provider
    },
    url_prefix='/agent'
)

# Register blueprint with Flask app
app.register_blueprint(agent_bp)
```

### Custom Data Source Integration

To use a custom data source, implement the `SourceInterface`:

```python
from agent_module.interfaces.base import SourceInterface

class CustomSourceAdapter(SourceInterface):
    def get_all_sources(self):
        # Implement source listing
        ...
    
    def get_source_by_id(self, source_id):
        # Implement source retrieval
        ...
```

### Custom LLM Provider Integration

To use a custom LLM provider, implement the `LLMInterface`:

```python
from agent_module.interfaces.base import LLMInterface

class CustomLLMAdapter(LLMInterface):
    def send_message(self, message, conversation, context=None, source_id=None):
        # Implement message sending
        ...
    
    def get_suggestions(self, conversation, source_id=None):
        # Implement suggestion generation
        ...
```

## Architecture

The agent module uses a modular architecture with the following components:

1. **Interfaces**: Define the contract for adapters
2. **Adapters**: Implement interfaces for specific backends
3. **Models**: Data structures for agent conversations
4. **Services**: Core functionality (auth, session management)
5. **Blueprints**: Flask routes and views

## License

GPL-3.0
