"""Streamlit UI for WasMAS multi-agent system"""

import streamlit as st
import time
from datetime import datetime
from typing import Dict, Any

from WasMAS.graph import MultiAgentGraph
from WasMAS.memory import MemoryStore


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
    """Display detailed intermediate results from agents with logs"""
    with st.expander("📊 Detailed Agent Logs & Results", expanded=True):
        
        # WebSearch Agent
        if "websearch_results" in state:
            st.markdown("### 🔍 Web Search Agent")
            ws_meta = state["websearch_results"].get("metadata", {})
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Query Information:**")
                original_q = ws_meta.get('original_query', 'N/A')
                st.text(f"Original: {original_q[:80]}...")
                
                if ws_meta.get('search_type') == 'multi-entity_comparison':
                    st.info("🔀 Multi-Entity Comparison Search")
                    entities = ws_meta.get('comparison_entities', [])
                    st.text(f"Entities: {', '.join(entities)}")
                else:
                    final_q = ws_meta.get('final_query', 'N/A')
                    st.text(f"Optimized: {final_q[:80]}...")
                    
                    attempts = ws_meta.get('search_attempts', 1)
                    if attempts > 1:
                        st.warning(f"⚠️ Required {attempts} search attempts")
            
            with col2:
                st.markdown("**Results:**")
                result_count = ws_meta.get('result_count', 0)
                validated = ws_meta.get('validated', False)
                
                if result_count > 0:
                    st.success(f"✓ Found {result_count} results")
                else:
                    st.error("✗ No results found")
                
                if ws_meta.get('search_attempts', 1) == 1:
                    if validated:
                        st.success("✓ Results validated as relevant")
                    else:
                        st.warning("⚠️ Results may not be fully relevant")
            
            # Show sources
            sources = state["websearch_results"].get("sources", [])
            if sources:
                with st.expander(f"🔗 View {len(sources)} Search Sources", expanded=False):
                    for i, source in enumerate(sources, 1):
                        st.markdown(f"{i}. [{source[:60]}...]({source})")
            
            st.markdown("---")
        
        # Scraper Agent
        if "scraper_results" in state:
            st.markdown("### 🌐 Web Scraper Agent")
            sc_meta = state["scraper_results"].get("metadata", {})
            
            urls_scraped = sc_meta.get('urls_scraped', 0)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Scraping Activity:**")
                if urls_scraped > 0:
                    st.success(f"✓ Successfully scraped {urls_scraped} URLs")
                else:
                    st.info("ℹ️ No URLs scraped (none available)")
            
            with col2:
                st.markdown("**Status:**")
                output = state["scraper_results"].get("output", "")
                if "Error" not in output:
                    content_length = len(output)
                    st.text(f"Content extracted: {content_length} chars")
                else:
                    st.warning("⚠️ Some errors occurred")
            
            # Show scraped URLs
            if urls_scraped > 0:
                sources = state["scraper_results"].get("sources", [])
                with st.expander(f"🔗 View {len(sources)} Scraped URLs", expanded=False):
                    for i, url in enumerate(sources, 1):
                        st.markdown(f"{i}. [{url[:60]}...]({url})")
            
            st.markdown("---")
        
        # Math Agent
        if "math_results" in state:
            st.markdown("### 🔢 Math Agent")
            
            output = state["math_results"].get("output", "")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Calculation:**")
                preview = output[:150] if len(output) > 150 else output
                st.text(preview)
            
            with col2:
                st.markdown("**Status:**")
                if "Error" not in output:
                    st.success("✓ Calculation completed")
                else:
                    st.error("✗ Calculation failed")
            
            st.markdown("---")
        
        # Comparison Agent
        if "comparison_results" in state:
            st.markdown("### ⚖️ Comparison Agent")
            comp_meta = state["comparison_results"].get("metadata", {})
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Comparison Details:**")
                items = comp_meta.get('items_compared', 0)
                st.text(f"Items compared: {items}")
            
            with col2:
                st.markdown("**Status:**")
                output = state["comparison_results"].get("output", "")
                if "Error" not in output:
                    st.success("✓ Comparison completed")
                else:
                    st.error("✗ Comparison failed")
            
            # Show sources used
            sources = state["comparison_results"].get("sources", [])
            if sources:
                with st.expander(f"📚 View {len(sources)} Comparison Sources", expanded=False):
                    for i, source in enumerate(sources, 1):
                        if source and source != "internal_calculation":
                            st.text(f"{i}. {source[:80]}...")
            
            st.markdown("---")
        
        # Summary
        total_agents = sum([
            1 if "websearch_results" in state else 0,
            1 if "scraper_results" in state else 0,
            1 if "math_results" in state else 0,
            1 if "comparison_results" in state else 0
        ])
        
        st.info(f"📋 Total Agents Executed: {total_agents}")


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
                
                if st.button(f"{query[:50]}...", key=f"recent_{timestamp}"):
                    st.session_state.current_query = query
        else:
            st.info("No recent queries")


def main():
    """Main Streamlit app"""
    st.set_page_config(
        page_title="WasMAS - Multi-Agent System",
        page_icon="📚",
        layout="wide"
    )
    
    # Initialize
    init_session_state()
    
    # Header
    st.title("📚 WasMAS")
    st.markdown("### Multi-Agent Information Retrieval System")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 💡 Example Queries")
        
        examples = [
            "Latest BMW 5 Series lease costs?",
            "compare UK's GDP growth in last 5 years with Germany's.",
            "Find latest news about AI",
        ]
        
        for example in examples:
            if st.button(example, key=f"example_{example[:20]}"):
                st.session_state.current_query = example
                
        
        st.markdown("---")
        display_recent_queries()
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        WasMAS uses multiple specialized agents to answer your queries:
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
