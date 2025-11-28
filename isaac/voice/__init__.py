"""
Voice Integration for Isaac

Provides speech-to-text, text-to-speech, and voice command capabilities
for hands-free interaction.
"""

from isaac.voice.speech_to_text import (
    SpeechToTextEngine,
    VoiceCommand,
)
from isaac.voice.text_to_speech import (
    TTSEngine,
    SpeechRequest,
    SpeechResult,
)
from isaac.voice.voice_shortcuts import (
    VoiceShortcut,
    VoiceShortcutManager,
)

__all__ = [
    'SpeechToTextEngine',
    'VoiceCommand',
    'TTSEngine',
    'SpeechRequest',
    'SpeechResult',
    'VoiceShortcut',
    'VoiceShortcutManager',
]
