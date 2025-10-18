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
        missing_entities = state.get("missing_entities", [])
        iteration = state.get("iteration", 0)
        
        self._log_start(query)
        
        try:
            if not DDGS_AVAILABLE:
                return self._mock_search(query)
            
            # If this is a retry iteration with missing entities, search specifically for them
            if iteration > 1 and missing_entities:
                self.logger.info(f"Retry iteration {iteration}: Targeting missing entities: {missing_entities}")
                return self._execute_targeted_search(query, missing_entities, state)
            
            # Special handling for comparison queries - search for each entity
            query_lower = query.lower()
            if "compare" in query_lower and ("vs" in query_lower or "with" in query_lower or "between" in query_lower):
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
    
    def _execute_targeted_search(self, query: str, missing_entities: List[str], state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute targeted search for specific missing entities"""
        # Extract the metric from original query
        query_lower = query.lower()
        metric = ""
        
        if "gdp" in query_lower:
            metric = "GDP growth"
        elif "price" in query_lower or "cost" in query_lower:
            metric = "price"
        elif "inflation" in query_lower:
            metric = "inflation rate"
        
        # Search for each missing entity
        all_results = []
        all_sources = []
        combined_output = ""
        
        for entity in missing_entities:
            # Create focused search query
            search_query = f"{entity} {metric} statistics data"
            if "last" in query_lower and "years" in query_lower:
                import re
                year_match = re.search(r'last\s+(\d+)\s+years?', query_lower)
                if year_match:
                    search_query += f" {year_match.group(1)} years"
            
            self.logger.info(f"Targeted search for {entity}: {search_query}")
            
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(search_query, max_results=5))
                    
                    if results:
                        combined_output += f"\n\n=== {entity} {metric} ===\n"
                        for result in results[:3]:
                            title = result.get('title', '')
                            body = result.get('body', '')
                            href = result.get('href', '')
                            
                            combined_output += f"\n{title}\n{body}\n"
                            if href:
                                all_sources.append(href)
                        
                        all_results.extend(results)
            except Exception as e:
                self.logger.error(f"Error searching for {entity}: {e}")
                combined_output += f"\n\nCould not find data for {entity}\n"
        
        # Merge with existing results
        existing = state.get("websearch_results", {})
        if existing:
            existing_output = existing.get("output", "")
            combined_output = existing_output + combined_output
            all_sources = existing.get("sources", []) + all_sources
        
        metadata = {
            "original_query": query,
            "search_type": "targeted_retry",
            "targeted_entities": missing_entities,
            "result_count": len(all_results)
        }
        
        state["websearch_results"] = self._create_output(
            output=combined_output.strip(),
            sources=all_sources,
            metadata=metadata
        )
        
        self._log_finish(f"Targeted search completed for {len(missing_entities)} entities")
        return state
    
    def _execute_comparison_search(self, query: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Special search strategy for comparison queries - search each entity separately"""
        import re
        
        # Extract entities using proper pattern matching
        entities = self._extract_entities_from_query(query)
        
        if not entities or len(entities) == 0:
            # Fallback: try simple capitalized word extraction
            words = query.split()
            skip_words = {'GDP', 'Price', 'Cost', 'Compare', 'Versus', 'With', 'And'}
            entities = []
            for word in words:
                clean = word.strip("'s,.")
                if clean and clean[0].isupper() and len(clean) > 2 and clean not in skip_words:
                    entities.append(clean)
        
        self.logger.info(f"Detected comparison entities: {entities}")
        
        # If we still don't have at least 2 entities, log warning
        if len(entities) < 2:
            self.logger.warning(f"Expected 2+ entities for comparison, found {len(entities)}")
        
        # Continue with search
        query_lower = query.lower()
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
    
    def _extract_entities_from_query(self, query: str) -> List[str]:
        """Extract entities to compare using pattern matching"""
        import re
        
        # Same patterns as controller agent (handles UK, USA, United Kingdom, etc.)
        patterns = [
            # Pattern for "compare X's ... with/and Y's"
            r"compare\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)'s.*?(?:with|and|to|versus|vs)\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)'s",
            # Pattern for "X vs Y"
            r"([A-Z][A-Z]+|[A-Z][A-Za-z]+)(?:'s)?\s+(?:vs|versus)\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+)(?:'s)?",
            # Pattern for "between X and Y"
            r"between\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+)(?:'s)?\s+and\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+)(?:'s)?",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                entity1 = match.group(1).strip()
                entity2 = match.group(2).strip()
                
                # Clean entities
                entity1 = self._clean_entity_name(entity1)
                entity2 = self._clean_entity_name(entity2)
                
                if entity1 and entity2 and len(entity1) > 1 and len(entity2) > 1:
                    return [entity1, entity2]
        
        return []
    
    def _clean_entity_name(self, entity: str) -> str:
        """Clean entity name"""
        remove_words = ["the", "a", "an", "of", "in", "last", "years", "year",
                       "gdp", "growth", "rate", "price", "cost", "data", "statistics"]
        words = entity.split()
        words = [w for w in words if w.lower() not in remove_words]
        return " ".join(words).strip()
    
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
        """Check if search results seem relevant to the query - GENERIC approach"""
        if not results:
            return False
        
        # Extract all meaningful words from query (nouns, proper nouns, key terms)
        query_lower = original_query.lower()
        
        # Remove stop words and extract key terms
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
                     "of", "with", "is", "are", "was", "were", "been", "be", "have", "has",
                     "had", "do", "does", "did", "will", "would", "should", "could", "may",
                     "might", "can", "about", "how", "what", "when", "where", "which", "who",
                     "much", "many", "more", "most", "some", "any", "all", "last", "years",
                     "year", "data", "information", "find", "search", "tell", "me"}
        
        # Extract words (alphanumeric, length > 2)
        import re
        words = re.findall(r'\b[a-z]{3,}\b', query_lower)
        
        # Filter out stop words and get key terms
        key_terms = [w for w in words if w not in stop_words]
        
        # Also extract capitalized words (entities) from original query
        capitalized = re.findall(r'\b[A-Z][A-Za-z]+\b', original_query)
        key_terms.extend([w.lower() for w in capitalized])
        
        # Remove duplicates
        key_terms = list(set(key_terms))
        
        # If we couldn't extract any key terms, assume results are valid if they exist
        if not key_terms:
            return len(results) > 0
        
        # Check if results contain key terms
        relevant_count = 0
        for result in results[:5]:  # Check first 5 results
            title = (result.get("title", "") or "").lower()
            body = (result.get("body", "") or result.get("description", "") or "").lower()
            combined = title + " " + body
            
            # Count how many key terms appear in this result
            term_matches = sum(1 for term in key_terms if term in combined)
            
            # Result is relevant if it contains at least 30% of key terms
            relevance_threshold = max(1, len(key_terms) * 0.3)
            
            if term_matches >= relevance_threshold:
                relevant_count += 1
        
        # At least 40% of results should be relevant
        return relevant_count >= max(2, len(results) * 0.4)
    
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
