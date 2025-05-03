# Getting Started with the AI Agent

This guide will help you set up and start using the AI Agent.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- API keys for at least one of the following LLM providers:
  - Groq (for Llama 3, Mixtral, and other models)
  - Anthropic (for Claude models)
  - OpenAI (for GPT models)
- Additional API keys for:
  - Daytona (for secure code execution)
  - Hugging Face (for image generation)

## Installation

### 1. Clone the Repository

If you're using git:

```bash
git clone https://github.com/yourusername/ai-agent.git
cd ai-agent
```

Or simply download and extract the project files to a directory of your choice.

### 2. Set Up a Virtual Environment (Recommended)

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up API Keys

You'll need to obtain API keys from the following services:

#### LLM Providers (at least one is required):
- **Groq**: Sign up at [groq.com](https://groq.com) to get an API key
- **Anthropic**: Sign up at [anthropic.com](https://www.anthropic.com) to get an API key
- **OpenAI**: Sign up at [openai.com](https://openai.com) to get an API key

#### Additional Services:
- **Daytona**: Sign up at [daytona.io](https://daytona.io) to get an API key
- **Hugging Face**: Sign up at [huggingface.co](https://huggingface.co) to get an API key

Set these as environment variables:

```bash
# On Windows (Command Prompt)
set GROQ_API_KEY=your_groq_api_key
set ANTHROPIC_API_KEY=your_anthropic_api_key
set OPENAI_API_KEY=your_openai_api_key
set DAYTONA_API_KEY=your_daytona_api_key
set HUGGINGFACE_API_KEY=your_huggingface_api_key

# On Windows (PowerShell)
$env:GROQ_API_KEY="your_groq_api_key"
$env:ANTHROPIC_API_KEY="your_anthropic_api_key"
$env:OPENAI_API_KEY="your_openai_api_key"
$env:DAYTONA_API_KEY="your_daytona_api_key"
$env:HUGGINGFACE_API_KEY="your_huggingface_api_key"

# On macOS/Linux
export GROQ_API_KEY="your_groq_api_key"
export ANTHROPIC_API_KEY="your_anthropic_api_key"
export OPENAI_API_KEY="your_openai_api_key"
export DAYTONA_API_KEY="your_daytona_api_key"
export HUGGINGFACE_API_KEY="your_huggingface_api_key"
```

Alternatively, you can create a `config.json` file in the project root:

```json
{
  "llm_provider": "groq",
  "llm_model": "llama3-70b-8192",
  "llm_temperature": 0.7,
  "groq_api_key": "your_groq_api_key",
  "anthropic_api_key": "your_anthropic_api_key",
  "openai_api_key": "your_openai_api_key",
  "daytona_api_key": "your_daytona_api_key",
  "huggingface_api_key": "your_huggingface_api_key",
  "host": "0.0.0.0",
  "port": 8000,
  "debug": false
}
```

## Running the Agent

### 1. Initialize the Agent

First, run the initialization script to set up the necessary directories and configuration:

```bash
python init.py
```

This script will:
- Create required directories
- Set up the configuration file if it doesn't exist
- Prepare the static files for the web UI

### 2. Start the Agent

Use the provided run script:

```bash
python run.py
```

This script will:
1. Check for required dependencies and install them if needed
2. Verify API keys are set
3. Start the agent with the web UI and API

### Manual Start

Alternatively, you can start the agent manually:

```bash
python -m src.app
```

## Using the Agent

Once the agent is running, you can interact with it in several ways:

### Web UI

Access the web UI at: http://localhost:8000/ui

The UI provides several tabs:
- **Chat**: Interact with the agent in a conversational manner
- **File Analysis**: Upload and analyze files
- **Code Execution**: Run code in a secure sandbox
- **Web Search**: Search the web and extract content
- **Image Generation**: Generate images from text prompts
- **Settings**: Configure the agent and select LLM providers

### API

The agent also provides a REST API that you can use to integrate with other applications:

- API documentation: http://localhost:8000/docs

Example API usage with curl:

```bash
# Process a query
curl -X POST "http://localhost:8000/api/query?query=Search%20for%20the%20latest%20AI%20research%20papers"

# Execute code
curl -X POST "http://localhost:8000/api/execute-code?code=print('Hello%2C%20World!')&language=python"

# Generate an image
curl -X POST "http://localhost:8000/api/generate-image?prompt=A%20futuristic%20city%20with%20flying%20cars"
```

## Configuring LLM Providers

The agent supports multiple LLM providers. You can configure which provider to use in the Settings tab of the web UI or by editing the `config.json` file.

### Available Providers and Models

1. **Groq**
   - Models: llama3-70b-8192, llama3-8b-8192, mixtral-8x7b-32768, gemma-7b-it
   - Best for: Fast inference and good performance across a range of tasks

2. **Anthropic**
   - Models: claude-3-opus-20240229, claude-3-sonnet-20240229, claude-3-haiku-20240307, claude-2.1
   - Best for: High-quality reasoning, safety, and long context windows

3. **OpenAI**
   - Models: gpt-4o, gpt-4-turbo, gpt-4, gpt-3.5-turbo
   - Best for: State-of-the-art capabilities and tool use

### Switching Providers

To switch providers:

1. In the web UI:
   - Go to the Settings tab
   - Select the desired provider from the dropdown
   - Enter the API key if not already set
   - Select a model for that provider
   - Click "Save Settings"

2. In the config.json file:
   ```json
   {
     "llm_provider": "anthropic",
     "llm_model": "claude-3-opus-20240229",
     "anthropic_api_key": "your_anthropic_api_key"
   }
   ```

3. Using environment variables:
   ```bash
   export LLM_PROVIDER="openai"
   export LLM_MODEL="gpt-4o"
   export OPENAI_API_KEY="your_openai_api_key"
   ```

## Example Use Cases

### 1. Research Assistant

Use the agent to search for information, summarize articles, and extract key insights:

```
Search for the latest developments in quantum computing
```

### 2. Data Analysis

Upload data files (CSV, Excel, JSON) and ask the agent to analyze them:

```
Analyze this dataset and identify trends in customer behavior
```

### 3. Code Helper

Get help with coding tasks or execute code snippets:

```
Write a Python function to calculate the Fibonacci sequence
```

### 4. Content Creation

Generate images or process text for content creation:

```
Generate an image of a mountain landscape at sunset
```

### 5. Document Processing

Extract and summarize information from documents:

```
Summarize the key points from this PDF report
```

## Troubleshooting

### Missing Dependencies

If you encounter errors about missing packages:

```bash
pip install -r requirements.txt
```

### API Key Issues

If the agent can't access API services:
1. Verify your API keys are correct
2. Check that the environment variables are set correctly
3. Try setting the keys in the Settings tab of the web UI

### Provider-Specific Issues

- **Groq**: If you encounter rate limits, try reducing the number of requests or switching to a different provider
- **Anthropic**: If you see errors about context length, try breaking your input into smaller chunks
- **OpenAI**: If you encounter billing issues, check your OpenAI account status

### Port Already in Use

If port 8000 is already in use:
1. Change the port in `config.json`
2. Or start the agent with a different port: `python -m src.app --port 8080`

## Next Steps

- Explore the different capabilities of the agent
- Try different LLM providers to see which works best for your needs
- Check the README.md for more detailed documentation
- Customize the agent by modifying the source code