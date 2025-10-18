"""Hierarchical Task Network Planner - Decomposes queries into executable sub-tasks"""

from typing import Dict, Any, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import re
from .base_agent import BaseAgent


class TaskType(Enum):
    """Types of tasks the system can execute"""
    SEARCH = "search"
    SCRAPE = "scrape"
    CALCULATE = "calculate"
    COMPARE = "compare"
    AGGREGATE = "aggregate"
    SYNTHESIZE = "synthesize"


class TaskStatus(Enum):
    """Execution status of a task"""
    PENDING = "pending"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Represents a single executable task"""
    id: str
    type: TaskType
    description: str
    parameters: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)  # IDs of tasks this depends on
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    priority: int = 0  # Higher = execute first
    
    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """Check if all dependencies are satisfied"""
        return all(dep_id in completed_tasks for dep_id in self.dependencies)


class PlannerAgent(BaseAgent):
    """
    Hierarchical planner that decomposes complex queries into ordered sub-tasks
    """
    
    def __init__(self):
        super().__init__("PlannerAgent")
        self.task_counter = 0
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create execution plan by decomposing query into sub-tasks"""
        query = state.get("query", "")
        self._log_start(f"Decomposing query into sub-tasks")
        
        try:
            # Step 1: Analyze query and extract information needs
            info_needs = self._analyze_information_needs(query)
            
            # Step 2: Decompose into tasks
            tasks = self._decompose_into_tasks(query, info_needs)
            
            # Step 3: Identify dependencies
            tasks = self._identify_dependencies(tasks, info_needs)
            
            # Step 4: Create execution order (topological sort)
            execution_order = self._create_execution_order(tasks)
            
            # Step 5: Package plan
            plan = {
                "tasks": {task.id: task for task in tasks},
                "execution_order": execution_order,
                "info_needs": info_needs,
                "total_tasks": len(tasks)
            }
            
            self._log_finish(f"Created plan with {len(tasks)} tasks")
            self._print_plan(plan)
            
            return {
                **state,
                "plan": plan,
                "planning_complete": True
            }
            
        except Exception as e:
            self._log_error(str(e))
            return {
                **state,
                "planning_complete": False,
                "error": str(e)
            }
    
    def _analyze_information_needs(self, query: str) -> Dict[str, Any]:
        """Analyze what information is needed to answer the query"""
        query_lower = query.lower()
        
        needs = {
            "entities": [],
            "metrics": [],
            "time_period": None,
            "operation": None,
            "requires_comparison": False,
            "requires_calculation": False,
            "requires_scraping": False,
            "extracted_urls": []
        }
        
        # Extract entities (countries, products, companies, etc.)
        needs["entities"] = self._extract_entities(query)
        
        # Extract metrics (GDP, price, rate, etc.)
        needs["metrics"] = self._extract_metrics(query)
        
        # Extract time period
        needs["time_period"] = self._extract_time_period(query)
        
        # Determine operation type
        if any(word in query_lower for word in ["compare", "versus", "vs", "difference", "contrast"]):
            needs["operation"] = "comparison"
            needs["requires_comparison"] = True
        elif any(word in query_lower for word in ["calculate", "sum", "average", "total", "mean"]):
            needs["operation"] = "calculation"
            needs["requires_calculation"] = True
        elif any(word in query_lower for word in ["search", "find", "what is", "who is", "latest"]):
            needs["operation"] = "search"
        else:
            needs["operation"] = "search"  # Default
        
        # Check for URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, query)
        if urls:
            needs["extracted_urls"] = urls
            needs["requires_scraping"] = True
        
        # Check for explicit scraping request
        if any(word in query_lower for word in ["scrape", "extract from", "content of"]):
            needs["requires_scraping"] = True
        
        return needs
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities (countries, products, companies) from query"""
        entities = []
        
        # Pattern matching for comparison queries
        patterns = [
            r"compare\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)'s.*?(?:with|and|to|versus|vs)\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)'s",
            r"([A-Z][A-Z]+|[A-Z][A-Za-z]+)(?:'s)?\s+(?:vs|versus)\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+)(?:'s)?",
            r"between\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+)(?:'s)?\s+and\s+([A-Z][A-Z]+|[A-Z][A-Za-z]+)(?:'s)?",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                entity1 = self._clean_entity(match.group(1))
                entity2 = self._clean_entity(match.group(2))
                if entity1:
                    entities.append(entity1)
                if entity2:
                    entities.append(entity2)
                break
        
        # If no pattern match, extract capitalized words (fallback)
        if not entities:
            skip_words = {'GDP', 'Price', 'Cost', 'Compare', 'Versus', 'With', 'And', 'The', 'Calculate'}
            words = query.split()
            for word in words:
                clean = word.strip("'s,.")
                if clean and clean[0].isupper() and len(clean) > 2 and clean not in skip_words:
                    entities.append(clean)
        
        return list(set(entities))  # Remove duplicates
    
    def _clean_entity(self, entity: str) -> str:
        """Clean entity name"""
        remove_words = ["the", "a", "an", "of", "in", "last", "years", "year"]
        words = entity.strip().split()
        words = [w for w in words if w.lower() not in remove_words]
        return " ".join(words).strip()
    
    def _extract_metrics(self, query: str) -> List[str]:
        """Extract metrics being queried (generic extraction)"""
        query_lower = query.lower()
        metrics = []
        
        # Economic metrics
        if "gdp" in query_lower:
            metrics.append("GDP")
        if "growth" in query_lower:
            metrics.append("growth")
        if "inflation" in query_lower:
            metrics.append("inflation")
        if "unemployment" in query_lower:
            metrics.append("unemployment")
        
        # Financial metrics
        if any(word in query_lower for word in ["price", "cost", "msrp"]):
            metrics.append("price")
        if "revenue" in query_lower:
            metrics.append("revenue")
        if "profit" in query_lower:
            metrics.append("profit")
        
        # If no specific metric, extract from context
        if not metrics:
            # Look for pattern "X's Y" where Y might be a metric
            pattern = r"'s\s+([a-z]+(?:\s+[a-z]+)?)"
            matches = re.findall(pattern, query_lower)
            metrics.extend(matches[:2])  # Take first 2
        
        return list(set(metrics))
    
    def _extract_time_period(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract time period from query"""
        query_lower = query.lower()
        
        # Pattern: "last N years"
        match = re.search(r'last\s+(\d+)\s+years?', query_lower)
        if match:
            from datetime import datetime
            num_years = int(match.group(1))
            current_year = datetime.now().year
            return {
                "type": "range",
                "start_year": current_year - num_years,
                "end_year": current_year,
                "description": f"last {num_years} years"
            }
        
        # Pattern: specific year
        match = re.search(r'\b(20\d{2})\b', query)
        if match:
            year = int(match.group(1))
            return {
                "type": "specific",
                "year": year,
                "description": str(year)
            }
        
        # Pattern: "current", "latest", "recent"
        if any(word in query_lower for word in ["current", "latest", "recent", "now"]):
            from datetime import datetime
            return {
                "type": "current",
                "year": datetime.now().year,
                "description": "current"
            }
        
        return None
    
    def _decompose_into_tasks(self, query: str, info_needs: Dict[str, Any]) -> List[Task]:
        """Decompose query into executable tasks"""
        tasks = []
        
        # Task decomposition based on operation type and entities
        operation = info_needs["operation"]
        entities = info_needs["entities"]
        metrics = info_needs["metrics"]
        time_period = info_needs["time_period"]
        
        if operation == "comparison" and len(entities) >= 2:
            # COMPARISON WORKFLOW:
            # 1. Search for each entity separately
            # 2. Compare the results
            # 3. Synthesize answer
            
            for entity in entities:
                search_query = self._build_search_query(entity, metrics, time_period)
                task = Task(
                    id=self._next_task_id(),
                    type=TaskType.SEARCH,
                    description=f"Search for {entity} {' '.join(metrics)} data",
                    parameters={
                        "entity": entity,
                        "metrics": metrics,
                        "time_period": time_period,
                        "search_query": search_query
                    },
                    priority=10  # High priority - needed first
                )
                tasks.append(task)
            
            # Comparison task depends on all search tasks
            search_task_ids = [t.id for t in tasks]
            comparison_task = Task(
                id=self._next_task_id(),
                type=TaskType.COMPARE,
                description=f"Compare {' vs '.join(entities)}",
                parameters={
                    "entities": entities,
                    "metrics": metrics,
                    "comparison_type": "entity"
                },
                dependencies=search_task_ids,
                priority=5
            )
            tasks.append(comparison_task)
        
        elif operation == "calculation":
            # CALCULATION WORKFLOW:
            # 1. Extract numbers/data (might need search first)
            # 2. Perform calculation
            # 3. Synthesize answer
            
            # Check if we need to search for data first
            if entities or metrics:
                search_task = Task(
                    id=self._next_task_id(),
                    type=TaskType.SEARCH,
                    description=f"Search for data needed for calculation",
                    parameters={
                        "entities": entities,
                        "metrics": metrics,
                        "search_query": query
                    },
                    priority=10
                )
                tasks.append(search_task)
                
                calc_task = Task(
                    id=self._next_task_id(),
                    type=TaskType.CALCULATE,
                    description="Perform calculation",
                    parameters={"operation": "calculate"},
                    dependencies=[search_task.id],
                    priority=5
                )
                tasks.append(calc_task)
            else:
                # Direct calculation (e.g., "Calculate 5 + 10")
                calc_task = Task(
                    id=self._next_task_id(),
                    type=TaskType.CALCULATE,
                    description="Perform calculation",
                    parameters={"operation": "calculate"},
                    priority=10
                )
                tasks.append(calc_task)
        
        elif operation == "search":
            # SEARCH WORKFLOW:
            # 1. Search for information
            # 2. Optionally scrape if URLs provided/found
            # 3. Synthesize answer
            
            if info_needs["requires_scraping"] and info_needs["extracted_urls"]:
                # User provided URLs - scrape them
                scrape_task = Task(
                    id=self._next_task_id(),
                    type=TaskType.SCRAPE,
                    description="Scrape provided URLs",
                    parameters={"urls": info_needs["extracted_urls"]},
                    priority=10
                )
                tasks.append(scrape_task)
            else:
                # Regular search
                search_task = Task(
                    id=self._next_task_id(),
                    type=TaskType.SEARCH,
                    description="Search for information",
                    parameters={
                        "entities": entities,
                        "metrics": metrics,
                        "time_period": time_period,
                        "search_query": query
                    },
                    priority=10
                )
                tasks.append(search_task)
                
                # If scraping requested, scrape search results
                if info_needs["requires_scraping"]:
                    scrape_task = Task(
                        id=self._next_task_id(),
                        type=TaskType.SCRAPE,
                        description="Scrape search result URLs",
                        parameters={"from_search_results": True},
                        dependencies=[search_task.id],
                        priority=5
                    )
                    tasks.append(scrape_task)
        
        # Always add synthesis task at the end
        synthesis_task = Task(
            id=self._next_task_id(),
            type=TaskType.SYNTHESIZE,
            description="Synthesize final answer",
            parameters={"operation": operation},
            dependencies=[t.id for t in tasks if t.type != TaskType.SYNTHESIZE],
            priority=1  # Lowest priority - runs last
        )
        tasks.append(synthesis_task)
        
        return tasks
    
    def _build_search_query(self, entity: str, metrics: List[str], time_period: Optional[Dict]) -> str:
        """Build optimized search query for an entity"""
        parts = [entity]
        
        if metrics:
            parts.extend(metrics)
        
        if time_period:
            if time_period["type"] == "range":
                parts.append(f"{time_period['start_year']}-{time_period['end_year']}")
            elif time_period["type"] == "specific":
                parts.append(str(time_period["year"]))
            elif time_period["type"] == "current":
                parts.append(str(time_period["year"]))
        
        parts.extend(["data", "statistics"])
        
        return " ".join(parts)
    
    def _identify_dependencies(self, tasks: List[Task], info_needs: Dict[str, Any]) -> List[Task]:
        """Identify and set dependencies between tasks (already done in decompose, but can refine here)"""
        # Dependencies are already set during decomposition
        # This method can add additional logic-based dependencies
        return tasks
    
    def _create_execution_order(self, tasks: List[Task]) -> List[str]:
        """Create execution order using topological sort"""
        # Build adjacency list
        task_map = {task.id: task for task in tasks}
        in_degree = {task.id: len(task.dependencies) for task in tasks}
        
        # Find tasks with no dependencies (ready to execute)
        ready_queue = [task.id for task in tasks if len(task.dependencies) == 0]
        ready_queue.sort(key=lambda tid: task_map[tid].priority, reverse=True)
        
        execution_order = []
        
        while ready_queue:
            # Pick highest priority task
            current_id = ready_queue.pop(0)
            execution_order.append(current_id)
            
            # Update dependencies
            for task in tasks:
                if current_id in task.dependencies:
                    in_degree[task.id] -= 1
                    if in_degree[task.id] == 0:
                        ready_queue.append(task.id)
                        ready_queue.sort(key=lambda tid: task_map[tid].priority, reverse=True)
        
        # Check for cycles
        if len(execution_order) != len(tasks):
            self.logger.error("Circular dependency detected in task graph!")
            # Return best effort order
            return [t.id for t in sorted(tasks, key=lambda t: t.priority, reverse=True)]
        
        return execution_order
    
    def _next_task_id(self) -> str:
        """Generate next task ID"""
        self.task_counter += 1
        return f"task_{self.task_counter}"
    
    def _print_plan(self, plan: Dict[str, Any]):
        """Print execution plan for debugging"""
        print("\n" + "="*70)
        print("📋 EXECUTION PLAN")
        print("="*70)
        
        tasks = plan["tasks"]
        execution_order = plan["execution_order"]
        
        print(f"\n📊 Information Needs:")
        info_needs = plan["info_needs"]
        print(f"   Entities: {info_needs['entities']}")
        print(f"   Metrics: {info_needs['metrics']}")
        print(f"   Operation: {info_needs['operation']}")
        if info_needs['time_period']:
            print(f"   Time Period: {info_needs['time_period']['description']}")
        
        print(f"\n🔄 Execution Order ({len(execution_order)} tasks):\n")
        
        for i, task_id in enumerate(execution_order, 1):
            task = tasks[task_id]
            deps = f" (depends on: {', '.join(task.dependencies)})" if task.dependencies else ""
            print(f"   {i}. [{task.type.value.upper()}] {task.description}{deps}")
        
        print("\n" + "="*70 + "\n")
