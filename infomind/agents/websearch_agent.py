"""Web Search Agent - Performs live web searches"""

from typing import Dict, Any, List
from .base_agent import BaseAgent

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
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
        """Perform web search with retry and validation"""
        query = state.get("query", "")
        self._log_start(query)
        
        try:
            if not DDGS_AVAILABLE:
                return self._mock_search(query)
            
            # Special handling for comparison queries - search for each entity
            query_lower = query.lower()
            if "compare" in query_lower and ("vs" in query_lower or "with" in query_lower):
                return self._execute_comparison_search(query, state)
            
            # Regular search with retry
            return self._execute_regular_search(query, state)
            
        except Exception as e:
            self._log_error(str(e))
            state["websearch_results"] = self._create_output(
                output=f"Error during web search: {str(e)}",
                sources=[]
            )
            return state
    
    def _execute_comparison_search(self, query: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Special search strategy for comparison queries - search each entity separately"""
        import re
        
        # Extract entities being compared
        query_lower = query.lower()
        
        # Try to extract country names or entities
        # Simple approach: look for capitalized words or known patterns
        words = query.split()
        entities = []
        # Skip common metric words
        skip_words = {'GDP', 'Price', 'Cost', 'Compare', 'Versus'}
        
        for word in words:
            clean = word.strip("'s,.")
            if clean and clean[0].isupper() and len(clean) > 2 and clean not in skip_words:
                entities.append(clean)
        
        self.logger.info(f"Detected comparison entities: {entities}")
        
        # Search for each entity separately
        all_results = []
        all_sources = []
        combined_output = ""
        
        # Extract the metric being compared (GDP, price, etc.)
        metric = ""
        if "gdp" in query_lower:
            metric = "GDP growth"
        elif "price" in query_lower or "cost" in query_lower:
            metric = "price"
        
        # Extract time period
        time_period = ""
        if "last" in query_lower and "years" in query_lower:
            match = re.search(r'last (\d+) years?', query_lower)
            if match:
                from datetime import datetime
                num_years = int(match.group(1))
                current_year = datetime.now().year
                time_period = f"{current_year - num_years}-{current_year}"
        
        # Search for each entity
        for i, entity in enumerate(entities[:2], 1):  # Limit to 2 entities
            search_query = f"{entity} {metric} {time_period} data statistics".strip()
            self.logger.info(f"Comparison search {i}: '{search_query}'")
            
            results = self._search(search_query, max_results=3)
            all_results.extend(results)
            
            formatted = self._format_results(results)
            combined_output += f"\n{'='*60}\n"
            combined_output += f"Search Results for {entity}:\n"
            combined_output += f"{'='*60}\n\n"
            combined_output += formatted
            
            sources = [r.get("link", "") or r.get("href", "") for r in results]
            all_sources.extend(sources)
        
        output = self._create_output(
            output=combined_output,
            sources=all_sources,
            metadata={
                "result_count": len(all_results),
                "original_query": query,
                "comparison_entities": entities,
                "search_type": "multi-entity_comparison"
            }
        )
        
        self._log_finish(f"Found {len(all_results)} results across {len(entities)} entities")
        state["websearch_results"] = output
        return state
    
    def _execute_regular_search(self, query: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Regular search with retry logic"""
        # Try up to 3 search strategies
        search_attempts = []
        
        # Strategy 1: Optimized query
        optimized_query = self._optimize_query(query)
        self.logger.info(f"Attempt 1 - Optimized query: '{optimized_query}'")
        results = self._search(optimized_query)
        search_attempts.append(("optimized", optimized_query, results))
        
        # Strategy 2: If results seem irrelevant or too few, try alternative query
        if len(results) < 3 or not self._validate_results(results, query):
            self.logger.warning(f"Initial search returned {len(results)} results or irrelevant content, trying alternative...")
            
            # Create a more specific alternative query
            alternative_query = self._create_alternative_query(query, optimized_query)
            self.logger.info(f"Attempt 2 - Alternative query: '{alternative_query}'")
            alt_results = self._search(alternative_query)
            search_attempts.append(("alternative", alternative_query, alt_results))
            
            # Use alternative if better
            if len(alt_results) > len(results) or self._validate_results(alt_results, query):
                results = alt_results
                optimized_query = alternative_query
        
        # Strategy 3: If still poor results, try simplified query
        if len(results) < 2:
            self.logger.warning(f"Still only {len(results)} results, trying simplified query...")
            simplified = self._simplify_query(query)
            self.logger.info(f"Attempt 3 - Simplified query: '{simplified}'")
            simple_results = self._search(simplified)
            search_attempts.append(("simplified", simplified, simple_results))
            
            if len(simple_results) > len(results):
                results = simple_results
                optimized_query = simplified
        
        # Format results
        formatted_results = self._format_results(results)
        sources = [r.get("link", "") or r.get("href", "") for r in results[:5]]
        
        output = self._create_output(
            output=formatted_results,
            sources=sources,
            metadata={
                "result_count": len(results),
                "original_query": query,
                "final_query": optimized_query,
                "search_attempts": len(search_attempts),
                "validated": self._validate_results(results, query)
            }
        )
        
        self._log_finish(f"Found {len(results)} results after {len(search_attempts)} attempts")
        state["websearch_results"] = output
        return state
    
    def _validate_results(self, results: List[Dict[str, Any]], original_query: str) -> bool:
        """Check if search results seem relevant to the query"""
        if not results:
            return False
        
        # Extract key terms from query
        query_lower = original_query.lower()
        key_terms = []
        
        # Look for important keywords
        if "gdp" in query_lower:
            key_terms.append("gdp")
        if "finland" in query_lower:
            key_terms.append("finland")
        if "singapore" in query_lower:
            key_terms.append("singapore")
        if "growth" in query_lower:
            key_terms.extend(["growth", "rate", "percent"])
        if "bmw" in query_lower:
            key_terms.append("bmw")
        if "price" in query_lower or "cost" in query_lower:
            key_terms.extend(["price", "cost", "msrp"])
        
        # If no specific terms extracted, can't validate effectively
        if not key_terms:
            return len(results) > 0
        
        # Check if at least 2 results contain relevant terms
        relevant_count = 0
        for result in results[:5]:
            title = (result.get("title", "") or "").lower()
            body = (result.get("body", "") or result.get("description", "") or "").lower()
            combined = title + " " + body
            
            # Count how many key terms appear
            matches = sum(1 for term in key_terms if term in combined)
            if matches >= 1:
                relevant_count += 1
        
        return relevant_count >= 2
    
    def _create_alternative_query(self, original: str, optimized: str) -> str:
        """Create an alternative search query if initial one fails"""
        query_lower = original.lower()
        
        # For comparison queries, search for each entity separately then combine
        if "compare" in query_lower:
            # Try adding "comparison table" or "versus"
            return f"{optimized} comparison table statistics"
        
        # For GDP/economic queries, add authoritative sources
        if "gdp" in query_lower:
            return f"{optimized} World Bank OECD IMF"
        
        # For time-series data, add "chart" or "graph"
        if any(word in query_lower for word in ["last", "years", "trend", "history"]):
            return f"{optimized} chart data"
        
        # Default: add "statistics data" if not present
        if "data" not in optimized.lower():
            return f"{optimized} statistics data"
        
        return optimized
    
    def _simplify_query(self, query: str) -> str:
        """Create a very simple, focused query"""
        # Take just the key nouns and remove everything else
        words = query.split()
        # Keep words that are likely important (capitalized, or key terms)
        important = []
        for word in words:
            clean = word.strip('?.,!').lower()
            if clean in ['gdp', 'growth', 'price', 'cost', 'lease', 'comparison', 'data', 'finland', 'singapore'] or word[0].isupper():
                important.append(clean)
        
        return ' '.join(important[:5])  # Max 5 words
    
    def _optimize_query(self, query: str) -> str:
        """Optimize query for better search results by removing problematic words and adding context"""
        import re
        from datetime import datetime
        
        # Convert to lowercase for analysis
        query_lower = query.lower()
        
        # Remove common question words that confuse search engines
        remove_phrases = [
            "how much does",
            "how much is",
            "how can i",
            "how do i",
            "how to",
            "what is the",
            "what are the",
            "tell me about",
            "give me",
            "search internet",
            "scrape web pages",
            "extract information",
            "find information about",
            "i want to know"
        ]
        
        optimized = query
        for phrase in remove_phrases:
            optimized = re.sub(rf'\b{re.escape(phrase)}\b', '', optimized, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        optimized = ' '.join(optimized.split())
        
        current_year = datetime.now().year
        
        # COMPARISON QUERIES - Need specific data points
        if "compare" in query_lower or "versus" in query_lower or " vs " in query_lower:
            # GDP comparison
            if "gdp" in query_lower:
                # Extract time period
                time_period = ""
                if "last" in query_lower and "years" in query_lower:
                    import re
                    match = re.search(r'last (\d+) years?', query_lower)
                    if match:
                        num_years = int(match.group(1))
                        time_period = f"{current_year - num_years}-{current_year}"
                
                # Keep the original entities being compared - don't remove them!
                # Just clean up question words
                optimized_clean = optimized  # Use already cleaned version
                
                # Add context words
                if time_period:
                    optimized = f"{optimized_clean} GDP growth {time_period} data comparison"
                else:
                    optimized = f"{optimized_clean} GDP growth data comparison"
            # General comparison
            else:
                optimized = f"{optimized} comparison data"
        
        # GDP / ECONOMIC QUERIES
        elif any(word in query_lower for word in ["gdp", "economic growth", "economy", "inflation", "unemployment"]):
            # Add year range for time-based queries
            if "last" in query_lower and "years" in query_lower:
                # Extract number (e.g., "last 5 years")
                import re
                match = re.search(r'last (\d+) years?', query_lower)
                if match:
                    num_years = int(match.group(1))
                    year_range = f"{current_year - num_years}-{current_year}"
                    optimized = re.sub(r'last \d+ years?', year_range, optimized, flags=re.IGNORECASE)
            
            # Add "data statistics" for better results
            if "data" not in query_lower and "statistics" not in query_lower:
                optimized = f"{optimized} data statistics"
        
        # PRICE/COST QUERIES
        elif any(word in query_lower for word in ["cost", "price", "lease", "buy", "purchase"]):
            # If query asks about "latest" or "current", add current year
            if any(word in query_lower for word in ["latest", "current", "new", "recent"]):
                if str(current_year) not in optimized:
                    optimized = f"{optimized} {current_year}"
            
            # Add pricing keywords if not present
            if not any(word in query_lower for word in ["msrp", "pricing", "cost"]):
                optimized = f"{optimized} price MSRP cost"
        
        # LATEST/CURRENT queries - add current year
        elif any(word in query_lower for word in ["latest", "current", "new", "recent"]):
            if str(current_year) not in optimized:
                optimized = f"{optimized} {current_year}"
        
        # Fallback: if optimization made query too short, use original
        if len(optimized.strip()) < 3:
            optimized = query
        
        return optimized.strip()
    
    def _search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform actual search using DuckDuckGo"""
        try:
            with DDGS() as ddgs:
                # Try to get more results for better coverage
                results = list(ddgs.text(query, max_results=max_results))
                
                # Log what we found
                if results:
                    self.logger.info(f"DuckDuckGo returned {len(results)} results")
                else:
                    self.logger.warning("DuckDuckGo returned no results, trying alternative search...")
                    # Simplify query and retry
                    # Remove common words that might confuse search
                    simplified = query.replace("how much does", "").replace("how can i", "")
                    results = list(ddgs.text(simplified, max_results=max_results))
                    
                return results
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            # Try a simplified search as fallback
            try:
                self.logger.info("Attempting fallback search with simplified query...")
                simple_query = " ".join(query.split()[:5])  # Take first 5 words
                with DDGS() as ddgs:
                    results = list(ddgs.text(simple_query, max_results=max_results))
                    return results
            except:
                return []
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results into readable text"""
        if not results:
            return "No search results found."
        
        formatted = "Search Results:\n\n"
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            snippet = result.get("body", "") or result.get("description", "") or "No description"
            link = result.get("link", "") or result.get("href", "")
            
            formatted += f"{i}. {title}\n"
            # Include MORE of the snippet for better context (was 200, now 400)
            formatted += f"   {snippet[:400]}...\n"
            if link:
                formatted += f"   Source: {link}\n"
            formatted += "\n"
        
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
