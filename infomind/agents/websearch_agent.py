"""Web Search Agent - Performs live web searches"""

from typing import Dict, Any, List
from .base_agent import BaseAgent

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False


class WebSearchAgent(BaseAgent):
    """
    Performs live web searches using DuckDuckGo
    """
    
    def __init__(self):
        super().__init__("WebSearchAgent")
        if not DDGS_AVAILABLE:
            self.logger.warning("DuckDuckGo search not available. Install with: pip install duckduckgo-search")
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform web search"""
        query = state.get("query", "")
        self._log_start(query)
        
        try:
            if not DDGS_AVAILABLE:
                return self._mock_search(query)
            
            results = self._search(query)
            
            # Format results
            formatted_results = self._format_results(results)
            sources = [r.get("link", "") for r in results[:5]]
            
            output = self._create_output(
                output=formatted_results,
                sources=sources,
                metadata={"result_count": len(results)}
            )
            
            self._log_finish(f"Found {len(results)} results")
            
            # Update state
            state["websearch_results"] = output
            return state
            
        except Exception as e:
            self._log_error(str(e))
            state["websearch_results"] = self._create_output(
                output=f"Error during web search: {str(e)}",
                sources=[]
            )
            return state
    
    def _search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform actual search using DuckDuckGo"""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return results
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return []
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results into readable text"""
        if not results:
            return "No search results found."
        
        formatted = "Search Results:\n\n"
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            snippet = result.get("body", "No description")
            link = result.get("link", "")
            
            formatted += f"{i}. {title}\n"
            formatted += f"   {snippet[:200]}...\n"
            formatted += f"   Source: {link}\n\n"
        
        return formatted
    
    def _mock_search(self, query: str) -> Dict[str, Any]:
        """Mock search results when DuckDuckGo is not available"""
        mock_result = f"Mock search results for: {query}\n\n"
        mock_result += "1. Example Result\n"
        mock_result += "   This is a mock result as DuckDuckGo search is not available.\n"
        mock_result += "   Source: https://example.com\n"
        
        state = {
            "websearch_results": self._create_output(
                output=mock_result,
                sources=["https://example.com"],
                metadata={"mock": True}
            )
        }
        return state
