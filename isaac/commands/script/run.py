"""
Script Command Runner - Natural Language Shell Scripting
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.nlscript import (
    EnglishToBashTranslator,
    NaturalLanguageScheduler,
    ScriptExplainer,
    ScriptGenerator,
    ScriptTemplateManager,
    ScriptValidator,
)


def execute_script(args: Dict[str, Any]) -> str:
    """Execute script command based on action.

    Args:
        args: Command arguments from Isaac

    Returns:
        Formatted output
    """
    action = args.get("action")
    input_text = args.get("input", "")
    template_name = args.get("template")
    output_path = args.get("output")
    when = args.get("when", "")
    strict = args.get("strict", False)
    detail_level = args.get("detail_level", "medium")

    # Try to get AI router from environment
    ai_router = _get_ai_router()

    try:
        if action == "translate":
            return handle_translate(input_text, ai_router, output_path)

        elif action == "generate":
            return handle_generate(input_text, ai_router, output_path)

        elif action == "explain":
            return handle_explain(input_text, ai_router, detail_level)

        elif action == "schedule":
            return handle_schedule(input_text, when, ai_router)

        elif action == "validate":
            return handle_validate(input_text, strict, ai_router)

        elif action == "template":
            return handle_template(template_name, output_path)

        elif action == "list-templates":
            return handle_list_templates()

        elif action == "list-scheduled":
            return handle_list_scheduled(ai_router)

        else:
            return f"❌ Unknown action: {action}"

    except Exception as e:
        return f"❌ Error executing script command: {str(e)}"


def handle_translate(input_text: str, ai_router, output_path: str) -> str:
    """Handle translate action."""
    if not input_text:
        return "❌ Please provide a natural language description to translate"

    translator = EnglishToBashTranslator(ai_router)
    result = translator.translate(input_text)

    output = "🔄 Translation Result\n\n"
    output += f"Natural Language: {input_text}\n\n"
    output += f"Bash Code:\n```bash\n{result['bash_code']}\n```\n\n"
    output += f"Explanation: {result['explanation']}\n"
    output += f"Confidence: {result['confidence']:.0%}\n"

    if result["warnings"]:
        output += "\n⚠️  Warnings:\n"
        for warning in result["warnings"]:
            output += f"  - {warning}\n"

    # Save to file if requested
    if output_path:
        try:
            with open(output_path, "w") as f:
                f.write(result["bash_code"])
            Path(output_path).chmod(0o755)
            output += f"\n✅ Script saved to: {output_path}"
        except Exception as e:
            output += f"\n❌ Failed to save script: {e}"

    return output


def handle_generate(input_text: str, ai_router, output_path: str) -> str:
    """Handle generate action."""
    if not input_text:
        return "❌ Please provide a description for the script to generate"

    generator = ScriptGenerator(ai_router)

    # Parse requirements if provided in format "description | req1, req2, req3"
    requirements = None
    if "|" in input_text:
        parts = input_text.split("|", 1)
        input_text = parts[0].strip()
        requirements = [r.strip() for r in parts[1].split(",")]

    output_file = Path(output_path) if output_path else None
    result = generator.generate(input_text, requirements, output_file)

    output = "🎯 Script Generation Result\n\n"
    output += f"Description: {input_text}\n\n"
    output += f"Generated Script:\n```bash\n{result['script']}\n```\n\n"

    if result["metadata"]:
        output += "📋 Metadata:\n"
        for key, value in result["metadata"].items():
            output += f"  - {key}: {value}\n"
        output += "\n"

    if result["tests"]:
        output += "🧪 Suggested Tests:\n"
        for test in result["tests"][:5]:  # Show first 5 tests
            output += f"  - {test}\n"
        output += "\n"

    if result["documentation"]:
        output += f"📖 Documentation:\n{result['documentation']}\n\n"

    if output_file:
        output += f"✅ Script saved to: {output_file}\n"
        output += f"   Metadata saved to: {output_file.with_suffix('.json')}\n"

    return output


def handle_explain(input_text: str, ai_router, detail_level: str) -> str:
    """Handle explain action."""
    if not input_text:
        return "❌ Please provide a script or file path to explain"

    explainer = ScriptExplainer(ai_router)

    # Check if input is a file path
    if os.path.exists(input_text):
        result = explainer.explain_file(Path(input_text), detail_level)
        file_info = f"File: {input_text}\n\n"
    else:
        result = explainer.explain(input_text, detail_level)
        file_info = ""

    output = "📖 Script Explanation\n\n"
    output += file_info
    output += f"Summary: {result['summary']}\n\n"

    if result["line_by_line"]:
        output += "📝 Line-by-Line Explanation:\n"
        for line in result["line_by_line"][:10]:  # Show first 10
            output += f"  {line}\n"
        output += "\n"

    if result["functions"]:
        output += "⚙️  Functions:\n"
        for func, desc in result["functions"].items():
            output += f"  - {func}: {desc}\n"
        output += "\n"

    if result.get("complexity"):
        comp = result["complexity"]
        output += f"📊 Complexity: {comp['level']} (score: {comp['score']})\n"
        output += f"   Lines: {comp['metrics']['lines']}, "
        output += f"Functions: {comp['metrics']['functions']}, "
        output += f"Loops: {comp['metrics']['loops']}\n\n"

    if result["potential_issues"]:
        output += "⚠️  Potential Issues:\n"
        for issue in result["potential_issues"]:
            output += f"  {issue}\n"

    return output


def handle_schedule(input_text: str, when: str, ai_router) -> str:
    """Handle schedule action."""
    if not input_text:
        return "❌ Please provide a script or command to schedule"

    if not when:
        return "❌ Please provide a schedule time (e.g., 'every day at 2pm')"

    scheduler = NaturalLanguageScheduler(ai_router)
    result = scheduler.schedule(input_text, when)

    output = "📅 Schedule Created\n\n"
    output += f"Command: {input_text}\n"
    output += f"When: {when}\n\n"
    output += f"Cron Expression: {result['cron_expression']}\n"
    output += f"Human Readable: {result['human_readable']}\n"
    output += f"Next Run: {result['next_run']}\n\n"
    output += f"Full Cron Command:\n{result['command']}\n\n"

    # Ask if user wants to add to crontab
    output += "💡 To add this to your crontab, run:\n"
    output += f"   echo '{result['command']}' | crontab -\n"
    output += '   Or use: /script schedule "command" --when "time" --add\n'

    return output


def handle_validate(input_text: str, strict: bool, ai_router) -> str:
    """Handle validate action."""
    if not input_text:
        return "❌ Please provide a script or file path to validate"

    validator = ScriptValidator(ai_router)

    # Check if input is a file path
    if os.path.exists(input_text):
        result = validator.validate_file(Path(input_text), strict)
        file_info = f"File: {input_text}\n\n"
    else:
        result = validator.validate(input_text, strict)
        file_info = ""

    output = "✅ Validation Result\n\n" if result["valid"] else "❌ Validation Failed\n\n"
    output += file_info

    output += f"Valid: {'✅ Yes' if result['valid'] else '❌ No'}\n"
    output += f"Safety Score: {result['safety_score']}/100\n"
    output += f"Mode: {'Strict' if strict else 'Normal'}\n\n"

    if result["errors"]:
        output += "❌ Errors:\n"
        for error in result["errors"]:
            output += f"  {error}\n"
        output += "\n"

    if result["warnings"]:
        output += "⚠️  Warnings:\n"
        for warning in result["warnings"]:
            output += f"  {warning}\n"
        output += "\n"

    if result["suggestions"]:
        output += "💡 Suggestions:\n"
        for suggestion in result["suggestions"]:
            output += f"  {suggestion}\n"
        output += "\n"

    if result.get("shellcheck_results"):
        sc = result["shellcheck_results"]
        if sc.get("warnings"):
            output += "🔍 Shellcheck Warnings:\n"
            for warning in sc["warnings"][:5]:  # Show first 5
                output += f"  {warning}\n"

    return output


def handle_template(template_name: str, output_path: str) -> str:
    """Handle template action."""
    if not template_name:
        return "❌ Please provide a template name"

    manager = ScriptTemplateManager()
    template = manager.get_template(template_name)

    if not template:
        output = f"❌ Template '{template_name}' not found\n\n"
        output += "Available templates:\n"
        for tmpl in manager.list_templates():
            output += f"  - {tmpl['name']}: {tmpl['description']}\n"
        return output

    output = f"📄 Template: {template_name}\n\n"
    output += f"Description: {template['description']}\n"
    output += f"Category: {template['category']}\n"

    if "variables" in template and template["variables"]:
        output += f"\nVariables:\n"
        for var in template["variables"]:
            output += f"  - {var}\n"

    output += f"\nScript:\n```bash\n{template['script']}\n```\n"

    # Save to file if requested
    if output_path:
        try:
            with open(output_path, "w") as f:
                f.write(template["script"])
            Path(output_path).chmod(0o755)
            output += f"\n✅ Template saved to: {output_path}"
        except Exception as e:
            output += f"\n❌ Failed to save template: {e}"

    return output


def handle_list_templates() -> str:
    """Handle list-templates action."""
    manager = ScriptTemplateManager()
    templates = manager.list_templates()

    output = "📚 Available Script Templates\n\n"

    # Group by category
    categories = {}
    for tmpl in templates:
        cat = tmpl["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tmpl)

    for category, tmpls in sorted(categories.items()):
        output += f"### {category.upper()}\n"
        for tmpl in tmpls:
            type_badge = "🔧" if tmpl["type"] == "custom" else "📦"
            output += f"  {type_badge} {tmpl['name']}: {tmpl['description']}\n"
        output += "\n"

    output += "💡 Use: /script template <name> to view a template\n"

    return output


def handle_list_scheduled(ai_router) -> str:
    """Handle list-scheduled action."""
    scheduler = NaturalLanguageScheduler(ai_router)
    scheduled = scheduler.list_scheduled_scripts()

    if not scheduled:
        return "📅 No scheduled scripts found in crontab"

    output = "📅 Scheduled Scripts\n\n"

    for i, item in enumerate(scheduled, 1):
        output += f"{i}. {item['command']}\n"
        output += f"   Schedule: {item['human_readable']}\n"
        output += f"   Cron: {item['cron_expression']}\n"
        output += f"   Next run: {item['next_run']}\n"
        if item.get("comment"):
            output += f"   Comment: {item['comment']}\n"
        output += "\n"

    return output


def _get_ai_router():
    """Get AI router instance if available."""
    try:
        from isaac.ai.router import AIRouter

        return AIRouter()
    except Exception:
        # AI router not available or not configured
        return None
