"""
title: Replicate Ideogram Pipeline
author: David Holmlund
author_url: https://github.com/holmlund
sponsor: Digitalist Open Tech
date: 2025-03-25
version: 1.01
license: MIT
description: Integrate Replicate Ideogram v2a API as an Open WebUI pipeline
requirements: pydantic, replicate==0.32.1
"""

import os
import logging
import re
import shlex
from difflib import get_close_matches
from typing import List, Dict, Union, Generator, Iterator, Optional, Any

import replicate
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -- Constants ----------------------------------------------------------------

AVAILABLE_STYLES = [
    "None",
    "Auto",
    "General",
    "Realistic",
    "Design",
    "Render 3D",
    "Anime"
]

AVAILABLE_ASPECT_RATIOS = [
    "1:1",
    "16:9",
    "9:16",
    "4:3",
    "3:4",
    "3:2",
    "2:3",
    "16:10",
    "10:16",
    "3:1",
    "1:3"
]

AVAILABLE_RESOLUTIONS = [
    "None",
    "512x1536",
    "576x1408",
    "576x1472",
    "576x1536",
    "640x1344",
    "640x1408",
    "640x1472",
    "640x1536",
    "704x1152",
    "704x1216",
    "704x1280",
    "704x1344",
    "704x1408",
    "704x1472",
    "736x1312",
    "768x1088",
    "768x1216",
    "768x1280",
    "768x1344",
    "832x960",
    "832x1024",
    "832x1088",
    "832x1152",
    "832x1216",
    "832x1248",
    "864x1152",
    "896x960",
    "896x1024",
    "896x1088",
    "896x1120",
    "896x1152",
    "960x832",
    "960x896",
    "960x1024",
    "960x1088",
    "1024x832",
    "1024x896",
    "1024x960",
    "1024x1024",
    "1088x768",
    "1088x832",
    "1088x896",
    "1088x960",
    "1120x896",
    "1152x704",
    "1152x832",
    "1152x864",
    "1152x896",
    "1216x704",
    "1216x768",
    "1216x832",
    "1248x832",
    "1280x704",
    "1280x768",
    "1280x800",
    "1312x736",
    "1344x640",
    "1344x704",
    "1344x768",
    "1408x576",
    "1408x640",
    "1408x704",
    "1472x576",
    "1472x640",
    "1472x704",
    "1536x512",
    "1536x576",
    "1536x640"
]

def fuzzy_match(input_text: str, candidates: List[str], default: str) -> str:
    """
    Generic fuzzy matching function for style, aspect ratio, and resolution.
    
    Args:
        input_text: The input text to match
        candidates: List of valid candidates to match against
        default: Default value to return if no match is found
        
    Returns:
        The matched value or default if no match found
    """
    if not input_text or input_text.lower() == "none":
        return default
        
    input_lower = input_text.lower().strip()
    
    # Try exact match first
    if input_text in candidates:
        return input_text
        
    # Try fuzzy matching
    candidate_map = {c.lower(): c for c in candidates}
    matches = get_close_matches(input_lower, candidate_map.keys(), n=1, cutoff=0.6)
    
    if matches:
        return candidate_map[matches[0]]
        
    logger.warning(f"No matching value found for: {input_text}")
    return default

def parse_command_params(user_message: str) -> Dict[str, Union[str, bool]]:
    """
    Parses command-line style parameters from the user message using shlex.split
    for proper handling of quoted strings.
    
    Args:
        user_message: The input message containing prompt and parameters
        
    Returns:
        A dictionary containing the prompt and any parsed parameters
        
    Example:
        >>> parse_command_params('A painting of a sunset --style "Realistic 3D" --aspect 16:9 --res 1280x720')
        {
            'prompt': 'A painting of a sunset',
            'style': 'Realistic 3D',
            'aspect': '16:9',
            'res': '1280x720'
        }
        
        >>> parse_command_params('Simple prompt without parameters')
        {'prompt': 'Simple prompt without parameters'}
    """
    try:
        # Use shlex.split for proper shell-like parsing
        parts = shlex.split(user_message)
        params = {}
        prompt_parts = []
        
        # First, collect all parts until we find a parameter
        i = 0
        while i < len(parts):
            if parts[i].startswith('--'):
                break
            prompt_parts.append(parts[i])
            i += 1
        
        # Store the clean prompt
        params['prompt'] = ' '.join(prompt_parts)
        
        # Then parse the parameters
        while i < len(parts):
            if parts[i].startswith('--'):
                # Found a parameter
                param_name = parts[i][2:]  # Remove '--'
                if i + 1 < len(parts) and not parts[i + 1].startswith('--'):
                    # Parameter has a value
                    params[param_name] = parts[i + 1]
                    i += 2
                else:
                    # Parameter without value
                    params[param_name] = True
                    i += 1
            else:
                # Skip any non-parameter text after parameters start
                i += 1
        
        return params
    except Exception as e:
        logger.error(f"Error parsing command parameters: {str(e)}")
        return {"prompt": user_message}  # Fallback to treating entire input as prompt

