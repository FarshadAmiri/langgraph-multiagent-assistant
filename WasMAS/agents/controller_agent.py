"""Controller Agent - Routes queries to appropriate agents with adaptive planning"""

import re
from typing import Dict, Any, List, Set
from .base_agent import BaseAgent


class ControllerAgent(BaseAgent):
    """
    Adaptive controller that tracks progress and plans multi-step workflows
    """
    
    def __init__(self):
        super().__init__("ControllerAgent")
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Route the query to appropriate agents with adaptive planning"""
        query = state.get("query", "")
        iteration = state.get("iteration", 0)
        
        self._log_start(f"Planning (Iteration {iteration + 1})")
        
        try:
            # First iteration: analyze query and create plan
            if iteration == 0:
                plan = self._create_initial_plan(query, state)
            else:
                # Subsequent iterations: check what's missing and replan
                plan = self._adaptive_replan(query, state)
            
            result = {
                "agents_to_call": plan["agents_to_call"],
                "query": query,
                "routing_complete": plan["complete"],
                "missing_entities": plan.get("missing_entities", []),
                "plan_notes": plan.get("notes", ""),
                "iteration": iteration + 1
            }
            
            self._log_finish(f"Plan: {', '.join(plan['agents_to_call'])} | Complete: {plan['complete']}")
            if plan.get("notes"):
                print(f"  📝 Plan Notes: {plan['notes']}")
            
            return result
            
        except Exception as e:
            self._log_error(str(e))
            return {
                "agents_to_call": ["synthesizer"],
                "query": query,
                "routing_complete": True,
                "error": str(e)
            }
    
    def _create_initial_plan(self, query: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create initial execution plan based on query analysis"""
        query_lower = query.lower()
        agents = []
        
        # Extract entities for comparison queries
        comparison_keywords = ["compare", "versus", "vs", "difference", "between", "contrast"]
        has_comparison = any(keyword in query_lower for keyword in comparison_keywords)
        
        entities = []
        if has_comparison:
            # Extract entities (countries, products, etc.)
            entities = self._extract_comparison_entities(query)
        
        # Determine initial agent sequence
        search_keywords = [
            "search", "find", "latest", "news", "information",
            "today", "current", "recent", "what is", "who is",
            "conferences", "events", "deadlines", "how much", "price",
            "cost", "lease", "buy", "purchase", "gdp", "growth",
            "economy", "market", "rate"
        ]
        
        math_keywords = [
            "calculate", "average", "sum", "total", "percentage",
            "inflation", "rate", "statistics", "mean", "median"
        ]
        
        scraping_keywords = ["scrape", "extract", "web page", "webpage", "detailed information", "full content", "article"]
        
        # Build agent sequence
        if any(keyword in query_lower for keyword in search_keywords) or has_comparison:
            agents.append("websearch")
        
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        has_url = bool(re.search(url_pattern, query))
        wants_scraping = any(keyword in query_lower for keyword in scraping_keywords)
        
        if has_url or wants_scraping:
            if "websearch" not in agents:
                agents.append("websearch")
            agents.append("scraper")
        
        if any(keyword in query_lower for keyword in math_keywords):
            agents.append("math")
        
        if has_comparison:
            agents.append("comparison")
        
        if not agents:
            agents.append("websearch")
        
        # DON'T add synthesizer yet - let adaptive loop decide when ready
        
        return {
            "agents_to_call": agents,
            "complete": False,  # Not complete until we validate results
            "expected_entities": entities,
            "notes": f"Initial plan for comparison query with entities: {entities}" if entities else "Initial data gathering"
        }
    
    def _adaptive_replan(self, query: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Adaptively replan based on what data we have vs what we need"""
        
        # Check what we have
        websearch_results = state.get("websearch_results", {})
        comparison_results = state.get("comparison_results", {})
        iteration = state.get("iteration", 0)
        
        # Extract expected entities from query
        expected_entities = self._extract_comparison_entities(query)
        
        # Check if we have data for all entities
        missing_entities = self._check_missing_entities(expected_entities, websearch_results, state)
        
        # Decide next steps
        if missing_entities and iteration < 3:  # Max 3 iterations to avoid infinite loops
            # Need to search for missing entities
            return {
                "agents_to_call": ["websearch", "comparison"],
                "complete": False,
                "missing_entities": missing_entities,
                "notes": f"Retry: Searching for missing data on {', '.join(missing_entities)}"
            }
        elif "compare" in query.lower() and not comparison_results:
            # Have data, need to compare
            return {
                "agents_to_call": ["comparison", "synthesizer"],
                "complete": True,
                "notes": "Data gathered, proceeding to comparison"
            }
        else:
            # Ready to synthesize
            return {
                "agents_to_call": ["synthesizer"],
                "complete": True,
                "notes": "All data gathered or max iterations reached, synthesizing answer"
            }
    
    def _extract_comparison_entities(self, query: str) -> List[str]:
        """Extract entities being compared from query"""
        # Common patterns: "A vs B", "compare A and B", "A versus B", "between A and B"
        
        # Try pattern matching - flexible patterns (handles UK, USA, United Kingdom, etc.)
        patterns = [
            # Pattern for "compare X's ... with/and Y's"
            r"compare\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)'s.*?(?:with|and|to|versus|vs)\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)'s",
            # Pattern for "X vs Y"
            r"([A-Z][A-Z]+|[A-Z][A-Za-z]+)(?:'s)?\s+(?:vs|versus)\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+)(?:'s)?",
            # Pattern for "between X and Y"
            r"between\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+)(?:'s)?\s+and\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+)(?:'s)?",
            # Pattern for "difference between X and Y"
            r"difference\s+between\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+)(?:'s)?\s+and\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+)(?:'s)?"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                entity1 = match.group(1).strip()
                entity2 = match.group(2).strip()
                
                # Clean up entities (remove "the", possessives, metric words)
                entity1 = self._clean_entity(entity1)
                entity2 = self._clean_entity(entity2)
                
                if entity1 and entity2:
                    # Make sure we have real entities, not just words like "last" or "years"
                    if len(entity1) > 1 and len(entity2) > 1:
                        return [entity1, entity2]
        
        return []
    
    def _clean_entity(self, entity: str) -> str:
        """Clean entity name"""
        # Remove common words
        remove_words = ["the", "a", "an", "of", "in", "last", "years", "year",
                       "gdp", "growth", "rate", "price", "cost", "data", "statistics"]
        
        words = entity.split()
        words = [w for w in words if w.lower() not in remove_words]
        
        return " ".join(words).strip()
    
    def _check_missing_entities(self, expected_entities: List[str], 
                                websearch_results: Dict[str, Any],
                                state: Dict[str, Any]) -> List[str]:
        """Check which entities are missing from search results"""
        if not expected_entities:
            return []
        
        # Get search output
        search_output = websearch_results.get("output", "").lower()
        
        # Check which entities are NOT mentioned in results
        missing = []
        for entity in expected_entities:
            entity_lower = entity.lower()
            # Check if entity appears in search results
            if entity_lower not in search_output:
                missing.append(entity)
        
        return missing
