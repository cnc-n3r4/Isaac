"""
Natural Language Scheduler

Converts natural language to cron expressions and manages scheduled scripts.
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
import re
import subprocess
import tempfile


class NaturalLanguageScheduler:
    """Manages script scheduling using natural language."""

    def __init__(self, ai_router=None):
        """
        Initialize scheduler.

        Args:
            ai_router: AIRouter instance for AI-powered scheduling
        """
        self.ai_router = ai_router
        self.schedule_patterns = self._init_patterns()

    def schedule(self, script: str, when: str) -> Dict[str, Any]:
        """
        Schedule a script using natural language.

        Args:
            script: The bash script or command to schedule
            when: Natural language description of when to run (e.g., "every day at 2pm")

        Returns:
            Dictionary with:
                - cron_expression: The cron expression
                - human_readable: Human-readable description
                - next_run: Estimated next run time
                - command: The full cron command
        """
        # Parse the natural language into cron expression
        cron_expr = self._parse_schedule(when)

        # Build the cron command
        cron_command = f"{cron_expr} {script}"

        # Calculate next run time (approximate)
        next_run = self._calculate_next_run(cron_expr)

        return {
            'cron_expression': cron_expr,
            'human_readable': self._cron_to_human(cron_expr),
            'next_run': next_run,
            'command': cron_command,
            'when_description': when
        }

    def add_to_crontab(self, script: str, when: str, comment: Optional[str] = None) -> bool:
        """
        Add a scheduled script to the user's crontab.

        Args:
            script: The bash script or command to schedule
            when: Natural language description of when to run
            comment: Optional comment for the crontab entry

        Returns:
            True if successful, False otherwise
        """
        try:
            schedule_info = self.schedule(script, when)
            cron_expr = schedule_info['cron_expression']

            # Get current crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_crontab = result.stdout if result.returncode == 0 else ""

            # Create new entry
            comment_line = f"# {comment}\n" if comment else f"# Scheduled: {when}\n"
            new_entry = f"{comment_line}{cron_expr} {script}\n"

            # Add new entry
            new_crontab = current_crontab + new_entry

            # Write back to crontab
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.cron') as f:
                f.write(new_crontab)
                temp_file = f.name

            subprocess.run(['crontab', temp_file], check=True)
            Path(temp_file).unlink()

            return True

        except Exception as e:
            print(f"Error adding to crontab: {e}")
            return False

    def list_scheduled_scripts(self) -> List[Dict[str, Any]]:
        """
        List all scheduled scripts from crontab.

        Returns:
            List of scheduled script information
        """
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode != 0:
                return []

            scheduled = []
            lines = result.stdout.split('\n')
            comment = None

            for line in lines:
                line = line.strip()
                if not line:
                    comment = None
                    continue

                if line.startswith('#'):
                    comment = line[1:].strip()
                    continue

                # Parse cron line
                parts = line.split(None, 5)
                if len(parts) >= 6:
                    cron_expr = ' '.join(parts[:5])
                    command = parts[5]

                    scheduled.append({
                        'cron_expression': cron_expr,
                        'command': command,
                        'comment': comment,
                        'human_readable': self._cron_to_human(cron_expr),
                        'next_run': self._calculate_next_run(cron_expr)
                    })
                    comment = None

            return scheduled

        except Exception as e:
            print(f"Error listing scheduled scripts: {e}")
            return []

    def _parse_schedule(self, when: str) -> str:
        """Parse natural language into cron expression."""
        when_lower = when.lower().strip()

        # Try pattern matching first
        for pattern, cron_func in self.schedule_patterns:
            match = re.search(pattern, when_lower)
            if match:
                return cron_func(match)

        # If AI router available, use it for complex expressions
        if self.ai_router:
            return self._ai_parse_schedule(when)

        # Fallback: default to daily at midnight
        return "0 0 * * *"

    def _ai_parse_schedule(self, when: str) -> str:
        """Use AI to parse complex schedule expressions."""
        prompt = f"""Convert the following natural language schedule description to a cron expression.

Schedule: {when}

Respond with ONLY the cron expression in the format:
minute hour day month weekday

Examples:
- "every day at 2pm" -> "0 14 * * *"
- "every Monday at 9am" -> "0 9 * * 1"
- "every 15 minutes" -> "*/15 * * * *"
- "first day of every month at midnight" -> "0 0 1 * *"

