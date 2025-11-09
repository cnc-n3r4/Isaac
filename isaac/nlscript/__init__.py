"""
Natural Language Shell Scripting Module

Converts natural language to bash scripts and provides script management features.
"""

from .translator import EnglishToBashTranslator
from .generator import ScriptGenerator
from .explainer import ScriptExplainer
from .scheduler import NaturalLanguageScheduler
from .templates import ScriptTemplateManager
from .validator import ScriptValidator

__all__ = [
    'EnglishToBashTranslator',
    'ScriptGenerator',
    'ScriptExplainer',
    'NaturalLanguageScheduler',
    'ScriptTemplateManager',
    'ScriptValidator'
]
