# InfoMind Quick Start Guide

Get up and running with InfoMind in 5 minutes!

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/FarshadAmiri/langgraph-multiagent-assistant.git
cd langgraph-multiagent-assistant

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Run Your First Query

### Option 1: Interactive CLI

```bash
python -m infomind.main
```

Then type your query:
```
🔍 Enter your query: Calculate the average of 10, 20, 30
```

### Option 2: Single Query

```bash
python -m infomind.main "Calculate the sum of 5, 10, 15"
```

### Option 3: Web Interface

```bash
streamlit run infomind/streamlit_app.py
```

Then open your browser to http://localhost:8501

## 💡 Example Queries to Try

### Mathematical Operations
```bash
python -m infomind.main "Calculate the average of 10, 20, 30, 40, 50"
python -m infomind.main "Find the median of 5, 15, 25, 35, 45"
python -m infomind.main "Calculate the sum of 100, 200, 300"
```

### Web Search (requires internet)
```bash
python -m infomind.main "Find latest news about AI"
python -m infomind.main "Search for Python tutorials"
```

### Comparison (requires internet)
```bash
python -m infomind.main "Compare Python and JavaScript"
python -m infomind.main "Compare gold and silver prices"
```

## 📊 Understanding the Output

When you run a query, you'll see:

1. **Activity Trace** - Shows which agents were called
   ```
   [USER] → [CONTROLLER] → [MATH] → [SYNTHESIZER]
   ```

2. **Intermediate Results** - Status of each agent
   ```
   ✓ Math Calculation: Completed
   ```

3. **Final Answer** - Combined results with sources
   ```
   📋 Answer to: Calculate the average of 10, 20, 30
   ...
   ```

4. **Runtime** - How long it took
   ```
   ⏱️  Total Runtime: 0.05 seconds
   ```

## 🔍 Where Are My Logs?

Logs are saved in `infomind/logs/`:
- **Agent logs**: `infomind/logs/{AgentName}.log`
- **JSON traces**: `infomind/logs/traces/trace_{timestamp}.json`
- **Memory DB**: `infomind/logs/memory.db`

View logs:
```bash
# View recent math agent activity
tail -20 infomind/logs/MathAgent.log

# View a trace file
cat infomind/logs/traces/trace_*.json | jq
```

## 🧪 Verify Installation

Run the test suite:
```bash
python test_system.py
```

You should see:
```
Results: 7 passed, 0 failed out of 7 tests
```

## 📝 Programmatic Usage

Create a Python script:

```python
from infomind.graph import MultiAgentGraph

# Initialize the system
graph = MultiAgentGraph()

# Run a query
result = graph.run("Calculate the average of 5, 10, 15")

# Access the result
print(result["final_answer"]["output"])
```

## 🎯 What's Next?

- **Read the full README** for detailed documentation
- **Try the examples** in `examples.py`
- **Explore the agents** in `infomind/agents/`
- **Customize** by adding your own agents

## 🐛 Troubleshooting

### Issue: Import errors
**Solution**: Make sure you're in the project root directory

### Issue: Module not found
**Solution**: Run `pip install -r requirements.txt`

### Issue: Web search fails
**Solution**: This is normal if you don't have internet access. The system still works with math and other operations.

### Issue: Permission errors on logs
**Solution**: Make sure you have write permissions in the `infomind/logs` directory

## 💬 Get Help

- 📖 Read the [README](README.md)
- 🤝 See [CONTRIBUTING](CONTRIBUTING.md) for development
- 🐛 Report issues on GitHub

## 🎉 You're Ready!

Start exploring InfoMind's multi-agent capabilities!

```bash
python -m infomind.main
```

Happy querying! 🚀
