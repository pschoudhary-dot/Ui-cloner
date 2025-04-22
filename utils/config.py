# --- Known Vision Models---
KNOWN_GEMINI_VISION_MODELS = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro-vision"]
KNOWN_OPENROUTER_FREE_VISION_MODELS = [
    "nousresearch/nous-hermes-2-vision-alpha",
]
# Add the user's requested default, but it's likely text-only
KNOWN_OPENROUTER_FREE_MODELS_WITH_WARNING = [
    "deepseek/deepseek-chat-v3-0324:free",
]
# --- Known OpenAI Vision Models ---
KNOWN_OPENAI_VISION_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]

DEFAULT_OPENROUTER_MODEL_ID = "deepseek/deepseek-chat-v3-0324:free"
DEFAULT_OPENAI_MODEL_ID = "gpt-4o"

# --- Default Provider ---
DEFAULT_PROVIDER = "OpenAI"

# --- API Call Timeout ---
API_TIMEOUT = 300 # seconds