"""Math Agent - Handles calculations and statistical operations"""

import re
import ast
import operator
from typing import Dict, Any
from .base_agent import BaseAgent


class MathAgent(BaseAgent):
    """
    Handles arithmetic, logical, and statistical calculations
    Uses a safe evaluation approach
    """
    
    def __init__(self):
        super().__init__("MathAgent")
        # Safe operators for evaluation
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform mathematical calculations"""
        query = state.get("query", "")
        self._log_start(query)
        
        try:
            # Extract and evaluate mathematical expressions
            result = self._process_math_query(query, state)
            
            output = self._create_output(
                output=result,
                sources=["internal_calculation"],
                metadata={"query": query}
            )
            
            self._log_finish(result)
            state["math_results"] = output
            return state
            
        except Exception as e:
            self._log_error(str(e))
            state["math_results"] = self._create_output(
                output=f"Error during calculation: {str(e)}",
                sources=[]
            )
            return state
    
    def _process_math_query(self, query: str, state: Dict[str, Any]) -> str:
        """Process mathematical query"""
        query_lower = query.lower()
        
        # Extract numbers from query or previous results
        numbers = self._extract_numbers(query, state)
        
        # Determine operation
        if "average" in query_lower or "mean" in query_lower:
            if numbers:
                result = sum(numbers) / len(numbers)
                return f"Average: {result:.2f} (calculated from {len(numbers)} values: {numbers})"
            return "No numbers found to calculate average"
        
        elif "sum" in query_lower or "total" in query_lower:
            if numbers:
                result = sum(numbers)
                return f"Sum: {result:.2f} (from values: {numbers})"
            return "No numbers found to calculate sum"
        
        elif "median" in query_lower:
            if numbers:
                sorted_nums = sorted(numbers)
                n = len(sorted_nums)
                median = sorted_nums[n//2] if n % 2 == 1 else (sorted_nums[n//2-1] + sorted_nums[n//2]) / 2
                return f"Median: {median:.2f} (from values: {sorted_nums})"
            return "No numbers found to calculate median"
        
        else:
            # Try to evaluate expression
            expressions = self._extract_expressions(query)
            if expressions:
                results = []
                for expr in expressions:
                    try:
                        result = self._safe_eval(expr)
                        results.append(f"{expr} = {result}")
                    except:
                        pass
                
                if results:
                    return "Calculation results:\n" + "\n".join(results)
            
            if numbers:
                return f"Found numbers: {numbers}. Please specify the operation (average, sum, median, etc.)"
            
            return "No mathematical operations or numbers detected in the query."
    
    def _extract_numbers(self, query: str, state: Dict[str, Any]) -> list:
        """Extract numbers from query and state"""
        numbers = []
        
        # Extract from query
        number_pattern = r'-?\d+\.?\d*'
        found = re.findall(number_pattern, query)
        numbers.extend([float(n) for n in found if n])
        
        # Could extract from previous results if needed
        # For now, just return numbers from query
        
        return numbers
    
    def _extract_expressions(self, query: str) -> list:
        """Extract mathematical expressions from query"""
        # Look for expressions with operators
        expr_pattern = r'(\d+\.?\d*\s*[\+\-\*\/\^]\s*\d+\.?\d*(?:\s*[\+\-\*\/\^]\s*\d+\.?\d*)*)'
        expressions = re.findall(expr_pattern, query)
        return expressions
    
    def _safe_eval(self, expr: str) -> float:
        """Safely evaluate mathematical expression"""
        # Replace ^ with **
        expr = expr.replace('^', '**')
        
        try:
            # Parse expression
            node = ast.parse(expr, mode='eval')
            return self._eval_node(node.body)
        except Exception as e:
            raise ValueError(f"Cannot evaluate expression: {expr}")
    
    def _eval_node(self, node):
        """Recursively evaluate AST node"""
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            op = self.operators.get(type(node.op))
            if op:
                return op(self._eval_node(node.left), self._eval_node(node.right))
        elif isinstance(node, ast.UnaryOp):
            op = self.operators.get(type(node.op))
            if op:
                return op(self._eval_node(node.operand))
        
        raise ValueError(f"Unsupported operation")
