"""
Task Runner - Execute multi-step tasks with failure recovery
Handles task execution, progress tracking, and failure recovery options
"""

from typing import Dict


def execute_task(task_plan: Dict, mode: str = "autonomous", approved: bool = False, shell_adapter = None, session_mgr = None) -> Dict:
    """
    Execute a planned multi-step task.
    
    Args:
        task_plan: Task plan from plan_task()
        mode: Execution mode ('autonomous', 'approve-once', 'step-by-step')
        approved: Whether user approved (for approve-once mode)
        shell_adapter: Shell adapter for execution
        session_mgr: Session manager
        
    Returns:
        dict: Task execution result
    """
    # Mock implementation for testing
    if mode == 'approve-once' and approved:
        return {
            'success': True,
            'steps_executed': len(task_plan.get('steps', [])),
            'approved': True
        }
    elif mode == 'autonomous':
        return {
            'success': True,
            'steps_executed': len(task_plan.get('steps', [])),
            'mode': 'autonomous'
        }
    else:
        return {
            'success': False,
            'error': 'Mode not supported in mock'
        }