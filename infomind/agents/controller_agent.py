"""Controller Agent - Routes queries to appropriate agents"""

import re
from typing import Dict, Any, List
from .base_agent import BaseAgent


class ControllerAgent(BaseAgent):
    """
    Interprets user queries and routes to appropriate agents
    """
    
    def __init__(self):
        super().__init__("ControllerAgent")
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Route the query to appropriate agents"""
        query = state.get("query", "")
        self._log_start(query)
        
        try:
            # Determine which agents to call based on query analysis
            agents_to_call = self._analyze_query(query)
            
            result = {
                "agents_to_call": agents_to_call,
                "query": query,
                "routing_complete": True
            }
            
            self._log_finish(f"Routing to: {', '.join(agents_to_call)}")
            return result
            
        except Exception as e:
            self._log_error(str(e))
            return {
                "agents_to_call": ["synthesizer"],  # Fallback
                "query": query,
                "error": str(e)
            }
    
    def _analyze_query(self, query: str) -> List[str]:
        """Analyze query and determine which agents to call"""
        query_lower = query.lower()
        agents = []
        
        # Web search keywords
        search_keywords = [
            "search", "find", "latest", "news", "information",
            "today", "current", "recent", "what is", "who is",
            "conferences", "events", "deadlines", "how much", "price",
            "cost", "lease", "buy", "purchase"
        ]
        
        # Scraping keywords (explicit user request)
        scraping_keywords = [
            "scrape", "extract", "web page", "webpage", "detailed information",
            "full content", "article"
        ]
        
        # Math/calculation keywords
        math_keywords = [
            "calculate", "average", "sum", "total", "percentage",
            "inflation", "rate", "statistics", "mean", "median"
        ]
        
        # Comparison keywords
        comparison_keywords = [
            "compare", "difference", "versus", "vs", "better",
            "contrast", "similarities", "between"
        ]
        
        # URL pattern
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        has_url = bool(re.search(url_pattern, query))
        
        # Check for explicit scraping request
        wants_scraping = any(keyword in query_lower for keyword in scraping_keywords)
        
        # Determine agents
        # For comparison queries, we need to gather data first
        has_comparison = any(keyword in query_lower for keyword in comparison_keywords)
        
        if any(keyword in query_lower for keyword in search_keywords) or has_comparison:
            agents.append("websearch")
        
        # Add scraper if explicitly requested or if URL provided
        if has_url or wants_scraping or ("summarize" in query_lower and "url" in query_lower):
            # Only add scraper after websearch if websearch is present
            if "websearch" not in agents:
                agents.append("websearch")
            agents.append("scraper")
        
        if any(keyword in query_lower for keyword in math_keywords):
            agents.append("math")
        
        # Add comparison after gathering data
        if has_comparison:
            agents.append("comparison")
        
        # If no specific agents identified, default to web search
        if not agents:
            agents.append("websearch")
        
        # Always add synthesizer at the end
        agents.append("synthesizer")
        
        return agents
