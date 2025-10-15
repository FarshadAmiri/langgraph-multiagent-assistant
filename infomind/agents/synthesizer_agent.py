"""Answer Synthesizer - Combines all agent outputs into final answer"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class AnswerSynthesizer(BaseAgent):
    """
    Combines all agent outputs into a final, human-readable answer
    with concise reasoning and cited sources
    """
    
    def __init__(self):
        super().__init__("AnswerSynthesizer")
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize final answer from all agent outputs"""
        query = state.get("query", "")
        self._log_start(query)
        
        try:
            # Gather all agent outputs
            agent_outputs = self._gather_outputs(state)
            
            # Synthesize final answer
            final_answer = self._synthesize_answer(query, agent_outputs)
            
            # Gather all sources
            all_sources = self._gather_sources(agent_outputs)
            
            output = self._create_output(
                output=final_answer,
                sources=all_sources,
                metadata={
                    "agents_used": list(agent_outputs.keys()),
                    "total_sources": len(all_sources)
                }
            )
            
            self._log_finish("Synthesis complete")
            state["final_answer"] = output
            return state
            
        except Exception as e:
            self._log_error(str(e))
            state["final_answer"] = self._create_output(
                output=f"Error during synthesis: {str(e)}",
                sources=[]
            )
            return state
    
    def _gather_outputs(self, state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Gather outputs from all agents"""
        outputs = {}
        
        result_keys = [
            "websearch_results",
            "scraper_results",
            "math_results",
            "comparison_results"
        ]
        
        for key in result_keys:
            if key in state:
                agent_name = key.replace("_results", "")
                outputs[agent_name] = state[key]
        
        return outputs
    
    def _gather_sources(self, agent_outputs: Dict[str, Dict[str, Any]]) -> List[str]:
        """Gather all sources from agent outputs"""
        all_sources = []
        
        for agent_output in agent_outputs.values():
            sources = agent_output.get("sources", [])
            all_sources.extend(sources)
        
        # Remove duplicates and filter
        unique_sources = []
        seen = set()
        for source in all_sources:
            if source and source not in seen and source != "internal_calculation":
                unique_sources.append(source)
                seen.add(source)
        
        return unique_sources
    
    def _synthesize_answer(
        self,
        query: str,
        agent_outputs: Dict[str, Dict[str, Any]]
    ) -> str:
        """Synthesize final answer from agent outputs"""
        
        answer = f"📋 Answer to: {query}\n\n"
        answer += "=" * 60 + "\n\n"
        
        if not agent_outputs:
            answer += "No data was gathered from any agents.\n"
            return answer
        
        # Add each agent's contribution
        for agent_name, output_data in agent_outputs.items():
            output_text = output_data.get("output", "")
            
            if output_text and not output_text.startswith("Error"):
                answer += f"🔍 From {agent_name.upper()}:\n"
                answer += "-" * 60 + "\n"
                
                # Limit each agent's output
                preview = output_text[:500] if len(output_text) > 500 else output_text
                answer += f"{preview}\n"
                
                if len(output_text) > 500:
                    answer += "...(truncated)\n"
                
                answer += "\n"
        
        # Add summary
        answer += "=" * 60 + "\n"
        answer += "📊 SUMMARY:\n"
        answer += "-" * 60 + "\n"
        
        # Create concise summary based on available data
        if "websearch" in agent_outputs:
            answer += "✓ Web search completed - found relevant information\n"
        
        if "scraper" in agent_outputs:
            answer += "✓ Content scraped from URLs\n"
        
        if "math" in agent_outputs:
            math_output = agent_outputs["math"].get("output", "")
            if "Error" not in math_output:
                answer += f"✓ Calculations: {math_output[:100]}\n"
        
        if "comparison" in agent_outputs:
            answer += "✓ Comparison analysis completed\n"
        
        # Add sources
        all_sources = self._gather_sources(agent_outputs)
        if all_sources:
            answer += f"\n📚 Sources ({len(all_sources)}):\n"
            for i, source in enumerate(all_sources[:5], 1):
                answer += f"  {i}. {source}\n"
            
            if len(all_sources) > 5:
                answer += f"  ... and {len(all_sources) - 5} more\n"
        
        return answer
