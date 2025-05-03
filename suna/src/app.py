import os
import sys
import json
import logging
import asyncio
import base64
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# FastAPI and Gradio imports
try:
    import gradio as gr
    from fastapi import FastAPI, UploadFile, File, HTTPException, Request
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from starlette.responses import FileResponse
    WEB_UI_AVAILABLE = True
except ImportError:
    WEB_UI_AVAILABLE = False
    print("Web UI dependencies not available. Please install with: pip install fastapi uvicorn gradio")

# Import the AI Agent
from src.agent import AIAgent
from src.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

# Create static folder for uploads and generated content
os.makedirs("static", exist_ok=True)

# Initialize the agent
config = Config()
agent = AIAgent(config)

# Create FastAPI app
app = FastAPI(title="AI Agent API", description="API for interacting with the AI Agent")

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Root endpoint that redirects to the UI or API docs."""
    if WEB_UI_AVAILABLE:
        return {"message": "AI Agent API is running. Visit /ui for the web interface or /docs for API documentation."}
    else:
        return {"message": "AI Agent API is running. Visit /docs for API documentation."}

@app.post("/api/query")
async def process_query(
    query: str,
    files: List[UploadFile] = []
):
    """
    Process a user query with optional file uploads.
    
    Args:
        query: The user's query or request
        files: Optional list of files to process
    
    Returns:
        The result of processing the query
    """
    try:
        # Process uploaded files
        uploaded_files = []
        for file in files:
            content = await file.read()
            uploaded_files.append({
                "filename": file.filename,
                "content": content
            })
        
        # Process the query
        result = await agent.process_query(query, files=uploaded_files)
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"Error in query processing: {str(e)}", exc_info=True)
        return HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute-code")
async def execute_code(code: str, language: str = "python"):
    """
    Execute code in a sandbox.
    
    Args:
        code: The code to execute
        language: The programming language (python, javascript, bash)
    
    Returns:
        The execution result
    """
    try:
        result = await agent.code_executor.execute_code(code, language)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error executing code: {str(e)}", exc_info=True)
        return HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_web(query: str, max_results: int = 5):
    """
    Search the web.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
    
    Returns:
        The search results
    """
    try:
        result = agent.web_tools.search_web(query, max_results)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error searching web: {str(e)}", exc_info=True)
        return HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape")
async def scrape_webpage(url: str, selector: str = None):
    """
    Scrape a webpage.
    
    Args:
        url: The URL to scrape
        selector: Optional CSS selector to extract specific content
    
    Returns:
        The scraped content
    """
    try:
        result = agent.web_tools.scrape_webpage(url, selector)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error scraping webpage: {str(e)}", exc_info=True)
        return HTTPException(status_code=500, detail=str(e))

@app.post("/api/summarize")
async def summarize_text(text: str, max_sentences: int = 5):
    """
    Summarize text.
    
    Args:
        text: The text to summarize
        max_sentences: Maximum number of sentences in the summary
    
    Returns:
        The summarization result
    """
    try:
        result = agent.text_processor.summarize_text(text, max_sentences)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error summarizing text: {str(e)}", exc_info=True)
        return HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-image")
async def generate_image(prompt: str):
    """
    Generate an image from a text prompt.
    
    Args:
        prompt: The text prompt
    
    Returns:
        The generated image information
    """
    try:
        result = agent.image_generator.generate_image(prompt)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}", exc_info=True)
        return HTTPException(status_code=500, detail=str(e))

@app.get("/api/llm/providers")
async def get_llm_providers():
    """
    Get available LLM providers.
    
    Returns:
        The available LLM providers
    """
    try:
        result = agent.llm.get_available_providers()
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error getting LLM providers: {str(e)}", exc_info=True)
        return HTTPException(status_code=500, detail=str(e))

@app.get("/api/llm/models")
async def get_llm_models(provider: str = None):
    """
    Get available LLM models for a provider.
    
    Args:
        provider: The LLM provider (groq, anthropic, openai)
    
    Returns:
        The available LLM models
    """
    try:
        # If provider is specified, temporarily switch to that provider
        original_provider = None
        if provider and provider != agent.llm.provider:
            original_provider = agent.llm.provider
            agent.llm.provider = provider
            # Note: This doesn't reinitialize the client, just gets the model list
        
        result = agent.llm.get_available_models()
        
        # Switch back to original provider if needed
        if original_provider:
            agent.llm.provider = original_provider
            
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error getting LLM models: {str(e)}", exc_info=True)
        return HTTPException(status_code=500, detail=str(e))

# Create Gradio UI if available
if WEB_UI_AVAILABLE:
    def create_gradio_ui():
        """Create a Gradio UI for the AI agent."""
        with gr.Blocks(theme=gr.themes.Soft(), title="AI Agent") as interface:
            gr.Markdown(
                """
                # AI Agent
                
                This AI agent can process various file types, search the web, run code in a sandbox, and perform reasoning.
                """
            )
            
            with gr.Tab("Chat"):
                with gr.Row():
                    with gr.Column(scale=3):
                        chat_history = gr.Chatbot(label="Conversation", height=500)
                        
                        with gr.Row():
                            user_input = gr.Textbox(
                                label="Ask anything...",
                                placeholder="Search the web, analyze data, execute code, or generate images...",
                                lines=2
                            )
                        file_upload = gr.File(label="Upload files", file_count="multiple")
                        
                    with gr.Column(scale=1):
                        with gr.Accordion("Examples", open=False):
                            gr.Examples(
                                examples=[
                                    ["Analyze the latest AI news trends"],
                                    ["Search for renewable energy breakthroughs"],
                                    ["Run a Python script to calculate fibonacci sequence"],
                                    ["Generate an image of a futuristic city"]
                                ],
                                inputs=user_input
                            )
                        
                        submit_btn = gr.Button("Submit", variant="primary")
                        clear_btn = gr.Button("Clear")
                
                async def process_chat(message, files, history):
                    # Process files
                    uploaded_files = []
                    for file in files:
                        with open(file.name, "rb") as f:
                            content = f.read()
                        uploaded_files.append({
                            "filename": os.path.basename(file.name),
                            "content": content
                        })
                    
                    # Process query
                    result = await agent.process_query(message, files=uploaded_files)
                    
                    # Format response based on intent
                    if result.get("success", False):
                        intent = result.get("intent", "general_question")
                        
                        if intent == "general_question":
                            response = result.get("response", "I couldn't generate a response.")
                        elif intent == "web_search":
                            search_results = result.get("search_results", {}).get("results", [])
                            response = f"Here's what I found for '{result.get('search_query', message)}':\n\n"
                            for i, res in enumerate(search_results[:3], 1):
                                response += f"{i}. [{res.get('title', 'No title')}]({res.get('url', '#')})\n{res.get('snippet', 'No description')}\n\n"
                        elif intent == "code_execution":
                            code = result.get("code", "")
                            execution_result = result.get("execution_result", {})
                            stdout = execution_result.get("stdout", "")
                            stderr = execution_result.get("stderr", "")
                            
                            response = f"I executed the following code in {result.get('language', 'python')}:\n\n```{result.get('language', 'python')}\n{code}\n```\n\n"
                            if execution_result.get("success", False):
                                response += f"**Result:**\n```\n{stdout}\n```"
                            else:
                                response += f"**Error:**\n```\n{stderr}\n```"
                        elif intent == "file_analysis":
                            response = f"I analyzed the files you provided. Here's a summary:\n\n"
                            for analysis in result.get("analysis_results", []):
                                filename = analysis.get("filename", "Unknown file")
                                file_type = analysis.get("type", "unknown")
                                
                                response += f"**{filename}** (Type: {file_type}):\n"
                                
                                if "summary" in analysis:
                                    summary = analysis.get("summary", {})
                                    if summary.get("success", False):
                                        response += f"Summary: {summary.get('summary', 'No summary available')[:300]}...\n"
                                
                                if "keywords" in analysis:
                                    keywords = analysis.get("keywords", {})
                                    if keywords.get("success", False):
                                        keyword_list = [k.get("word") for k in keywords.get("keywords", [])[:10]]
                                        response += f"Keywords: {', '.join(keyword_list)}\n"
                                
                                response += "\n"
                        elif intent == "text_processing":
                            operation = result.get("operation", "summarize")
                            operation_result = result.get("result", {})
                            
                            response = f"I processed the text using the '{operation}' operation.\n\n"
                            
                            if operation == "summarize" and operation_result.get("success", False):
                                response += f"**Summary:**\n{operation_result.get('summary', 'No summary available')}\n\n"
                                response += f"Reduced by {operation_result.get('reduction_percentage', 0)}% (from {operation_result.get('original_length', 0)} to {operation_result.get('summary_length', 0)} characters)"
                            elif operation == "extract_keywords" and operation_result.get("success", False):
                                keywords = operation_result.get("keywords", [])
                                response += "**Keywords:**\n"
                                for kw in keywords:
                                    response += f"- {kw.get('word')}: {kw.get('frequency')} occurrences\n"
                            elif operation == "analyze_sentiment" and operation_result.get("success", False):
                                response += f"**Sentiment:** {operation_result.get('sentiment', 'neutral')}\n"
                                response += f"Score: {operation_result.get('score', 0)}\n"
                                response += f"Positive words: {operation_result.get('positive_words', 0)}\n"
                                response += f"Negative words: {operation_result.get('negative_words', 0)}"
                            elif operation == "extract_entities" and operation_result.get("success", False):
                                entities = operation_result.get("entities", {})
                                response += "**Entities:**\n"
                                for entity_type, entity_list in entities.items():
                                    response += f"- {entity_type}: {', '.join(entity_list)}\n"
                        elif intent == "image_generation":
                            image_result = result.get("image_result", {})
                            
                            if image_result.get("success", False):
                                prompt = result.get("prompt", "")
                                image_path = image_result.get("image_path", "")
                                
                                # Save image to static folder for web access
                                filename = os.path.basename(image_path)
                                static_path = f"static/{filename}"
                                import shutil
                                shutil.copy(image_path, static_path)
                                
                                response = f"I generated an image based on your prompt: '{prompt}'\n\n"
                                response += f"![Generated Image]({static_path})"
                            else:
                                response = f"I couldn't generate an image. Error: {image_result.get('error', 'Unknown error')}"
                        else:
                            response = f"I processed your request, but I'm not sure how to display the results for intent '{intent}'."
                    else:
                        response = f"I encountered an error: {result.get('error', 'Unknown error')}"
                    
                    history.append((message, response))
                    return "", None, history
                
                submit_btn.click(
                    fn=process_chat,
                    inputs=[user_input, file_upload, chat_history],
                    outputs=[user_input, file_upload, chat_history],
                    show_progress=True
                )
                
                clear_btn.click(
                    fn=lambda: ("", None, []),
                    outputs=[user_input, file_upload, chat_history]
                )

            with gr.Tab("File Analysis"):
                with gr.Row():
                    with gr.Column():
                        analysis_upload = gr.File(label="Upload files for analysis", file_count="multiple")
                        analyze_btn = gr.Button("Analyze Files", variant="primary")
                    
                    with gr.Column():
                        file_preview = gr.DataFrame(label="File Preview", interactive=False)
                        analysis_results = gr.JSON(label="Analysis Results")
                
                async def analyze_files(files):
                    if not files:
                        return None, {"error": "No files uploaded"}
                    
                    # Process files
                    uploaded_files = []
                    for file in files:
                        with open(file.name, "rb") as f:
                            content = f.read()
                        uploaded_files.append({
                            "filename": os.path.basename(file.name),
                            "content": content
                        })
                    
                    # Process query for file analysis
                    result = await agent.process_query("Analyze these files", files=uploaded_files)
                    
                    # Create preview dataframe
                    preview_data = []
                    for file_info in result.get("file_info", []):
                        preview_data.append({
                            "Filename": file_info.get("filename", "Unknown"),
                            "Type": file_info.get("info", {}).get("type", "Unknown"),
                            "Size": os.path.getsize(file_info.get("path", ""))
                        })
                    
                    import pandas as pd
                    preview_df = pd.DataFrame(preview_data) if preview_data else None
                    
                    return preview_df, result.get("analysis_results", {})
                
                analyze_btn.click(
                    fn=analyze_files,
                    inputs=analysis_upload,
                    outputs=[file_preview, analysis_results],
                    show_progress=True
                )

            with gr.Tab("Code Execution"):
                with gr.Row():
                    with gr.Column():
                        code_input = gr.Code(
                            label="Enter code",
                            language="python",
                            interactive=True,
                            lines=10
                        )
                        lang_select = gr.Dropdown(
                            label="Language",
                            choices=["Python", "JavaScript", "Bash"],
                            value="Python"
                        )
                        execute_btn = gr.Button("Run in Sandbox", variant="primary")
                    
                    with gr.Column():
                        exec_output = gr.Textbox(label="Execution Output", lines=10)
                        exec_details = gr.JSON(label="Execution Details")
                
                async def execute_code_sandbox(code, language):
                    if not code.strip():
                        return "No code provided", {"error": "No code provided"}
                    
                    # Map language selection to lowercase
                    lang = language.lower()
                    
                    # Execute code
                    result = await agent.code_executor.execute_code(code, lang)
                    
                    # Format output
                    if result.get("success", False):
                        output = result.get("stdout", "")
                    else:
                        output = f"Error: {result.get('stderr', result.get('error', 'Unknown error'))}"
                    
                    return output, result
                
                execute_btn.click(
                    fn=execute_code_sandbox,
                    inputs=[code_input, lang_select],
                    outputs=[exec_output, exec_details],
                    show_progress=True
                )

            with gr.Tab("Web Search"):
                with gr.Row():
                    with gr.Column():
                        search_input = gr.Textbox(
                            label="Search query",
                            placeholder="Enter your search query...",
                            lines=2
                        )
                        max_results = gr.Slider(
                            label="Maximum results",
                            minimum=1,
                            maximum=20,
                            value=5,
                            step=1
                        )
                        search_btn = gr.Button("Search", variant="primary")
                    
                    with gr.Column():
                        search_results_output = gr.JSON(label="Search Results")
                        search_content = gr.Markdown(label="Content Preview")
                
                async def perform_search(query, max_results):
                    if not query.strip():
                        return {"error": "No search query provided"}, "No search query provided"
                    
                    # Perform search
                    search_results = agent.web_tools.search_web(query, int(max_results))
                    
                    # Format content preview
                    content = f"# Search Results for '{query}'\n\n"
                    
                    if search_results.get("success", False) and search_results.get("results"):
                        for i, result in enumerate(search_results["results"], 1):
                            content += f"## {i}. {result.get('title', 'No title')}\n"
                            content += f"[{result.get('url', '#')}]({result.get('url', '#')})\n\n"
                            content += f"{result.get('snippet', 'No description')}\n\n"
                            content += "---\n\n"
                    else:
                        content += "No results found or search failed."
                    
                    return search_results, content
                
                search_btn.click(
                    fn=perform_search,
                    inputs=[search_input, max_results],
                    outputs=[search_results_output, search_content],
                    show_progress=True
                )

            with gr.Tab("Image Generation"):
                with gr.Row():
                    with gr.Column():
                        image_prompt = gr.Textbox(
                            label="Image prompt",
                            placeholder="Describe the image you want to generate...",
                            lines=3
                        )
                        generate_btn = gr.Button("Generate Image", variant="primary")
                    
                    with gr.Column():
                        generated_image = gr.Image(label="Generated Image")
                        image_details = gr.JSON(label="Image Details")
                
                async def generate_image_ui(prompt):
                    if not prompt.strip():
                        return None, {"error": "No prompt provided"}
                    
                    # Generate image
                    result = agent.image_generator.generate_image(prompt)
                    
                    if result.get("success", False):
                        return result.get("image_path"), result
                    else:
                        return None, result
                
                generate_btn.click(
                    fn=generate_image_ui,
                    inputs=image_prompt,
                    outputs=[generated_image, image_details],
                    show_progress=True
                )

            with gr.Tab("Settings"):
                with gr.Row():
                    with gr.Column():
                        # LLM Provider selection
                        provider_select = gr.Dropdown(
                            label="LLM Provider",
                            choices=["groq", "anthropic", "openai"],
                            value=config.get("llm_provider", "groq")
                        )
                        
                        # API Keys
                        groq_key = gr.Textbox(
                            label="Groq API Key",
                            type="password",
                            value=config.get("groq_api_key", "")
                        )
                        anthropic_key = gr.Textbox(
                            label="Anthropic API Key",
                            type="password",
                            value=config.get("anthropic_api_key", "")
                        )
                        openai_key = gr.Textbox(
                            label="OpenAI API Key",
                            type="password",
                            value=config.get("openai_api_key", "")
                        )
                        daytona_key = gr.Textbox(
                            label="Daytona API Key",
                            type="password",
                            value=config.get("daytona_api_key", "")
                        )
                        huggingface_key = gr.Textbox(
                            label="Hugging Face API Key",
                            type="password",
                            value=config.get("huggingface_api_key", "")
                        )
                    
                    with gr.Column():
                        # Model selection (will be updated based on provider)
                        model_select = gr.Dropdown(
                            label="AI Model",
                            choices=["llama3-70b-8192", "mixtral-8x7b-32768", "gemma-7b-it"],
                            value=config.get("llm_model", "llama3-70b-8192")
                        )
                        
                        # Temperature setting
                        temp_slider = gr.Slider(
                            label="Creativity Temperature",
                            minimum=0.1,
                            maximum=1.0,
                            value=float(config.get("llm_temperature", 0.7)),
                            step=0.1
                        )
                        
                        # Save button and status
                        save_btn = gr.Button("Save Settings", variant="primary")
                        settings_status = gr.Textbox(label="Status", interactive=False)
                
                # Function to update model choices based on provider
                def update_model_choices(provider):
                    if provider == "groq":
                        return gr.Dropdown.update(
                            choices=["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768", "gemma-7b-it"],
                            value="llama3-70b-8192"
                        )
                    elif provider == "anthropic":
                        return gr.Dropdown.update(
                            choices=["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-2.1"],
                            value="claude-3-opus-20240229"
                        )
                    elif provider == "openai":
                        return gr.Dropdown.update(
                            choices=["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                            value="gpt-4o"
                        )
                    else:
                        return gr.Dropdown.update(
                            choices=["llama3-70b-8192"],
                            value="llama3-70b-8192"
                        )
                
                # Connect provider selection to model choices update
                provider_select.change(
                    fn=update_model_choices,
                    inputs=provider_select,
                    outputs=model_select
                )
                
                # Function to save settings
                def save_settings(provider, model, temperature, groq_key, anthropic_key, openai_key, daytona_key, huggingface_key):
                    # Update environment variables
                    if groq_key:
                        os.environ["GROQ_API_KEY"] = groq_key
                    if anthropic_key:
                        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
                    if openai_key:
                        os.environ["OPENAI_API_KEY"] = openai_key
                    if daytona_key:
                        os.environ["DAYTONA_API_KEY"] = daytona_key
                    if huggingface_key:
                        os.environ["HUGGINGFACE_API_KEY"] = huggingface_key
                    
                    # Update config
                    config.update({
                        "llm_provider": provider,
                        "llm_model": model,
                        "llm_temperature": temperature,
                        "groq_api_key": groq_key,
                        "anthropic_api_key": anthropic_key,
                        "openai_api_key": openai_key,
                        "daytona_api_key": daytona_key,
                        "huggingface_api_key": huggingface_key
                    })
                    
                    # Save config to file
                    config.save("config.json")
                    
                    # Reinitialize agent components
                    agent._initialize_components()
                    
                    return "Settings saved successfully! LLM provider changed to " + provider
                
                save_btn.click(
                    fn=save_settings,
                    inputs=[provider_select, model_select, temp_slider, groq_key, anthropic_key, openai_key, daytona_key, huggingface_key],
                    outputs=settings_status
                )

        return interface

    # Mount Gradio interface to FastAPI app
    gradio_app = gr.mount_gradio_app(app, create_gradio_ui(), path="/ui")

# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    host = config.get("host", "0.0.0.0")
    port = int(config.get("port", 8000))
    debug = config.get("debug", False)
    
    print(f"Starting AI Agent API on http://{host}:{port}")
    print(f"API documentation available at http://{host}:{port}/docs")
    
    if WEB_UI_AVAILABLE:
        print(f"Web UI available at http://{host}:{port}/ui")
    
    uvicorn.run(app, host=host, port=port, debug=debug)