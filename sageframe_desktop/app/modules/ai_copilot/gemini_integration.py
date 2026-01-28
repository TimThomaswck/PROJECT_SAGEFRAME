"""
Gemini LLM Integration for AI Co-Pilot

Handles Google Generative AI (Gemini) API key management and LLM-powered message generation.
"""

from typing import Optional
import keyring
import warnings
import os
import sys

# Suppress all warnings from google.generativeai package
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", module="google.generativeai")

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
except Exception:
    # If import fails for any reason, set to False
    GENAI_AVAILABLE = False


GEMINI_KEYRING_SERVICE = "sageframe_gemini_cli"
GEMINI_KEY_NAME = "api_key"


def get_gemini_api_key() -> Optional[str]:
    """
    Retrieve Gemini API key from system keyring.
    
    Returns:
        API key if available, None otherwise
    """
    try:
        api_key = keyring.get_password(GEMINI_KEYRING_SERVICE, GEMINI_KEY_NAME)
        return api_key if api_key and api_key.strip() else None
    except Exception as e:
        print(f"Error retrieving Gemini API key: {e}")
        return None


def is_gemini_configured() -> bool:
    """Check if Gemini API key is configured."""
    return get_gemini_api_key() is not None


def configure_gemini() -> bool:
    """
    Configure Gemini with stored API key.
    
    Returns:
        True if configuration successful, False otherwise
    """
    if not GENAI_AVAILABLE:
        print("Warning: google-generativeai not installed")
        return False
    
    api_key = get_gemini_api_key()
    if not api_key:
        return False
    
    try:
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        return False


def generate_with_gemini(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = "gemini-2.5-flash",
) -> Optional[str]:
    """
    Generate text using Gemini LLM.
    
    Args:
        prompt: User prompt/message
        system_prompt: System instructions for Jarvis persona
        model: Model name (default: gemini-2.5-flash for MVP, gemini-2.0-flash-exp for advanced)
        
    Returns:
        Generated text or None if error
    """
    if not GENAI_AVAILABLE:
        return None
    
    if not configure_gemini():
        return None
    
    try:
        # Use GenerativeModel with system instruction
        if system_prompt:
            model_instance = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_prompt
            )
            response = model_instance.generate_content(prompt)
        else:
            # Fallback: simple generation without system prompt
            model_instance = genai.GenerativeModel(model_name=model)
            response = model_instance.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        return None
        
    except Exception as e:
        print(f"Error generating with Gemini: {e}")
        return None
