# AI-Powered CV Generator - Frontend

This is the frontend and orchestration component of the AI-Powered CV Generator. It provides a web interface for users to input their professional information, which is then used to scrape web content and generate a tailored CV using a local Large Language Model (LLM) via Ollama.

## Table of Contents

- [Description](#description)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Description

This application serves as the user-facing part of the CV generation suite. It consists of a simple web UI built with HTML and Tailwind CSS, and a Flask backend that acts as an orchestrator. The user provides URLs to their online profiles (like GitHub or a personal blog), a job description for a role they're targeting, and any other relevant details.

The Flask application then coordinates with two external services:
1.  **Web Scraper API**: A separate backend service that crawls the provided URLs and extracts clean text content.
2.  **Ollama**: A service for running large language models locally. It takes the scraped content and user inputs to generate a professional CV.

The final CV is presented in Markdown format and can be downloaded as a styled PDF.

## Architecture

The system is composed of three main services that work together:

1.  **Frontend & Orchestrator (This Repository)**: A Flask application that serves the `index.html` user interface and handles the business logic. It makes requests to the Scraper API and the Ollama API.
2.  **Web Scraper API**: A separate FastAPI backend responsible for crawling web pages and extracting text. This must be running and accessible by the Flask app.
3.  **Ollama Service**: A running instance of [Ollama](https://ollama.com/) with one or more LLMs downloaded (e.g., Llama 3, Mistral). This service handles the actual CV text generation.

The data flow is as follows:
`User Interface -> Flask App -> Scraper API -> Flask App -> Ollama API -> Flask App -> User Interface`

## Features

-   **Simple Web Interface**: Clean, single-page application for easy user input.
-   **Multi-URL Scraping**: Ability to provide multiple URLs with configurable scraping depth for each.
-   **AI-Powered Content Generation**: Leverages a local LLM via Ollama to synthesize information and write a professional CV.
-   **Targeted CVs**: Tailors the generated CV based on a provided job description.
-   **Interactive Prompt Editing**: Allows the user to review and edit the final prompt before it's sent to the AI.
-   **Real-time Progress Log**: Shows the status of scraping and generation steps.
-   **PDF Download**: Converts the final Markdown CV into a professionally styled PDF document.

## Prerequisites

Before you can run this application, you must have the following services running and accessible:

1.  **Web Scraper API**: The scraper backend component must be running. Please refer to its `README.md` for setup instructions.
2.  **Ollama**: You must have Ollama installed and running on your machine or network.
    -   Download from [ollama.com](https://ollama.com/).
    -   Pull at least one model, for example:
        ```bash
        ollama pull llama3
        ```
3.  **Python**: Python 3.8 or newer.
4.  **Pip**: The Python package installer.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For macOS/Linux
    python3 -m venv env
    source env/bin/activate

    # For Windows
    python -m venv env
    .\env\Scripts\activate
    ```

3.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a file named `.env` in the root of the project directory. This file will store the URLs for your dependency services.

    ```env
    # .env file
    # URL for the running Web Scraper API
    SCRAPER_API_URL="http://localhost:8000/scrape"

    # URL for the running Ollama service
    OLLAMA_API_URL="http://localhost:11434"

    # Optional: Set the host and port for this Flask app
    FLASK_HOST="127.0.0.1"
    FLASK_PORT="5001"
    ```
    *Note: Adjust the URLs if your services are running on different hosts or ports.*

## Usage

1.  **Run the Flask application:**
    For development:
    ```bash
    python app.py
    ```
    For production, it is recommended to use a WSGI server like Gunicorn:
    ```bash
    gunicorn --bind ${FLASK_HOST}:${FLASK_PORT} app:app
    ```

2.  **Access the application:**
    Open your web browser and navigate to `http://127.0.0.1:5001` (or the host and port you configured).

3.  **Generate a CV:**
    -   Fill in the "Info Links" with URLs to your online profiles (GitHub, LinkedIn, portfolio, etc.) and select a scrape depth.
    -   Paste the target job description.
    -   Add any other details you want the AI to consider.
    -   Select an available AI model from the dropdown.
    -   Click "Start Process".
    -   Review the generated prompt in the modal and click "Generate CV with this Prompt".
    -   Edit the generated CV in the text area if needed, and click "Download PDF".

## Configuration

The application's behavior can be configured via environment variables, which can be placed in a `.env` file.

| Variable          | Description                                           | Default                    |
| ----------------- | ----------------------------------------------------- | -------------------------- |
| `SCRAPER_API_URL` | The full endpoint URL for the Web Scraper API.        | `http://localhost:8000/scrape` |
| `OLLAMA_API_URL`  | The base URL for the Ollama API service.              | `http://localhost:11434`   |
| `FLASK_HOST`      | The host address for the Flask application to run on. | `127.0.0.1`                |
| `FLASK_PORT`      | The port for the Flask application to run on.         | `5001`                     |

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for bugs, feature requests, or improvements.

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
