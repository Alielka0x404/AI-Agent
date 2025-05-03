# General AI Agent

A versatile AI agent capable of executing complex tasks across domains including information gathering, content creation, software development, data analysis, and problem-solving.

## Features

- **Multiple LLM Providers**: Support for Groq, Anthropic (Claude), and OpenAI (GPT) models
- **File Processing**: Process various file types including Python, JavaScript, PDF, Word, Excel, PowerPoint, CSV, JSON, XML, and archives.
- **Web Search & Scraping**: Search the web and extract content from websites.
- **Code Execution**: Run code in a secure sandbox environment.
- **Data Analysis**: Analyze structured data with statistical methods.
- **Text Processing**: Summarize text, extract keywords, analyze sentiment, and extract entities.
- **Image Generation**: Generate images from text prompts.
- **Reasoning**: Use LLMs for advanced reasoning and problem-solving.

## Architecture

The agent is built with a modular architecture:

- **Core Agent**: Coordinates all components and handles user queries.
- **Tools**: Specialized modules for different tasks (file processing, web search, etc.).
- **LLM Integration**: Supports multiple providers (Groq, Anthropic, OpenAI) for language model capabilities.
- **Web UI**: Provides a user-friendly interface with Gradio and FastAPI.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-agent.git
   cd ai-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   # At least one of these LLM API keys is required
   export GROQ_API_KEY="your_groq_api_key"
   export ANTHROPIC_API_KEY="your_anthropic_api_key"
   export OPENAI_API_KEY="your_openai_api_key"
   
   # Additional API keys
   export DAYTONA_API_KEY="your_daytona_api_key"
   export HUGGINGFACE_API_KEY="your_huggingface_api_key"
   ```

## Usage

### Starting the Agent

Run the initialization script first (only needed once):

```bash
python init.py
```

Then run the application:

```bash
python run.py
```

This will start the FastAPI server and Gradio UI. You can access:
- Web UI: http://localhost:8000/ui
- API docs: http://localhost:8000/docs

### Using the API

You can interact with the agent through the API:

```python
import requests

# Process a query
response = requests.post(
    "http://localhost:8000/api/query",
    params={"query": "Search for the latest AI research papers"}
)
print(response.json())

# Execute code
response = requests.post(
    "http://localhost:8000/api/execute-code",
    params={"code": "print('Hello, World!')", "language": "python"}
)
print(response.json())
```

## Configuration

You can configure the agent by:

1. Setting environment variables
2. Creating a `config.json` file
3. Using the Settings tab in the web UI

Configuration options include:
- LLM provider and model
- API keys
- Web UI settings
- Sandbox execution limits

### LLM Providers

The agent supports the following LLM providers:

1. **Groq**
   - Models: llama3-70b-8192, llama3-8b-8192, mixtral-8x7b-32768, gemma-7b-it
   - Requires: GROQ_API_KEY

2. **Anthropic**
   - Models: claude-3-opus-20240229, claude-3-sonnet-20240229, claude-3-haiku-20240307, claude-2.1
   - Requires: ANTHROPIC_API_KEY

3. **OpenAI**
   - Models: gpt-4o, gpt-4-turbo, gpt-4, gpt-3.5-turbo
   - Requires: OPENAI_API_KEY

## Components

### File Processor

Handles various file types and extracts their content:
- Text files (Python, JavaScript, HTML, CSS, JSON, etc.)
- Documents (PDF, Word, PowerPoint)
- Data files (Excel, CSV, JSON, XML)
- Archives (ZIP, TAR, GZ)

### Web Tools

Provides web search and content extraction capabilities:
- Search the web using DuckDuckGo
- Scrape and extract data from websites
- Extract article content

### Code Executor

Executes code in a secure sandbox environment:
- Supports Python, JavaScript, and Bash
- Uses Daytona for secure execution
- Provides execution metrics

### Data Analyzer

Analyzes structured data:
- Basic statistical analysis
- Correlation analysis
- Time series analysis
- Distribution analysis

### Text Processor

Processes and analyzes text:
- Text summarization
- Keyword extraction
- Sentiment analysis
- Entity extraction

### Image Generator

Generates images from text prompts:
- Uses Hugging Face's text-to-image models
- Supports various image generation models

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Groq](https://groq.com/) for LLM API
- [Anthropic](https://www.anthropic.com/) for Claude API
- [OpenAI](https://openai.com/) for GPT API
- [Daytona](https://daytona.io/) for secure code execution
- [Hugging Face](https://huggingface.co/) for image generation models
- [FastAPI](https://fastapi.tiangolo.com/) and [Gradio](https://gradio.app/) for the web interface