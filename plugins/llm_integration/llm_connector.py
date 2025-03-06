"""
LLM connector for DigiPet application.
Handles the interface to language model APIs.
"""
import logging
import time
import json
import random
from typing import Dict, List, Any, Optional
import requests

logger = logging.getLogger(__name__)

class LLMConnector:
    """
    Connects to a language model API for generating responses.
    
    Attributes:
        api_key (str): API key for the LLM service
        model (str): Model identifier to use
        api_url (str): URL for the API endpoint
        headers (dict): HTTP headers for API requests
        max_retries (int): Maximum number of request retries
    """
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        Initialize the LLM connector.
        
        Args:
            api_key (str): API key for the LLM service
            model (str, optional): Model identifier to use
        """
        self.api_key = api_key
        self.model = model
        
        # API configuration
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self.max_retries = 3
        
        logger.debug(f"LLM connector initialized with model: {model}")
    
    def check_availability(self) -> bool:
        """
        Check if the LLM API is available.
        
        Returns:
            bool: True if the API is available, False otherwise
        """
        try:
            # Test with a simple request
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers=self.headers,
                timeout=5
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                logger.info("LLM API is available")
                return True
            else:
                logger.warning(f"LLM API returned status {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Error checking LLM API availability: {e}")
            return False
    
    def generate_response(self, prompt: str, max_tokens: int = 100, temperature: float = 0.7) -> Optional[str]:
        """
        Generate a response using the LLM API.
        
        Args:
            prompt (str): The prompt to send to the LLM
            max_tokens (int, optional): Maximum response length
            temperature (float, optional): Randomness parameter
        
        Returns:
            Optional[str]: The generated response, or None if an error occurred
        """
        # Prepare the request payload
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        
        # Try to send the request with retries
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    data=json.dumps(payload),
                    timeout=10
                )
                
                # Check if the request was successful
                if response.status_code == 200:
                    # Parse the response
                    result = response.json()
                    
                    # Extract the generated text
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content'].strip()
                        logger.debug(f"Generated response: {content[:50]}...")
                        return content
                
                # Handle rate limiting
                elif response.status_code == 429:
                    logger.warning(f"Rate limited by LLM API (attempt {attempt+1}/{self.max_retries})")
                    
                    # Extract retry delay if available
                    retry_after = response.headers.get('Retry-After', '1')
                    delay = int(retry_after) if retry_after.isdigit() else 1
                    
                    # Wait before retrying
                    time.sleep(delay + 1)
                    continue
                
                # Handle other errors
                else:
                    logger.error(f"LLM API returned status {response.status_code}: {response.text}")
                    
                    # Only retry on server errors
                    if response.status_code >= 500:
                        time.sleep(1)
                        continue
                    else:
                        return None
            
            except Exception as e:
                logger.error(f"Error generating response (attempt {attempt+1}/{self.max_retries}): {e}")
                time.sleep(1)
        
        # If we get here, all retries failed
        logger.error(f"Failed to generate response after {self.max_retries} attempts")
        return None
    
    def generate_chat_response(self, messages: List[Dict[str, str]], max_tokens: int = 100, temperature: float = 0.7) -> Optional[str]:
        """
        Generate a response using the LLM API with a chat history.
        
        Args:
            messages (list): List of message dictionaries with 'role' and 'content'
            max_tokens (int, optional): Maximum response length
            temperature (float, optional): Randomness parameter
        
        Returns:
            Optional[str]: The generated response, or None if an error occurred
        """
        # Prepare the request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        
        # Try to send the request with retries
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    data=json.dumps(payload),
                    timeout=10
                )
                
                # Check if the request was successful
                if response.status_code == 200:
                    # Parse the response
                    result = response.json()
                    
                    # Extract the generated text
                    if 'choices' in result and len(result['choices']) > 0:
                        content = result['choices'][0]['message']['content'].strip()
                        logger.debug(f"Generated chat response: {content[:50]}...")
                        return content
                
                # Handle rate limiting
                elif response.status_code == 429:
                    logger.warning(f"Rate limited by LLM API (attempt {attempt+1}/{self.max_retries})")
                    
                    # Extract retry delay if available
                    retry_after = response.headers.get('Retry-After', '1')
                    delay = int(retry_after) if retry_after.isdigit() else 1
                    
                    # Wait before retrying
                    time.sleep(delay + 1)
                    continue
                
                # Handle other errors
                else:
                    logger.error(f"LLM API returned status {response.status_code}: {response.text}")
                    
                    # Only retry on server errors
                    if response.status_code >= 500:
                        time.sleep(1)
                        continue
                    else:
                        return None
            
            except Exception as e:
                logger.error(f"Error generating chat response (attempt {attempt+1}/{self.max_retries}): {e}")
                time.sleep(1)
        
        # If we get here, all retries failed
        logger.error(f"Failed to generate chat response after {self.max_retries} attempts")
        return None