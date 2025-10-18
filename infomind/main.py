"""Main CLI interface for InfoMind multi-agent system"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import json

from infomind.graph import MultiAgentGraph
from infomind.memory import MemoryStore
from infomind.utils.logger import get_logger


class InfoMindCLI:
    """Command-line interface for InfoMind"""
    
    def __init__(self):
        self.logger = get_logger("InfoMindCLI")
        self.graph = MultiAgentGraph()
        self.memory = MemoryStore()
        self.trace_dir = Path(__file__).parent / "logs" / "traces"
        self.trace_dir.mkdir(parents=True, exist_ok=True)
    
    def print_header(self):
        """Print CLI header"""
        print("\n" + "=" * 70)
        print("  📚 InfoMind - Multi-Agent Information Retrieval System")
        print("=" * 70 + "\n")
    
    def print_activity_trace(self, state: Dict[str, Any]):
        """Print activity trace"""
        print("\n🔄 Activity Trace:")
        print("-" * 70)
        
        agents_called = []
        if "agents_to_call" in state:
            agents_called = state["agents_to_call"]
        
        if agents_called:
            trace = " → ".join([f"[{agent.upper()}]" for agent in agents_called])
            print(f"[USER] → [CONTROLLER] → {trace}")
        else:
            print("[USER] → [CONTROLLER] → [SYNTHESIZER]")
        
        print("-" * 70 + "\n")
    
    def print_final_answer(self, state: Dict[str, Any]):
        """Print final answer"""
        if "final_answer" in state:
            answer = state["final_answer"]
            output = answer.get("output", "No answer generated")
            
            print("\n" + "=" * 70)
            print("  🎯 FINAL ANSWER")
            print("=" * 70 + "\n")
            print(output)
            print("\n" + "=" * 70 + "\n")
    
    def save_trace(self, query: str, state: Dict[str, Any], runtime: float):
        """Save execution trace to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trace_file = self.trace_dir / f"trace_{timestamp}.json"
        
        trace = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "runtime_seconds": runtime,
            "agents_called": state.get("agents_to_call", []),
            "final_answer": state.get("final_answer", {}),
            "full_state": {
                k: v for k, v in state.items()
                if k not in ["final_answer"]  # Avoid duplication
            }
        }
        
        try:
            with open(trace_file, 'w') as f:
                json.dump(trace, f, indent=2, default=str)
            self.logger.info(f"Trace saved to {trace_file}")
        except Exception as e:
            self.logger.error(f"Failed to save trace: {e}")
    
    def run_query(self, query: str):
        """Run a single query"""
        print(f"\n📝 Query: {query}\n")
        
        # Track runtime
        start_time = time.time()
        
        try:
            # Run the graph
            self.logger.info(f"Processing query: {query}")
            state = self.graph.run(query)
            
            # Calculate runtime
            runtime = time.time() - start_time
            
            # Print activity trace
            self.print_activity_trace(state)
            
            # Print intermediate results summary
            print("📊 Intermediate Results:")
            print("-" * 70)
            
            # WebSearch Agent Details
            if "websearch_results" in state:
                ws_meta = state["websearch_results"].get("metadata", {})
                print("\n🔍 WEB SEARCH AGENT:")
                print(f"   Original Query: {ws_meta.get('original_query', 'N/A')}")
                
                if ws_meta.get('search_type') == 'multi-entity_comparison':
                    print(f"   Search Type: Multi-Entity Comparison")
                    entities = ws_meta.get('comparison_entities', [])
                    print(f"   Entities: {', '.join(entities)}")
                    print(f"   Results Found: {ws_meta.get('result_count', 0)}")
                else:
                    print(f"   Final Query: {ws_meta.get('final_query', 'N/A')}")
                    print(f"   Search Attempts: {ws_meta.get('search_attempts', 1)}")
                    print(f"   Results Found: {ws_meta.get('result_count', 0)}")
                    print(f"   Results Validated: {'✓' if ws_meta.get('validated') else '✗'}")
                
                print("   Status: ✓ Completed")
            
            # Scraper Agent Details
            if "scraper_results" in state:
                sc_meta = state["scraper_results"].get("metadata", {})
                print("\n🌐 WEB SCRAPER AGENT:")
                print(f"   URLs Scraped: {sc_meta.get('urls_scraped', 0)}")
                if sc_meta.get('urls_scraped', 0) > 0:
                    sources = state["scraper_results"].get("sources", [])
                    for i, url in enumerate(sources[:3], 1):
                        print(f"   {i}. {url[:60]}...")
                print("   Status: ✓ Completed")
            
            # Math Agent Details
            if "math_results" in state:
                print("\n🔢 MATH AGENT:")
                output = state["math_results"].get("output", "")
                preview = output[:100] if len(output) > 100 else output
                print(f"   Result: {preview}")
                print("   Status: ✓ Completed")
            
            # Comparison Agent Details
            if "comparison_results" in state:
                comp_meta = state["comparison_results"].get("metadata", {})
                print("\n⚖️  COMPARISON AGENT:")
                print(f"   Items Compared: {comp_meta.get('items_compared', 0)}")
                print("   Status: ✓ Completed")
            
            print("-" * 70)
            
            # Print final answer
            self.print_final_answer(state)
            
            # Print runtime
            print(f"⏱️  Total Runtime: {runtime:.2f} seconds\n")
            
            # Store in memory
            if "final_answer" in state:
                final_answer = state["final_answer"]
                self.memory.store_interaction(
                    query=query,
                    agent="MultiAgentSystem",
                    output=final_answer.get("output", ""),
                    sources=final_answer.get("sources", []),
                    metadata={"runtime": runtime}
                )
            
            # Save trace
            self.save_trace(query, state, runtime)
            
            return state
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            print(f"\n❌ Error: {e}\n")
            return None
    
    def interactive_mode(self):
        """Run in interactive mode"""
        self.print_header()
        
        print("💡 Example queries:")
        print("  - Compare today's price of gold and silver")
        print("  - Calculate the average of 10, 20, 30, 40, 50")
        print("  - Find latest news about AI developments")
        print("\nType 'exit' or 'quit' to exit\n")
        
        while True:
            try:
                query = input("🔍 Enter your query: ").strip()
                
                if not query:
                    continue
                
                if query.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye!\n")
                    break
                
                self.run_query(query)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
    
    def single_query_mode(self, query: str):
        """Run a single query and exit"""
        self.print_header()
        self.run_query(query)


def main():
    """Main entry point"""
    cli = InfoMindCLI()
    
    if len(sys.argv) > 1:
        # Single query mode
        query = " ".join(sys.argv[1:])
        cli.single_query_mode(query)
    else:
        # Interactive mode
        cli.interactive_mode()


if __name__ == "__main__":
    main()
