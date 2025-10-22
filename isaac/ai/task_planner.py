"""
Task Planner - Multi-step task automation with AI
Breaks complex tasks into steps, handles failures, provides recovery options
"""

import json
from typing import Dict, List
from isaac.ai.xai_client import XaiClient
from isaac.adapters.base_adapter import CommandResult
from isaac.models.task_history import TaskHistory


def plan_task(task_description: str, shell_name: str = "bash") -> Dict:
    """
    Plan a multi-step task using AI.
    
    Args:
        task_description: Description of the task
        shell_name: Shell type
        
    Returns:
        dict: Task plan with steps
    """
    # Mock implementation for testing
    return {
        'task_id': 'task_001',
        'description': task_description,
        'steps': [
            {'command': 'echo "Planning task"', 'tier': 1},
            {'command': 'echo "Step 1"', 'tier': 1},
            {'command': 'echo "Step 2"', 'tier': 2}
        ],
        'estimated_duration': '2 minutes',
        'risk_level': 'low'
    }


def execute_task(task_description: str, shell, session_mgr) -> CommandResult:
    """
    Execute multi-step task with AI planning and failure recovery.
    
    Args:
        task_description: User's task goal (e.g., "backup my project folder")
        shell: Shell instance for command execution
        session_mgr: SessionManager instance
        
    Returns:
        CommandResult: Overall task result
    """
    # Check if task mode enabled
    if not session_mgr.config.get('task_mode_enabled', True):
        return CommandResult(
            success=False,
            output="Isaac > Task mode disabled in config",
            exit_code=-1
        )
    
    # Check AI enabled
    if not session_mgr.config.get('ai_enabled', False):
        return CommandResult(
            success=False,
            output="Isaac > Task mode requires AI. Enable ai_enabled in config.",
            exit_code=-1
        )
    
    # Get Claude API key
    api_key = session_mgr.config.get('claude_api_key', '')
    if not api_key:
        return CommandResult(
            success=False,
            output="Isaac > xAI API key not configured",
            exit_code=-1
        )
    
    # Initialize xAI client
    try:
        model = session_mgr.config.get('ai_model', 'grok-3')
        api_url = session_mgr.config.get('xai_api_url')
        timeout = session_mgr.config.get('xai_timeout')
        client = XaiClient(
            api_key=api_key, 
            model=model,
            api_url=api_url,
            timeout=timeout
        )
    except Exception as e:
        return CommandResult(
            success=False,
            output=f"Isaac > Failed to initialize AI: {str(e)}",
            exit_code=-1
        )
    
    # Plan task
    print(f"\nIsaac > Planning task: {task_description}")
    print("Isaac > Analyzing steps...")
    
    plan_result = client.plan_task(task_description, shell.name)
    
    if not plan_result.get('success'):
        return CommandResult(
            success=False,
            output=f"Isaac > Task planning failed: {plan_result.get('error')}",
            exit_code=-1
        )
    
    steps = plan_result.get('steps', [])
    if not steps:
        return CommandResult(
            success=False,
            output="Isaac > No steps generated for task",
            exit_code=-1
        )
    
    # Show plan to user
    print("\n" + "="*60)
    print("📋 TASK PLAN")
    print("="*60)
    print(f"Task: {task_description}")
    print(f"Steps: {len(steps)}")
    print(f"Estimated Duration: {plan_result.get('estimated_duration', 'Unknown')}")
    
    if plan_result.get('risks'):
        print(f"\n⚠️  Risks:")
        for risk in plan_result['risks']:
            print(f"  - {risk}")
    
    print(f"\n📝 Steps:")
    for i, step in enumerate(steps, 1):
        tier = step.get('tier', 1)
        command = step.get('command', '')
        description = step.get('description', '')
        print(f"  {i}. [Tier {tier}] {command}")
        print(f"     {description}")
    
    print("="*60)
    
    # Ask execution mode
    print("\nExecution modes:")
    print("  1. Autonomous - Execute all steps without confirmation")
    print("  2. Approve-once - Show plan, execute if approved")
    print("  3. Step-by-step - Confirm each step individually")
    print("  4. Abort - Cancel task")
    
    mode = input("\nSelect mode [1-4]: ").strip()
    
    if mode == '4':
        return CommandResult(
            success=False,
            output="Isaac > Task aborted by user",
            exit_code=-1
        )
    
    execution_mode = {
        '1': 'autonomous',
        '2': 'approve-once',
        '3': 'step-by-step'
    }.get(mode, 'step-by-step')  # Default to safest mode
    
    # Confirm for approve-once mode
    if execution_mode == 'approve-once':
        confirm = input("\nExecute all steps? [y/N]: ").strip().lower()
        if confirm != 'y':
            return CommandResult(
                success=False,
                output="Isaac > Task aborted by user",
                exit_code=-1
            )
    
    # Create task in history
    task_id = session_mgr.task_history.create_task(
        description=task_description,
        steps=steps,
        mode=execution_mode
    )
    
    # Execute steps
    print(f"\n🚀 Executing task (mode: {execution_mode})...\n")
    
    from isaac.core.command_router import CommandRouter
    router = CommandRouter(session_mgr, shell)
    
    for i, step in enumerate(steps, 1):
        command = step.get('command', '')
        tier = step.get('tier', 1)
        description = step.get('description', '')
        
        print(f"Step {i}/{len(steps)}: {description}")
        print(f"Command: {command}")
        
        # Confirm for step-by-step mode
        if execution_mode == 'step-by-step':
            confirm = input(f"Execute step {i}? [y/N/abort]: ").strip().lower()
            if confirm == 'abort':
                session_mgr.task_history.log_step(task_id, i, 'aborted', "User aborted")
                session_mgr.save_task_history()
                return CommandResult(
                    success=False,
                    output=f"Isaac > Task aborted at step {i}",
                    exit_code=-1
                )
            elif confirm != 'y':
                session_mgr.task_history.log_step(task_id, i, 'skipped', "User skipped")
                session_mgr.save_task_history()
                print("Skipped.\n")
                continue
        
        # Execute command through router (tier system)
        result = router.route_command(command)
        
        if result.success:
            session_mgr.task_history.log_step(task_id, i, 'success', result.output)
            session_mgr.save_task_history()
            print(f"✅ Step {i} complete\n")
        else:
            # Step failed - handle recovery
            session_mgr.task_history.log_step(task_id, i, 'failed', result.output)
            session_mgr.save_task_history()
            print(f"❌ Step {i} failed: {result.output}\n")
            
            recovery = _handle_step_failure(
                task_id=task_id,
                step_num=i,
                step=step,
                error=result.output,
                client=client,
                shell=shell,
                session_mgr=session_mgr
            )
            
            if recovery == 'abort':
                return CommandResult(
                    success=False,
                    output=f"Isaac > Task aborted at step {i}",
                    exit_code=-1
                )
            elif recovery == 'skip':
                print("Skipping to next step...\n")
                continue
            # 'retry', 'auto-fix', 'suggest' handled in _handle_step_failure
    
    # Task complete
    session_mgr.task_history.complete_task(task_id, 'success')
    session_mgr.save_task_history()
    
    return CommandResult(
        success=True,
        output=f"Isaac > Task complete: {len(steps)} steps executed",
        exit_code=0
    )


