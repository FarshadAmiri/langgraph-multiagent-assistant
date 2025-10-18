# InfoMind System Architecture

## 🏗️ High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                         User Interfaces                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  CLI Mode   │  │ Streamlit UI │  │  Python API          │   │
│  │  (main.py)  │  │ (streamlit_  │  │  (graph.run())       │   │
│  │             │  │  app.py)     │  │                      │   │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬───────────┘   │
└─────────┼────────────────┼─────────────────────┼───────────────┘
          │                │                     │
          └────────────────┼─────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Orchestration                      │
│                          (graph.py)                             │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     StateGraph Workflow                   │  │
│  │                                                           │  │
│  │   [Entry] → [Controller] → [Execute Agents]               │  │
│  │                                    ↓                      │  │
│  │                              [Synthesizer] → [END]        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
        ▼                                     ▼
┌──────────────────┐              ┌──────────────────────┐
│  Controller      │              │  Agent Executor      │
│  Agent           │──[routing]──▶│  (Sequential)       │
│                  │              │                      │
│  • Query         │              │  Executes agents     │
│    analysis      │              │  based on routing    │
│  • Route to      │              │                      │
│    agents        │              └──────────┬───────────┘
└──────────────────┘                         │
                                             │
                 ┌───────────────────────────┼───────────────────────────┐
                 │                           │                           │
                 ▼                           ▼                           ▼
        ┌────────────────┐         ┌────────────────┐         ┌────────────────┐
        │  WebSearch     │         │  WebScraper    │         │  Math          │
        │  Agent         │         │  Agent         │         │  Agent         │
        │                │         │                │         │                │
        │  DuckDuckGo    │         │  BeautifulSoup │         │  Calculations  │
        │  Search        │         │  Scraping      │         │  (avg/sum/med) │
        └────────────────┘         └────────────────┘         └────────────────┘
                 │                           │                           │
                 └───────────────────────────┼───────────────────────────┘
                                             │
                                             ▼
                                   ┌────────────────┐
                                   │  Comparison    │
                                   │  Agent         │
                                   │                │
                                   │  Compares      │
                                   │  Multi-sources │
                                   └────────┬───────┘
                                            │
                                            ▼
                                   ┌────────────────┐
                                   │  Answer        │
                                   │  Synthesizer   │
                                   │                │
                                   │  Combines all  │
                                   │  outputs       │
                                   └────────┬───────┘
                                            │
        ┌───────────────────────────────────┴───────────────────────────────────┐
        │                                                                       │
        ▼                                                                       ▼
┌──────────────────┐                                                  ┌──────────────────┐
│  Memory System   │                                                  │  Logging System  │
│  (memory.py)     │                                                  │  (logger.py)     │
│                  │                                                  │                  │
│  SQLite DB       │                                                  │  • Per-agent     │
│  • Queries       │                                                  │    logs          │
│  • Outputs       │                                                  │  • JSON traces   │
│  • Sources       │                                                  │  • Timestamps    │
│  • Metadata      │                                                  │  • Activity      │
└──────────────────┘                                                  └──────────────────┘
```

## 🔄 Data Flow

### 1. Query Processing Flow

```
User Query
    │
    ▼
┌─────────────────────┐
│ ControllerAgent     │
│ • Analyze query     │
│ • Detect keywords   │
│ • Route to agents   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ State Object        │
│ {                   │
│   query: "...",     │
│   agents_to_call: []│
│ }                   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Agent Executor      │
│ For each agent:     │
│ • Execute           │
│ • Update state      │
│ • Pass to next      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ State Updated       │
│ {                   │
│   ...               │
│   agent_results: {} │
│   sources: []       │
│ }                   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ AnswerSynthesizer   │
│ • Combine results   │
│ • Format answer     │
│ • Cite sources      │
└──────┬──────────────┘
       │
       ▼
    Final Answer
```

### 2. Message Structure

Every agent communication follows this structure:

```python
{
    "output": "Agent's result text",
    "sources": ["source1", "source2", ...],
    "timestamp": "2025-10-15T12:00:00",
    "agent": "AgentName",
    "metadata": {
        "key": "value",
        "runtime": 0.05
    }
}
```

### 3. State Management

```python
class AgentState(TypedDict):
    query: str                           # User's query
    agents_to_call: list                 # Agents to execute
    websearch_results: Dict[str, Any]    # WebSearch output
    scraper_results: Dict[str, Any]      # Scraper output
    math_results: Dict[str, Any]         # Math output
    comparison_results: Dict[str, Any]   # Comparison output
    final_answer: Dict[str, Any]         # Synthesized answer
    routing_complete: bool               # Routing status
