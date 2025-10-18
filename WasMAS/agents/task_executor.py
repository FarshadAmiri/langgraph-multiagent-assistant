"""Task Executor - Executes planned tasks in order"""

from typing import Dict, Any, List
from .base_agent import BaseAgent
from .planner_agent import Task, TaskType, TaskStatus


class TaskExecutor(BaseAgent):
    """
    Executes tasks from the plan in the correct order
    """
    
    def __init__(self, websearch_agent, scraper_agent, math_agent, comparison_agent):
        super().__init__("TaskExecutor")
        self.websearch = websearch_agent
        self.scraper = scraper_agent
        self.math = math_agent
        self.comparison = comparison_agent
    
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all tasks in the plan"""
        plan = state.get("plan", {})
        if not plan:
            self._log_error("No plan found in state")
            return state
        
        tasks = plan["tasks"]
        execution_order = plan["execution_order"]
        
        self._log_start(f"Executing {len(execution_order)} tasks")
        
        completed_tasks = set()
        task_results = {}
        
        for task_id in execution_order:
            task = tasks[task_id]
            
            # Skip if already completed
            if task.status == TaskStatus.COMPLETED:
                completed_tasks.add(task_id)
                continue
            
            # Check if ready to execute
            if not task.is_ready(completed_tasks):
                self.logger.warning(f"Task {task_id} not ready - dependencies not met")
                continue
            
            # Execute task
            self.logger.info(f"Executing: {task.description}")
            task.status = TaskStatus.EXECUTING
            
            try:
                result = self._execute_task(task, state, task_results)
                task.result = result
                task.status = TaskStatus.COMPLETED
                completed_tasks.add(task_id)
                task_results[task_id] = result
                
                # Update state with results
                state = self._update_state_with_result(state, task, result)
                
            except Exception as e:
                self.logger.error(f"Task {task_id} failed: {e}")
                task.status = TaskStatus.FAILED
                task.result = {"error": str(e)}
        
        self._log_finish(f"Completed {len(completed_tasks)}/{len(execution_order)} tasks")
        
        state["task_results"] = task_results
        state["execution_complete"] = len(completed_tasks) == len(execution_order)
        
        return state
    
    def _execute_task(self, task: Task, state: Dict[str, Any], previous_results: Dict[str, Any]) -> Any:
        """Execute a single task based on its type"""
        
        if task.type == TaskType.SEARCH:
            return self._execute_search_task(task, state)
        
        elif task.type == TaskType.SCRAPE:
            return self._execute_scrape_task(task, state, previous_results)
        
        elif task.type == TaskType.CALCULATE:
            return self._execute_calculate_task(task, state)
        
        elif task.type == TaskType.COMPARE:
            return self._execute_compare_task(task, state, previous_results)
        
        elif task.type == TaskType.SYNTHESIZE:
            # Synthesis is handled separately
            return {"status": "pending_synthesis"}
        
        else:
            raise ValueError(f"Unknown task type: {task.type}")
    
    def _execute_search_task(self, task: Task, state: Dict[str, Any]) -> Any:
        """Execute a search task"""
        params = task.parameters
        
        # Build search query from parameters
        if "search_query" in params:
            search_query = params["search_query"]
        else:
            # Construct from components
            entity = params.get("entity", "")
            metrics = params.get("metrics", [])
            time_period = params.get("time_period")
            
            query_parts = [entity] if entity else []
            query_parts.extend(metrics)
            
            if time_period and time_period.get("type") == "range":
                query_parts.append(f"{time_period['start_year']}-{time_period['end_year']}")
            
            query_parts.extend(["data", "statistics"])
            search_query = " ".join(query_parts)
        
        # Execute search
        search_state = {
            **state,
            "query": search_query,
            "iteration": 1,
            "missing_entities": []
        }
        
        result_state = self.websearch.execute(search_state)
        
        return {
            "query": search_query,
            "entity": params.get("entity"),
            "results": result_state.get("websearch_results")
        }
    
    def _execute_scrape_task(self, task: Task, state: Dict[str, Any], previous_results: Dict[str, Any]) -> Any:
        """Execute a scrape task"""
        params = task.parameters
        
        if "urls" in params:
            # Direct URLs provided
            urls = params["urls"]
        elif params.get("from_search_results"):
            # Get URLs from search results
            urls = []
            for dep_id in task.dependencies:
                dep_result = previous_results.get(dep_id, {})
                if "results" in dep_result:
                    search_results = dep_result["results"]
                    urls.extend(search_results.get("sources", []))
        else:
            urls = []
        
        # Execute scraping
        scrape_state = {
            **state,
            "websearch_results": {"sources": urls}
        }
        
        result_state = self.scraper.execute(scrape_state)
        
        return {
            "urls": urls,
            "results": result_state.get("scraper_results")
        }
    
    def _execute_calculate_task(self, task: Task, state: Dict[str, Any]) -> Any:
        """Execute a calculation task"""
        math_state = {**state}
        result_state = self.math.execute(math_state)
        
        return {
            "results": result_state.get("math_results")
        }
    
    def _execute_compare_task(self, task: Task, state: Dict[str, Any], previous_results: Dict[str, Any]) -> Any:
        """Execute a comparison task"""
        params = task.parameters
        
        # Collect data from dependent search tasks
        entity_data = {}
        for dep_id in task.dependencies:
            dep_result = previous_results.get(dep_id, {})
            if "entity" in dep_result and "results" in dep_result:
                entity = dep_result["entity"]
                entity_data[entity] = dep_result["results"]
        
        # Aggregate websearch results for comparison
        combined_output = ""
        all_sources = []
        
        for entity, results in entity_data.items():
            if results:
                combined_output += f"\n{'='*60}\n"
                combined_output += f"{entity} Data:\n"
                combined_output += f"{'='*60}\n\n"
                combined_output += results.get("output", "")
                all_sources.extend(results.get("sources", []))
        
        # Update state with combined results
        state["websearch_results"] = {
            "output": combined_output,
            "sources": all_sources,
            "metadata": {
                "entities": list(entity_data.keys()),
                "comparison_ready": True
            }
        }
        
        # Execute comparison
        comparison_state = {**state}
        result_state = self.comparison.execute(comparison_state)
        
        return {
            "entities": params.get("entities", []),
            "entity_data": entity_data,
            "results": result_state.get("comparison_results")
        }
    
    def _update_state_with_result(self, state: Dict[str, Any], task: Task, result: Any) -> Dict[str, Any]:
        """Update state with task results"""
        
        if task.type == TaskType.SEARCH:
            # Merge search results (for multi-entity searches)
            existing = state.get("websearch_results", {})
            new_results = result.get("results", {})
            
            if existing and existing.get("output"):
                # Append to existing
                combined_output = existing["output"] + "\n\n" + new_results.get("output", "")
                combined_sources = existing.get("sources", []) + new_results.get("sources", [])
                
                state["websearch_results"] = {
                    "output": combined_output,
                    "sources": combined_sources,
                    "metadata": new_results.get("metadata", {})
                }
            else:
                state["websearch_results"] = new_results
        
        elif task.type == TaskType.SCRAPE:
            state["scraper_results"] = result.get("results", {})
        
        elif task.type == TaskType.CALCULATE:
            state["math_results"] = result.get("results", {})
        
        elif task.type == TaskType.COMPARE:
            state["comparison_results"] = result.get("results", {})
        
        return state
