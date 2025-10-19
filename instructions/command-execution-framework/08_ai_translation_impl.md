# Implementation: AI Translation Layer (Phase 2 Placeholder)

## Goal
Create AI translation module for natural language to command translation. This is a **placeholder implementation** for Phase 2 integration.

**Time Estimate:** 90 minutes (for full AI integration in Phase 2)

---

## Architecture Reminder

**Purpose:** Translate natural language → executable commands
- Resolve ambiguous paths ("my documents" → actual path)
- Generate command suggestions
- Provide confidence scores
- Require confirmation for destructive operations

**User expects:**
```bash
isaac> backup my documents
AI: Translating 'my documents'... → /home/user/Documents
Destination: (prompts)
Execute? (y/n)
```

---

## File to Create

**Path:** `isaac/core/ai_translator.py`

**Lines:** ~80 (placeholder version)

---

## Complete Implementation (Placeholder)

```python
"""
AI Translator - Natural language to command translation.

PHASE 2 PLACEHOLDER:
This module provides the interface for AI-powered translation.
Current implementation uses simple heuristics.
Full AI integration coming in Phase 3.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict
import os


@dataclass
class TranslationResult:
    """
    Result of AI translation.
    
    Attributes:
        original: Original user input
        translated: Translated command string
        resolved_paths: Dict of path resolutions
        confidence: Confidence score (0.0 - 1.0)
        needs_confirmation: Whether user confirmation required
    """
    original: str
    translated: str
    resolved_paths: Dict[str, str]
    confidence: float
    needs_confirmation: bool


class AITranslator:
    """
    Translate natural language to executable commands.
    
    PLACEHOLDER: Uses simple heuristics until Phase 3 AI integration.
    """
    
    def __init__(self):
        """Initialize translator."""
        self.common_paths = self._build_common_paths()
    
    def translate(self, user_input: str) -> Optional[TranslationResult]:
        """
        Translate natural language input to command.
        
        Args:
            user_input: User's natural language command
            
        Returns:
            TranslationResult or None if unable to translate
            
        Example:
            "backup my documents" →
            TranslationResult(
                original="backup my documents",
                translated="backup ~/Documents",
                resolved_paths={"my documents": "~/Documents"},
                confidence=0.8,
                needs_confirmation=True
            )
        """
        # PLACEHOLDER: Simple pattern matching
        # Phase 3 will replace with actual AI translation
        
        lower_input = user_input.lower()
        
        # Try to resolve common path references
        for phrase, path in self.common_paths.items():
            if phrase in lower_input:
                resolved_input = lower_input.replace(phrase, str(path))
                return TranslationResult(
                    original=user_input,
                    translated=resolved_input,
                    resolved_paths={phrase: str(path)},
                    confidence=0.7,  # Medium confidence for heuristic
                    needs_confirmation=True
                )
        
        # No translation possible with current heuristics
        return None
    
    def _build_common_paths(self) -> Dict[str, Path]:
        """
        Build dictionary of common path references.
        
        Returns:
            Dict mapping phrases to actual paths
        """
        home = Path.home()
        
        common = {
            "my documents": home / "Documents",
            "documents": home / "Documents",
            "my downloads": home / "Downloads",
            "downloads": home / "Downloads",
            "desktop": home / "Desktop",
            "my desktop": home / "Desktop",
            "pictures": home / "Pictures",
            "my pictures": home / "Pictures",
            "music": home / "Music",
            "my music": home / "Music",
            "videos": home / "Videos",
            "my videos": home / "Videos",
        }
        
        # Filter to only existing paths
        return {k: v for k, v in common.items() if v.exists()}
    
    def suggest_paths(self, partial: str) -> list[str]:
        """
        Suggest paths based on partial input.
        
        Args:
            partial: Partial path string
            
        Returns:
            List of suggested paths
            
        PLACEHOLDER: Returns common paths only.
        Phase 3 will use AI for smarter suggestions.
        """
        partial_lower = partial.lower()
        
        suggestions = []
        for phrase, path in self.common_paths.items():
            if partial_lower in phrase:
                suggestions.append(f"{phrase} → {path}")
        
        return suggestions[:5]  # Limit to 5 suggestions


def create_translator():
    """
    Factory function to create AITranslator instance.
    
    Returns:
        AITranslator instance
    """
    return AITranslator()
```

