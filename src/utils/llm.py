import os
import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Union

# Import LLM providers
try:
    import groq
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import anthropic
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logger = logging.getLogger(__name__)

class LLMManager:
    """Manager for Language Model interactions."""
    
    def __init__(self, config):
        """
        Initialize the LLM Manager with configuration.
        
        Args:
            config: Configuration object or dictionary
        """
        self.config = config
        self.provider = config.get("llm_provider", "groq").lower()
        self.model = config.get("llm_model", self._get_default_model())
        self.temperature = config.get("llm_temperature", 0.7)
        
        # Initialize the LLM client
        self.client = self._initialize_client()
        self.langchain_llm = self._initialize_langchain()
        
        # Log initialization
        logger.info(f"LLM Manager initialized with provider: {self.provider}, model: {self.model}")
    
    def _get_default_model(self):
        """Get the default model based on the provider."""
        if self.provider == "groq":
            return "llama3-70b-8192"
        elif self.provider == "anthropic":
            return "claude-3-opus-20240229"
        elif self.provider == "openai":
            return "gpt-4o"
        else:
            return "llama3-70b-8192"  # Default to Groq's Llama 3
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client based on the provider."""
        if self.provider == "groq":
            return self._initialize_groq()
        elif self.provider == "anthropic":
            return self._initialize_anthropic()
        elif self.provider == "openai":
            return self._initialize_openai()
        else:
            logger.warning(f"Unsupported LLM provider: {self.provider}")
            return None
    
    def _initialize_groq(self):
        """Initialize Groq client."""
        if not GROQ_AVAILABLE:
            logger.warning("Groq package not available. Please install with: pip install groq")
            return None
                
        api_key = self.config.get("groq_api_key")
        if not api_key:
            logger.warning("Groq API key not found in configuration")
            return None
                
        try:
            return groq.Client(api_key=api_key)
        except Exception as e:
            logger.error(f"Error initializing Groq client: {str(e)}")
            return None
    
    def _initialize_anthropic(self):
        """Initialize Anthropic client."""
        if not ANTHROPIC_AVAILABLE:
            logger.warning("Anthropic package not available. Please install with: pip install anthropic")
            return None
                
        api_key = self.config.get("anthropic_api_key")
        if not api_key:
            logger.warning("Anthropic API key not found in configuration")
            return None
                
        try:
            return anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            logger.error(f"Error initializing Anthropic client: {str(e)}")
            return None
    
    def _initialize_openai(self):
        """Initialize OpenAI client."""
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI package not available. Please install with: pip install openai")
            return None
                
        api_key = self.config.get("openai_api_key")
        if not api_key:
            logger.warning("OpenAI API key not found in configuration")
            return None
                
        try:
            return openai.OpenAI(api_key=api_key)
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            return None
    
    def _initialize_langchain(self):
        """Initialize LangChain integration for the LLM."""
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain package not available. Please install with: pip install langchain")
            return None
            
        if self.provider == "groq":
            return self._initialize_langchain_groq()
        elif self.provider == "anthropic":
            return self._initialize_langchain_anthropic()
        elif self.provider == "openai":
            return self._initialize_langchain_openai()
        else:
            return None
    
    def _initialize_langchain_groq(self):
        """Initialize LangChain integration for Groq."""
        if not GROQ_AVAILABLE:
            return None
                
        api_key = self.config.get("groq_api_key")
        if not api_key:
            return None
                
        try:
            return ChatGroq(
                groq_api_key=api_key,
                model_name=self.model,
                temperature=self.temperature
            )
        except Exception as e:
            logger.error(f"Error initializing LangChain Groq integration: {str(e)}")
            return None
    
    def _initialize_langchain_anthropic(self):
        """Initialize LangChain integration for Anthropic."""
        if not ANTHROPIC_AVAILABLE:
            return None
                
        api_key = self.config.get("anthropic_api_key")
        if not api_key:
            return None
                
        try:
            return ChatAnthropic(
                anthropic_api_key=api_key,
                model_name=self.model,
                temperature=self.temperature
            )
        except Exception as e:
            logger.error(f"Error initializing LangChain Anthropic integration: {str(e)}")
            return None
    
    def _initialize_langchain_openai(self):
        """Initialize LangChain integration for OpenAI."""
        if not OPENAI_AVAILABLE:
            return None
                
        api_key = self.config.get("openai_api_key")
        if not api_key:
            return None
                
        try:
            return ChatOpenAI(
                openai_api_key=api_key,
                model_name=self.model,
                temperature=self.temperature
            )
        except Exception as e:
            logger.error(f"Error initializing LangChain OpenAI integration: {str(e)}")
            return None
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt (str): The user prompt
            system_prompt (str, optional): System prompt to guide the model
            
        Returns:
            Dict[str, Any]: The result containing the generated text
        """
        if not self.client:
            return {
                "success": False,
                "error": f"LLM client for {self.provider} is not initialized"
            }
            
        try:
            if self.provider == "groq":
                return await self._generate_groq(prompt, system_prompt)
            elif self.provider == "anthropic":
                return await self._generate_anthropic(prompt, system_prompt)
            elif self.provider == "openai":
                return await self._generate_openai(prompt, system_prompt)
            else:
                return {
                    "success": False,
                    "error": f"Generation not implemented for provider: {self.provider}"
                }
                
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_groq(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response using Groq."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        
        return {
            "success": True,
            "text": response.choices[0].message.content,
            "model": self.model,
            "provider": self.provider
        }
    
    async def _generate_anthropic(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response using Anthropic."""
        system = system_prompt or ""
        
        response = self.client.messages.create(
            model=self.model,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature
        )
        
        return {
            "success": True,
            "text": response.content[0].text,
            "model": self.model,
            "provider": self.provider
        }
    
    async def _generate_openai(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response using OpenAI."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        
        return {
            "success": True,
            "text": response.choices[0].message.content,
            "model": self.model,
            "provider": self.provider
        }
    
    async def reason(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Use the LLM for reasoning about a query.
        
        Args:
            query (str): The query to reason about
            context (str, optional): Additional context for reasoning
            
        Returns:
            Dict[str, Any]: The reasoning result
        """
        if not self.langchain_llm:
            return {
                "success": False,
                "error": "LangChain LLM is not initialized"
            }
            
        try:
            template = """
            You are a reasoning engine tasked with analyzing the following query:
            
            {query}
            
            {context_section}
            
            Think step-by-step and provide a detailed analysis. Include:
            1. Key components or factors to consider
            2. Logical reasoning steps
            3. Potential approaches or solutions
            4. Conclusions based on your analysis
            
            Show your work clearly and be thorough in your reasoning process.
            """
            
            context_section = f"\nContext:\n{context}\n" if context else ""
            
            prompt_template = PromptTemplate(
                input_variables=["query", "context_section"],
                template=template
            )
            
            chain = LLMChain(llm=self.langchain_llm, prompt=prompt_template)
            response = chain.run(query=query, context_section=context_section)
            
            return {
                "success": True,
                "query": query,
                "reasoning": response
            }
            
        except Exception as e:
            logger.error(f"Error in reasoning: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_models(self) -> Dict[str, Any]:
        """
        Get a list of available models for the current provider.
        
        Returns:
            Dict[str, Any]: The available models
        """
        if self.provider == "groq":
            models = [
                {"id": "llama3-70b-8192", "name": "Llama 3 70B", "context_length": 8192},
                {"id": "llama3-8b-8192", "name": "Llama 3 8B", "context_length": 8192},
                {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "context_length": 32768},
                {"id": "gemma-7b-it", "name": "Gemma 7B", "context_length": 8192}
            ]
        elif self.provider == "anthropic":
            models = [
                {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "context_length": 200000},
                {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "context_length": 200000},
                {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "context_length": 200000},
                {"id": "claude-2.1", "name": "Claude 2.1", "context_length": 100000}
            ]
        elif self.provider == "openai":
            models = [
                {"id": "gpt-4o", "name": "GPT-4o", "context_length": 128000},
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context_length": 128000},
                {"id": "gpt-4", "name": "GPT-4", "context_length": 8192},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context_length": 16385}
            ]
        else:
            models = []
        
        return {
            "success": True,
            "provider": self.provider,
            "current_model": self.model,
            "models": models
        }
    
    def get_available_providers(self) -> Dict[str, Any]:
        """
        Get a list of available LLM providers.
        
        Returns:
            Dict[str, Any]: The available providers
        """
        providers = []
        
        if GROQ_AVAILABLE and self.config.get("groq_api_key"):
            providers.append({
                "id": "groq",
                "name": "Groq",
                "available": True
            })
        else:
            providers.append({
                "id": "groq",
                "name": "Groq",
                "available": False,
                "reason": "API key missing or package not installed"
            })
        
        if ANTHROPIC_AVAILABLE and self.config.get("anthropic_api_key"):
            providers.append({
                "id": "anthropic",
                "name": "Anthropic (Claude)",
                "available": True
            })
        else:
            providers.append({
                "id": "anthropic",
                "name": "Anthropic (Claude)",
                "available": False,
                "reason": "API key missing or package not installed"
            })
        
        if OPENAI_AVAILABLE and self.config.get("openai_api_key"):
            providers.append({
                "id": "openai",
                "name": "OpenAI",
                "available": True
            })
        else:
            providers.append({
                "id": "openai",
                "name": "OpenAI",
                "available": False,
                "reason": "API key missing or package not installed"
            })
        
        return {
            "success": True,
            "current_provider": self.provider,
            "providers": providers
        }