"""
Voice Integration - Speech-to-text and voice command recognition
Isaac's voice interface for hands-free development assistance
"""

import json
import os
import queue
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class VoiceCommand:
    """Represents a recognized voice command."""

    command_id: str
    text: str
    confidence: float
    timestamp: float
    language: str
    duration: float
    audio_file: Optional[str] = None


@dataclass
class VoiceShortcut:
    """Represents a voice-activated shortcut."""

    shortcut_id: str
    trigger_phrase: str
    command: str
    description: str
    enabled: bool = True
    usage_count: int = 0
    last_used: Optional[float] = None


class SpeechToTextEngine:
    """Base class for speech-to-text engines."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the speech-to-text engine."""
        self.config = config or {}
        self.is_listening = False
        self.language = self.config.get("language", "en-US")

    def start_listening(self, callback: Callable[[VoiceCommand], None]) -> bool:
        """Start listening for voice input.

        Args:
            callback: Function to call when voice command is recognized

        Returns:
            True if listening started successfully
        """
        raise NotImplementedError

    def stop_listening(self) -> bool:
        """Stop listening for voice input.

        Returns:
            True if stopped successfully
        """
        raise NotImplementedError

    def recognize_file(self, audio_file: str) -> Optional[VoiceCommand]:
        """Recognize speech from an audio file.

        Args:
            audio_file: Path to audio file

        Returns:
            Recognized voice command or None
        """
        raise NotImplementedError


class WhisperSTTEngine(SpeechToTextEngine):
    """OpenAI Whisper-based speech-to-text engine."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Whisper engine."""
        super().__init__(config)
        self.model_size = self.config.get("model_size", "base")
        self.device = self.config.get("device", "cpu")

        # Check if whisper is available
        try:
            import whisper

            self.whisper = whisper
            self.model = None
        except ImportError:
            raise ImportError(
                "whisper package not installed. Install with: pip install openai-whisper"
            )

    def _load_model(self):
        """Load the Whisper model if not already loaded."""
        if self.model is None:
            print(f"Loading Whisper model ({self.model_size})...")
            self.model = self.whisper.load_model(self.model_size, device=self.device)
            print("Whisper model loaded successfully")

    def start_listening(self, callback: Callable[[VoiceCommand], None]) -> bool:
        """Start continuous listening with Whisper."""
        # Note: Whisper doesn't support real-time streaming by default
        # This would require additional audio streaming setup
        self.is_listening = True
        # For now, return False as continuous listening isn't implemented
        return False

    def stop_listening(self) -> bool:
        """Stop listening."""
        self.is_listening = False
        return True

    def recognize_file(self, audio_file: str) -> Optional[VoiceCommand]:
        """Recognize speech from audio file using Whisper."""
        try:
            self._load_model()

            start_time = time.time()
            result = self.model.transcribe(audio_file, language=self.language.split("-")[0])

            duration = time.time() - start_time

            if result and result.get("text"):
                return VoiceCommand(
                    command_id=f"whisper_{int(time.time() * 1000)}",
                    text=result["text"].strip(),
                    confidence=result.get("confidence", 0.8),  # Whisper doesn't provide confidence
                    timestamp=time.time(),
                    language=self.language,
                    duration=duration,
                    audio_file=audio_file,
                )

        except Exception as e:
            print(f"Whisper recognition error: {e}")

        return None


class GoogleSTTEngine(SpeechToTextEngine):
    """Google Speech-to-Text engine."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Google STT engine."""
        super().__init__(config)
        self.api_key = self.config.get("api_key")

        try:
            from google.cloud import speech

            self.speech_client = speech.SpeechClient()
        except ImportError:
            raise ImportError("google-cloud-speech package not installed")

    def recognize_file(self, audio_file: str) -> Optional[VoiceCommand]:
        """Recognize speech using Google Speech-to-Text."""
        try:
            from google.cloud import speech

            with open(audio_file, "rb") as audio_file_obj:
                content = audio_file_obj.read()

            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=self.language,
            )

            start_time = time.time()
            response = self.speech_client.recognize(config=config, audio=audio)
            duration = time.time() - start_time

            if response.results:
                result = response.results[0]
                if result.alternatives:
                    alternative = result.alternatives[0]
                    return VoiceCommand(
                        command_id=f"google_{int(time.time() * 1000)}",
                        text=alternative.transcript,
                        confidence=alternative.confidence,
                        timestamp=time.time(),
                        language=self.language,
                        duration=duration,
                        audio_file=audio_file,
                    )

        except Exception as e:
            print(f"Google STT recognition error: {e}")

        return None


