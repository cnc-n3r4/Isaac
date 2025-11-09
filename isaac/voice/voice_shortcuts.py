"""
Voice Shortcuts - Voice-activated command shortcuts
Isaac's system for quick voice commands and macros
"""

import os
import json
import time
import threading
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
import re
try:
    import fuzzywuzzy
    from fuzzywuzzy import fuzz
except ImportError:
    fuzzywuzzy = None
    fuzz = None


@dataclass
class VoiceShortcut:
    """Represents a voice shortcut configuration."""
    id: str
    name: str
    phrases: List[str]  # Multiple ways to trigger the shortcut
    command: str  # The command to execute
    description: str = ""
    category: str = "general"
    priority: int = 0  # Higher priority shortcuts are checked first
    enabled: bool = True
    context: Optional[str] = None  # Context where shortcut is active
    cooldown: float = 0.0  # Minimum time between executions (seconds)
    last_used: float = 0.0
    usage_count: int = 0
    success_rate: float = 1.0


@dataclass
class ShortcutMatch:
    """Result of matching a voice input against shortcuts."""
    shortcut: VoiceShortcut
    confidence: float
    matched_phrase: str
    fuzzy_score: int
    context_match: bool = True


class VoiceShortcutManager:
    """Manages voice shortcuts and their execution."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize voice shortcut manager."""
        self.config = config or {}
        self.shortcuts: Dict[str, VoiceShortcut] = {}
        self.shortcuts_file = Path.home() / '.isaac' / 'voice_shortcuts.json'
        self.context_stack: List[str] = []
        self.is_active = True

        # Fuzzy matching settings
        self.fuzzy_threshold = self.config.get('fuzzy_threshold', 80)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7)

        # Load default shortcuts
        self._load_default_shortcuts()

        # Load user shortcuts
        self._load_user_shortcuts()

    def _load_default_shortcuts(self):
        """Load built-in voice shortcuts."""
        default_shortcuts = [
            VoiceShortcut(
                id="help",
                name="Help",
                phrases=["help", "what can you do", "assist me", "show commands"],
                command="/help",
                description="Show available commands and help",
                category="system"
            ),

            VoiceShortcut(
                id="status",
                name="System Status",
                phrases=["status", "how are you", "system status", "check status"],
                command="/status",
                description="Check system status",
                category="system"
            ),

            VoiceShortcut(
                id="run_tests",
                name="Run Tests",
                phrases=["run tests", "execute tests", "test", "run the tests"],
                command="/run_tests",
                description="Run test suite",
                category="development"
            ),

            VoiceShortcut(
                id="stop",
                name="Stop Current Task",
                phrases=["stop", "cancel", "quit", "abort"],
                command="/stop",
                description="Stop current operation",
                category="system"
            ),

            VoiceShortcut(
                id="workspace_list",
                name="List Workspaces",
                phrases=["list workspaces", "show workspaces", "what workspaces"],
                command="/workspace list",
                description="List available workspaces",
                category="workspace"
            ),

            VoiceShortcut(
                id="workspace_create",
                name="Create Workspace",
                phrases=["create workspace", "new workspace", "make workspace"],
                command="/workspace create",
                description="Create a new workspace",
                category="workspace"
            ),

            VoiceShortcut(
                id="workspace_switch",
                name="Switch Workspace",
                phrases=["switch to workspace", "change workspace", "go to workspace"],
                command="/workspace switch",
                description="Switch to a different workspace",
                category="workspace"
            ),

            VoiceShortcut(
                id="debug_start",
                name="Start Debugging",
                phrases=["start debugging", "debug", "begin debug", "debug mode"],
                command="/debug start",
                description="Start debugging session",
                category="debug"
            ),

            VoiceShortcut(
                id="debug_stop",
                name="Stop Debugging",
                phrases=["stop debugging", "end debug", "exit debug"],
                command="/debug stop",
                description="Stop debugging session",
                category="debug"
            ),

            VoiceShortcut(
                id="voice_transcribe",
                name="Transcribe Audio",
                phrases=["transcribe", "transcribe audio", "convert to text"],
                command="/voice transcribe",
                description="Transcribe audio file to text",
                category="voice"
            ),

            VoiceShortcut(
                id="voice_listen",
                name="Start Voice Listening",
                phrases=["listen", "start listening", "voice mode", "listen to me"],
                command="/voice listen",
                description="Start voice command listening",
                category="voice"
            ),

            VoiceShortcut(
                id="voice_stop",
                name="Stop Voice Listening",
                phrases=["stop listening", "quiet", "be quiet", "shut up"],
                command="/voice stop",
                description="Stop voice command listening",
                category="voice"
            ),

            VoiceShortcut(
                id="language_switch",
                name="Switch Language",
                phrases=["switch language", "change language", "speak spanish", "habla español"],
                command="/language switch",
                description="Switch system language",
                category="language"
            ),

            VoiceShortcut(
                id="save_work",
                name="Save Work",
                phrases=["save", "save work", "save changes", "commit"],
                command="/save",
                description="Save current work",
                category="file"
            ),

            VoiceShortcut(
                id="open_file",
                name="Open File",
                phrases=["open file", "edit file", "show file"],
                command="/open",
                description="Open a file for editing",
                category="file"
            ),

            VoiceShortcut(
                id="search_code",
                name="Search Code",
                phrases=["search code", "find code", "grep", "search"],
                command="/search",
                description="Search through codebase",
                category="search"
            ),

            VoiceShortcut(
                id="run_command",
                name="Run Command",
                phrases=["run command", "execute command", "shell command"],
                command="/run",
                description="Execute a shell command",
                category="system"
            ),

            VoiceShortcut(
                id="show_logs",
                name="Show Logs",
                phrases=["show logs", "logs", "view logs", "check logs"],
                command="/logs",
                description="Show system logs",
                category="system"
            ),

            VoiceShortcut(
                id="performance_check",
                name="Performance Check",
                phrases=["performance", "check performance", "system performance"],
                command="/performance",
                description="Check system performance",
                category="system"
            )
        ]

        for shortcut in default_shortcuts:
            self.shortcuts[shortcut.id] = shortcut

    def _load_user_shortcuts(self):
        """Load user-defined shortcuts from file."""
        try:
            if self.shortcuts_file.exists():
                with open(self.shortcuts_file, 'r', encoding='utf-8') as f:
                    user_shortcuts_data = json.load(f)

                for shortcut_data in user_shortcuts_data:
                    shortcut = VoiceShortcut(**shortcut_data)
                    self.shortcuts[shortcut.id] = shortcut

        except Exception as e:
            print(f"Error loading user shortcuts: {e}")

    def _save_user_shortcuts(self):
        """Save user-defined shortcuts to file."""
        try:
            self.shortcuts_file.parent.mkdir(parents=True, exist_ok=True)

            # Only save user-defined shortcuts (not defaults)
            user_shortcuts = [
                shortcut for shortcut in self.shortcuts.values()
                if not shortcut.id.startswith('default_')
            ]

            with open(self.shortcuts_file, 'w', encoding='utf-8') as f:
                json.dump([{
                    'id': s.id,
                    'name': s.name,
                    'phrases': s.phrases,
                    'command': s.command,
                    'description': s.description,
                    'category': s.category,
                    'priority': s.priority,
                    'enabled': s.enabled,
                    'context': s.context,
                    'cooldown': s.cooldown,
                    'last_used': s.last_used,
                    'usage_count': s.usage_count,
                    'success_rate': s.success_rate
                } for s in user_shortcuts], f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error saving user shortcuts: {e}")

    def add_shortcut(self, shortcut: VoiceShortcut) -> bool:
        """Add a new voice shortcut."""
        try:
            # Validate shortcut
            if not shortcut.id or not shortcut.phrases or not shortcut.command:
                return False

            # Check for duplicate ID
            if shortcut.id in self.shortcuts:
                return False

            self.shortcuts[shortcut.id] = shortcut
            self._save_user_shortcuts()
            return True

        except Exception as e:
            print(f"Error adding shortcut: {e}")
            return False

    def remove_shortcut(self, shortcut_id: str) -> bool:
        """Remove a voice shortcut."""
        if shortcut_id in self.shortcuts:
            # Don't allow removal of default shortcuts
            if shortcut_id.startswith('default_'):
                return False

            del self.shortcuts[shortcut_id]
            self._save_user_shortcuts()
            return True
        return False

    def update_shortcut(self, shortcut_id: str, updates: Dict[str, Any]) -> bool:
        """Update a voice shortcut."""
        if shortcut_id not in self.shortcuts:
            return False

        shortcut = self.shortcuts[shortcut_id]

        # Don't allow updates to default shortcuts except for usage stats
        if shortcut_id.startswith('default_'):
            allowed_fields = {'last_used', 'usage_count', 'success_rate'}
            updates = {k: v for k, v in updates.items() if k in allowed_fields}

        for key, value in updates.items():
            if hasattr(shortcut, key):
                setattr(shortcut, key, value)

        self._save_user_shortcuts()
        return True

    def match_shortcut(self, voice_text: str, context: Optional[str] = None) -> Optional[ShortcutMatch]:
        """Match voice input against available shortcuts.

        Args:
            voice_text: The voice input text
            context: Current context (optional)

        Returns:
            Best matching shortcut or None
        """
        if not voice_text or not self.is_active:
            return None

        voice_text = voice_text.lower().strip()
        best_match = None
        best_score = 0

        # Get active shortcuts (enabled and matching context)
        active_shortcuts = [
            s for s in self.shortcuts.values()
            if s.enabled and self._is_context_match(s, context)
        ]

        # Sort by priority (higher first)
        active_shortcuts.sort(key=lambda s: s.priority, reverse=True)

        for shortcut in active_shortcuts:
            # Check cooldown
            if time.time() - shortcut.last_used < shortcut.cooldown:
                continue

            match_result = self._match_shortcut_phrases(shortcut, voice_text)
            if match_result:
                score = match_result['confidence'] * (1 + shortcut.priority * 0.1)
                if score > best_score and score >= self.confidence_threshold:
                    best_score = score
                    best_match = ShortcutMatch(
                        shortcut=shortcut,
                        confidence=score,
                        matched_phrase=match_result['matched_phrase'],
                        fuzzy_score=match_result['fuzzy_score'],
                        context_match=True
                    )

        return best_match

    def _match_shortcut_phrases(self, shortcut: VoiceShortcut, voice_text: str) -> Optional[Dict[str, Any]]:
        """Match voice text against a shortcut's phrases."""
        best_match = None
        best_score = 0

        for phrase in shortcut.phrases:
            phrase_lower = phrase.lower()

            # Exact match
            if phrase_lower in voice_text:
                return {
                    'matched_phrase': phrase,
                    'confidence': 1.0,
                    'fuzzy_score': 100
                }

            # Fuzzy match (if available)
            if fuzz:
                fuzzy_score = fuzz.partial_ratio(phrase_lower, voice_text)
                if fuzzy_score >= self.fuzzy_threshold:
                    confidence = fuzzy_score / 100.0
                    if confidence > best_score:
                        best_score = confidence
                        best_match = {
                            'matched_phrase': phrase,
                            'confidence': confidence,
                            'fuzzy_score': fuzzy_score
                        }
            else:
                # Simple substring match if fuzzywuzzy not available
                if phrase_lower in voice_text:
                    confidence = 0.8
                    if confidence > best_score:
                        best_score = confidence
                        best_match = {
                            'matched_phrase': phrase,
                            'confidence': confidence,
                            'fuzzy_score': 80
                        }

            # Word-based matching
            voice_words = set(voice_text.split())
            phrase_words = set(phrase_lower.split())
            if phrase_words and voice_words:
                overlap = len(phrase_words.intersection(voice_words))
                word_confidence = overlap / len(phrase_words)
                if word_confidence > 0.7 and word_confidence > best_score:
                    best_score = word_confidence
                    best_match = {
                        'matched_phrase': phrase,
                        'confidence': word_confidence,
                        'fuzzy_score': int(word_confidence * 100)
                    }

        return best_match

    def _is_context_match(self, shortcut: VoiceShortcut, current_context: Optional[str]) -> bool:
        """Check if shortcut is valid for current context."""
        if not shortcut.context:
            return True  # No context restriction

        if not current_context:
            return False  # Shortcut requires context but none provided

        # Check context stack
        return any(ctx in self.context_stack for ctx in shortcut.context.split(','))

    def execute_shortcut(self, match: ShortcutMatch, executor: Callable[[str], Any]) -> bool:
        """Execute a matched shortcut.

        Args:
            match: The shortcut match result
            executor: Function to execute the command

        Returns:
            True if execution was successful
        """
        try:
            # Update usage statistics
            shortcut = match.shortcut
            shortcut.last_used = time.time()
            shortcut.usage_count += 1

            # Execute the command
            result = executor(shortcut.command)

            # Update success rate (simple moving average)
            success = result is not None and getattr(result, 'success', True)
            shortcut.success_rate = (shortcut.success_rate * 0.9) + (1.0 if success else 0.0)

            # Save updated statistics
            self.update_shortcut(shortcut.id, {
                'last_used': shortcut.last_used,
                'usage_count': shortcut.usage_count,
                'success_rate': shortcut.success_rate
            })

            return success

        except Exception as e:
            print(f"Error executing shortcut {match.shortcut.id}: {e}")
            return False

    def push_context(self, context: str):
        """Push a context onto the context stack."""
        if context not in self.context_stack:
            self.context_stack.append(context)

    def pop_context(self, context: str):
        """Pop a context from the context stack."""
        if context in self.context_stack:
            self.context_stack.remove(context)

    def clear_context(self):
        """Clear the context stack."""
        self.context_stack.clear()

    def get_context(self) -> List[str]:
        """Get current context stack."""
        return self.context_stack.copy()

    def get_shortcuts(self, category: Optional[str] = None,
                      enabled_only: bool = True) -> List[VoiceShortcut]:
        """Get list of shortcuts, optionally filtered by category."""
        shortcuts = list(self.shortcuts.values())

        if enabled_only:
            shortcuts = [s for s in shortcuts if s.enabled]

        if category:
            shortcuts = [s for s in shortcuts if s.category == category]

        # Sort by priority, then by usage count
        shortcuts.sort(key=lambda s: (s.priority, s.usage_count), reverse=True)

        return shortcuts

    def get_shortcut_stats(self) -> Dict[str, Any]:
        """Get statistics about shortcut usage."""
        total_shortcuts = len(self.shortcuts)
        enabled_shortcuts = len([s for s in self.shortcuts.values() if s.enabled])
        total_usage = sum(s.usage_count for s in self.shortcuts.values())
        avg_success_rate = sum(s.success_rate for s in self.shortcuts.values()) / max(total_shortcuts, 1)

        category_stats = {}
        for shortcut in self.shortcuts.values():
            if shortcut.category not in category_stats:
                category_stats[shortcut.category] = {
                    'count': 0,
                    'usage': 0,
                    'avg_success': 0.0
                }
            category_stats[shortcut.category]['count'] += 1
            category_stats[shortcut.category]['usage'] += shortcut.usage_count

        for cat_stats in category_stats.values():
            if cat_stats['count'] > 0:
                cat_stats['avg_success'] = sum(
                    s.success_rate for s in self.shortcuts.values()
                    if s.category == list(category_stats.keys())[list(category_stats.values()).index(cat_stats)]
                ) / cat_stats['count']

        return {
            'total_shortcuts': total_shortcuts,
            'enabled_shortcuts': enabled_shortcuts,
            'total_usage': total_usage,
            'average_success_rate': avg_success_rate,
            'category_stats': category_stats,
            'most_used': max(self.shortcuts.values(), key=lambda s: s.usage_count, default=None)
        }

    def enable_shortcut(self, shortcut_id: str) -> bool:
        """Enable a shortcut."""
        return self.update_shortcut(shortcut_id, {'enabled': True})

    def disable_shortcut(self, shortcut_id: str) -> bool:
        """Disable a shortcut."""
        return self.update_shortcut(shortcut_id, {'enabled': False})

    def import_shortcuts(self, shortcuts_data: List[Dict[str, Any]]) -> int:
        """Import shortcuts from data."""
        imported_count = 0
        for shortcut_data in shortcuts_data:
            try:
                shortcut = VoiceShortcut(**shortcut_data)
                if self.add_shortcut(shortcut):
                    imported_count += 1
            except:
                continue
        return imported_count

    def export_shortcuts(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Export shortcuts to data."""
        shortcuts = self.get_shortcuts(category, enabled_only=False)
        return [{
            'id': s.id,
            'name': s.name,
            'phrases': s.phrases,
            'command': s.command,
            'description': s.description,
            'category': s.category,
            'priority': s.priority,
            'enabled': s.enabled,
            'context': s.context,
            'cooldown': s.cooldown,
            'last_used': s.last_used,
            'usage_count': s.usage_count,
            'success_rate': s.success_rate
        } for s in shortcuts]

    def set_fuzzy_threshold(self, threshold: int):
        """Set fuzzy matching threshold (0-100)."""
        self.fuzzy_threshold = max(0, min(100, threshold))

    def set_confidence_threshold(self, threshold: float):
        """Set confidence threshold (0.0-1.0)."""
        self.confidence_threshold = max(0.0, min(1.0, threshold))

    def reset_usage_stats(self):
        """Reset usage statistics for all shortcuts."""
        for shortcut in self.shortcuts.values():
            shortcut.usage_count = 0
            shortcut.success_rate = 1.0
            shortcut.last_used = 0.0

        self._save_user_shortcuts()

    def cleanup_unused_shortcuts(self, days_threshold: int = 30) -> int:
        """Remove shortcuts that haven't been used in specified days."""
        cutoff_time = time.time() - (days_threshold * 24 * 60 * 60)
        to_remove = []

        for shortcut_id, shortcut in self.shortcuts.items():
            if (not shortcut_id.startswith('default_') and
                shortcut.last_used < cutoff_time and
                shortcut.usage_count == 0):
                to_remove.append(shortcut_id)

        for shortcut_id in to_remove:
            del self.shortcuts[shortcut_id]

        if to_remove:
            self._save_user_shortcuts()

        return len(to_remove)