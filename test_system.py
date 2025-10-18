"""Simple tests for WasMAS system"""

import sys
from WasMAS.graph import MultiAgentGraph
from WasMAS.memory import MemoryStore


def test_math_average():
    """Test math agent - average calculation"""
    print("Testing: Math Agent - Average Calculation...", end=" ")
    graph = MultiAgentGraph()
    result = graph.run("Calculate the average of 10, 20, 30")
    
    assert "final_answer" in result, "No final answer in result"
    output = result["final_answer"]["output"]
    assert "20.00" in output or "20.0" in output, "Incorrect average calculation"
    print("✓ PASSED")
    return True


def test_math_sum():
    """Test math agent - sum calculation"""
    print("Testing: Math Agent - Sum Calculation...", end=" ")
    graph = MultiAgentGraph()
    result = graph.run("Calculate the sum of 5, 10, 15")
    
    assert "final_answer" in result, "No final answer in result"
    output = result["final_answer"]["output"]
    assert "30" in output, "Incorrect sum calculation"
    print("✓ PASSED")
    return True


def test_math_median():
    """Test math agent - median calculation"""
    print("Testing: Math Agent - Median Calculation...", end=" ")
    graph = MultiAgentGraph()
    result = graph.run("Find the median of 1, 2, 3, 4, 5")
    
    assert "final_answer" in result, "No final answer in result"
    output = result["final_answer"]["output"]
    assert "3" in output, "Incorrect median calculation"
    print("✓ PASSED")
    return True


def test_controller_routing():
    """Test controller agent routing"""
    print("Testing: Controller Agent Routing...", end=" ")
    graph = MultiAgentGraph()
    result = graph.run("Calculate the average of 1, 2, 3")
    
    assert "agents_to_call" in result, "No agents_to_call in result"
    agents = result["agents_to_call"]
    assert "math" in agents, "Math agent not called for calculation query"
    print("✓ PASSED")
    return True


def test_memory_storage():
    """Test memory storage"""
    print("Testing: Memory Storage...", end=" ")
    memory = MemoryStore()
    
    interaction_id = memory.store_interaction(
        query="test query",
        agent="TestAgent",
        output="test output",
        sources=["test_source"],
        metadata={"test": True}
    )
    
    assert interaction_id > 0, "Failed to store interaction"
    
    recent = memory.get_recent_interactions(limit=1)
    assert len(recent) > 0, "Failed to retrieve recent interactions"
    assert recent[0]["query"] == "test query", "Incorrect query retrieved"
    print("✓ PASSED")
    return True


def test_synthesizer():
    """Test answer synthesizer"""
    print("Testing: Answer Synthesizer...", end=" ")
    graph = MultiAgentGraph()
    result = graph.run("What is 5 + 5")
    
    assert "final_answer" in result, "No final answer in result"
    final_answer = result["final_answer"]
    assert "output" in final_answer, "No output in final answer"
    assert "timestamp" in final_answer, "No timestamp in final answer"
    assert "agent" in final_answer, "No agent in final answer"
    assert final_answer["agent"] == "AnswerSynthesizer", "Wrong agent"
    print("✓ PASSED")
    return True


def test_logging():
    """Test logging infrastructure"""
    print("Testing: Logging Infrastructure...", end=" ")
    from pathlib import Path
    
    graph = MultiAgentGraph()
    result = graph.run("test logging")
    
    # Check if log directory exists
    log_dir = Path("WasMAS/logs")
    assert log_dir.exists(), "Log directory not created"
    
    # Check if at least one log file exists
    log_files = list(log_dir.glob("*.log"))
    assert len(log_files) > 0, "No log files created"
    print("✓ PASSED")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  WasMAS System Tests")
    print("=" * 70 + "\n")
    
    tests = [
        test_controller_routing,
        test_math_average,
        test_math_sum,
        test_math_median,
        test_synthesizer,
        test_memory_storage,
        test_logging,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ FAILED - {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
