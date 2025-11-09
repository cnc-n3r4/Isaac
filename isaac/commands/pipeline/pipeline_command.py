"""
Pipeline command for managing intelligent pipelines
Isaac's pipeline management interface
"""

import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from isaac.pipelines.manager import PipelineManager
from isaac.pipelines.runner import PipelineRunner
from isaac.pipelines.pattern_learner import PatternLearner
from isaac.pipelines.models import Pipeline


class PipelineCommand:
    """Command interface for pipeline management."""

    def __init__(self):
        """Initialize pipeline command."""
        self.manager = PipelineManager()
        self.runner = PipelineRunner()
        self.learner = PatternLearner()

    def execute(self, args: List[str]) -> Dict[str, Any]:
        """Execute pipeline command.

        Args:
            args: Command arguments

        Returns:
            Command result
        """
        if not args:
            return self._show_help()

        action = args[0].lower()

        try:
            if action == 'list':
                return self._list_pipelines(args[1:])
            elif action == 'create':
                return self._create_pipeline(args[1:])
            elif action == 'run':
                return self._run_pipeline(args[1:])
            elif action == 'status':
                return self._show_status(args[1:])
            elif action == 'delete':
                return self._delete_pipeline(args[1:])
            elif action == 'edit':
                return self._edit_pipeline(args[1:])
            elif action == 'analyze':
                return self._analyze_patterns(args[1:])
            elif action == 'suggest':
                return self._show_suggestions(args[1:])
            elif action == 'templates':
                return self._list_templates(args[1:])
            elif action == 'export':
                return self._export_pipeline(args[1:])
            elif action == 'import':
                return self._import_pipeline(args[1:])
            else:
                return {
                    'success': False,
                    'output': f"Unknown action: {action}\n{self._get_help_text()}",
                    'exit_code': 1
                }
        except Exception as e:
            return {
                'success': False,
                'output': f"Error executing pipeline command: {e}",
                'exit_code': 1
            }

    def _list_pipelines(self, args: List[str]) -> Dict[str, Any]:
        """List all pipelines."""
        pipelines = self.manager.list_pipelines()

        if not pipelines:
            return {
                'success': True,
                'output': "No pipelines found. Create one with '/pipeline create <name>'",
                'exit_code': 0
            }

        output = "Available Pipelines:\n"
        output += "=" * 50 + "\n"

        for pipeline in sorted(pipelines, key=lambda p: p.name):
            created = datetime.fromtimestamp(pipeline.created_at).strftime("%Y-%m-%d")
            steps_count = len(pipeline.steps)
            output += f"• {pipeline.name} ({pipeline.id})\n"
            output += f"  {pipeline.description}\n"
            output += f"  Steps: {steps_count} | Created: {created}\n\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _create_pipeline(self, args: List[str]) -> Dict[str, Any]:
        """Create a new pipeline."""
        parser = argparse.ArgumentParser(prog='/pipeline create', exit_on_error=False)
        parser.add_argument('name', help='Pipeline name')
        parser.add_argument('-d', '--description', help='Pipeline description')
        parser.add_argument('-t', '--template', help='Template to use')

        try:
            parsed = parser.parse_args(args)
        except SystemExit:
            return {
                'success': False,
                'output': "Usage: /pipeline create <name> [-d description] [-t template]",
                'exit_code': 1
            }

        try:
            if parsed.template:
                # Create from template
                pipeline = self.manager.create_pipeline_from_template(
                    parsed.template, parsed.name, parsed.description
                )
                output = f"Created pipeline '{pipeline.name}' from template '{parsed.template}'\n"
            else:
                # Create empty pipeline
                pipeline_id = parsed.name.lower().replace(' ', '_')
                pipeline = Pipeline(
                    id=pipeline_id,
                    name=parsed.name,
                    description=parsed.description or ""
                )
                self.manager.create_pipeline(pipeline)
                output = f"Created empty pipeline '{pipeline.name}'\n"
                output += "Add steps with '/pipeline edit <name>'\n"

            output += f"Pipeline ID: {pipeline.id}\n"
            output += f"Steps: {len(pipeline.steps)}\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }

        except ValueError as e:
            return {
                'success': False,
                'output': f"Error creating pipeline: {e}",
                'exit_code': 1
            }

    def _run_pipeline(self, args: List[str]) -> Dict[str, Any]:
        """Run a pipeline."""
        parser = argparse.ArgumentParser(prog='/pipeline run', exit_on_error=False)
        parser.add_argument('pipeline_id', help='Pipeline ID to run')
        parser.add_argument('--wait', action='store_true', help='Wait for pipeline completion')
        parser.add_argument('variables', nargs='*', help='Variables in key=value format')

        try:
            parsed = parser.parse_args(args)
        except SystemExit:
            return {
                'success': False,
                'output': "Usage: /pipeline run <pipeline_id> [--wait] [var1=value1 var2=value2 ...]",
                'exit_code': 1
            }

        pipeline = self.manager.get_pipeline(parsed.pipeline_id)

        if not pipeline:
            return {
                'success': False,
                'output': f"Pipeline '{parsed.pipeline_id}' not found",
                'exit_code': 1
            }

        # Parse variables
        variables = {}
        for var_arg in parsed.variables:
            if '=' in var_arg:
                key, value = var_arg.split('=', 1)
                variables[key] = value

        # Start execution
        if parsed.wait:
            # Run synchronously
            execution = self.runner.run_pipeline_sync(pipeline, variables)
            output = f"Executed pipeline '{pipeline.name}'\n"
            output += f"Status: {execution.status.value}\n"
            if execution.end_time and execution.start_time:
                duration = execution.end_time - execution.start_time
                output += f"Duration: {duration:.2f}s\n"
            if execution.error_message:
                output += f"Error: {execution.error_message}\n"
        else:
            # Run asynchronously
            execution_id = self.runner.run_pipeline(pipeline, variables)
            output = f"Started pipeline '{pipeline.name}'\n"
            output += f"Execution ID: {execution_id}\n"
            output += f"Monitor with: /pipeline status {execution_id}\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _show_status(self, args: List[str]) -> Dict[str, Any]:
        """Show pipeline execution status."""
        if not args:
            # Show all executions
            executions = self.runner.list_executions()
            if not executions:
                return {
                    'success': True,
                    'output': "No active pipeline executions",
                    'exit_code': 0
                }

            output = "Active Pipeline Executions:\n"
            output += "=" * 50 + "\n"

            for execution in sorted(executions, key=lambda e: e.start_time, reverse=True):
                pipeline = self.manager.get_pipeline(execution.pipeline_id)
                pipeline_name = pipeline.name if pipeline else execution.pipeline_id

                status_emoji = {
                    'pending': '⏳',
                    'running': '▶️',
                    'success': '✅',
                    'failed': '❌',
                    'cancelled': '⏹️',
                    'paused': '⏸️'
                }.get(execution.status.value, '❓')

                start_time = datetime.fromtimestamp(execution.start_time).strftime("%H:%M:%S")
                duration = execution.duration
                duration_str = f"{duration:.1f}s" if duration else "running"

                output += f"{status_emoji} {pipeline_name} ({execution.execution_id[:8]})\n"
                output += f"  Started: {start_time} | Duration: {duration_str}\n"

                if execution.error_message:
                    output += f"  Error: {execution.error_message}\n"

                output += "\n"

            return {
                'success': True,
                'output': output,
                'exit_code': 0
            }

        # Show specific execution
        execution_id = args[0]
        execution = self.runner.get_execution(execution_id)

        if not execution:
            return {
                'success': False,
                'output': f"Execution '{execution_id}' not found",
                'exit_code': 1
            }

        pipeline = self.manager.get_pipeline(execution.pipeline_id)
        pipeline_name = pipeline.name if pipeline else execution.pipeline_id

        output = f"Pipeline: {pipeline_name}\n"
        output += f"Execution ID: {execution.execution_id}\n"
        output += f"Status: {execution.status.value.upper()}\n"
        output += f"Started: {datetime.fromtimestamp(execution.start_time).strftime('%Y-%m-%d %H:%M:%S')}\n"

        if execution.end_time:
            duration = execution.end_time - execution.start_time
            output += f"Duration: {duration:.2f} seconds\n"

        if execution.error_message:
            output += f"Error: {execution.error_message}\n"

        # Show step results
        if execution.steps_results:
            output += "\nStep Results:\n"
            for step_id, result in execution.steps_results.items():
                status = "✅" if result['success'] else "❌"
                duration = result.get('duration', 0)
                output += f"  {status} {step_id}: {duration:.2f}s\n"

                if not result['success']:
                    error_output = result.get('output', '')[:100]
                    if len(error_output) > 100:
                        error_output += "..."
                    output += f"    Error: {error_output}\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _delete_pipeline(self, args: List[str]) -> Dict[str, Any]:
        """Delete a pipeline."""
        if not args:
            return {
                'success': False,
                'output': "Usage: /pipeline delete <pipeline_id>",
                'exit_code': 1
            }

        pipeline_id = args[0]

        if self.manager.delete_pipeline(pipeline_id):
            return {
                'success': True,
                'output': f"Deleted pipeline '{pipeline_id}'",
                'exit_code': 0
            }
        else:
            return {
                'success': False,
                'output': f"Pipeline '{pipeline_id}' not found",
                'exit_code': 1
            }

    def _edit_pipeline(self, args: List[str]) -> Dict[str, Any]:
        """Edit a pipeline (placeholder for now)."""
        return {
            'success': False,
            'output': "Pipeline editing not yet implemented. Use JSON files for now.",
            'exit_code': 1
        }

    def _analyze_patterns(self, args: List[str]) -> Dict[str, Any]:
        """Analyze command history for patterns."""
        # For now, return a placeholder since we need command history access
        return {
            'success': True,
            'output': "Pattern analysis requires command history access.\n"
                     "This feature will analyze your command patterns to suggest pipelines.\n"
                     "Use '/pipeline suggest' to see current suggestions.",
            'exit_code': 0
        }

    def _show_suggestions(self, args: List[str]) -> Dict[str, Any]:
        """Show pipeline suggestions."""
        # For now, show template suggestions
        templates = self.manager.get_pipeline_templates()

        output = "Pipeline Suggestions:\n"
        output += "=" * 30 + "\n\n"

        output += "Available Templates:\n"
        for template in templates:
            output += f"• {template['name']} ({template['id']})\n"
            output += f"  {template['description']}\n"
            output += f"  Create with: /pipeline create \"My {template['name']}\" -t {template['id']}\n\n"

        output += "Pattern-based suggestions will appear here as you use commands.\n"
        output += "Run '/pipeline analyze' to scan your command history.\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _list_templates(self, args: List[str]) -> Dict[str, Any]:
        """List available pipeline templates."""
        templates = self.manager.get_pipeline_templates()

        output = "Available Pipeline Templates:\n"
        output += "=" * 35 + "\n\n"

        for template in templates:
            output += f"📋 {template['name']} ({template['id']})\n"
            output += f"   Category: {template['category']}\n"
            output += f"   {template['description']}\n"
            output += f"   Steps: {len(template['steps'])}\n\n"

            # Show steps
            for i, step in enumerate(template['steps'], 1):
                output += f"   {i}. {step['name']}\n"
            output += "\n"

        return {
            'success': True,
            'output': output,
            'exit_code': 0
        }

    def _export_pipeline(self, args: List[str]) -> Dict[str, Any]:
        """Export a pipeline."""
        if len(args) < 2:
            return {
                'success': False,
                'output': "Usage: /pipeline export <pipeline_id> <export_path>",
                'exit_code': 1
            }

        pipeline_id = args[0]
        export_path = Path(args[1])

        if self.manager.export_pipeline(pipeline_id, export_path):
            return {
                'success': True,
                'output': f"Exported pipeline '{pipeline_id}' to {export_path}",
                'exit_code': 0
            }
        else:
            return {
                'success': False,
                'output': f"Pipeline '{pipeline_id}' not found",
                'exit_code': 1
            }

    def _import_pipeline(self, args: List[str]) -> Dict[str, Any]:
        """Import a pipeline."""
        if not args:
            return {
                'success': False,
                'output': "Usage: /pipeline import <import_path>",
                'exit_code': 1
            }

        import_path = Path(args[0])

        if not import_path.exists():
            return {
                'success': False,
                'output': f"File not found: {import_path}",
                'exit_code': 1
            }

        pipeline = self.manager.import_pipeline(import_path)
        if pipeline:
            return {
                'success': True,
                'output': f"Imported pipeline '{pipeline.name}' (ID: {pipeline.id})",
                'exit_code': 0
            }
        else:
            return {
                'success': False,
                'output': f"Failed to import pipeline from {import_path}",
                'exit_code': 1
            }

    def _show_help(self) -> Dict[str, Any]:
        """Show help text."""
        return {
            'success': True,
            'output': self._get_help_text(),
            'exit_code': 0
        }

    def _get_help_text(self) -> str:
        """Get help text."""
        return """Isaac Pipeline Manager - Intelligent Workflow Automation

USAGE:
  /pipeline <action> [arguments...]

ACTIONS:
  list                           List all pipelines
  create <name> [-d desc] [-t template]  Create new pipeline
  run <id> [var=value ...]       Run a pipeline
  status [execution_id]          Show execution status
  delete <id>                    Delete a pipeline
  edit <id>                      Edit pipeline (not implemented)
  analyze                        Analyze command patterns
  suggest                        Show pipeline suggestions
  templates                      List available templates
  export <id> <path>             Export pipeline to file
  import <path>                  Import pipeline from file

EXAMPLES:
  /pipeline create "Build App" -d "Build and test application"
  /pipeline create "Deploy Prod" -t deploy
  /pipeline run build_app version=1.2.3
  /pipeline status
  /pipeline templates

Pipeline files are stored in ~/.isaac/pipelines/
"""