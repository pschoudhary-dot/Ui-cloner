import google.generativeai as genai
from openai import OpenAI
import requests
import base64
import io
import re
from PIL import Image
import logging
import traceback
from .config import API_TIMEOUT
from .prompts import SYSTEM_PROMPT

def generate_code_from_image(provider, api_key, model_id_to_use, img_bytes):
    """Generates a single HTML file using the selected provider and model."""
    if not api_key: return None, f"{provider} API Key is missing."
    if not model_id_to_use: return None, "Model ID is missing."
    if not img_bytes: return None, "Image data is missing."

    logging.info(f"Generating code using {provider} model: {model_id_to_use}")

    prompt = SYSTEM_PROMPT

    try:
        # --- Encode Image for APIs that need it ---
        base64_image = base64.b64encode(img_bytes).decode('utf-8')
        image_data_url = f"data:image/png;base64,{base64_image}"

        # --- Provider-Specific API Calls ---
        generated_html = None
        error_message = None
        api_timeout = API_TIMEOUT

        if provider == "Google Gemini":
            genai.configure(api_key=api_key)
            img_pil = Image.open(io.BytesIO(img_bytes))
            generation_config = genai.GenerationConfig(temperature=0.25)
            model = genai.GenerativeModel(model_id_to_use, generation_config=generation_config)
            logging.info(f"Calling Gemini model {model_id_to_use}...")
            response = model.generate_content([prompt, img_pil], request_options={'timeout': api_timeout})

            if not response.parts:
                 reason = "Unknown reason."
                 if hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
                     reason = f"Blocked: {response.prompt_feedback.block_reason}"
                 elif hasattr(response, 'candidates') and response.candidates and response.candidates[0].finish_reason != 'STOP':
                     reason = f"Finished early: {response.candidates[0].finish_reason}"
                 error_message = f"Gemini: Failed to generate content. {reason}"
                 logging.error(error_message)
                 return None, error_message

            generated_html = response.text
            logging.info(f"Gemini: Code generation successful (length: {len(generated_html)}).")

        elif provider == "OpenRouter":
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
            logging.info(f"Calling OpenRouter model {model_id_to_use}...")
            response = client.chat.completions.create(
                model=model_id_to_use,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data_url
                                },
                            },
                        ],
                    }
                ],
                #max_tokens=4096,
                temperature=0.1,
                timeout=api_timeout
            )
            generated_html = response.choices[0].message.content
            logging.info(f"OpenRouter: Code generation successful (length: {len(generated_html)}).")

        elif provider == "OpenAI":
            client = OpenAI(api_key=api_key)
            logging.info(f"Calling OpenAI model {model_id_to_use}...")
            response = client.chat.completions.create(
                model=model_id_to_use,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data_url,
                                    "detail": "high"
                                },
                            },
                        ],
                    }
                ],
                #max_tokens=4096,
                temperature=0.1,
                timeout=api_timeout
            )
            generated_html = response.choices[0].message.content
            logging.info(f"OpenAI: Code generation successful (length: {len(generated_html)}).")

        # --- Post-processing and Validation ---
        if generated_html:
            if not generated_html.strip().lower().startswith("<!doctype html") and not generated_html.strip().lower().startswith("<html"):
                logging.warning(f"{provider}: Output doesn't start with <!DOCTYPE html> or <html>. It might be incomplete or contain extra text.")
                match = re.search(r"```html\n(.*?)```", generated_html, re.DOTALL | re.IGNORECASE)
                if match:
                    generated_html = match.group(1).strip()
                    logging.info("Extracted HTML from markdown code block.")
                else:
                    if "<head>" in generated_html.lower() and "<body>" in generated_html.lower():
                         logging.warning("HTML detected but missing doctype. Proceeding cautiously.")
                    else:
                        error_message = f"{provider}: Generated output does not appear to be valid HTML code. It might be an error message or explanation instead."
                        logging.error(error_message)
                        return None, error_message

        return generated_html, None 

    except genai.types.BlockedPromptException as e:
        error_message = f"Gemini: Prompt blocked. {e}"
        logging.error(error_message)
        return None, error_message
    except genai.types.StopCandidateException as e:
        error_message = f"Gemini: Generation stopped unexpectedly. {e}"
        logging.error(error_message)
        return None, error_message
    except requests.exceptions.RequestException as e:
        error_message = f"{provider}: API request failed (Network/Connection Error): {e}"
        logging.error(error_message)
        return None, error_message
    except OpenAI.APIStatusError as e:
        error_message = f"{provider}: API Error ({e.status_code}): {e.message}"
        logging.error(error_message)
        return None, error_message
    except OpenAI.APIConnectionError as e:
        error_message = f"{provider}: API Connection Error: {e}"
        logging.error(error_message)
        return None, error_message
    except OpenAI.AuthenticationError as e:
        error_message = f"{provider}: Authentication Error - Check your API Key. {e}"
        logging.error(error_message)
        return None, error_message
    except OpenAI.RateLimitError as e:
        error_message = f"{provider}: Rate Limit Exceeded. Please wait and try again. {e}"
        logging.error(error_message)
        return None, error_message
    except OpenAI.APITimeoutError as e:
        error_message = f"{provider}: API Request Timed Out. {e}"
        logging.error(error_message)
        return None, error_message
    except Exception as e:
        error_message = f"{provider}: An unexpected error occurred during code generation: {e}\n{traceback.format_exc()}"
        logging.error(error_message)
        return None, error_message