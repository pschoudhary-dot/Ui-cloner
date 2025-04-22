# Multimodal Website UI Cloner

This project is a Streamlit web application that takes a screenshot of a website UI and uses a multimodal Large Language Model (LLM) to generate a single HTML file that visually clones the input image.

## How it Works

1.  **Input:** You upload a screenshot (PNG, JPG, JPEG, WEBP) of a website UI.
2.  **Provider & Model Selection:** Choose an LLM provider (OpenAI, Google Gemini, or OpenRouter) and enter the corresponding API key. Select an available vision-capable model from the chosen provider.
3.  **Generation:** The application sends the image and a prompt to the selected LLM API.
4.  **Output:** The LLM analyzes the image and generates HTML code (often including inline CSS and potentially basic JavaScript) to replicate the visual structure.
5.  **Preview & Download:** The generated HTML is displayed in an inline preview within the app, and you can download it as a `.html` file.

**Note:** This tool focuses on *visual cloning* of static elements. It does not replicate backend logic, complex JavaScript interactions, or dynamic content.

## Technologies Used

*   **Frontend:** Streamlit
*   **Image Processing:** Pillow (PIL Fork)
*   **API Interaction:** requests
*   **LLM APIs:**
    *   Google Generative AI (for Gemini models)
    *   OpenAI API (for GPT models)
    *   OpenRouter API (for various models, including free options)
*   **Core Logic:** Python

## Setup and Installation

Follow these steps to set up and run the project locally:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/pschoudhary-dot/Ui-cloner
    cd Ui-cloner
    ```

2.  **Create and Activate a Virtual Environment (Recommended):**
    *If you don't have Python installed, please download and install it from [Python's official website](https://www.python.org/downloads/)*
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **API Keys:**
    *   Obtain an API key from the provider you intend to use:
        *   **OpenAI:** [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
        *   **Google AI Studio (Gemini):** [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
        *   **OpenRouter:** [https://openrouter.ai/keys](https://openrouter.ai/keys)
    *   You will be prompted to enter the API key in the application's sidebar when you select the corresponding provider.

5.  **Run the Application:**
    ```bash
    streamlit run app.py
    ```

6.  **Open in Browser:** Streamlit will typically provide a local URL (e.g., `http://localhost:8501`) to access the application in your web browser.

Now you can select your provider, enter your API key, choose a model, upload a screenshot, and generate HTML clones!