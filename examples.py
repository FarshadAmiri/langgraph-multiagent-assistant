"""Example usage of InfoMind multi-agent system"""

from infomind.graph import MultiAgentGraph


def example_math_calculation():
    """Example: Mathematical calculation"""
    print("\n" + "=" * 70)
    print("Example 1: Mathematical Calculation")
    print("=" * 70)
    
    graph = MultiAgentGraph()
    
    # Calculate average
    result = graph.run("Calculate the average of 10, 20, 30, 40, 50")
    print(result["final_answer"]["output"])
    
    print("\n")


def example_sum_calculation():
    """Example: Sum calculation"""
    print("\n" + "=" * 70)
    print("Example 2: Sum Calculation")
    print("=" * 70)
    
    graph = MultiAgentGraph()
    
    # Calculate sum
    result = graph.run("Calculate the sum of 15, 25, 35, 45, 55")
    print(result["final_answer"]["output"])
    
    print("\n")


def example_median_calculation():
    """Example: Median calculation"""
    print("\n" + "=" * 70)
    print("Example 3: Median Calculation")
    print("=" * 70)
    
    graph = MultiAgentGraph()
    
    # Calculate median
    result = graph.run("Find the median of 5, 15, 25, 35, 45")
    print(result["final_answer"]["output"])
    
    print("\n")


def example_web_search():
    """Example: Web search"""
    print("\n" + "=" * 70)
    print("Example 4: Web Search")
    print("=" * 70)
    
    graph = MultiAgentGraph()
    
    # Search for information
    result = graph.run("Find information about artificial intelligence")
    print(result["final_answer"]["output"])
    
    print("\n")


def example_comparison():
    """Example: Comparison query"""
    print("\n" + "=" * 70)
    print("Example 5: Comparison Query")
    print("=" * 70)
    
    graph = MultiAgentGraph()
    
    # Compare items
    result = graph.run("Compare Python and JavaScript programming languages")
    print(result["final_answer"]["output"])
    
    print("\n")


def main():
    """Run all examples"""
    print("\n")
    print("=" * 70)
    print("  InfoMind - Multi-Agent System Examples")
    print("=" * 70)
    
    # Run examples
    example_math_calculation()
    example_sum_calculation()
    example_median_calculation()
    
    # Note: Web search and comparison may not work without internet
    print("\nNote: The following examples require internet connectivity:")
    print("- Web Search")
    print("- Comparison (when it requires web data)")
    print("\nYou can run these interactively using: python -m infomind.main")


if __name__ == "__main__":
    main()
