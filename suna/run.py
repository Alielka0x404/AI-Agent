#!/usr/bin/env python3
"""
Startup script for the AI Agent.
This script checks dependencies, sets up the environment, and starts the agent.
"""

import os
import sys
import subprocess
import importlib.util
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('startup.log')
    ]
)

logger = logging.getLogger(__name__)

def check_dependency(package_name):
    """Check if a Python package is installed."""
    return importlib.util.find_spec(package_name) is not None

def install_dependencies():
    """Install dependencies from requirements.txt."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing dependencies: {str(e)}")
        return False

def check_api_keys():
    """Check if required API keys are set."""
    missing_keys = []
    
    # Check LLM API keys (at least one should be present)
    llm_keys_present = False
    
    # Check Groq API key
    if os.environ.get("GROQ_API_KEY"):
        llm_keys_present = True
    
    # Check Anthropic API key
    if os.environ.get("ANTHROPIC_API_KEY"):
        llm_keys_present = True
    
    # Check OpenAI API key
    if os.environ.get("OPENAI_API_KEY"):
        llm_keys_present = True
    
    if not llm_keys_present:
        missing_keys.append("At least one of: GROQ_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY")
    
    # Check Daytona API key
    if not os.environ.get("DAYTONA_API_KEY"):
        missing_keys.append("DAYTONA_API_KEY")
    
    # Check Hugging Face API key
    if not os.environ.get("HUGGINGFACE_API_KEY"):
        missing_keys.append("HUGGINGFACE_API_KEY")
    
    return missing_keys

def main():
    """Main entry point."""
    logger.info("Starting AI Agent")
    
    # Check for Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        logger.error("Python 3.8 or higher is required")
        print("Error: Python 3.8 or higher is required")
        return 1
    
    # Check for core dependencies
    core_deps = ["fastapi", "uvicorn", "gradio"]
    missing_deps = [dep for dep in core_deps if not check_dependency(dep)]
    
    if missing_deps:
        logger.warning(f"Missing core dependencies: {', '.join(missing_deps)}")
        print(f"Missing dependencies: {', '.join(missing_deps)}")
        
        # Ask to install dependencies
        install = input("Would you like to install the required dependencies? (y/n): ")
        if install.lower() == 'y':
            if not install_dependencies():
                logger.error("Failed to install dependencies")
                print("Error: Failed to install dependencies")
                return 1
        else:
            logger.info("Dependency installation skipped")
            print("Dependency installation skipped. The agent may not function correctly.")
    
    # Check for API keys
    missing_keys = check_api_keys()
    if missing_keys:
        logger.warning(f"Missing API keys: {', '.join(missing_keys)}")
        print(f"Warning: Missing API keys: {', '.join(missing_keys)}")
        print("The agent may have limited functionality without these keys.")
        
        # Ask to set API keys
        set_keys = input("Would you like to set these API keys now? (y/n): ")
        if set_keys.lower() == 'y':
            for key in missing_keys:
                if key.startswith("At least one of:"):
                    print("You need at least one of the following LLM API keys:")
                    groq_key = input("Enter GROQ_API_KEY (or press Enter to skip): ")
                    if groq_key:
                        os.environ["GROQ_API_KEY"] = groq_key
                        logger.info("Set GROQ_API_KEY")
                    
                    anthropic_key = input("Enter ANTHROPIC_API_KEY (or press Enter to skip): ")
                    if anthropic_key:
                        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
                        logger.info("Set ANTHROPIC_API_KEY")
                    
                    openai_key = input("Enter OPENAI_API_KEY (or press Enter to skip): ")
                    if openai_key:
                        os.environ["OPENAI_API_KEY"] = openai_key
                        logger.info("Set OPENAI_API_KEY")
                else:
                    value = input(f"Enter {key}: ")
                    if value:
                        os.environ[key] = value
                        logger.info(f"Set {key}")
    
    # Start the agent
    try:
        logger.info("Starting the agent")
        print("Starting the AI Agent...")
        
        # Import and run the app
        from src.app import app
        import uvicorn
        
        # Get configuration
        try:
            from src.config import config
            host = config.get("host", "0.0.0.0")
            port = int(config.get("port", 8000))
            debug = config.get("debug", False)
        except ImportError:
            host = "0.0.0.0"
            port = 8000
            debug = False
        
        print(f"AI Agent starting on http://{host}:{port}")
        print(f"API documentation available at http://{host}:{port}/docs")
        print(f"Web UI available at http://{host}:{port}/ui")
        
        uvicorn.run(app, host=host, port=port, debug=debug)
        
        return 0
    except Exception as e:
        logger.error(f"Error starting the agent: {str(e)}", exc_info=True)
        print(f"Error starting the agent: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())