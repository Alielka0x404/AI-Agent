import os
import sys
import json
import tempfile
import logging
import asyncio
import uuid
import traceback
import base64
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent.log')
    ]
)

logger = logging.getLogger(__name__)

class AIAgent:
    """
    A general-purpose AI agent capable of executing various tasks including:
    - File processing
    - Web search and content extraction
    - Code execution in sandbox
    - Data analysis
    - Text processing and summarization
    - Image generation
    """
    
    def __init__(self, config_path=None):
        """
        Initialize the AI Agent with configuration.
        
        Args:
            config_path (str, optional): Path to a configuration file
        """
        # Load configuration
        self.config = self._load_config(config_path)
        logger.info("Initializing AI Agent")
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {self.temp_dir}")
        
        # Initialize components
        self._initialize_components()
    
    def _load_config(self, config_path=None):
        """Load configuration from file or environment variables."""
        try:
            # Import here to avoid circular imports
            from src.config import Config
            return Config(config_path)
        except ImportError:
            # If config module is not available, create a basic config
            logger.warning("Config module not found, using basic configuration")
            return {
                "llm_provider": os.environ.get("LLM_PROVIDER", "groq"),
                "llm_model": os.environ.get("LLM_MODEL", "llama3-70b-8192"),
                "groq_api_key": os.environ.get("GROQ_API_KEY", ""),
                "daytona_api_key": os.environ.get("DAYTONA_API_KEY", ""),
                "huggingface_api_key": os.environ.get("HUGGINGFACE_API_KEY", "")
            }
    
    def _initialize_components(self):
        """Initialize all agent components."""
        try:
            # Import components
            from src.utils.llm import LLMManager
            from src.tools.file_processor import FileProcessor
            from src.tools.web_tools import WebTools
            from src.tools.code_executor import CodeExecutor
            from src.tools.data_analyzer import DataAnalyzer
            from src.tools.text_processor import TextProcessor
            from src.tools.image_generator import ImageGenerator
            
            # Initialize LLM
            self.llm = LLMManager(self.config)
            
            # Initialize tools
            self.file_processor = FileProcessor(self.config)
            self.web_tools = WebTools(self.config)
            self.code_executor = CodeExecutor(self.config)
            self.data_analyzer = DataAnalyzer(self.config)
            self.text_processor = TextProcessor(self.config)
            self.image_generator = ImageGenerator(self.config)
            
            logger.info("All components initialized")
            
        except ImportError as e:
            logger.error(f"Error importing components: {str(e)}")
            # Set placeholder attributes
            self.llm = None
            self.file_processor = None
            self.web_tools = None
            self.code_executor = None
            self.data_analyzer = None
            self.text_processor = None
            self.image_generator = None
    
    async def process_query(self, query: str, context: Dict = None, files: List = None) -> Dict[str, Any]:
        """
        Process a user query with optional context and files.
        
        Args:
            query (str): The user's query or request
            context (Dict, optional): Additional context for the query
            files (List, optional): List of files to process
            
        Returns:
            Dict[str, Any]: The result of processing the query
        """
        try:
            logger.info(f"Processing query: {query}")
            
            # Process files if provided
            file_info = []
            if files:
                logger.info(f"Processing {len(files)} files")
                for file_data in files:
                    temp_path = os.path.join(self.temp_dir, file_data.get('filename', f"file_{uuid.uuid4().hex}"))
                    with open(temp_path, 'wb') as f:
                        f.write(file_data.get('content', b''))
                    
                    # Process the file and get info
                    if self.file_processor:
                        file_result = self.file_processor.process_file(temp_path)
                    else:
                        file_result = {"error": "File processor not initialized"}
                        
                    file_info.append({
                        "filename": file_data.get('filename', os.path.basename(temp_path)),
                        "path": temp_path,
                        "info": file_result
                    })
            
            # Determine the intent of the query
            intent = await self._determine_intent(query)
            logger.info(f"Determined intent: {intent}")
            
            # Process based on intent
            if intent == "web_search" and self.web_tools:
                return await self._handle_web_search(query, context)
                
            elif intent == "code_execution" and self.code_executor:
                return await self._handle_code_execution(query, context)
                
            elif intent == "file_analysis" and file_info and self.data_analyzer:
                return await self._handle_file_analysis(query, file_info, context)
                
            elif intent == "text_processing" and self.text_processor:
                return await self._handle_text_processing(query, context)
                
            elif intent == "image_generation" and self.image_generator:
                return await self._handle_image_generation(query, context)
                
            else:  # general_question or fallback
                return await self._handle_general_question(query, context, file_info)
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    async def _determine_intent(self, query: str) -> str:
        """Determine the intent of the query."""
        # Simple keyword-based intent detection as fallback
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["search", "find", "look up", "google"]):
            return "web_search"
        elif any(word in query_lower for word in ["code", "program", "execute", "run"]):
            return "code_execution"
        elif any(word in query_lower for word in ["analyze", "analysis", "data", "file", "dataset"]):
            return "file_analysis"
        elif any(word in query_lower for word in ["summarize", "summary", "extract", "sentiment"]):
            return "text_processing"
        elif any(word in query_lower for word in ["image", "picture", "generate", "create", "draw"]):
            return "image_generation"
        else:
            return "general_question"
        
        # Note: In the full implementation, we would use the LLM for more accurate intent detection
    
    async def _handle_web_search(self, query: str, context: Dict = None) -> Dict[str, Any]:
        """Handle web search intent."""
        try:
            # Extract search query (simplified version)
            search_query = query.replace("search", "").replace("find", "").replace("look up", "").strip()
            if not search_query:
                search_query = query
            
            # Perform web search
            search_results = self.web_tools.search_web(search_query)
            
            if not search_results.get("success", False):
                return {
                    "success": False,
                    "intent": "web_search",
                    "error": search_results.get("error", "Search failed")
                }
            
            # Scrape the first result for more context
            web_content = None
            if search_results.get("results"):
                first_url = search_results["results"][0]["url"]
                web_content = self.web_tools.scrape_webpage(first_url)
            
            # For now, return the raw results (in full implementation, we would use LLM to analyze)
            return {
                "success": True,
                "intent": "web_search",
                "query": query,
                "search_query": search_query,
                "search_results": search_results,
                "web_content": web_content if web_content and web_content.get('success', False) else None
            }
            
        except Exception as e:
            logger.error(f"Error handling web search: {str(e)}", exc_info=True)
            return {
                "success": False,
                "intent": "web_search",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    async def _handle_code_execution(self, query: str, context: Dict = None) -> Dict[str, Any]:
        """Handle code execution intent."""
        try:
            # Extract code from the query (simplified version)
            # In full implementation, we would use LLM to extract or generate code
            code_lines = []
            language = "python"  # Default
            
            # Look for code blocks
            if "```" in query:
                blocks = query.split("```")
                for i in range(1, len(blocks), 2):
                    if i < len(blocks):
                        block = blocks[i]
                        # Check if the block starts with a language identifier
                        lines = block.strip().split("\n")
                        if lines and lines[0].lower() in ["python", "javascript", "js", "bash", "shell"]:
                            language = lines[0].lower()
                            if language == "js":
                                language = "javascript"
                            if language == "shell":
                                language = "bash"
                            code_lines.extend(lines[1:])
                        else:
                            code_lines.extend(lines)
            
            # If no code blocks found, try to extract code based on indentation
            if not code_lines:
                lines = query.split("\n")
                in_code = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code = not in_code
                    elif in_code or line.startswith("    ") or line.startswith("\t"):
                        code_lines.append(line)
            
            # If still no code found, return error
            if not code_lines:
                return {
                    "success": False,
                    "intent": "code_execution",
                    "error": "No code found in the query"
                }
            
            code_to_execute = "\n".join(code_lines)
            
            # Execute the code
            execution_result = await self.code_executor.execute_code(code_to_execute, language)
            
            return {
                "success": True,
                "intent": "code_execution",
                "query": query,
                "code": code_to_execute,
                "language": language,
                "execution_result": execution_result
            }
            
        except Exception as e:
            logger.error(f"Error handling code execution: {str(e)}", exc_info=True)
            return {
                "success": False,
                "intent": "code_execution",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    async def _handle_file_analysis(self, query: str, file_info: List, context: Dict = None) -> Dict[str, Any]:
        """Handle file analysis intent."""
        try:
            analysis_results = []
            
            for file_item in file_info:
                file_type = file_item.get("info", {}).get("type")
                filename = file_item.get("filename")
                
                if file_type in ["csv", "excel", "json"]:
                    # For data files, perform statistical analysis
                    data_content = file_item.get("info", {}).get("content", {})
                    analysis_result = self.data_analyzer.analyze_data(data_content)
                    analysis_results.append({
                        "filename": filename,
                        "type": file_type,
                        "analysis": analysis_result
                    })
                elif file_type in ["pdf", "docx", "text", "md"]:
                    # For text files, perform text analysis
                    text_content = file_item.get("info", {}).get("content", "")
                    if isinstance(text_content, str):
                        summary = self.text_processor.summarize_text(text_content)
                        keywords = self.text_processor.extract_keywords(text_content)
                        
                        analysis_results.append({
                            "filename": filename,
                            "type": file_type,
                            "summary": summary,
                            "keywords": keywords
                        })
                else:
                    # For other file types, just include basic info
                    analysis_results.append({
                        "filename": filename,
                        "type": file_type,
                        "info": file_item.get("info", {})
                    })
            
            return {
                "success": True,
                "intent": "file_analysis",
                "query": query,
                "file_info": file_info,
                "analysis_results": analysis_results
            }
            
        except Exception as e:
            logger.error(f"Error handling file analysis: {str(e)}", exc_info=True)
            return {
                "success": False,
                "intent": "file_analysis",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    async def _handle_text_processing(self, query: str, context: Dict = None) -> Dict[str, Any]:
        """Handle text processing intent."""
        try:
            # Extract text and operation from the query (simplified version)
            # In full implementation, we would use LLM to extract text and operation
            
            # Default operation is summarize
            operation = "summarize"
            
            # Try to determine operation from query
            query_lower = query.lower()
            if "summarize" in query_lower or "summary" in query_lower:
                operation = "summarize"
            elif "keyword" in query_lower or "extract keyword" in query_lower:
                operation = "extract_keywords"
            elif "sentiment" in query_lower or "analyze sentiment" in query_lower:
                operation = "analyze_sentiment"
            elif "entity" in query_lower or "extract entity" in query_lower:
                operation = "extract_entities"
            
            # Extract text - everything after the operation keyword
            text_to_process = None
            for op_keyword in [operation, "text", "content", "article", "document"]:
                if op_keyword in query_lower:
                    parts = query.split(op_keyword, 1)
                    if len(parts) > 1:
                        text_to_process = parts[1].strip()
                        break
            
            # If text is not provided, return error
            if not text_to_process:
                return {
                    "success": False,
                    "intent": "text_processing",
                    "error": "No text provided for processing",
                    "operation": operation
                }
            
            # Process the text based on the operation
            if operation == "summarize":
                result = self.text_processor.summarize_text(text_to_process)
            elif operation == "extract_keywords":
                result = self.text_processor.extract_keywords(text_to_process)
            elif operation == "analyze_sentiment":
                result = self.text_processor.analyze_sentiment(text_to_process)
            elif operation == "extract_entities":
                result = self.text_processor.extract_entities(text_to_process)
            else:
                # Default to summarization
                result = self.text_processor.summarize_text(text_to_process)
                operation = "summarize"
            
            return {
                "success": True,
                "intent": "text_processing",
                "query": query,
                "text": text_to_process,
                "operation": operation,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error handling text processing: {str(e)}", exc_info=True)
            return {
                "success": False,
                "intent": "text_processing",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    async def _handle_image_generation(self, query: str, context: Dict = None) -> Dict[str, Any]:
        """Handle image generation intent."""
        try:
            # Extract prompt from the query (simplified version)
            # In full implementation, we would use LLM to extract prompt
            
            # Remove common phrases
            prompt = query.lower()
            for phrase in ["generate an image", "create an image", "make an image", 
                          "draw", "generate", "create", "picture", "image", "of"]:
                prompt = prompt.replace(phrase, "")
            
            # Clean up the prompt
            image_prompt = prompt.strip()
            
            # Generate the image
            image_result = self.image_generator.generate_image(image_prompt)
            
            if not image_result.get("success", False):
                return {
                    "success": False,
                    "intent": "image_generation",
                    "error": image_result.get("error", "Failed to generate image"),
                    "prompt": image_prompt
                }
            
            return {
                "success": True,
                "intent": "image_generation",
                "query": query,
                "prompt": image_prompt,
                "image_result": image_result
            }
            
        except Exception as e:
            logger.error(f"Error handling image generation: {str(e)}", exc_info=True)
            return {
                "success": False,
                "intent": "image_generation",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    async def _handle_general_question(self, query: str, context: Dict = None, file_info: List = None) -> Dict[str, Any]:
        """Handle general question intent."""
        try:
            # In full implementation, we would use LLM to generate a response
            # For now, return a simple response
            
            return {
                "success": True,
                "intent": "general_question",
                "query": query,
                "response": f"I received your question: '{query}'. In the full implementation, I would use an LLM to generate a detailed response."
            }
            
        except Exception as e:
            logger.error(f"Error handling general question: {str(e)}", exc_info=True)
            return {
                "success": False,
                "intent": "general_question",
                "error": str(e),
                "traceback": traceback.format_exc()
            }