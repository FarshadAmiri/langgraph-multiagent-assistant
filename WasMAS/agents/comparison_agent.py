"""Comparison Agent - Compares multiple items or results"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class ComparisonAgent(BaseAgent):
    """
    Compares multi-item outputs and summarizes differences
    """
    
    def __init__(self):
        super().__init__("ComparisonAgent")
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Compare items from various sources"""
        query = state.get("query", "")
        self._log_start(query)
        
        try:
            # Gather data to compare from previous agent results
            comparison_data = self._gather_comparison_data(state)
            
            if not comparison_data:
                self._log_finish("No data to compare")
                state["comparison_results"] = self._create_output(
                    output="No comparable data found from previous agents.",
                    sources=[]
                )
                return state
            
            # Perform comparison
            comparison_result = self._compare_data(comparison_data, query)
            
            # Extract sources
            sources = []
            for item in comparison_data:
                sources.extend(item.get("sources", []))
            
            output = self._create_output(
                output=comparison_result,
                sources=list(set(sources)),
                metadata={"items_compared": len(comparison_data)}
            )
            
            self._log_finish(f"Compared {len(comparison_data)} items")
            state["comparison_results"] = output
            return state
            
        except Exception as e:
            self._log_error(str(e))
            state["comparison_results"] = self._create_output(
                output=f"Error during comparison: {str(e)}",
                sources=[]
            )
            return state
    
    def _gather_comparison_data(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gather data from various agent results"""
        data = []
        
        # From web search
        if "websearch_results" in state:
            data.append({
                "source": "websearch",
                "content": state["websearch_results"].get("output", ""),
                "sources": state["websearch_results"].get("sources", [])
            })
        
        # From scraper
        if "scraper_results" in state:
            data.append({
                "source": "scraper",
                "content": state["scraper_results"].get("output", ""),
                "sources": state["scraper_results"].get("sources", [])
            })
        
        # From math
        if "math_results" in state:
            data.append({
                "source": "math",
                "content": state["math_results"].get("output", ""),
                "sources": state["math_results"].get("sources", [])
            })
        
        return data
    
    def _compare_data(self, data: List[Dict[str, Any]], query: str) -> str:
        """Compare the gathered data"""
        if len(data) < 2:
            return f"Only one data source available. Cannot perform comparison.\n\n{data[0]['content']}"
        
        comparison = "Comparison Analysis:\n\n"
        
        # Identify comparison items from query
        query_lower = query.lower()
        
        # Extract key terms for comparison
        comparison += "Data from different sources:\n\n"
        
        for i, item in enumerate(data, 1):
            source = item["source"]
            content = item["content"]
            
            # Trim content for comparison
            preview = content[:300] if len(content) > 300 else content
            
            comparison += f"{i}. Source: {source.upper()}\n"
            comparison += f"   {preview}...\n\n"
        
        # Add summary
        comparison += "Summary:\n"
        comparison += f"- Compared {len(data)} different data sources\n"
        
        # Look for similarities and differences
        if any("price" in query_lower or "cost" in query_lower for _ in [query_lower]):
            comparison += "- Focus: Price/Cost comparison\n"
        elif any("news" in query_lower or "article" in query_lower for _ in [query_lower]):
            comparison += "- Focus: News/Article comparison\n"
        else:
            comparison += "- General comparison of available data\n"
        
        return comparison