class VoskSTTEngine(SpeechToTextEngine):
    """Vosk offline speech-to-text engine."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Vosk engine."""
        super().__init__(config)
        self.model_path = self.config.get("model_path")

        try:
            from vosk import Model

            if not self.model_path or not os.path.exists(self.model_path):
                raise ValueError(f"Vosk model not found at: {self.model_path}")

            self.vosk_model = Model(self.model_path)
            self.recognizer = None

        except ImportError:
            raise ImportError("vosk package not installed")

    def recognize_file(self, audio_file: str) -> Optional[VoiceCommand]:
        """Recognize speech using Vosk."""
        try:
            import json
            import wave

            from vosk import KaldiRecognizer

            wf = wave.open(audio_file, "rb")
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                print("Audio file must be WAV format mono PCM.")
                return None

            self.recognizer = KaldiRecognizer(self.vosk_model, wf.getframerate())
            self.recognizer.SetWords(True)

            start_time = time.time()
            results = []

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if self.recognizer.AcceptWaveform(data):
                    results.append(json.loads(self.recognizer.Result()))

            results.append(json.loads(self.recognizer.FinalResult()))
            duration = time.time() - start_time

            # Combine results
            full_text = ""
            confidence = 0.0
            word_count = 0

            for result in results:
                if "result" in result:
                    for word in result["result"]:
                        full_text += word.get("word", "") + " "
                        confidence += word.get("conf", 0)
                        word_count += 1

            if word_count > 0:
                confidence /= word_count

            if full_text.strip():
                return VoiceCommand(
                    command_id=f"vosk_{int(time.time() * 1000)}",
                    text=full_text.strip(),
                    confidence=confidence,
                    timestamp=time.time(),
                    language=self.language,
                    duration=duration,
                    audio_file=audio_file,
                )

        except Exception as e:
            print(f"Vosk recognition error: {e}")

        return None


