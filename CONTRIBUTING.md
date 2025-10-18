# Contributing to WasMAS

Thank you for your interest in contributing to WasMAS! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/langgraph-multiagent-assistant.git
   cd langgraph-multiagent-assistant
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🏗️ Project Structure

```
WasMAS/
├── agents/          # Agent implementations
├── utils/           # Utility modules (logging, etc.)
├── graph.py         # LangGraph orchestration
├── main.py          # CLI interface
├── streamlit_app.py # Streamlit UI
└── memory.py        # Memory system
```

## 🧪 Testing

Run the test suite before submitting changes:

```bash
python test_system.py
```

### Adding Tests

When adding new features, please include tests in `test_system.py`:

```python
def test_your_feature():
    """Test description"""
    print("Testing: Your Feature...", end=" ")
    # Your test code here
    print("✓ PASSED")
    return True
```

## 📝 Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to all classes and functions
- Keep functions focused and small
- Add comments for complex logic

### Example:

```python
def example_function(param: str) -> dict:
    """
    Brief description of what this function does
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
    """
    # Implementation
    pass
```

## 🤖 Adding New Agents

To add a new agent:

1. Create a new file in `WasMAS/agents/`:

```python
from .base_agent import BaseAgent
from typing import Dict, Any

class YourAgent(BaseAgent):
    """Description of your agent"""
    
    def __init__(self):
        super().__init__("YourAgent")
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's task"""
        query = state.get("query", "")
        self._log_start(query)
        
        try:
            # Your logic here
            result = "your result"
            
            output = self._create_output(
                output=result,
                sources=["your_source"],
                metadata={}
            )
            
            self._log_finish(result)
            state["your_agent_results"] = output
            return state
            
        except Exception as e:
            self._log_error(str(e))
            state["your_agent_results"] = self._create_output(
                output=f"Error: {str(e)}",
                sources=[]
            )
            return state
```

2. Update `graph.py` to include your agent:

```python
from .agents.your_agent import YourAgent

class MultiAgentGraph:
    def __init__(self):
        # ... existing agents
        self.your_agent = YourAgent()
    
    def _execute_agents_node(self, state):
        agent_map = {
            # ... existing agents
            "youragent": self.your_agent
        }
        # ... rest of the code
```

3. Update `controller_agent.py` to route to your agent:

```python
def _analyze_query(self, query: str) -> List[str]:
    # Add detection logic
    if "your_keyword" in query_lower:
        agents.append("youragent")
```

4. Add tests for your agent in `test_system.py`

## 📚 Documentation

- Update README.md if adding user-facing features
- Add docstrings to all new functions and classes
- Include examples in docstrings where helpful
- Update this CONTRIBUTING.md if changing contribution process

## 🐛 Reporting Bugs

When reporting bugs, please include:

1. Description of the bug
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. System information (OS, Python version)
6. Relevant logs from `WasMAS/logs/`

## 💡 Feature Requests

We welcome feature requests! Please:

1. Check if the feature already exists
2. Describe the feature and its use case
3. Explain why it would be useful
4. Provide examples if applicable

## 🔄 Pull Request Process

1. Ensure all tests pass
2. Update documentation as needed
3. Follow the code style guidelines
4. Write clear commit messages
5. Reference any related issues

### Commit Message Format

```
type: brief description

Detailed description if needed

Fixes #issue_number
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests for new features

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No unnecessary dependencies added
```

## 📧 Questions?

If you have questions, please:

1. Check existing issues
2. Review the README.md
3. Open a new issue with your question

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## 🙏 Thank You!

Your contributions help make WasMAS better for everyone!
