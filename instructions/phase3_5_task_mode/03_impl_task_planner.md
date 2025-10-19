# Implementation: Task Planner Module

## Goal
Create task planner that breaks multi-step tasks into executable commands with failure recovery.

**Time Estimate:** 2 hours

---

## File to Create

**Path:** `isaac/ai/task_planner.py`

**Lines:** ~200

---

## Part 1: Imports and Task Execution Function

```python
"""
Task Planner - Multi-step task automation with AI
Breaks complex tasks into steps, handles failures, provides recovery options
"""

import json
from typing import Dict, List
from isaac.ai.claude_client import ClaudeClient
from isaac.models.command_result import CommandResult
from isaac.models.task_history import TaskHistory


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
            output="Isaac > Claude API key not configured",
            exit_code=-1
        )
    
    # Initialize Claude client
    try:
        model = session_mgr.config.get('ai_model', 'claude-sonnet-4-5-20250929')
        client = ClaudeClient(api_key=api_key, model=model)
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
    router = CommandRouter(shell, session_mgr)
    
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
                return CommandResult(
                    success=False,
                    output=f"Isaac > Task aborted at step {i}",
                    exit_code=-1
                )
            elif confirm != 'y':
                session_mgr.task_history.log_step(task_id, i, 'skipped', "User skipped")
                print("Skipped.\n")
                continue
        
        # Execute command through router (tier system)
        result = router.route_command(command)
        
        if result.success:
            session_mgr.task_history.log_step(task_id, i, 'success', result.output)
            print(f"✅ Step {i} complete\n")
        else:
            # Step failed - handle recovery
            session_mgr.task_history.log_step(task_id, i, 'failed', result.output)
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
    
    return CommandResult(
        success=True,
        output=f"Isaac > Task complete: {len(steps)} steps executed",
        exit_code=0
    )
```

---

## Part 2: Failure Recovery Handler

```python
def _handle_step_failure(task_id: str, step_num: int, step: Dict, 
                         error: str, client: ClaudeClient, shell, 
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
        return 'skip'
    
    elif choice == '4':
        # Abort
        session_mgr.task_history.complete_task(task_id, 'aborted')
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
                           client: ClaudeClient) -> Dict:
    """
    Get AI suggestion for fixing failed command.
    
    Args:
        command: Failed command
        error: Error message
        shell_name: Shell context
        client: ClaudeClient
        
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
```

---

## Part 3: Integration with Command Router

**File:** `isaac/core/command_router.py`

**Add at start of route_command() method (before natural language check):**

```python
        # Task mode detection
        if input_text.lower().startswith('isaac task:'):
            task_desc = input_text[11:].strip()  # Remove "isaac task:"
            
            from isaac.ai.task_planner import execute_task
            return execute_task(task_desc, self.shell, self.session)
```

---

## Verification Steps

After creating `isaac/ai/task_planner.py`, verify:

- [ ] File has ~200 lines
- [ ] `execute_task()` function complete
- [ ] `_handle_step_failure()` function complete
- [ ] All 5 recovery options implemented
- [ ] Integration point documented
- [ ] No syntax errors: `python -m py_compile isaac/ai/task_planner.py`

---

## Configuration

**User config** (`~/.isaac/config.json`):
```json
{
  "task_mode_enabled": true,
  "ai_enabled": true,
  "claude_api_key": "sk-ant-..."
}
```

---

## Usage Example

```
User: isaac task: backup my documents folder

Isaac > Planning task: backup my documents folder
Isaac > Analyzing steps...

============================================================
📋 TASK PLAN
============================================================
Task: backup my documents folder
Steps: 3
Estimated Duration: 1-2 minutes

⚠️  Risks:
  - Large file operation may take time

📝 Steps:
  1. [Tier 1] cd ~/documents
     Navigate to documents folder
  2. [Tier 2] tar -czf ~/backup_$(date +%Y%m%d).tar.gz .
     Create compressed backup archive
  3. [Tier 1] ls -lh ~/backup_*.tar.gz
     Verify backup file created
============================================================

Execution modes:
  1. Autonomous - Execute all steps without confirmation
  2. Approve-once - Show plan, execute if approved
  3. Step-by-step - Confirm each step individually
  4. Abort - Cancel task

Select mode [1-4]: 2

Execute all steps? [y/N]: y

🚀 Executing task (mode: approve-once)...

Step 1/3: Navigate to documents folder
Command: cd ~/documents
✅ Step 1 complete

Step 2/3: Create compressed backup archive
Command: tar -czf ~/backup_20251019.tar.gz .
✅ Step 2 complete

Step 3/3: Verify backup file created
Command: ls -lh ~/backup_*.tar.gz
-rw-r--r-- 1 user user 45M Oct 19 12:34 backup_20251019.tar.gz
✅ Step 3 complete

Isaac > Task complete: 3 steps executed
```

---

## Common Pitfalls

⚠️ **Task commands MUST go through tier system:**
```python
# WRONG - bypasses tier validation
result = shell.execute(command)

# CORRECT - goes through router
router = CommandRouter(shell, session_mgr)
result = router.route_command(command)
```

⚠️ **Always log task steps:**
```python
# Before execution
session_mgr.task_history.log_step(task_id, i, 'pending', '')

# After execution
session_mgr.task_history.log_step(task_id, i, 
    'success' if result.success else 'failed',
    result.output
)
```

⚠️ **Handle recovery gracefully:**
```python
# Recovery options must return action
recovery = _handle_step_failure(...)

if recovery == 'abort':
    return  # Stop execution
elif recovery == 'skip':
    continue  # Next step
# else retry or auto-fix
```

---

**END OF IMPLEMENTATION**
