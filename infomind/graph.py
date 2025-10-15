"""LangGraph orchestration for multi-agent system"""

from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
from .agents.controller_agent import ControllerAgent
from .agents.websearch_agent import WebSearchAgent
from .agents.scraper_agent import WebScraperAgent
from .agents.math_agent import MathAgent
from .agents.comparison_agent import ComparisonAgent
from .agents.synthesizer_agent import AnswerSynthesizer


class AgentState(TypedDict):
    """State schema for the agent system"""
    query: str
    agents_to_call: list
    websearch_results: Dict[str, Any]
    scraper_results: Dict[str, Any]
    math_results: Dict[str, Any]
    comparison_results: Dict[str, Any]
    final_answer: Dict[str, Any]
    routing_complete: bool


class MultiAgentGraph:
    """LangGraph-based multi-agent orchestration"""
    
    def __init__(self):
        # Initialize all agents
        self.controller = ControllerAgent()
        self.websearch = WebSearchAgent()
        self.scraper = WebScraperAgent()
        self.math = MathAgent()
        self.comparison = ComparisonAgent()
        self.synthesizer = AnswerSynthesizer()
        
        # Build graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create workflow
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("controller", self._controller_node)
        workflow.add_node("execute_agents", self._execute_agents_node)
        workflow.add_node("synthesizer", self._synthesizer_node)
        
        # Set entry point
        workflow.set_entry_point("controller")
        
        # Controller routes to agent executor
        workflow.add_edge("controller", "execute_agents")
        
        # Agent executor routes to synthesizer
        workflow.add_edge("execute_agents", "synthesizer")
        
        # Synthesizer ends the workflow
        workflow.add_edge("synthesizer", END)
        
        return workflow.compile()
    
    def _controller_node(self, state: AgentState) -> AgentState:
        """Controller agent node"""
        result = self.controller.execute(state)
        state.update(result)
        return state
    
    def _execute_agents_node(self, state: AgentState) -> AgentState:
        """Execute all required agents in sequence"""
        agents_to_call = state.get("agents_to_call", [])
        
        # Map agent names to agent instances
        agent_map = {
            "websearch": self.websearch,
            "scraper": self.scraper,
            "math": self.math,
            "comparison": self.comparison
        }
        
        # Execute each agent in sequence (except synthesizer)
        for agent_name in agents_to_call:
            if agent_name != "synthesizer" and agent_name in agent_map:
                agent = agent_map[agent_name]
                state = agent.execute(state)
        
        return state
    
    def _synthesizer_node(self, state: AgentState) -> AgentState:
        """Synthesizer agent node"""
        return self.synthesizer.execute(state)
    
    def run(self, query: str) -> Dict[str, Any]:
        """
        Run the multi-agent system with a query
        
        Args:
            query: User's question
            
        Returns:
            Final state with answer
        """
        initial_state = {
            "query": query,
            "agents_to_call": [],
            "routing_complete": False
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state