Cron expression:"""

        try:
            response = self.ai_router.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50
            )
            cron_expr = response.content.strip()
            # Validate it looks like a cron expression
            if self._validate_cron(cron_expr):
                return cron_expr
        except:
            pass

        # Fallback
        return "0 0 * * *"

    def _init_patterns(self) -> List[Tuple[str, callable]]:
        """Initialize schedule patterns."""
        patterns = [
            # Every X minutes
            (r'every (\d+) minutes?', lambda m: f"*/{m.group(1)} * * * *"),

            # Every hour
            (r'every hour', lambda m: "0 * * * *"),
            (r'hourly', lambda m: "0 * * * *"),

            # Daily at specific time
            (r'every day at (\d+):?(\d+)?\s*(am|pm)?', self._parse_daily),
            (r'daily at (\d+):?(\d+)?\s*(am|pm)?', self._parse_daily),

            # Specific times
            (r'at (\d+):(\d+)\s*(am|pm)?', self._parse_time),

            # Weekly
            (r'every (monday|tuesday|wednesday|thursday|friday|saturday|sunday)', self._parse_weekly),
            (r'every week on (monday|tuesday|wednesday|thursday|friday|saturday|sunday)', self._parse_weekly),

            # Monthly
            (r'first day of (?:the )?month', lambda m: "0 0 1 * *"),
            (r'last day of (?:the )?month', lambda m: "0 0 28-31 * *"),
            (r'every month on (?:the )?(\d+)(?:st|nd|rd|th)?', lambda m: f"0 0 {m.group(1)} * *"),

            # Special keywords
            (r'every day', lambda m: "0 0 * * *"),
            (r'daily', lambda m: "0 0 * * *"),
            (r'every week', lambda m: "0 0 * * 0"),
            (r'weekly', lambda m: "0 0 * * 0"),
            (r'every month', lambda m: "0 0 1 * *"),
            (r'monthly', lambda m: "0 0 1 * *"),

            # Midnight/noon
            (r'(?:at )?midnight', lambda m: "0 0 * * *"),
            (r'(?:at )?noon', lambda m: "0 12 * * *"),
        ]

        return patterns

    def _parse_daily(self, match) -> str:
        """Parse daily schedule."""
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3)

        if period:
            if period.lower() == 'pm' and hour != 12:
                hour += 12
            elif period.lower() == 'am' and hour == 12:
                hour = 0

        return f"{minute} {hour} * * *"

    def _parse_time(self, match) -> str:
        """Parse specific time."""
        hour = int(match.group(1))
        minute = int(match.group(2))
        period = match.group(3)

        if period:
            if period.lower() == 'pm' and hour != 12:
                hour += 12
            elif period.lower() == 'am' and hour == 12:
                hour = 0

        return f"{minute} {hour} * * *"

    def _parse_weekly(self, match) -> str:
        """Parse weekly schedule."""
        days = {
            'monday': '1', 'tuesday': '2', 'wednesday': '3',
            'thursday': '4', 'friday': '5', 'saturday': '6', 'sunday': '0'
        }
        day = match.group(1).lower()
        day_num = days.get(day, '0')
        return f"0 0 * * {day_num}"

    def _cron_to_human(self, cron_expr: str) -> str:
        """Convert cron expression to human-readable format."""
        parts = cron_expr.split()
        if len(parts) != 5:
            return "Invalid cron expression"

        minute, hour, day, month, weekday = parts

        # Build human-readable description
        desc_parts = []

        # Frequency
        if minute == '*' and hour == '*':
            desc_parts.append("Every minute")
        elif minute.startswith('*/'):
            interval = minute[2:]
            desc_parts.append(f"Every {interval} minutes")
        elif hour == '*':
            desc_parts.append("Every hour")
        elif day == '*' and month == '*' and weekday == '*':
            desc_parts.append("Every day")

        # Time
        if hour != '*' and not hour.startswith('*/'):
            hour_int = int(hour)
            minute_int = int(minute) if minute != '*' else 0
            period = 'AM' if hour_int < 12 else 'PM'
            display_hour = hour_int if hour_int <= 12 else hour_int - 12
            if display_hour == 0:
                display_hour = 12
            desc_parts.append(f"at {display_hour}:{minute_int:02d} {period}")

        # Day of week
        if weekday != '*':
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            try:
                day_name = days[int(weekday)]
                desc_parts.append(f"on {day_name}")
            except (ValueError, IndexError):
                pass

        # Day of month
        if day != '*' and weekday == '*':
            desc_parts.append(f"on day {day}")

        return ' '.join(desc_parts) if desc_parts else cron_expr

    def _calculate_next_run(self, cron_expr: str) -> str:
        """Calculate approximate next run time."""
        # This is a simplified calculation
        # For production, use a library like croniter
        parts = cron_expr.split()
        if len(parts) != 5:
            return "Unknown"

        minute, hour, day, month, weekday = parts
        now = datetime.now()

        # Simple cases
        if minute.startswith('*/'):
            interval = int(minute[2:])
            return f"Within {interval} minutes"

        if hour == '*':
            return "Within the next hour"

        if hour != '*' and minute != '*':
            try:
                target_hour = int(hour)
                target_minute = int(minute)
                if target_hour > now.hour or (target_hour == now.hour and target_minute > now.minute):
                    return f"Today at {target_hour}:{target_minute:02d}"
                else:
                    return f"Tomorrow at {target_hour}:{target_minute:02d}"
            except ValueError:
                pass

        return "See cron expression for details"

    def _validate_cron(self, cron_expr: str) -> bool:
        """Validate a cron expression."""
        parts = cron_expr.split()
        if len(parts) != 5:
            return False

        # Basic validation of each field
        try:
            minute, hour, day, month, weekday = parts

            # Check ranges (simplified)
            for field, min_val, max_val in [
                (minute, 0, 59),
                (hour, 0, 23),
                (day, 1, 31),
                (month, 1, 12),
                (weekday, 0, 7)
            ]:
                if field == '*':
                    continue
                if field.startswith('*/'):
                    continue
                if '-' in field:
                    continue
                if ',' in field:
                    continue

                # Try to parse as int
                val = int(field)
                if val < min_val or val > max_val:
                    return False

            return True
        except (ValueError, AttributeError):
            return False