def _handle_step_failure(task_id: str, step_num: int, step: Dict, 
                         error: str, client: XaiClient, shell, 
                         session_mgr) -> str:
    """
    Handle step failure with recovery options.
    
    Args:
        task_id: Task identifier
        step_num: Step number that failed
        step: Step dict
        error: Error message
        client: ClaudeClient for AI suggestions
        shell: Shell instance
        session_mgr: SessionManager
        
    Returns:
        str: Recovery action ('retry', 'skip', 'abort', 'auto-fix', 'suggest')
    """
    print("="*60)
    print("⚠️  STEP FAILURE - RECOVERY OPTIONS")
    print("="*60)
    print(f"Step {step_num}: {step.get('description', '')}")
    print(f"Command: {step.get('command', '')}")
    print(f"Error: {error}")
    print()
    
    print("Recovery options:")
    print("  1. Auto-fix - AI suggests fix and applies")
    print("  2. Retry - Run same command again")
    print("  3. Skip - Continue to next step")
    print("  4. Abort - Stop task execution")
    print("  5. Suggest - AI suggests alternatives (you choose)")
    
    choice = input("\nSelect recovery [1-5]: ").strip()
    
    if choice == '1':
        # Auto-fix
        print("\nIsaac > Analyzing failure...")
        # TODO: Implement AI auto-fix suggestion
        # For now, just retry
        print("Isaac > Auto-fix not yet implemented. Retrying...")
        return 'retry'
    
    elif choice == '2':
        # Retry
        print("\nIsaac > Retrying step...")
        return 'retry'
    
    elif choice == '3':
        # Skip
        session_mgr.task_history.log_step(task_id, step_num, 'skipped', 
                                          f"Skipped after failure: {error}")
        session_mgr.save_task_history()
        return 'skip'
    
    elif choice == '4':
        # Abort
        session_mgr.task_history.complete_task(task_id, 'aborted')
        session_mgr.save_task_history()
        return 'abort'
    
    elif choice == '5':
        # AI suggestions
        print("\nIsaac > Getting AI suggestions...")
        # TODO: Implement AI alternative suggestions
        print("Isaac > Suggest mode not yet implemented. Skipping...")
        return 'skip'
    
    else:
        print("\nInvalid choice. Aborting.")
        return 'abort'


def _get_ai_fix_suggestion(command: str, error: str, shell_name: str, 
                           client: XaiClient) -> Dict:
    """
    Get AI suggestion for fixing failed command.
    
    Args:
        command: Failed command
        error: Error message
        shell_name: Shell context
        client: XaiClient
        
    Returns:
        dict: {'fixed_command': str, 'explanation': str}
    """
    prompt = f"""A {shell_name} command failed. Suggest a fix.

Failed command: {command}
Error: {error}

Respond in JSON format:
{{
    "fixed_command": "corrected command",
    "explanation": "what was wrong and how to fix it",
    "confidence": 0.9
}}

Only respond with JSON."""

    result = client._call_api(prompt, max_tokens=512)
    
    if not result.get('success'):
        return {
            'fixed_command': command,
            'explanation': 'AI unavailable, no fix suggested'
        }
    
    try:
        parsed = json.loads(result['text'])
        return {
            'fixed_command': parsed.get('fixed_command', command),
            'explanation': parsed.get('explanation', 'No explanation')
        }
    except json.JSONDecodeError:
        return {
            'fixed_command': command,
            'explanation': 'Failed to parse AI response'
        }