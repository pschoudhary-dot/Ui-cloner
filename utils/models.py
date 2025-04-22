import streamlit as st
import google.generativeai as genai
from openai import OpenAI
import requests
import logging
from .config import (
    KNOWN_GEMINI_VISION_MODELS,
    KNOWN_OPENROUTER_FREE_VISION_MODELS,
    KNOWN_OPENROUTER_FREE_MODELS_WITH_WARNING,
    KNOWN_OPENAI_VISION_MODELS
)

@st.cache_data(ttl=3600)
def get_available_gemini_models(api_key):
    """Fetches and filters Gemini models supporting 'generateContent' (implies vision)."""
    available_models_dict = {}
    error_message = None
    if not api_key: return {}, "Google API Key is missing."
    logging.info("Fetching Gemini models...")
    try:
        genai.configure(api_key=api_key)
        models = genai.list_models()
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                 base_model_name = m.name.split('/')[-1].split('-preview')[0].replace('-latest', '')
                 is_known_vision = any(known_base in base_model_name for known_base in KNOWN_GEMINI_VISION_MODELS)
                 if is_known_vision:
                    display_key = f"{m.display_name} ({m.name.split('/')[-1]})"
                    available_models_dict[display_key] = m.name
                    logging.info(f"Found suitable Gemini model: {display_key}")
    except Exception as e:
        error_message = f"Gemini: Could not list models. Check API key/network: {e}"
        logging.error(error_message)
        genai.configure(api_key="INVALID_KEY_AFTER_ERROR")
    if not available_models_dict and not error_message:
        error_message = "Gemini: No vision-capable models found with this key."
    return available_models_dict, error_message

@st.cache_data(ttl=3600)
def get_available_openrouter_models(api_key):
    """Fetches OpenRouter models, filters for FREE models, and adds warnings for non-vision ones."""
    available_models_dict = {}
    error_message = None
    if not api_key: return {}, "OpenRouter API Key is missing."
    logging.info("Fetching OpenRouter models...")
    try:
        response = requests.get("https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {api_key}"})
        response.raise_for_status()
        models_data = response.json().get('data', [])

        for model in models_data:
            model_id = model.get('id')
            pricing = model.get('pricing', {})
            is_free = pricing.get('prompt') == "0" and pricing.get('completion') == "0"

            if is_free:
                model_name = model.get('name', model_id)
                display_key_base = f"{model_name} (ID: {model_id})"

                # Check if it's a known vision model or heuristically likely
                is_known_vision = model_id in KNOWN_OPENROUTER_FREE_VISION_MODELS or \
                                  any(term in model_id.lower() for term in ["vision", "gpt-4o", "claude-3"])
                is_warned_model = model_id in KNOWN_OPENROUTER_FREE_MODELS_WITH_WARNING

                # Add all free models, but add a warning if not known/likely vision
                if is_known_vision or is_warned_model:
                    display_key = display_key_base
                    if not is_known_vision:
                        display_key += " [⚠️ Text Only?]"
                        logging.warning(f"Found free model '{model_id}' but it might lack vision support.")
                    else:
                         logging.info(f"Found suitable Free OpenRouter Vision model: {display_key_base}")
                    available_models_dict[display_key] = model_id
                else:
                    # Include other free models without explicit vision check, but add warning
                    display_key = f"{display_key_base} [⚠️ Vision? Check Docs]"
                    available_models_dict[display_key] = model_id
                    logging.info(f"Found other free OpenRouter model: {display_key_base} (Vision capability unknown)")


    except requests.exceptions.RequestException as e:
        error_message = f"OpenRouter: Could not list models. Check API key/network: {e}"
        logging.error(error_message)
    except Exception as e:
        error_message = f"OpenRouter: Error processing models list: {e}"
        logging.error(error_message)

    if not available_models_dict and not error_message:
        error_message = "OpenRouter: No FREE models found."
    return available_models_dict, error_message

@st.cache_data(ttl=3600) # Cache for 1 hour
def get_available_openai_models(api_key):
    """Fetches OpenAI models and filters for known VISION models."""
    available_models_dict = {}
    error_message = None
    if not api_key: return {}, "OpenAI API Key is missing."
    logging.info("Fetching OpenAI models...")
    try:
        # Use a placeholder if key is invalid just for listing, actual call needs valid key
        client = OpenAI(api_key=api_key if api_key else "DUMMY_KEY")
        models = client.models.list()
        for model in models.data:
            model_id = model.id
            # Filter based on known vision model identifiers
            is_known_vision = any(known_id in model_id for known_id in KNOWN_OPENAI_VISION_MODELS)
            if is_known_vision:
                display_key = f"OpenAI: {model_id}"
                available_models_dict[display_key] = model_id
                logging.info(f"Found suitable OpenAI model: {display_key}")

    except Exception as e:
        if "Incorrect API key" in str(e):
             error_message = "OpenAI: Incorrect API key provided."
        else:
             error_message = f"OpenAI: Could not list models. Check API key/permissions: {e}"
        logging.error(error_message)
    if not available_models_dict and not error_message:
        error_message = "OpenAI: No models matching known vision capabilities found."
    return available_models_dict, error_message