class Pipeline:
    """
    A pipeline that calls Replicate's Ideogram model, allowing command-line style
    parameter input for style, aspect ratio, and resolution.
    """
    class Valves(BaseModel):
        REPLICATE_API_TOKEN: str

    def __init__(self):
        self.name = "Replicate Ideogram Pipeline"

        # Get API token from environment variable or valve configuration
        self.api_token = os.getenv("REPLICATE_API_TOKEN", "")
        self.valves = self.Valves(REPLICATE_API_TOKEN=self.api_token)

        if not self.api_token:
            raise ValueError(
                "REPLICATE_API_TOKEN environment variable or valve configuration is required"
            )

        # Initialize Replicate client with explicit headers
        self.client = replicate.Client(
            headers={
                "User-Agent": "replicate-ideogram-pipeline/1.0.1",
                "Authorization": f"Token {self.api_token}"
            }
        )

    async def on_startup(self):
        """
        Called on application startup (if using an async framework).
        Refreshes client with the latest token from valves if available.
        """
        logger.info(f"on_startup: {__name__}")
        if self.valves.REPLICATE_API_TOKEN:
            self.api_token = self.valves.REPLICATE_API_TOKEN
            self.client = replicate.Client(
                headers={
                    "User-Agent": "replicate-ideogram-pipeline/1.0.1",
                    "Authorization": f"Token {self.api_token}"
                }
            )

    async def on_shutdown(self):
        """
        Called on application shutdown (if using an async framework).
        """
        logger.info(f"on_shutdown: {__name__}")

    def get_style_from_input(self, input_text: str) -> str:
        """Fuzzy-match the user's input text to an available style."""
        return fuzzy_match(input_text, AVAILABLE_STYLES, "None")

    def get_aspect_ratio_from_input(self, input_text: str) -> str:
        """Fuzzy-match the user's input text to an available aspect ratio."""
        return fuzzy_match(input_text, AVAILABLE_ASPECT_RATIOS, "1:1")

    def get_resolution_from_input(self, input_text: str) -> str:
        """
        Fuzzy-match the user's input text to an available resolution.
        Also validates the resolution format.
        """
        if not input_text or input_text.lower() == "none":
            return "None"
            
        # Clean and normalize the input
        input_lower = input_text.lower().strip()
        
        # Basic format validation (widthxheight)
        if not re.match(r'^\d+x\d+$', input_lower):
            logger.warning(f"Invalid resolution format: {input_text}. Expected format: widthxheight")
            return "None"
            
        return fuzzy_match(input_text, AVAILABLE_RESOLUTIONS, "None")

    def pipe(
        self,
        user_message: str,
        model_id: str,
        messages: Optional[List[dict]] = None,
        body: Optional[dict] = None
    ) -> Union[str, Generator, Iterator]:
        """
        Primary entry point for image generation.
        Extract command-line style params (--style, --aspect, --res) from the end of the prompt,
        and pass the parameters to Replicate's 'ideogram-ai/ideogram-v2a' model.
        
        Args:
            user_message: The user's input message containing prompt and parameters
            model_id: The model ID to use (currently unused as we only support ideogram-v2a)
            messages: Optional list of previous messages (currently unused)
            body: Optional request body (currently unused)
            
        Returns:
            A string containing markdown-formatted image URL or error message 
            
        Example:
            >>> pipeline = Pipeline()
            >>> result = pipeline.pipe(
            ...     "A beautiful sunset over mountains --style Realistic --aspect 16:9"
            ... )
            >>> print(result)
            "![image](https://replicate.delivery/...)"
        """
        logger.info(f"pipe: {__name__}")
        try:
            # 1) Parse command-line style params
            params = parse_command_params(user_message)
            
            # Validate required prompt
            if not params.get("prompt", "").strip():
                return "Error: Prompt is required"
                
            # Warn about unknown parameters
            known_params = {"prompt", "style", "aspect", "res"}
            unknown_params = set(params.keys()) - known_params
            if unknown_params:
                logger.warning(f"Unknown parameters ignored: {unknown_params}")
            
            selected_style = self.get_style_from_input(params.get("style", "None"))
            selected_aspect = self.get_aspect_ratio_from_input(params.get("aspect", "1:1"))
            selected_resolution = self.get_resolution_from_input(params.get("res", "None"))
            clean_prompt = params.get("prompt", "").strip()

            logger.info(f"Matched style: {selected_style}")
            logger.info(f"Matched aspect ratio: {selected_aspect}")
            logger.info(f"Matched resolution: {selected_resolution}")
            logger.info(f"Clean prompt: {clean_prompt}")

            # 2) Prepare input params
            input_params = {
                "prompt": clean_prompt,
                "magic_prompt_option": "Auto"
            }
            
            # Handle resolution first as it overrides aspect ratio
            if selected_resolution != "None":
                try:
                    # Validate resolution format before adding
                    width, height = map(int, selected_resolution.split('x'))
                    if width <= 0 or height <= 0:
                        raise ValueError(f"Invalid resolution dimensions: {selected_resolution}")
                    input_params["resolution"] = selected_resolution
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid resolution value: {selected_resolution}. Error: {str(e)}")
                    # Fallback to aspect ratio if resolution is invalid
                    if selected_aspect != "1:1":
                        input_params["aspect_ratio"] = selected_aspect
            elif selected_aspect != "1:1":
                input_params["aspect_ratio"] = selected_aspect
                
            if selected_style != "None":
                input_params["style_type"] = selected_style

            logger.info(f"Final input params: {input_params}")

            # 3) Call the replicate model
            output = self.client.run("ideogram-ai/ideogram-v2a", input=input_params)

            # 4) Construct return message
            if output:
                # Format the single image URL as markdown
                return f"![image]({output})\n"
            else:
                return "No image was generated."
        except Exception as e:
            logger.exception("Error generating image")
            return f"Error generating image: {str(e)}"
        