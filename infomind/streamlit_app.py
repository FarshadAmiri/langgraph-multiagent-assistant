"""Streamlit UI for InfoMind multi-agent system"""

import streamlit as st
import time
from datetime import datetime
from typing import Dict, Any

from .graph import MultiAgentGraph
from .memory import MemoryStore


def init_session_state():
    """Initialize Streamlit session state"""
    if 'graph' not in st.session_state:
        st.session_state.graph = MultiAgentGraph()
    if 'memory' not in st.session_state:
        st.session_state.memory = MemoryStore()
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []


def display_agent_activity(agents_to_call):
    """Display agent activity trace"""
    if agents_to_call:
        trace = " → ".join([f"**{agent.upper()}**" for agent in agents_to_call])
        st.info(f"🔄 **Activity Trace:** USER → CONTROLLER → {trace}")


def display_intermediate_results(state: Dict[str, Any]):
    """Display intermediate results from agents"""
    with st.expander("📊 Intermediate Results", expanded=False):
        cols = st.columns(2)
        
        col_idx = 0
        if "websearch_results" in state:
            with cols[col_idx % 2]:
                st.success("✓ Web Search: Completed")
                col_idx += 1
        
        if "scraper_results" in state:
            with cols[col_idx % 2]:
                st.success("✓ Web Scraper: Completed")
                col_idx += 1
        
        if "math_results" in state:
            with cols[col_idx % 2]:
                st.success("✓ Math Calculation: Completed")
                col_idx += 1
        
        if "comparison_results" in state:
            with cols[col_idx % 2]:
                st.success("✓ Comparison: Completed")
                col_idx += 1


def display_final_answer(state: Dict[str, Any]):
    """Display final answer"""
    if "final_answer" in state:
        answer = state["final_answer"]
        output = answer.get("output", "No answer generated")
        sources = answer.get("sources", [])
        
        st.markdown("### 🎯 Final Answer")
        st.markdown(output)
        
        if sources and sources != ["internal_calculation"]:
            with st.expander(f"📚 Sources ({len(sources)})", expanded=False):
                for i, source in enumerate(sources, 1):
                    st.markdown(f"{i}. {source}")


def display_recent_queries():
    """Display recent queries from memory"""
    with st.sidebar:
        st.markdown("### 📜 Recent Queries")
        
        recent = st.session_state.memory.get_recent_interactions(limit=5)
        
        if recent:
            for interaction in recent:
                query = interaction.get("query", "")
                timestamp = interaction.get("timestamp", "")
                
                # Format timestamp
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = timestamp
                
                if st.button(f"🕐 {time_str}: {query[:30]}...", key=f"recent_{timestamp}"):
                    st.session_state.current_query = query
        else:
            st.info("No recent queries")


def main():
    """Main Streamlit app"""
    st.set_page_config(
        page_title="InfoMind - Multi-Agent System",
        page_icon="📚",
        layout="wide"
    )
    
    # Initialize
    init_session_state()
    
    # Header
    st.title("📚 InfoMind")
    st.markdown("### Multi-Agent Information Retrieval System")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 💡 Example Queries")
        
        examples = [
            "Calculate the average of 10, 20, 30, 40, 50",
            "Calculate the sum of 100, 200, 300",
            "Find latest news about AI",
            "Compare Python and JavaScript",
        ]
        
        for example in examples:
            if st.button(example, key=f"example_{example[:20]}"):
                st.session_state.current_query = example
        
        st.markdown("---")
        display_recent_queries()
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        InfoMind uses multiple specialized agents to answer your queries:
        - **Controller**: Routes queries
        - **WebSearch**: Searches the web
        - **Scraper**: Extracts content
        - **Math**: Performs calculations
        - **Comparison**: Compares items
        - **Synthesizer**: Combines results
        """)
    
    # Main area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "🔍 Enter your query:",
            value=st.session_state.get("current_query", ""),
            placeholder="e.g., Calculate the average of 10, 20, 30"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.button("🚀 Submit", type="primary", use_container_width=True)
    
    if submit and query:
        # Clear current query
        if "current_query" in st.session_state:
            del st.session_state.current_query
        
        # Create placeholders
        status_placeholder = st.empty()
        activity_placeholder = st.empty()
        intermediate_placeholder = st.empty()
        answer_placeholder = st.empty()
        metrics_placeholder = st.empty()
        
        try:
            # Show processing
            with status_placeholder:
                st.info("🔄 Processing your query...")
            
            # Track time
            start_time = time.time()
            
            # Run query
            state = st.session_state.graph.run(query)
            
            # Calculate runtime
            runtime = time.time() - start_time
            
            # Clear processing message
            status_placeholder.empty()
            
            # Display results
            with activity_placeholder.container():
                display_agent_activity(state.get("agents_to_call", []))
            
            with intermediate_placeholder.container():
                display_intermediate_results(state)
            
            with answer_placeholder.container():
                display_final_answer(state)
            
            # Display metrics
            with metrics_placeholder.container():
                cols = st.columns(4)
                with cols[0]:
                    st.metric("⏱️ Runtime", f"{runtime:.2f}s")
                with cols[1]:
                    agents_count = len([k for k in state.keys() if k.endswith("_results")])
                    st.metric("🤖 Agents Used", agents_count)
                with cols[2]:
                    sources_count = len(state.get("final_answer", {}).get("sources", []))
                    st.metric("📚 Sources", sources_count)
                with cols[3]:
                    st.metric("✅ Status", "Complete")
            
            # Store in memory
            if "final_answer" in state:
                final_answer = state["final_answer"]
                st.session_state.memory.store_interaction(
                    query=query,
                    agent="MultiAgentSystem",
                    output=final_answer.get("output", ""),
                    sources=final_answer.get("sources", []),
                    metadata={"runtime": runtime}
                )
            
            # Add to history
            st.session_state.query_history.append({
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "runtime": runtime
            })
            
        except Exception as e:
            status_placeholder.error(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
