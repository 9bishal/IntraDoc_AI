"""
LLM Integration — Groq API interface.

Provides clean abstraction for:
1. Text generation using Groq API (free, fast, reliable)
2. Health checks for Groq connectivity
3. Support for Mixtral-8x7B, Llama2-70B, etc.
"""

import os
import requests
import logging

logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Custom exception for LLM-related errors."""
    pass


def get_llm_config():
    """
    Get LLM configuration from environment variables.

    Returns:
        dict: {
            'api_key': str,
            'model': str,
            'timeout': int,
            'api_url': str
        }
    """
    return {
        'api_key': os.getenv('GROQ_API_KEY', ''),
        'model': os.getenv('LLM_MODEL', 'llama-3.1-8b-instant'),
        'timeout': int(os.getenv('LLM_TIMEOUT', '120')),
        'api_url': 'https://api.groq.com/openai/v1',
    }


def generate_response(messages, model=None, timeout=None):
    """
    Generate a response from Groq API using the specified model.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
                 [
                     {"role": "system", "content": "..."},
                     {"role": "user", "content": "..."}
                 ]
        model: Optional model name. Defaults to LLM_MODEL env var or 'mixtral-8x7b-32768'
        timeout: Optional timeout in seconds. Defaults to LLM_TIMEOUT or 120

    Returns:
        generator: Yields response text chunks

    Raises:
        OllamaError: If connection fails, times out, or returns an error
    """
    config = get_llm_config()
    model = model or config['model']
    timeout = timeout or config['timeout']

    # Validate API key
    if not config['api_key']:
        raise OllamaError(
            "GROQ_API_KEY environment variable is not set. "
            "Please configure your Groq API key in .env file."
        )

    url = f"{config['api_url']}/chat/completions"

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 512,
    }

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    try:
        logger.info(f"Sending request to Groq API: {model}")
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)

        if response.status_code != 200:
            error_detail = response.text
            try:
                error_data = response.json()
                error_detail = error_data.get('error', {}).get('message', response.text)
            except:
                pass
            raise OllamaError(
                f"Groq API error: {response.status_code} - {error_detail}"
            )

        data = response.json()
        choices = data.get('choices', [])
        
        if not choices:
            raise OllamaError("Groq API returned no response choices")
        
        message = choices[0].get('message', {})
        response_text = message.get('content', '')

        if not response_text:
            raise OllamaError("Groq API returned an empty response")

        # Yield the response as a generator to match streaming interface
        yield response_text

    except OllamaError:
        # Re-raise OllamaError to be caught by RAG pipeline
        raise
    except requests.exceptions.ConnectionError as e:
        raise OllamaError(
            f"Cannot connect to Groq API. Check your internet connection and API key."
        )
    except requests.exceptions.Timeout as e:
        raise OllamaError(
            f"Groq API request timed out after {timeout}s. "
            f"Try increasing LLM_TIMEOUT env variable."
        )
    except requests.exceptions.RequestException as e:
        raise OllamaError(f"Groq API request failed: {str(e)}")
    except ValueError as e:
        raise OllamaError(f"Failed to parse Groq API response: {str(e)}")


def check_ollama_health():
    """
    Check if Groq API is accessible.

    Returns:
        dict: {
            'ollama_reachable': bool,
            'model_available': bool,
            'available_models': list,
            'error': str or None
        }
    """
    config = get_llm_config()
    
    # Check if the API key is set
    has_api_key = bool(config.get('api_key'))
    
    if not has_api_key:
        return {
            'ollama_reachable': False,
            'model_available': False,
            'available_models': [config['model']],
            'error': 'GROQ_API_KEY not configured. Please set GROQ_API_KEY in .env file.',
        }
    
    # Simple connectivity check by attempting a minimal request
    url = f"{config['api_url']}/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": config['model'],
        "messages": [
            {"role": "user", "content": "ping"}
        ],
        "max_tokens": 10,
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return {
                'ollama_reachable': True,
                'model_available': True,
                'available_models': [config['model']],
                'error': None,
            }
        else:
            try:
                error_msg = response.json().get('error', {}).get('message', response.text)
            except:
                error_msg = response.text
            return {
                'ollama_reachable': False,
                'model_available': False,
                'available_models': [config['model']],
                'error': f"Groq API returned: {error_msg}",
            }

    except requests.exceptions.RequestException as e:
        return {
            'ollama_reachable': False,
            'model_available': False,
            'available_models': [config['model']],
            'error': f"Cannot reach Groq API: {str(e)}",
        }
    except Exception as e:
        return {
            'ollama_reachable': False,
            'model_available': False,
            'available_models': [config['model']],
            'error': f"Groq health check failed: {str(e)}",
        }
