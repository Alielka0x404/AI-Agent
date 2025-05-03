import os
import logging
import base64
import tempfile
import uuid
import traceback
from typing import Dict, List, Any, Optional, Union
from io import BytesIO

logger = logging.getLogger(__name__)

# Check if PIL is available
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Check if requests is available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class ImageGenerator:
    """Tools for generating images from text prompts."""
    
    def __init__(self, config=None):
        """
        Initialize the image generator.
        
        Args:
            config (dict, optional): Configuration for image generation
        """
        self.config = config or {}
        self.huggingface_token = self.config.get("huggingface_api_key", os.environ.get("HUGGINGFACE_API_KEY", ""))
        self.temp_dir = tempfile.mkdtemp()
        
        # Check if required packages are available
        if not PIL_AVAILABLE:
            logger.warning("PIL not available. Please install with: pip install Pillow")
        
        if not REQUESTS_AVAILABLE:
            logger.warning("Requests not available. Please install with: pip install requests")
    
    def generate_image(self, prompt: str, model: str = None) -> Dict[str, Any]:
        """
        Generate an image from a text prompt.
        
        Args:
            prompt (str): The text prompt
            model (str, optional): The model to use for generation
            
        Returns:
            Dict[str, Any]: The generated image information
        """
        if not PIL_AVAILABLE or not REQUESTS_AVAILABLE:
            return {
                "success": False,
                "error": "Required packages not available. Please install with: pip install Pillow requests"
            }
            
        if not self.huggingface_token:
            return {
                "success": False,
                "error": "Hugging Face API token not found. Please set HUGGINGFACE_API_KEY environment variable."
            }
            
        try:
            # Use default model if not specified
            model = model or "stabilityai/stable-diffusion-xl-base-1.0"
            
            # API URL for the model
            api_url = f"https://api-inference.huggingface.co/models/{model}"
            
            # Set up headers with token
            headers = {"Authorization": f"Bearer {self.huggingface_token}"}
            
            # Prepare payload
            payload = {"inputs": prompt}
            
            # Make API request
            response = requests.post(api_url, headers=headers, json=payload)
            
            # Check for successful response
            if response.status_code == 200:
                # Save the image to a temporary file
                image_data = response.content
                img = Image.open(BytesIO(image_data))
                
                # Generate a unique filename
                filename = f"generated_image_{uuid.uuid4().hex}.png"
                temp_img_path = os.path.join(self.temp_dir, filename)
                img.save(temp_img_path)
                
                # Convert image to base64 for web display
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                return {
                    "success": True,
                    "image_path": temp_img_path,
                    "filename": filename,
                    "base64_image": img_str,
                    "prompt": prompt,
                    "model": model,
                    "width": img.width,
                    "height": img.height
                }
            else:
                error_message = f"API request failed with status code {response.status_code}"
                try:
                    error_details = response.json()
                    error_message = f"{error_message}: {error_details.get('error', '')}"
                except:
                    error_details = response.text
                
                return {
                    "success": False,
                    "error": error_message,
                    "details": error_details
                }
                
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def get_available_models(self) -> Dict[str, Any]:
        """
        Get a list of available image generation models.
        
        Returns:
            Dict[str, Any]: The available models
        """
        # This is a static list of popular models
        # In a production environment, you might want to query the Hugging Face API
        models = [
            {
                "id": "stabilityai/stable-diffusion-xl-base-1.0",
                "name": "Stable Diffusion XL",
                "description": "State-of-the-art text-to-image model with high quality and detail"
            },
            {
                "id": "runwayml/stable-diffusion-v1-5",
                "name": "Stable Diffusion v1.5",
                "description": "Balanced text-to-image model with good quality and speed"
            },
            {
                "id": "CompVis/stable-diffusion-v1-4",
                "name": "Stable Diffusion v1.4",
                "description": "Earlier version of Stable Diffusion"
            },
            {
                "id": "prompthero/openjourney",
                "name": "Openjourney",
                "description": "Midjourney-inspired Stable Diffusion fine-tune"
            }
        ]
        
        return {
            "success": True,
            "models": models,
            "default_model": "stabilityai/stable-diffusion-xl-base-1.0"
        }