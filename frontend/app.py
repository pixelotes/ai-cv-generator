import os
import requests
import markdown2
import io
import concurrent.futures
from flask import Flask, request, jsonify, render_template, send_file
from weasyprint import HTML, CSS
from dotenv import load_dotenv

# Load environment variables from a .env file for configuration
load_dotenv()

# --- Configuration ---
app = Flask(__name__)

# Get config from environment variables or use defaults
SCRAPER_API_URL = os.getenv("SCRAPER_API_URL", "http://localhost:8000/scrape")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
SCRAPER_TIMEOUT = 180
OLLAMA_TIMEOUT = 600
SINGLE_URL_TIMEOUT = 90

# --- PDF Styling ---
PDF_STYLES = """
@page { size: A4; margin: 1.5cm; }
body { font-family: 'Helvetica', 'Arial', sans-serif; line-height: 1.6; color: #333; }
h1 { color: #1a202c; border-bottom: 2px solid #2d3748; padding-bottom: 5px; margin-bottom: 0.5em; font-size: 24pt; text-align: center; }
h2 { color: #2d3748; border-bottom: 1px solid #718096; padding-bottom: 3px; margin-top: 1.2em; margin-bottom: 0.8em; font-size: 16pt; }
p, ul { margin-bottom: 1em; }
ul { padding-left: 20px; list-style-type: disc; }
li { margin-bottom: 0.3em; }
a { color: #2b6cb0; text-decoration: none; }
strong { color: #2d3748; }
"""

# --- Routes ---

@app.route('/')
def index():
    """Renders the main HTML page."""
    return render_template('index.html')

@app.route('/health_checks')
def health_checks():
    """Checks the status of the scraper API and Ollama, and fetches Ollama models."""
    status = {"scraper": False, "ollama": False, "ollama_models": []}
    try:
        scraper_base_url = SCRAPER_API_URL.replace('/scrape', '')
        response = requests.get(f"{scraper_base_url}/health", timeout=3)
        if response.ok and response.json().get("status") == "healthy":
            status["scraper"] = True
    except requests.exceptions.RequestException:
        status["scraper"] = False
    try:
        response = requests.get(f"{OLLAMA_API_URL}/api/tags", timeout=3)
        if response.ok:
            status["ollama"] = True
            models_data = response.json().get("models", [])
            status["ollama_models"] = [model.get("name") for model in models_data]
    except requests.exceptions.RequestException:
        status["ollama"] = False
    return jsonify(status)

def scrape_url(url, depth):
    """
    Helper function to scrape a single URL with a specific depth.
    """
    try:
        scraper_payload = {
            "url": url,
            "depth": int(depth),
            "max_pages": 10
        }
        response = requests.post(SCRAPER_API_URL, json=scraper_payload, timeout=SINGLE_URL_TIMEOUT)
        response.raise_for_status()
        
        result = response.json()
        if result.get("success"):
            return {"url": url, "success": True, "content": result.get('content', '')}
        else:
            return {"url": url, "success": False, "error": result.get('error', 'Unknown error')}
            
    except requests.exceptions.Timeout:
        return {"url": url, "success": False, "error": f"Request timed out after {SINGLE_URL_TIMEOUT}s"}
    except (requests.exceptions.RequestException, ValueError) as e:
        return {"url": url, "success": False, "error": str(e)}

@app.route('/scrape_urls', methods=['POST'])
def scrape_urls_endpoint():
    """
    Endpoint receives a list of objects, each with a URL and a depth, and scrapes them.
    """
    data = request.get_json()
    urls_with_depth = data.get('urls_with_depth', [])
    if not urls_with_depth:
        return jsonify({"error": "At least one URL with depth is required."}), 400

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(scrape_url, item['url'], item['depth']): item['url'] for item in urls_with_depth}
        try:
            for future in concurrent.futures.as_completed(future_to_url, timeout=SCRAPER_TIMEOUT):
                results.append(future.result())
        except concurrent.futures.TimeoutError:
             return jsonify({"error": f"Scraping process timed out after {SCRAPER_TIMEOUT} seconds."}), 504
    
    return jsonify({"results": results})

@app.route('/generate_prompt', methods=['POST'])
def generate_prompt_endpoint():
    """
    NEW: Takes scraped data and other details and constructs the Ollama prompt.
    """
    data = request.get_json()
    scraped_results = data.get('scrapedResults', [])
    job_offer = data.get('jobOffer', '')
    additional_details = data.get('additionalDetails', '')

    scraped_text_parts = []
    for result in scraped_results:
        if result.get("success"):
            scraped_text_parts.append(f"--- Content from {result.get('url')} ---\n{result.get('content')}\n\n")
    
    if not scraped_text_parts:
        return jsonify({"error": "No content was successfully scraped. Cannot generate a prompt."}), 400

    scraped_text = "\n".join(scraped_text_parts)
    prompt = f"""
You are an expert CV and resume writer. Your task is to create a professional, concise, and compelling curriculum vitae (CV) based on the information provided below. The output must be in clean, well-structured Markdown format.

**Candidate Information (from web scraping):**
{scraped_text}

**Additional Details provided by the candidate:**
{additional_details}

**Target Job Description:**
{job_offer}

**Instructions:**
1. Synthesize all provided information into a coherent CV.
2. Tailor the CV to the **Target Job Description**.
3. Use standard sections: Name/Contact, Professional Summary, Work Experience, Skills, Education, Projects.
4. The final output must be only the CV in Markdown format. Do not add any extra text or explanations.
"""
    return jsonify({"prompt": prompt})


@app.route('/create_final_cv', methods=['POST'])
def create_final_cv():
    """
    UPDATED: Takes a final prompt and a model, and generates the CV using Ollama.
    """
    data = request.get_json()
    prompt = data.get('prompt')
    model = data.get('model')

    if not model or not prompt:
        return jsonify({"error": "A model and a prompt are required."}), 400

    try:
        ollama_payload = {"model": model, "prompt": prompt, "stream": False}
        response = requests.post(f"{OLLAMA_API_URL}/api/generate", json=ollama_payload, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        
        raw_response = response.json().get("response", "Error: No response text from Ollama.")

        cv_start_index = raw_response.find("# ")
        if cv_start_index != -1:
            cv_text = raw_response[cv_start_index:]
        else:
            cv_text = raw_response

        return jsonify({"cv": cv_text})

    except requests.exceptions.Timeout:
        return jsonify({"error": f"Ollama generation timed out after {OLLAMA_TIMEOUT} seconds."}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to communicate with Ollama: {str(e)}"}), 500


@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    """Converts the provided Markdown CV text into a styled PDF for download."""
    data = request.get_json()
    cv_markdown = data.get('cv_markdown')
    if not cv_markdown:
        return jsonify({"error": "No CV content provided."}), 400
    html_content = markdown2.markdown(cv_markdown, extras=["tables", "fenced-code-blocks"])
    try:
        html = HTML(string=html_content)
        css = CSS(string=PDF_STYLES)
        pdf_bytes = html.write_pdf(stylesheets=[css])
        return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf', as_attachment=True, download_name='Generated_CV.pdf')
    except Exception as e:
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500


if __name__ == '__main__':
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", 5001))
    app.run(host=host, port=port, debug=True)
