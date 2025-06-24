# Advanced Web Scraper API
A high-performance FastAPI-based web scraping service that extracts text content from URLs with advanced features like JavaScript rendering, CSS selectors, and configurable depth crawling.

## Features
Dynamic & Static Scraping: Choose between fast HTTP requests for static sites and full browser rendering for JavaScript-heavy applications.

- Depth-based Crawling: Crawl websites up to 5 levels deep within the same domain.

- Granular Content Extraction: Use CSS selectors to target specific elements for precise text extraction.

- Custom Headers: Send custom HTTP headers, including User-Agent and authentication tokens.

- Concurrent Processing: Asynchronous scraping using asyncio, httpx, and Playwright for high performance.

- Rate Limiting: Configurable timeouts and page limits to prevent abuse.

- API Documentation: Auto-generated and interactive OpenAPI/Swagger docs.

## Quick Start
### Local Development
Install Dependencies:
```bash
pip install -r requirements.txt
```
Install Playwright Browsers:
Playwright requires downloading browser binaries. This command installs the recommended browsers.
```bash
playwright install
```
Run the Application:
```bash
python main.py
```
The API will be available at http://localhost:8000.

## API Endpoint
The primary endpoint is POST /scrape. The GET endpoint has been removed as the advanced options are better suited to a JSON request body.

### POST /scrape
Scrape a URL with specified parameters.

Request Body:
```json
{
  "url": "https://example.com",
  "depth": 1,
  "max_pages": 10,
  "timeout": 30,
  "js_rendering": false,
  "css_selector": "article.post-content",
  "headers": {
    "User-Agent": "My-Custom-Scraper/1.0",
    "Authorization": "Bearer your_token_here"
  }
}
```
**Parameters:**

- url (string, required): The starting URL to scrape.

- depth (integer, optional, default: 1): Crawling depth (1-5).

- max_pages (integer, optional, default: 50): Maximum pages to scrape (1-100).

- timeout (integer, optional, default: 30): Request timeout in seconds.

- js_rendering (boolean, optional, default: false): Set to true to use a headless browser to render JavaScript. This is slower but necessary for single-page applications (SPAs) or dynamic content.

- css_selector (string, optional, default: null): Provide a CSS selector (e.g., #main, .article) to extract text from a specific part of the page. If not found or not provided, it extracts from the main body.

- headers (object, optional, default: null): A dictionary of custom HTTP headers to send with each request.

**Response:**
```json
{
  "url": "https://example.com",
  "content": "Extracted text from the specified element...",
  "links_found": ["https://example.com/page1", "https://example.com/page2"],
  "pages_scraped": 5,
  "timestamp": "2024-01-15T10:30:00",
  "success": true,
  "error": null
}
```
## Usage Examples
cURL Examples
1. Basic Static Scrape:
```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.djangoproject.com/"}'
```
2. Scrape a JavaScript-Rendered Page:
```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://react.dev/", "js_rendering": true}'
```
3. Target a Specific Element with a CSS Selector:
```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://fastapi.tiangolo.com/", "css_selector": ".md-content"}'
```
4. Deep Scrape with Custom Headers:
```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-target-site.com/docs",
    "depth": 3,
    "max_pages": 20,
    "headers": {
      "User-Agent": "Docs-Scraper-Bot/1.0"
    }
  }'
```
## Python Client Example
```python
import requests
import json

api_url = "http://localhost:8000/scrape"

# Scrape a dynamic site and target a specific element
payload = {
    "url": "https://www.theverge.com/",
    "js_rendering": True,
    "css_selector": "main" # Extract content only from the <main> tag
}

try:
    response = requests.post(api_url, json=payload, timeout=120)
    response.raise_for_status() # Raise an exception for bad status codes
    data = response.json()
    
    if data['success']:
        print(f"Scraped {data['pages_scraped']} pages from {data['url']}")
        print(f"Content length: {len(data['content'])} characters")
        # print("\nFirst 500 characters of content:\n")
        # print(data['content'][:500])
    else:
        print(f"Scraping failed: {data['error']}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred with the request: {e}")
```

## API Documentation
Interactive API documentation is available via FastAPI's auto-generated UIs:

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

## Architecture
The scraper uses a powerful, modern async stack:

FastAPI: For the web framework.

httpx: Asynchronous HTTP client for fast static requests.

Playwright: For full headless browser automation and JavaScript rendering.

BeautifulSoup: For robust HTML parsing and text extraction.

asyncio: To manage concurrent scraping tasks efficiently.