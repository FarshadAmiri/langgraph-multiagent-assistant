"""Web Scraper Agent - Extracts content from URLs"""

import re
from typing import Dict, Any, List
from .base_agent import BaseAgent

try:
    import requests
    from bs4 import BeautifulSoup
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False


class WebScraperAgent(BaseAgent):
    """
    Extracts key text/data from URLs using requests + BeautifulSoup4
    """
    
    def __init__(self):
        super().__init__("WebScraperAgent")
        if not SCRAPING_AVAILABLE:
            self.logger.warning("Web scraping not available. Install with: pip install requests beautifulsoup4")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape content from URLs"""
        query = state.get("query", "")
        self._log_start(query)
        
        try:
            # Extract URLs from query or from previous search results
            urls = self._extract_urls(query, state)
            
            if not urls:
                self._log_finish("No URLs to scrape")
                state["scraper_results"] = self._create_output(
                    output="No URLs found to scrape.",
                    sources=[]
                )
                return state
            
            # Scrape each URL
            scraped_content = []
            for url in urls[:3]:  # Limit to 3 URLs
                # Skip empty or invalid URLs
                if not url or not url.startswith(('http://', 'https://')):
                    self.logger.warning(f"Skipping invalid URL: {url}")
                    continue
                    
                content = self._scrape_url(url)
                if content:
                    scraped_content.append({
                        "url": url,
                        "content": content
                    })
            
            # Format results
            formatted = self._format_scraped_content(scraped_content)
            sources = [item["url"] for item in scraped_content]
            
            output = self._create_output(
                output=formatted,
                sources=sources,
                metadata={"urls_scraped": len(scraped_content)}
            )
            
            self._log_finish(f"Scraped {len(scraped_content)} URLs")
            state["scraper_results"] = output
            return state
            
        except Exception as e:
            self._log_error(str(e))
            state["scraper_results"] = self._create_output(
                output=f"Error during scraping: {str(e)}",
                sources=[]
            )
            return state
    
    def _extract_urls(self, query: str, state: Dict[str, Any]) -> List[str]:
        """Extract URLs from query or state"""
        urls = []
        
        # Extract from query
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls.extend(re.findall(url_pattern, query))
        
        # Extract from search results if available
        if "websearch_results" in state:
            search_sources = state["websearch_results"].get("sources", [])
            # Take top 3 URLs from search results for scraping
            urls.extend(search_sources[:3])
            self.logger.info(f"Found {len(search_sources)} URLs from search results, will scrape top 3")
        
        return list(set(urls))  # Remove duplicates
    
    def _scrape_url(self, url: str) -> str:
        """Scrape content from a single URL"""
        if not SCRAPING_AVAILABLE:
            return f"Scraping not available for {url}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit length but allow more content for better context (was 2000, now 5000)
            return text[:5000] if text else "No content extracted"
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
            return f"Error scraping {url}: {str(e)}"
    
    def _format_scraped_content(self, scraped_content: List[Dict[str, str]]) -> str:
        """Format scraped content"""
        if not scraped_content:
            return "No content scraped."
        
        formatted = "Scraped Content:\n\n"
        for i, item in enumerate(scraped_content, 1):
            formatted += f"{i}. From: {item['url']}\n"
            formatted += f"   {item['content'][:500]}...\n\n"
        
        return formatted
