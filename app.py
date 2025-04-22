import streamlit as st
from PIL import Image
import io
import logging
import traceback
import streamlit.components.v1 as components
from utils.config import (
    DEFAULT_PROVIDER,
    DEFAULT_OPENROUTER_MODEL_ID
)
from utils.models import (
    get_available_gemini_models,
    get_available_openrouter_models,
    get_available_openai_models
)
from utils.generation import generate_code_from_image

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration --- 
st.set_page_config(layout="wide", page_title="Multimodal Website UI Cloner")
st.title("🤖 Multimodal Website UI Cloner")
st.caption("Input a screenshot -> Get a single HTML file clone (visual only).")

# --- Provider and API Key Selection ---
st.sidebar.header("1. Provider & API Key")
provider_options = ("OpenAI", "Google Gemini", "OpenRouter")
selected_provider = st.sidebar.radio(
    "Choose LLM Provider:",
    provider_options,
    index=provider_options.index(DEFAULT_PROVIDER)
)

google_api_key = ""
openrouter_api_key = ""
openai_api_key = ""

# Conditional API Key Input
if selected_provider == "Google Gemini":
    google_api_key = st.sidebar.text_input("Google AI Studio API Key", type="password", help="Required for Gemini models.", key="google_key")
elif selected_provider == "OpenRouter":
    openrouter_api_key = st.sidebar.text_input("OpenRouter API Key", type="password", help="Required for OpenRouter models.", key="or_key")
    st.sidebar.markdown("[Get OpenRouter Key](https://openrouter.ai/keys)")
elif selected_provider == "OpenAI":
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password", help="Required for OpenAI models.", key="openai_key")
    st.sidebar.markdown("[Get OpenAI Key](https://platform.openai.com/api-keys)")

# --- Model Selection---
st.sidebar.header("2. Model Selection")
available_models = {}
model_id = None
selected_model_key = None
list_error = None

# Determine the correct API key to use for fetching models
fetch_key = openai_api_key if selected_provider == "OpenAI" else \
            google_api_key if selected_provider == "Google Gemini" else \
            openrouter_api_key

if fetch_key:
    if selected_provider == "Google Gemini":
        available_models, list_error = get_available_gemini_models(fetch_key)
    elif selected_provider == "OpenRouter":
        available_models, list_error = get_available_openrouter_models(fetch_key)
    elif selected_provider == "OpenAI":
        available_models, list_error = get_available_openai_models(fetch_key)
else:
    st.sidebar.info(f"Enter {selected_provider} API Key to list models.")

# Display errors or populate selectbox
if list_error:
    st.sidebar.error(list_error)
elif not available_models and fetch_key:
     st.sidebar.warning(f"No suitable models found for {selected_provider}. Check API key permissions or model availability.")
elif available_models:
    model_options = sorted(list(available_models.keys()))
    default_index = 0

    # Set Default Model Logic
    if selected_provider == "OpenAI":
         preferred_default_key = next((k for k in model_options if "gpt-4o" in k and "mini" not in k), None)
         if preferred_default_key:
             default_index = model_options.index(preferred_default_key)
             st.sidebar.success(f"Defaulting to {preferred_default_key}")
         else:
             st.sidebar.info(f"Using first available OpenAI model: {model_options[0]}")
    elif selected_provider == "OpenRouter":
        found_default = False
        preferred_default_key = next((k for k, v in available_models.items() if v == DEFAULT_OPENROUTER_MODEL_ID and "[⚠️" not in k), None)
        warned_default_key = next((k for k, v in available_models.items() if v == DEFAULT_OPENROUTER_MODEL_ID and "[⚠️" in k), None)
        target_key_to_find = preferred_default_key or warned_default_key

        if target_key_to_find and target_key_to_find in model_options:
            default_index = model_options.index(target_key_to_find)
            found_default = True
            if "[⚠️" in target_key_to_find:
                st.sidebar.warning(f"Default model '{DEFAULT_OPENROUTER_MODEL_ID}' selected, but may lack vision capabilities or have other limitations.")
            else:
                st.sidebar.success(f"Default free vision model '{DEFAULT_OPENROUTER_MODEL_ID}' found.")
        elif model_options: # If default not found, use the first available
             st.sidebar.warning(f"Requested default '{DEFAULT_OPENROUTER_MODEL_ID}' not found/suitable. Using first available: {model_options[0]}")
    elif selected_provider == "Google Gemini":
        preferred_default_key = next((k for k in model_options if "1.5 Pro" in k), None)
        if preferred_default_key:
            default_index = model_options.index(preferred_default_key)
            st.sidebar.success(f"Defaulting to {preferred_default_key}")
        else:
            st.sidebar.info(f"Using first available Gemini model: {model_options[0]}")

    selected_model_key = st.sidebar.selectbox(
        f"Choose Available {selected_provider} Model:",
        options=model_options,
        index=default_index,
        key=f"model_select_{selected_provider}",
        help="Select a model. Models with [⚠️] might have limitations (e.g., text-only)." + (" (Free only)" if selected_provider == "OpenRouter" else "")
    )
    if selected_model_key:
        model_id = available_models[selected_model_key]
        st.sidebar.info(f"Selected Model ID: `{model_id}`")

