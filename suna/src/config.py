import os
import json
from pathlib import Path

class Config:
    """Configuration manager for the AI Agent."""
    
    def __init__(self, config_path=None):
        """
        Initialize configuration from environment variables and optional config file.
        
        Args:
            config_path (str, optional): Path to a JSON configuration file
        """
        # Default configuration
        self.default_config = {
            # LLM settings
            "llm_provider": os.environ.get("LLM_PROVIDER", "groq"),
            "llm_model": os.environ.get("LLM_MODEL", "llama3-70b-8192"),
            "llm_temperature": float(os.environ.get("LLM_TEMPERATURE", "0.7")),
            
            # API keys
            "groq_api_key": os.environ.get("GROQ_API_KEY", ""),
            "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
            "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
            "daytona_api_key": os.environ.get("DAYTONA_API_KEY", ""),
            "huggingface_api_key": os.environ.get("HUGGINGFACE_API_KEY", ""),
            
            # Web UI settings
            "host": os.environ.get("HOST", "0.0.0.0"),
            "port": int(os.environ.get("PORT", "8000")),
            "debug": os.environ.get("DEBUG", "False").lower() == "true",
            
            # File processing
            "max_file_size_mb": int(os.environ.get("MAX_FILE_SIZE_MB", "10")),
            "allowed_file_types": os.environ.get("ALLOWED_FILE_TYPES", "").split(",") or None,
            
            # Sandbox settings
            "sandbox_timeout": int(os.environ.get("SANDBOX_TIMEOUT", "30")),
            "sandbox_memory_limit": os.environ.get("SANDBOX_MEMORY_LIMIT", "2Gi"),
            "sandbox_cpu_limit": os.environ.get("SANDBOX_CPU_LIMIT", "2000m"),
        }
        
        # Load configuration from file if provided
        self.config = self.default_config.copy()
        if config_path:
            self._load_from_file(config_path)
    
    def _load_from_file(self, config_path):
        """Load configuration from a JSON file."""
        try:
            path = Path(config_path)
            if path.exists() and path.is_file():
                with open(path, 'r') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
        except Exception as e:
            print(f"Error loading configuration from {config_path}: {str(e)}")
    
    def get(self, key, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value."""
        self.config[key] = value
    
    def update(self, config_dict):
        """Update configuration with values from a dictionary."""
        self.config.update(config_dict)
    
    def to_dict(self):
        """Convert configuration to dictionary."""
        return self.config.copy()
    
    def save(self, config_path):
        """Save configuration to a JSON file."""
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving configuration to {config_path}: {str(e)}")
            return False

# Create a default configuration instance
config = Config()