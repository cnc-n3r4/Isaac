"""
Natural Language Shell Scripting Module

Converts natural language to bash scripts and provides script management features.
"""

from .explainer import ScriptExplainer
from .generator import ScriptGenerator
from .scheduler import NaturalLanguageScheduler
from .templates import ScriptTemplateManager
from .translator import EnglishToBashTranslator
from .validator import ScriptValidator

__all__ = [
    "EnglishToBashTranslator",
    "ScriptGenerator",
    "ScriptExplainer",
    "NaturalLanguageScheduler",
    "ScriptTemplateManager",
    "ScriptValidator",
]
