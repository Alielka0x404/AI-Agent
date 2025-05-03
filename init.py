#!/usr/bin/env python3
"""
Initialization script for the AI Agent.
This script sets up the project structure and prepares the environment.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('init.log')
    ]
)

logger = logging.getLogger(__name__)

def create_directory(path):
    """Create a directory if it doesn't exist."""
    try:
        os.makedirs(path, exist_ok=True)
        logger.info(f"Created directory: {path}")
        return True
    except Exception as e:
        logger.error(f"Error creating directory {path}: {str(e)}")
        return False

def create_config(config_path, api_keys=None):
    """Create a configuration file."""
    try:
        # Default configuration
        config = {
            "llm_provider": "groq",
            "llm_model": "llama3-70b-8192",
            "llm_temperature": 0.7,
            "host": "0.0.0.0",
            "port": 8000,
            "debug": False,
            "max_file_size_mb": 10,
            "sandbox_timeout": 30,
            "sandbox_memory_limit": "2Gi",
            "sandbox_cpu_limit": "2000m"
        }
        
        # Add API keys if provided
        if api_keys:
            config.update(api_keys)
        
        # Write configuration to file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"Created configuration file: {config_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating configuration file: {str(e)}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Initialize the AI Agent")
    parser.add_argument("--groq-key", help="Groq API key")
    parser.add_argument("--anthropic-key", help="Anthropic API key")
    parser.add_argument("--openai-key", help="OpenAI API key")
    parser.add_argument("--daytona-key", help="Daytona API key")
    parser.add_argument("--huggingface-key", help="Hugging Face API key")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    args = parser.parse_args()
    
    logger.info("Initializing AI Agent")
    
    # Create directories
    directories = [
        "static",
        "logs",
        "data",
        "uploads"
    ]
    
    for directory in directories:
        create_directory(directory)
    
    # Create configuration file if it doesn't exist
    config_path = Path(args.config)
    if not config_path.exists():
        # Collect API keys
        api_keys = {}
        
        # From command line arguments
        if args.groq_key:
            api_keys["groq_api_key"] = args.groq_key
        if args.anthropic_key:
            api_keys["anthropic_api_key"] = args.anthropic_key
        if args.openai_key:
            api_keys["openai_api_key"] = args.openai_key
        if args.daytona_key:
            api_keys["daytona_api_key"] = args.daytona_key
        if args.huggingface_key:
            api_keys["huggingface_api_key"] = args.huggingface_key
        
        # From environment variables
        if not api_keys.get("groq_api_key") and os.environ.get("GROQ_API_KEY"):
            api_keys["groq_api_key"] = os.environ.get("GROQ_API_KEY")
        if not api_keys.get("anthropic_api_key") and os.environ.get("ANTHROPIC_API_KEY"):
            api_keys["anthropic_api_key"] = os.environ.get("ANTHROPIC_API_KEY")
        if not api_keys.get("openai_api_key") and os.environ.get("OPENAI_API_KEY"):
            api_keys["openai_api_key"] = os.environ.get("OPENAI_API_KEY")
        if not api_keys.get("daytona_api_key") and os.environ.get("DAYTONA_API_KEY"):
            api_keys["daytona_api_key"] = os.environ.get("DAYTONA_API_KEY")
        if not api_keys.get("huggingface_api_key") and os.environ.get("HUGGINGFACE_API_KEY"):
            api_keys["huggingface_api_key"] = os.environ.get("HUGGINGFACE_API_KEY")
        
        # Create configuration file
        create_config(config_path, api_keys)
    else:
        logger.info(f"Configuration file already exists: {config_path}")
    
    # Create a simple index.html file in the static directory
    static_index = Path("static/index.html")
    if not static_index.exists():
        try:
            with open(static_index, 'w') as f:
                f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Agent</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .links {
            margin-top: 20px;
        }
        .links a {
            display: inline-block;
            margin-right: 15px;
            padding: 10px 15px;
            background-color: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }
        .links a:hover {
            background-color: #2980b9;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI Agent</h1>
        <p>Welcome to the AI Agent. This agent can help you with various tasks including:</p>
        <ul>
            <li>File processing and analysis</li>
            <li>Web search and content extraction</li>
            <li>Code execution in a secure sandbox</li>
            <li>Data analysis</li>
            <li>Text processing and summarization</li>
            <li>Image generation</li>
        </ul>
        <div class="links">
            <a href="/ui">Web UI</a>
            <a href="/docs">API Documentation</a>
        </div>
    </div>
</body>
</html>""")
            logger.info(f"Created static index file: {static_index}")
        except Exception as e:
            logger.error(f"Error creating static index file: {str(e)}")
    
    logger.info("Initialization complete")
    print("AI Agent initialized successfully!")
    print("You can now run the agent with: python run.py")

if __name__ == "__main__":
    main()