class VoiceCommandRecognizer:
    """Main voice command recognition system."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize voice command recognizer."""
        self.config = config or {}
        self.engines = {}
        self.active_engine = None
        self.shortcuts = {}
        self.command_queue = queue.Queue()
        self.is_active = False

        # Load available engines
        self._load_engines()

        # Load voice shortcuts
        self._load_shortcuts()

    def _load_engines(self):
        """Load available speech-to-text engines."""
        engines_config = self.config.get("engines", {})

        # Try to load Whisper (preferred for offline use)
        if engines_config.get("whisper", {}).get("enabled", True):
            try:
                self.engines["whisper"] = WhisperSTTEngine(engines_config.get("whisper", {}))
                if self.active_engine is None:
                    self.active_engine = "whisper"
            except Exception as e:
                print(f"Failed to load Whisper engine: {e}")

        # Try to load Google STT
        if engines_config.get("google", {}).get("enabled", False):
            try:
                self.engines["google"] = GoogleSTTEngine(engines_config.get("google", {}))
                if self.active_engine is None:
                    self.active_engine = "google"
            except Exception as e:
                print(f"Failed to load Google STT engine: {e}")

        # Try to load Vosk (offline)
        if engines_config.get("vosk", {}).get("enabled", False):
            try:
                self.engines["vosk"] = VoskSTTEngine(engines_config.get("vosk", {}))
                if self.active_engine is None:
                    self.active_engine = "vosk"
            except Exception as e:
                print(f"Failed to load Vosk engine: {e}")

        if not self.engines:
            print("Warning: No speech-to-text engines available. Voice commands will not work.")
            print(
                "Install optional dependencies: pip install openai-whisper google-cloud-speech vosk"
            )
            # Don't raise error, just continue with empty engines dict

    def _load_shortcuts(self):
        """Load voice shortcuts from configuration."""
        shortcuts_config = self.config.get("shortcuts", [])

        for shortcut_config in shortcuts_config:
            shortcut = VoiceShortcut(**shortcut_config)
            self.shortcuts[shortcut.trigger_phrase.lower()] = shortcut

    def start_voice_recognition(self) -> bool:
        """Start voice command recognition.

        Returns:
            True if started successfully
        """
        if not self.active_engine or self.active_engine not in self.engines:
            return False

        self.is_active = True

        # Start background processing thread
        self.processing_thread = threading.Thread(target=self._process_commands, daemon=True)
        self.processing_thread.start()

        return True

    def stop_voice_recognition(self) -> bool:
        """Stop voice command recognition.

        Returns:
            True if stopped successfully
        """
        self.is_active = False
        return True

    def recognize_from_file(self, audio_file: str) -> Optional[VoiceCommand]:
        """Recognize voice command from audio file.

        Args:
            audio_file: Path to audio file

        Returns:
            Recognized voice command or None
        """
        if not self.active_engine or self.active_engine not in self.engines:
            return None

        engine = self.engines[self.active_engine]
        return engine.recognize_file(audio_file)

    def process_voice_command(self, voice_command: VoiceCommand) -> Dict[str, Any]:
        """Process a recognized voice command.

        Args:
            voice_command: The recognized voice command

        Returns:
            Processing result
        """
        result = {
            "command_id": voice_command.command_id,
            "original_text": voice_command.text,
            "processed": False,
            "action": None,
            "confidence": voice_command.confidence,
            "shortcut_used": None,
        }

        # Check for voice shortcuts first
        text_lower = voice_command.text.lower().strip()

        for trigger_phrase, shortcut in self.shortcuts.items():
            if shortcut.enabled and trigger_phrase in text_lower:
                result["processed"] = True
                result["action"] = "shortcut"
                result["shortcut_used"] = shortcut.shortcut_id
                result["command"] = shortcut.command

                # Update shortcut usage
                shortcut.usage_count += 1
                shortcut.last_used = time.time()

                break

        # If no shortcut matched, treat as natural language command
        if not result["processed"]:
            result["action"] = "natural_language"
            result["command"] = voice_command.text

        return result

    def add_shortcut(self, shortcut: VoiceShortcut) -> bool:
        """Add a new voice shortcut.

        Args:
            shortcut: The shortcut to add

        Returns:
            True if added successfully
        """
        self.shortcuts[shortcut.trigger_phrase.lower()] = shortcut
        self._save_shortcuts()
        return True

    def remove_shortcut(self, shortcut_id: str) -> bool:
        """Remove a voice shortcut.

        Args:
            shortcut_id: The shortcut ID to remove

        Returns:
            True if removed successfully
        """
        for trigger_phrase, shortcut in list(self.shortcuts.items()):
            if shortcut.shortcut_id == shortcut_id:
                del self.shortcuts[trigger_phrase]
                self._save_shortcuts()
                return True
        return False

    def get_shortcuts(self) -> List[VoiceShortcut]:
        """Get all voice shortcuts.

        Returns:
            List of voice shortcuts
        """
        return list(self.shortcuts.values())

    def _process_commands(self):
        """Background thread for processing voice commands."""
        while self.is_active:
            try:
                # Check for new commands in queue
                if not self.command_queue.empty():
                    voice_command = self.command_queue.get(timeout=1)
                    result = self.process_voice_command(voice_command)
                    # Here you would typically send the result to Isaac's command processor
                    print(f"Processed voice command: {result}")
                else:
                    time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing voice command: {e}")

    def _save_shortcuts(self):
        """Save shortcuts to configuration file."""
        try:
            config_path = Path.home() / ".isaac" / "voice_shortcuts.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)

            shortcuts_data = [asdict(shortcut) for shortcut in self.shortcuts.values()]

            with open(config_path, "w") as f:
                json.dump(shortcuts_data, f, indent=2)

        except Exception as e:
            print(f"Error saving voice shortcuts: {e}")

    def get_available_engines(self) -> List[str]:
        """Get list of available speech-to-text engines.

        Returns:
            List of engine names
        """
        return list(self.engines.keys())

    def set_active_engine(self, engine_name: str) -> bool:
        """Set the active speech-to-text engine.

        Args:
            engine_name: Name of the engine to activate

        Returns:
            True if set successfully
        """
        if engine_name in self.engines:
            self.active_engine = engine_name
            return True
        return False

    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about available engines.

        Returns:
            Engine information
        """
        return {
            "active_engine": self.active_engine,
            "available_engines": list(self.engines.keys()),
            "engine_details": {
                name: {
                    "type": type(engine).__name__,
                    "language": getattr(engine, "language", "unknown"),
                }
                for name, engine in self.engines.items()
            },
        }
