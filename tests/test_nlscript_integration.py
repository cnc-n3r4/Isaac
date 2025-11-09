"""
Integration tests for Natural Language Shell Scripting
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from isaac.nlscript import (
    EnglishToBashTranslator,
    ScriptGenerator,
    ScriptExplainer,
    NaturalLanguageScheduler,
    ScriptTemplateManager,
    ScriptValidator
)


class TestEnglishToBashTranslator:
    """Test the English to Bash translator."""

    def test_simple_translation(self):
        """Test simple command translation."""
        translator = EnglishToBashTranslator()
        result = translator.translate("list all files")

        assert result['bash_code']
        assert 'ls' in result['bash_code']
        assert result['confidence'] > 0

    def test_translation_with_pattern(self):
        """Test translation with pattern matching."""
        translator = EnglishToBashTranslator()
        result = translator.translate("show current directory")

        assert 'pwd' in result['bash_code']
        assert result['explanation']

    def test_dangerous_command_warning(self):
        """Test that dangerous commands produce warnings."""
        translator = EnglishToBashTranslator()
        result = translator.translate("delete all log files")

        assert result['warnings']  # Should have warnings for deletion
        assert any('destructive' in w.lower() or 'delete' in w.lower() for w in result['warnings'])

    def test_cache(self):
        """Test translation caching."""
        translator = EnglishToBashTranslator()

        # First translation
        result1 = translator.translate("list files")

        # Second translation (should be cached)
        result2 = translator.translate("list files")

        assert result1['bash_code'] == result2['bash_code']

    def test_simple_translate_method(self):
        """Test simple translate method."""
        translator = EnglishToBashTranslator()
        bash_code = translator.translate_simple("show current directory")

        assert bash_code
        assert isinstance(bash_code, str)


class TestScriptGenerator:
    """Test the script generator."""

    def test_basic_generation(self):
        """Test basic script generation."""
        generator = ScriptGenerator()
        result = generator.generate("Create a backup script")

        assert result['script']
        assert '#!/bin/bash' in result['script'] or '#!/bin/sh' in result['script']
        assert result['metadata']
        assert result['generated_at']

    def test_generation_with_requirements(self):
        """Test generation with specific requirements."""
        generator = ScriptGenerator()
        requirements = ['Must handle errors', 'Must be idempotent']
        result = generator.generate("Deploy script", requirements=requirements)

        assert result['script']
        assert result['metadata']

    def test_save_script(self, tmp_path):
        """Test saving generated script."""
        generator = ScriptGenerator()
        output_file = tmp_path / "test_script.sh"

        result = generator.generate(
            "Hello world script",
            output_file=output_file
        )

        assert output_file.exists()
        assert output_file.stat().st_mode & 0o111  # Check executable bit

        # Check metadata file
        metadata_file = output_file.with_suffix('.json')
        assert metadata_file.exists()

    def test_script_history(self):
        """Test script generation history."""
        generator = ScriptGenerator()

        generator.generate("Script 1")
        generator.generate("Script 2")

        history = generator.list_generated_scripts()
        assert len(history) >= 2


class TestScriptExplainer:
    """Test the script explainer."""

    def test_basic_explanation(self):
        """Test basic script explanation."""
        explainer = ScriptExplainer()
        script = """#!/bin/bash
echo "Hello World"
"""
        result = explainer.explain(script)

        assert result['summary']
        assert 'complexity' in result

    def test_explain_complex_script(self):
        """Test explanation of complex script."""
        explainer = ScriptExplainer()
        script = """#!/bin/bash
set -e

backup_dir() {
    tar -czf backup.tar.gz "$1"
}