```

## 🧩 Agent Responsibilities

### ControllerAgent
**Purpose**: Query routing and orchestration
**Input**: User query
**Output**: List of agents to call
**Key Logic**:
- Keyword detection (search, calculate, compare)
- URL pattern recognition
- Sequential agent ordering

### WebSearchAgent
**Purpose**: Live web search
**Tools**: DuckDuckGo API
**Input**: Query string
**Output**: Formatted search results + sources
**Features**:
- Result formatting
- Source extraction
- Error handling

### WebScraperAgent
**Purpose**: URL content extraction
**Tools**: BeautifulSoup4, requests
**Input**: URLs (from query or search results)
**Output**: Cleaned text content
**Features**:
- HTML parsing
- Content cleaning
- Multiple URL handling

### MathAgent
**Purpose**: Mathematical calculations
**Tools**: Safe Python evaluation
**Input**: Query with numbers/operations
**Output**: Calculation results
**Supported**: Average, Sum, Median, Expressions

### ComparisonAgent
**Purpose**: Multi-source comparison
**Input**: Results from other agents
**Output**: Comparison summary
**Features**:
- Data aggregation
- Difference highlighting
- Summary generation

### AnswerSynthesizer
**Purpose**: Final answer generation
**Input**: All agent results
**Output**: Coherent answer with sources
**Features**:
- Result combination
- Source citation
- Summary creation
- Formatting

## 🗄️ Storage Systems

### Memory (SQLite)
```sql
CREATE TABLE interactions (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    query TEXT,
    agent TEXT,
    output TEXT,
    sources TEXT,
    metadata TEXT
);
```

### Logging Files
```
infomind/logs/
├── ControllerAgent.log
├── WebSearchAgent.log
├── WebScraperAgent.log
├── MathAgent.log
├── ComparisonAgent.log
├── AnswerSynthesizer.log
├── InfoMindCLI.log
├── memory.db
└── traces/
    ├── trace_20251015_120747.json
    └── trace_20251015_120757.json
```

## 🔒 Design Principles

1. **Modularity**: Each agent is independent and replaceable
2. **State-Based**: All communication through shared state
3. **Logging**: Comprehensive logging at every step
4. **Error Handling**: Graceful degradation on failures
5. **Extensibility**: Easy to add new agents
6. **Testability**: Each component can be tested independently

## 🚀 Execution Flow Example

Query: "Calculate the average of 10, 20, 30"

```
1. User submits query via CLI/UI/API
   ↓
2. MultiAgentGraph.run() called
   ↓
3. ControllerAgent analyzes query
   - Detects "calculate" + "average"
   - Routes to: [math, synthesizer]
   ↓
4. Execute Agents Node
   - Executes MathAgent
   - MathAgent extracts [10, 20, 30]
   - Calculates average: 20.0
   - Updates state with result
   ↓
5. AnswerSynthesizer
   - Reads math_results from state
   - Formats final answer
   - Adds sources and metadata
   ↓
6. Return final state to user
   ↓
7. Display results + log + store in memory
```

## 📊 Performance Characteristics

- **Initialization**: ~0.5s (load dependencies)
- **Math Operations**: <0.01s per query
- **Web Search**: 0.5-2s (network dependent)
- **Web Scraping**: 1-3s per URL
- **Memory Storage**: <0.01s per interaction

## 🔧 Configuration Points

1. **API Keys**: Via .env file
2. **Log Directory**: `infomind/logs/`
3. **Database Path**: `infomind/logs/memory.db`
4. **Max Search Results**: 5 (configurable)
5. **Max URLs to Scrape**: 3 (configurable)

## 🎯 Extension Points

To add a new agent:

1. Create class in `infomind/agents/new_agent.py`
2. Inherit from `BaseAgent`
3. Implement `execute(state)` method
4. Register in `graph.py`
5. Update routing in `controller_agent.py`
6. Add tests in `test_system.py`

## ✨ Key Features

- **Sequential Execution**: Agents run in order
- **State Persistence**: Results accumulate in state
- **Source Tracking**: All sources are cited
- **Activity Tracing**: Clear execution visualization
- **Error Resilience**: System continues on agent failures
- **Memory Context**: Access to past interactions

## 📝 Summary

InfoMind's architecture is:
- ✅ Modular and maintainable
- ✅ Based on LangGraph StateGraph
- ✅ Fully logged and traceable
- ✅ Extensible for new agents
- ✅ Production-ready with error handling
