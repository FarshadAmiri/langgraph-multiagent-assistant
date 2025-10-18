# WasMAS - Multi-Agent Information Retrieval System

A sophisticated multi-agent Python system built with LangGraph and LangChain that coordinates multiple intelligent agents to answer complex queries using real-world tools.

## 🌟 Features

- **Multi-Agent Coordination**: Intelligent routing and orchestration of specialized agents
- **Real-World Tools**: Web search, scraping, mathematical calculations, and comparisons
- **Memory System**: Lightweight SQLite-based memory for tracking interactions
- **Comprehensive Logging**: Detailed logs and trace files for debugging and monitoring
- **Clean CLI Interface**: Simple command-line interface with activity traces
- **Modular Design**: Easy to extend with new agents

## 🏗️ Architecture

### Core Agents

1. **ControllerAgent** - Interprets queries and routes to appropriate agents
2. **WebSearchAgent** - Performs live web searches using DuckDuckGo
3. **WebScraperAgent** - Extracts content from URLs using BeautifulSoup4
4. **MathAgent** - Handles arithmetic and statistical calculations
5. **ComparisonAgent** - Compares multiple items and summarizes differences
6. **AnswerSynthesizer** - Combines all outputs into a coherent final answer

### Workflow

```
UserInput → ControllerAgent → [Specialized Agents] → AnswerSynthesizer → Output
```

Each agent passes structured messages containing:
- `task`: What needs to be done
- `output`: Results of the operation
- `sources`: Citations and references
- `timestamp`: When the operation occurred
- `metadata`: Additional context

## 📦 Project Structure

```
WasMAS/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py          # Base class for all agents
│   ├── controller_agent.py    # Query routing
│   ├── websearch_agent.py     # Web searching
│   ├── scraper_agent.py       # Content extraction
│   ├── math_agent.py          # Calculations
│   ├── comparison_agent.py    # Item comparison
│   └── synthesizer_agent.py   # Answer synthesis
├── utils/
│   ├── __init__.py
│   └── logger.py              # Shared logging
├── graph.py                    # LangGraph orchestration
├── main.py                     # CLI interface
├── memory.py                   # Memory store
└── logs/                       # Log files and traces
    └── traces/                 # JSON trace files
```

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/FarshadAmiri/langgraph-multiagent-assistant.git
cd langgraph-multiagent-assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Set up API keys for advanced features:
```bash
# Create .env file for API keys if using premium services
echo "OPENAI_API_KEY=your-key-here" > .env
```

## 💻 Usage

### Option 1: CLI Interactive Mode

Run the CLI in interactive mode:

```bash
python -m WasMAS.main
```

### Option 2: CLI Single Query Mode

Run a single query and exit:

```bash
python -m WasMAS.main "Calculate the average of 10, 20, 30"
```

### Option 3: Streamlit Web UI

Run the Streamlit web interface:

```bash
streamlit run WasMAS/streamlit_app.py
```

This provides a user-friendly web interface with:
- Real-time agent activity visualization
- Intermediate results display
- Recent query history
- Example queries
- Performance metrics

### Option 4: Programmatic Usage

Use WasMAS in your Python code:

```python
from WasMAS.graph import MultiAgentGraph

graph = MultiAgentGraph()
result = graph.run("Calculate the sum of 10 and 20")
print(result["final_answer"]["output"])
```

See `examples.py` for more usage examples.

### Example Queries

```bash
# Mathematical operations
python -m WasMAS.main "Calculate the average of 15, 25, 35, 45"

# Web search
python -m WasMAS.main "Find latest news about AI developments"

# Comparison
python -m WasMAS.main "Compare Python and JavaScript"

# Complex queries
python -m WasMAS.main "Find and compare recent news about OpenAI and Anthropic"
```

## 📊 Output Example

```
================================================================================
  📚 WasMAS - Multi-Agent Information Retrieval System
================================================================================

📝 Query: Calculate the average of 10, 20, 30

🔄 Activity Trace:
------------------------------------------------------------------------
[USER] → [CONTROLLER] → [MATH] → [SYNTHESIZER]
------------------------------------------------------------------------

📊 Intermediate Results:
------------------------------------------------------------------------
✓ Math Calculation: Completed
------------------------------------------------------------------------

================================================================================
  🎯 FINAL ANSWER
================================================================================

📋 Answer to: Calculate the average of 10, 20, 30

================================================================

🔍 From MATH:
----------------------------------------------------------------
Average: 20.00 (calculated from 3 values: [10.0, 20.0, 30.0])

================================================================
📊 SUMMARY:
----------------------------------------------------------------
✓ Calculations: Average: 20.00 (calculated from 3 values: [10.0, 20.0, 30.0])

================================================================================

⏱️  Total Runtime: 0.05 seconds
```

## 🔧 Configuration

### Logging

Logs are stored in `WasMAS/logs/`:
- Individual agent logs: `{agent_name}.log`
- Execution traces: `traces/trace_{timestamp}.json`

### Memory

Memory database is stored at `WasMAS/logs/memory.db`:
- Stores all interactions
- Enables context-aware follow-up queries
- Can be cleared with `memory.clear_old_interactions(days=30)`

## 🧪 Testing

The system can be tested with various query types:

```python
from WasMAS.graph import MultiAgentGraph

graph = MultiAgentGraph()
result = graph.run("Calculate the sum of 5 and 10")
print(result["final_answer"]["output"])
```

## 🔍 Logging & Monitoring

Every agent logs:
- Start and finish times
- Task descriptions
- Key results (truncated for readability)
- Errors and warnings

Activity traces show the execution flow:
```
[USER] → [CONTROLLER] → [WEBSEARCH] → [SCRAPER] → [SYNTHESIZER]
```

JSON traces in `logs/traces/` contain:
- Full execution state
- Runtime metrics
- All intermediate results
- Source citations

## 🛠️ Extending the System

### Adding a New Agent

1. Create a new agent class inheriting from `BaseAgent`:

```python
from WasMAS.agents.base_agent import BaseAgent

class MyNewAgent(BaseAgent):
    def __init__(self):
        super().__init__("MyNewAgent")
    
    def execute(self, state):
        # Your logic here
        return state
```

2. Add the agent to `graph.py`:

```python
self.my_agent = MyNewAgent()
workflow.add_node("myagent", self._my_agent_node)
```

3. Update the controller's routing logic in `controller_agent.py`

## 📝 Requirements

- Python 3.8+
- langgraph >= 0.0.50
- langchain >= 0.1.0
- requests >= 2.31.0
- beautifulsoup4 >= 4.12.0
- duckduckgo-search >= 4.0.0

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

Built with:
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [LangChain](https://github.com/langchain-ai/langchain) - LLM framework
- [DuckDuckGo Search](https://github.com/deedy5/duckduckgo_search) - Web search
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) - Web scraping

## 📧 Contact

For questions or feedback, please open an issue on GitHub.