---

## Phase 3 Integration Plan

**When implementing full AI translation:**

1. **Replace `translate()` method:**
   - Integrate with LLM API (OpenAI, Anthropic, etc.)
   - Use context from command history
   - Improve path resolution accuracy
   - Add multi-step reasoning

2. **Enhance `suggest_paths()` method:**
   - Use filesystem traversal with AI ranking
   - Consider recent command history
   - Fuzzy matching with confidence scores

3. **Add learning system:**
   ```python
   def learn_from_feedback(self, translation: TranslationResult, was_correct: bool):
       """Learn from user confirmations/rejections"""
       pass
   ```

4. **Add context management:**
   ```python
   def set_context(self, session_history, current_directory):
       """Provide context for better translations"""
       pass
   ```

---

## Verification Steps

After implementation, verify:

- [ ] File exists at `isaac/core/ai_translator.py`
- [ ] No syntax errors on import
- [ ] Can instantiate: `translator = AITranslator()`
- [ ] Translate common phrases: `translator.translate("backup my documents")` returns valid result
- [ ] Suggest paths: `translator.suggest_paths("doc")` returns suggestions
- [ ] None return for untranslatable: `translator.translate("xyzabc")` returns None

## Test Manually

```python
# In Python REPL at project root
from isaac.core.ai_translator import create_translator

translator = create_translator()

# Test translation
result = translator.translate("backup my documents")
if result:
    print(f"Original: {result.original}")
    print(f"Translated: {result.translated}")
    print(f"Resolved: {result.resolved_paths}")
    print(f"Confidence: {result.confidence}")
# Expected: Translation with ~/Documents resolution

# Test suggestions
suggestions = translator.suggest_paths("doc")
print(f"Suggestions: {suggestions}")
# Expected: List including "documents" variations

# Test untranslatable
result = translator.translate("gibberish xyz")
print(f"Result: {result}")
# Expected: None
```

---

## Common Pitfalls

- ⚠️ **Placeholder awareness** - This is a **simplified version**. Full AI integration happens in Phase 3.

- ⚠️ **Path existence** - Only suggest paths that actually exist on the system.

- ⚠️ **Confidence scores** - Heuristic-based translations should have medium confidence (0.5-0.8).

- ⚠️ **Confirmation required** - Always set `needs_confirmation=True` for destructive operations.

- ⚠️ **Case insensitivity** - Use `.lower()` for phrase matching.

---

## Integration with CommandRouter

**Current usage in router (see 02_command_router_impl.md):**

```python
def _handle_natural(self, tokens: List[str], original: str) -> CommandResult:
    """Handle natural language command."""
    
    # Try AI translation (Phase 2)
    from isaac.core.ai_translator import create_translator
    translator = create_translator()
    
    translation = translator.translate(original)
    if translation:
        # Show translation to user
        print(f"\nAI Translation:")
        print(f"  {translation.original}")
        print(f"  → {translation.translated}")
        print(f"  Confidence: {translation.confidence:.0%}\n")
        
        if translation.needs_confirmation:
            confirm = input("Execute? (y/n): ").strip().lower()
            if confirm not in ['y', 'yes']:
                return CommandResult(
                    success=False,
                    message="Cancelled by user",
                    status_symbol='⊘'
                )
        
        # Re-execute with translated command
        return self.execute(translation.translated)
    else:
        # No translation available
        return CommandResult(
            success=False,
            message=f"Unable to translate: {original}",
            status_symbol='✗',
            suggestion="Try being more specific or use explicit commands"
        )
```

---

**END OF IMPLEMENTATION**

**NOTE:** This is a **placeholder** for Phase 2. Full AI integration with LLM API coming in Phase 3 (see phase3_ai_integration_yaml_request.md in mailbox).
