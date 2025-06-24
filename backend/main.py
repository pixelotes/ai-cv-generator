from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Dict, Optional
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import asyncio
import logging
from datetime import datetime
import re
from playwright.async_api import async_playwright, Browser

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Advanced Web Scraper API",
    description="API for scraping web content with JavaScript rendering, CSS selectors, and configurable depth.",
    version="2.0.0"
)

# --- Pydantic Models ---
class ScrapeRequest(BaseModel):
    url: HttpUrl = Field(..., description="The starting URL to scrape.")
    depth: int = Field(1, ge=1, le=5, description="How many levels deep to scrape (1-5).")
    max_pages: int = Field(50, ge=1, le=100, description="Maximum number of pages to scrape (1-100).")
    timeout: int = Field(30, ge=5, le=120, description="Request timeout in seconds.")
    js_rendering: bool = Field(False, description="Enable JavaScript rendering with a headless browser.")
    css_selector: Optional[str] = Field(None, description="CSS selector to extract text from a specific element.")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers to send with requests.")

class ScrapeResponse(BaseModel):
    url: str
    content: str
    links_found: List[str]
    pages_scraped: int
    timestamp: str
    success: bool
    error: Optional[str] = None

# --- Web Scraper Class ---
class WebScraper:
    """
    A sophisticated web scraper that handles both static and JavaScript-rendered pages,
    with support for custom headers and targeted content extraction.
    """
    def __init__(self, timeout: int = 30, headers: Optional[Dict[str, str]] = None, js_rendering: bool = False):
        self.timeout = timeout
        self.scraped_urls = set()
        self.js_rendering = js_rendering
        self.playwright = None
        self.browser = None

        # Set up headers, providing a default User-Agent if none are specified
        self.headers = headers or {}
        if 'User-Agent' not in self.headers:
            self.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
        # httpx session is now created inside the context manager
        self.session = None

    async def __aenter__(self):
        """Initialize resources for scraping."""
        self.session = httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True)
        if self.js_rendering:
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch()
                logger.info("Playwright headless browser started.")
            except Exception as e:
                logger.error(f"Failed to start Playwright: {e}")
                raise RuntimeError("Could not start headless browser for JS rendering.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources."""
        if self.session:
            await self.session.aclose()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            logger.info("Playwright headless browser stopped.")

    def clean_text(self, text: str) -> str:
        """Cleans and normalizes extracted text by removing excess whitespace."""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_text_from_html(self, html: str, css_selector: Optional[str] = None) -> str:
        """
        Extracts meaningful text from HTML. If a CSS selector is provided,
        it targets that element specifically. Otherwise, it intelligently
        removes common non-content tags.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # If a selector is provided, try to find that specific element
        if css_selector:
            target_element = soup.select_one(css_selector)
            if target_element:
                return self.clean_text(target_element.get_text())
            else:
                logger.warning(f"CSS Selector '{css_selector}' not found. Falling back to general extraction.")
        
        # General extraction logic
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
        
        main_content = soup.find(['main', 'article', 'div.content', 'div.post']) or soup.body or soup
        return self.clean_text(main_content.get_text())

    def extract_links(self, html: str, base_url: str) -> List[str]:
        """Extracts all unique absolute links from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Resolve relative URLs to absolute URLs
            full_url = urljoin(base_url, href)
            if full_url.startswith(('http://', 'https://')):
                links.add(full_url)
        return list(links)

    def is_same_domain(self, url1: str, url2: str) -> bool:
        """Checks if two URLs belong to the same domain."""
        return urlparse(url1).netloc == urlparse(url2).netloc

    async def scrape_single_page(self, url: str, css_selector: Optional[str] = None) -> tuple[str, List[str]]:
        """
        Scrapes a single page. Uses Playwright for JS-heavy sites if enabled,
        otherwise uses httpx for speed.
        """
        try:
            html = ""
            if self.js_rendering:
                # Use Playwright for JS rendering
                page = await self.browser.new_page(extra_http_headers=self.headers)
                await page.goto(url, timeout=self.timeout * 1000)
                # A simple wait for network activity to cease can be effective
                await page.wait_for_load_state('networkidle')
                html = await page.content()
                await page.close()
            else:
                # Use httpx for static HTML
                response = await self.session.get(url)
                response.raise_for_status()
                html = response.text

            content = self.extract_text_from_html(html, css_selector)
            links = self.extract_links(html, url)
            return content, links

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return "", []

    async def scrape_with_depth(self, start_url: str, depth: int, max_pages: int, css_selector: Optional[str]) -> Dict:
        """
        Recursively scrapes a website starting from a URL up to a specified depth.
        """
        all_content = []
        all_links = set()
        to_visit = {start_url}
        
        for current_depth in range(depth):
            if not to_visit or len(self.scraped_urls) >= max_pages:
                break
            
            logger.info(f"Scraping depth {current_depth + 1}, visiting {len(to_visit)} URLs...")
            
            current_level_urls = list(to_visit)
            to_visit = set()
            
            tasks = []
            for url in current_level_urls:
                if url not in self.scraped_urls and len(self.scraped_urls) < max_pages:
                    self.scraped_urls.add(url)
                    # For the initial URL and its direct links, use the specific selector.
                    # For deeper links, a general scrape might be more appropriate.
                    # Here we pass the selector for all levels for consistency.
                    tasks.append(self.scrape_single_page(url, css_selector))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    continue
                
                content, links = result
                if content:
                    all_content.append(content)
                
                for link in links:
                    all_links.add(link)
                    if (current_depth < depth - 1 and self.is_same_domain(start_url, link)):
                        to_visit.add(link)
        
        return {
            'content': '\n\n'.join(all_content),
            'links': list(all_links),
            'pages_scraped': len(self.scraped_urls)
        }


# --- API Endpoints ---
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Advanced Web Scraper API", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    """Returns the health status of the API."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(request: ScrapeRequest):
    """
    Scrapes a URL with advanced options:
    - **url**: The starting URL to scrape.
    - **depth**: How many levels deep to crawl (1-5).
    - **max_pages**: Maximum number of pages to visit (1-100).
    - **timeout**: Request timeout in seconds.
    - **js_rendering**: Use a headless browser to render JavaScript. Slower but necessary for dynamic sites.
    - **css_selector**: Target a specific element for text extraction (e.g., `article.content`).
    - **headers**: Send custom HTTP headers (e.g., for authentication or User-Agent).
    """
    try:
        logger.info(f"Starting scrape for: {request.url} with params: {request.model_dump(exclude={'url'})}")
        
        scraper_config = {
            "timeout": request.timeout,
            "headers": request.headers,
            "js_rendering": request.js_rendering,
        }

        async with WebScraper(**scraper_config) as scraper:
            result = await scraper.scrape_with_depth(
                str(request.url),
                request.depth,
                request.max_pages,
                request.css_selector
            )

        return ScrapeResponse(
            url=str(request.url),
            content=result['content'],
            links_found=result['links'],
            pages_scraped=result['pages_scraped'],
            timestamp=datetime.utcnow().isoformat(),
            success=True
        )

    except HTTPException:
        # Re-raise HTTPExceptions directly to let FastAPI handle them
        raise
    except Exception as e:
        logger.error(f"Scraping failed for {request.url}: {str(e)}", exc_info=True)
        return ScrapeResponse(
            url=str(request.url),
            content="",
            links_found=[],
            pages_scraped=0,
            timestamp=datetime.utcnow().isoformat(),
            success=False,
            error=str(e)
        )

# Note: The GET endpoint is removed to simplify the API.
# The complexity of the new options (like the 'headers' dict) doesn't
# translate well to URL query parameters. The POST method is more suitable.

if __name__ == "__main__":
    import uvicorn
    # It is recommended to install playwright browsers before running.
    # In your terminal: `playwright install`
    uvicorn.run(app, host="0.0.0.0", port=8000)