# --- Input Method ---
st.sidebar.header("3. Input")
actual_api_key = openai_api_key if selected_provider == "OpenAI" else \
                 google_api_key if selected_provider == "Google Gemini" else \
                 openrouter_api_key

input_disabled = not model_id or not actual_api_key

# input_method = st.sidebar.radio("Choose input method:", ("Website URL", "Upload Screenshot"), disabled=input_disabled, key="input_method") # Remove URL option
uploaded_file = st.sidebar.file_uploader("Upload Screenshot:", type=["png", "jpg", "jpeg", "webp"], disabled=input_disabled, key="file_uploader")

screenshot_bytes = None
# url_input = "" # Remove URL variable
# uploaded_file = None # Already defined above

# if input_method == "Website URL":
#     #url_input = st.sidebar.text_input("Enter Website URL:", "https://streamlit.io", disabled=input_disabled, key="url_input")
#     st.write("Inprogressssss!")
# else:
#     uploaded_file = st.sidebar.file_uploader("Upload Screenshot:", type=["png", "jpg", "jpeg", "webp"], disabled=input_disabled, key="file_uploader")


submit_button = st.sidebar.button("Generate Clone", disabled=input_disabled, type="primary")

# --- Main Area---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Input Image")
    input_image_placeholder = st.empty()
    input_image_placeholder.info("Provide a screenshot and click 'Generate'.")

with col2:
    st.subheader("Generated HTML Output")
    output_placeholder = st.empty()
    output_placeholder.info("Generated HTML preview and download link will appear here.")

if submit_button:
    img_bytes = None
    error_msg = None
    input_image_placeholder.empty()
    output_placeholder.empty()

    with st.spinner("Processing input..."):
        # if input_method == "Website URL":
        #     if url_input:
        #         logging.info(f"Taking screenshot for URL: {url_input}")
        #         img_bytes, error_msg = take_screenshot(url_input)
        #         if error_msg:
        #             st.error(f"Screenshot Error: {error_msg}")
        #         elif not img_bytes:
        #             st.error("Screenshot failed: No image data received.")
        #     else:
        #         st.warning("Please enter a Website URL.")
        if uploaded_file:
            logging.info(f"Reading uploaded file: {uploaded_file.name}")
            img_bytes = uploaded_file.getvalue()
        else:
            st.warning("Please upload a screenshot file.")

    if img_bytes:
        try:
            # Display the input image
            img_pil = Image.open(io.BytesIO(img_bytes))
            with col1:
                st.image(img_pil, caption="Input Screenshot", use_container_width=True)

            # Generate Code
            with st.spinner(f"Generating HTML with {selected_provider} ({model_id})... This may take a minute or two."):
                generated_html, gen_error = generate_code_from_image(
                    provider=selected_provider,
                    api_key=actual_api_key,
                    model_id_to_use=model_id,
                    img_bytes=img_bytes
                )

            # Display Output or Error
            with col2:
                if gen_error:
                    st.error(f"Code Generation Error: {gen_error}")
                elif generated_html:
                    st.success("HTML generation complete!")

                    # Display HTML Preview
                    st.subheader("Preview")
                    components.html(generated_html, height=600, scrolling=True)

                    # Provide Download Button
                    st.subheader("Download")
                    st.download_button(
                        label="Download HTML File",
                        data=generated_html,
                        file_name="generated_clone.html",
                        mime="text/html",
                    )
                else:
                    st.error("Code generation failed: No HTML content received.")

        except Exception as e:
            st.error(f"An unexpected error occurred in the main process: {e}\n{traceback.format_exc()}")
            logging.error(f"Main process error: {e}\n{traceback.format_exc()}")
    elif not error_msg:
        st.warning("Could not proceed without a valid input image.")

# --- Footer/Instructions --- # Remove this section
# st.sidebar.markdown("---")
# st.sidebar.markdown("**How it works:**")
# st.sidebar.markdown("1. Choose your LLM provider (OpenAI, Gemini, or OpenRouter) and enter your API key.")
# st.sidebar.markdown("2. Select an available model (vision-capable models are preferred). OpenRouter shows all free models.")
# st.sidebar.markdown("3. Enter a website URL (a screenshot will be taken) or upload a screenshot image.")
# st.sidebar.markdown("4. Click 'Generate HTML Clone'.")
# st.sidebar.markdown("5. The AI analyzes the image and generates HTML/CSS code to replicate the visual structure.")
# st.sidebar.markdown("6. A preview is shown, and you can download the generated HTML file.")
# st.sidebar.markdown("**Note:** This tool focuses on *visual cloning* of static elements. It does not replicate backend logic, complex JavaScript interactions, or dynamic content.")