main() {
    for dir in /home/*; do
        backup_dir "$dir"
    done
}

main "$@"
"""
        result = explainer.explain(script, detail_level='detailed')

        assert result['summary']
        assert result['functions']
        assert 'backup_dir' in result['functions'] or 'main' in result['functions']
        assert result['complexity']
        assert result['complexity']['level'] in ['Simple', 'Moderate', 'Complex', 'Very Complex']

    def test_explain_dangerous_script(self):
        """Test explanation identifies dangerous operations."""
        explainer = ScriptExplainer()
        script = """#!/bin/bash
rm -rf /tmp/*
"""
        result = explainer.explain(script)

        assert result['potential_issues']

    def test_explain_command(self):
        """Test single command explanation."""
        explainer = ScriptExplainer()
        explanation = explainer.explain_command("ls -la")

        assert explanation
        assert isinstance(explanation, str)

    def test_complexity_assessment(self):
        """Test complexity assessment."""
        explainer = ScriptExplainer()

        simple_script = "echo 'hello'"
        complex_script = """#!/bin/bash
set -e
for i in {1..10}; do
    if [ $i -gt 5 ]; then
        echo $i | grep 5
    fi
done
"""

        simple_result = explainer.explain(simple_script)
        complex_result = explainer.explain(complex_script)

        assert simple_result['complexity']['score'] < complex_result['complexity']['score']


class TestNaturalLanguageScheduler:
    """Test the natural language scheduler."""

    def test_parse_daily_schedule(self):
        """Test parsing daily schedule."""
        scheduler = NaturalLanguageScheduler()
        result = scheduler.schedule("echo 'hello'", "every day at 2pm")

        assert result['cron_expression']
        assert '14' in result['cron_expression']  # 2pm = 14:00
        assert result['human_readable']

    def test_parse_hourly_schedule(self):
        """Test parsing hourly schedule."""
        scheduler = NaturalLanguageScheduler()
        result = scheduler.schedule("backup.sh", "every hour")

        assert result['cron_expression']
        assert '0 * * * *' == result['cron_expression']

    def test_parse_weekly_schedule(self):
        """Test parsing weekly schedule."""
        scheduler = NaturalLanguageScheduler()
        result = scheduler.schedule("cleanup.sh", "every Monday")

        assert result['cron_expression']
        assert '1' in result['cron_expression']  # Monday = 1

    def test_parse_minutes_schedule(self):
        """Test parsing minute interval schedule."""
        scheduler = NaturalLanguageScheduler()
        result = scheduler.schedule("check.sh", "every 15 minutes")

        assert result['cron_expression']
        assert '*/15' in result['cron_expression']

    def test_cron_to_human(self):
        """Test converting cron to human readable."""
        scheduler = NaturalLanguageScheduler()

        # Test daily schedule
        result = scheduler.schedule("test.sh", "every day at midnight")
        assert 'midnight' in result['human_readable'].lower() or '12:00 AM' in result['human_readable']


class TestScriptTemplateManager:
    """Test the script template manager."""

    def test_list_templates(self):
        """Test listing templates."""
        manager = ScriptTemplateManager()
        templates = manager.list_templates()

        assert len(templates) > 0
        assert any(t['name'] == 'basic' for t in templates)

    def test_get_template(self):
        """Test getting a template."""
        manager = ScriptTemplateManager()
        template = manager.get_template('basic')

        assert template
        assert template['script']
        assert template['description']
        assert '#!/bin/bash' in template['script']

    def test_generate_from_template(self):
        """Test generating script from template."""
        manager = ScriptTemplateManager()
        variables = {
            'description': 'Test script',
            'script_name': 'test.sh'
        }

        script = manager.generate_from_template('basic', variables)

        assert 'Test script' in script
        assert 'test.sh' in script

    def test_add_custom_template(self):
        """Test adding custom template."""
        manager = ScriptTemplateManager()

        success = manager.add_custom_template(
            name='test_template',
            script='#!/bin/bash\necho "{message}"',
            description='Test template',
            variables=['message']
        )

        assert success

        # Verify it was added
        template = manager.get_template('test_template')
        assert template
        assert template['description'] == 'Test template'

    def test_backup_template(self):
        """Test backup template exists and works."""
        manager = ScriptTemplateManager()
        template = manager.get_template('backup')

        assert template
        assert 'backup' in template['description'].lower()

        # Generate from template
        variables = {
            'source_dir': '/home/user/data',
            'backup_dir': '/backups'
        }
        script = manager.generate_from_template('backup', variables)

        assert '/home/user/data' in script
        assert '/backups' in script


class TestScriptValidator:
    """Test the script validator."""

    def test_validate_simple_script(self):
        """Test validating a simple script."""
        validator = ScriptValidator()
        script = """#!/bin/bash
echo "Hello World"
"""
        result = validator.validate(script)

        assert result['valid']
        assert result['safety_score'] > 0

    def test_validate_dangerous_script(self):
        """Test validating dangerous script."""
        validator = ScriptValidator()
        script = """#!/bin/bash
rm -rf /
"""
        result = validator.validate(script)

        assert len(result['warnings']) > 0
        assert result['safety_score'] < 100
        assert any('recursive deletion' in w.lower() or 'root directory' in w.lower()
                   for w in result['warnings'])

    def test_validate_syntax_error(self):
        """Test validation catches syntax errors."""
        validator = ScriptValidator()
        script = """#!/bin/bash
if [ true ]; then
    echo "missing fi"
"""
        result = validator.validate(script)

        # Should detect syntax error or unmatched brace
        assert not result['valid'] or len(result['errors']) > 0

    def test_best_practices(self):
        """Test best practice suggestions."""
        validator = ScriptValidator()
        script = """echo "hello"
rm file.txt
"""
        result = validator.validate(script)

        # Should suggest adding shebang, set -e, etc.
        assert len(result['suggestions']) > 0

    def test_strict_validation(self):
        """Test strict validation mode."""
        validator = ScriptValidator()
        script = """#!/bin/bash
echo "hello"
"""
        result = validator.validate(script, strict=True)

        # Strict mode should flag missing set -e, set -u
        assert not result['valid'] or len(result['warnings']) > 0

    def test_is_safe_to_run(self):
        """Test safety check."""
        validator = ScriptValidator()

        safe_script = """#!/bin/bash
set -e
echo "Hello"
"""
        dangerous_script = """#!/bin/bash
rm -rf /*
"""

        assert validator.is_safe_to_run(safe_script)
        assert not validator.is_safe_to_run(dangerous_script)


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_translate_validate_workflow(self):
        """Test translate -> validate workflow."""
        translator = EnglishToBashTranslator()
        validator = ScriptValidator()

        # Translate natural language to bash
        result = translator.translate("show disk usage")

        # Validate the generated script
        validation = validator.validate(result['bash_code'])

        assert validation['safety_score'] > 50  # Should be safe

    def test_generate_explain_workflow(self):
        """Test generate -> explain workflow."""
        generator = ScriptGenerator()
        explainer = ScriptExplainer()

        # Generate a script
        gen_result = generator.generate("Simple hello world script")

        # Explain the generated script
        expl_result = explainer.explain(gen_result['script'])

        assert expl_result['summary']
        assert expl_result['complexity']

    def test_template_validate_workflow(self):
        """Test template -> validate workflow."""
        manager = ScriptTemplateManager()
        validator = ScriptValidator()

        # Get template
        variables = {
            'description': 'Test',
            'script_name': 'test'
        }
        script = manager.generate_from_template('basic', variables)

        # Validate the template
        validation = validator.validate(script)

        assert validation['valid']

    def test_end_to_end_workflow(self, tmp_path):
        """Test complete end-to-end workflow."""
        # 1. Translate natural language
        translator = EnglishToBashTranslator()
        translation = translator.translate("list all text files")

        # 2. Validate the translation
        validator = ScriptValidator()
        validation = validator.validate(translation['bash_code'])
        assert validation['valid']

        # 3. Save to file
        script_file = tmp_path / "script.sh"
        with open(script_file, 'w') as f:
            f.write(translation['bash_code'])
        script_file.chmod(0o755)

        # 4. Explain the saved script
        explainer = ScriptExplainer()
        explanation = explainer.explain_file(script_file)
        assert explanation['summary']

        # 5. Schedule it (don't actually add to crontab in test)
        scheduler = NaturalLanguageScheduler()
        schedule = scheduler.schedule(str(script_file), "every day at 2pm")
        assert schedule['cron_expression']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
