import logging
import json
import re
import time
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urlparse, urljoin

# Web tools
try:
    import requests
    from bs4 import BeautifulSoup
    WEB_TOOLS_AVAILABLE = True
except ImportError:
    WEB_TOOLS_AVAILABLE = False

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

logger = logging.getLogger(__name__)

class WebTools:
    """Tools for web search and content extraction."""
    
    def __init__(self, config=None):
        """
        Initialize web tools.
        
        Args:
            config (dict, optional): Configuration for web tools
        """
        self.config = config or {}
        self.user_agent = self.config.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        self.timeout = self.config.get("request_timeout", 10)
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay = self.config.get("retry_delay", 1)
        
        # Check if required packages are available
        if not WEB_TOOLS_AVAILABLE:
            logger.warning("Web tools dependencies not available. Please install with: pip install requests beautifulsoup4")
        
        if not DDGS_AVAILABLE:
            logger.warning("DuckDuckGo search not available. Please install with: pip install duckduckgo-search")
    
    def search_web(self, query: str, max_results: int = 5, time_period: str = None) -> Dict[str, Any]:
        """
        Search the web using DuckDuckGo.
        
        Args:
            query (str): Search query
            max_results (int, optional): Maximum number of results to return
            time_period (str, optional): Time period for results (d, w, m, y)
            
        Returns:
            Dict[str, Any]: Search results
        """
        if not DDGS_AVAILABLE:
            return {
                "success": False,
                "error": "DuckDuckGo search not available. Please install with: pip install duckduckgo-search"
            }
            
        try:
            results = []
            with DDGS() as ddgs:
                search_params = {"max_results": max_results}
                if time_period:
                    search_params["time"] = time_period
                    
                search_results = list(ddgs.text(query, **search_params))
                
                for result in search_results:
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("href", ""),
                        "snippet": result.get("body", ""),
                        "source": result.get("source", "")
                    })
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def scrape_webpage(self, url: str, selector: Optional[str] = None, include_links: bool = True, include_images: bool = False) -> Dict[str, Any]:
        """
        Scrape and extract data from a webpage.
        
        Args:
            url (str): URL to scrape
            selector (str, optional): CSS selector to extract specific content
            include_links (bool, optional): Whether to include links in the result
            include_images (bool, optional): Whether to include image information
            
        Returns:
            Dict[str, Any]: Scraped content
        """
        if not WEB_TOOLS_AVAILABLE:
            return {
                "success": False,
                "error": "Web scraping tools not available. Please install with: pip install requests beautifulsoup4"
            }
            
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return {
                    "success": False,
                    "error": f"Invalid URL: {url}"
                }
            
            # Make request with retries
            response = None
            for attempt in range(self.max_retries):
                try:
                    headers = {
                        'User-Agent': self.user_agent,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Referer': 'https://www.google.com/',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                    }
                    
                    response = requests.get(url, headers=headers, timeout=self.timeout)
                    response.raise_for_status()
                    break
                except requests.RequestException as e:
                    logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    else:
                        return {
                            "success": False,
                            "url": url,
                            "error": f"Failed after {self.max_retries} attempts: {str(e)}"
                        }
            
            # Parse content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.title.string if soup.title else "No title found"
            
            # Extract metadata
            metadata = {
                "url": url,
                "status_code": response.status_code,
                "content_type": response.headers.get('Content-Type', ''),
                "encoding": response.encoding,
            }
            
            # Extract meta tags
            meta_tags = {}
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                if name and content:
                    meta_tags[name] = content
            
            # Extract text content
            if selector:
                selected_elements = soup.select(selector)
                if selected_elements:
                    text_content = "\n".join([el.get_text(separator='\n', strip=True) for el in selected_elements])
                else:
                    text_content = "No content found matching the selector"
            else:
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                text_content = soup.get_text(separator='\n', strip=True)
            
            # Extract links if requested
            links = []
            if include_links:
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    link_text = link.get_text(strip=True)
                    
                    # Convert relative URLs to absolute
                    if not bool(urlparse(href).netloc):
                        href = urljoin(url, href)
                    
                    links.append({
                        "text": link_text,
                        "url": href
                    })
            
            # Extract images if requested
            images = []
            if include_images:
                for img in soup.find_all('img', src=True):
                    src = img['src']
                    alt = img.get('alt', '')
                    
                    # Convert relative URLs to absolute
                    if not bool(urlparse(src).netloc):
                        src = urljoin(url, src)
                    
                    images.append({
                        "src": src,
                        "alt": alt
                    })
            
            result = {
                "success": True,
                "url": url,
                "title": title,
                "metadata": metadata,
                "meta_tags": meta_tags,
                "text_content": text_content
            }
            
            if include_links:
                result["links"] = links
                
            if include_images:
                result["images"] = images
            
            return result
            
        except Exception as e:
            logger.error(f"Error scraping webpage {url}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
    
    def extract_article(self, url: str) -> Dict[str, Any]:
        """
        Extract article content from a webpage, focusing on the main content.
        
        Args:
            url (str): URL of the article
            
        Returns:
            Dict[str, Any]: Extracted article content
        """
        if not WEB_TOOLS_AVAILABLE:
            return {
                "success": False,
                "error": "Web scraping tools not available. Please install with: pip install requests beautifulsoup4"
            }
            
        try:
            # First get the general page content
            page_result = self.scrape_webpage(url, include_links=False)
            if not page_result["success"]:
                return page_result
            
            soup = BeautifulSoup(page_result["metadata"]["content"], 'html.parser')
            
            # Try to find the article content using common patterns
            article_content = None
            
            # Method 1: Look for article tag
            article_tag = soup.find('article')
            if article_tag:
                article_content = article_tag.get_text(separator='\n', strip=True)
            
            # Method 2: Look for common content containers
            if not article_content:
                for selector in ['.post-content', '.entry-content', '.article-content', '.content-area', '#content', '.main-content']:
                    content_div = soup.select_one(selector)
                    if content_div:
                        article_content = content_div.get_text(separator='\n', strip=True)
                        break
            
            # Method 3: Look for the largest div with paragraphs
            if not article_content:
                paragraphs_count = {}
                for div in soup.find_all('div'):
                    p_count = len(div.find_all('p', recursive=False))
                    if p_count > 0:
                        paragraphs_count[div] = p_count
                
                if paragraphs_count:
                    main_content_div = max(paragraphs_count.items(), key=lambda x: x[1])[0]
                    article_content = main_content_div.get_text(separator='\n', strip=True)
            
            # If we still don't have content, use the whole page text
            if not article_content:
                article_content = page_result["text_content"]
            
            # Extract publication date
            pub_date = None
            for meta in soup.find_all('meta'):
                property_val = meta.get('property', '')
                name_val = meta.get('name', '')
                if 'published_time' in property_val or 'date' in property_val or 'date' in name_val:
                    pub_date = meta.get('content')
                    break
            
            # Extract author
            author = None
            author_meta = soup.find('meta', {'name': 'author'}) or soup.find('meta', {'property': 'article:author'})
            if author_meta:
                author = author_meta.get('content')
            else:
                author_elem = soup.find(class_=re.compile('author|byline', re.I))
                if author_elem:
                    author = author_elem.get_text(strip=True)
            
            return {
                "success": True,
                "url": url,
                "title": page_result["title"],
                "author": author,
                "publication_date": pub_date,
                "content": article_content,
                "metadata": page_result["metadata"],
                "meta_tags": page_result["meta_tags"]
            }
            
        except Exception as e:
            logger.error(f"Error extracting article from {url}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }