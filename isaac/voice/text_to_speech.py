"""
Text-to-Speech - Convert text responses to speech
Isaac's voice output system for audio feedback
"""

import os
import platform
import queue
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class SpeechRequest:
    """Represents a text-to-speech request."""

    request_id: str
    text: str
    voice: str
    speed: float
    priority: int  # 0=low, 1=normal, 2=high
    timestamp: float
    callback: Optional[Callable] = None


@dataclass
class SpeechResult:
    """Result of a text-to-speech operation."""

    request_id: str
    success: bool
    audio_file: Optional[str]
    duration: float
    error: Optional[str]


class TTSEngine:
    """Base class for text-to-speech engines."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the TTS engine."""
        self.config = config or {}
        self.language = self.config.get("language", "en")
        self.voice = self.config.get("voice", "default")

    def speak(self, text: str, voice: str = None, speed: float = 1.0) -> Optional[str]:
        """Convert text to speech and return audio file path.

        Args:
            text: Text to speak
            voice: Voice to use (optional)
            speed: Speech speed multiplier

        Returns:
            Path to generated audio file or None if failed
        """
        raise NotImplementedError

    def get_available_voices(self) -> List[str]:
        """Get list of available voices.

        Returns:
            List of voice names
        """
        raise NotImplementedError


class PyTTSx3Engine(TTSEngine):
    """pyttsx3-based text-to-speech engine (offline)."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize pyttsx3 engine."""
        super().__init__(config)

        try:
            import pyttsx3

            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", int(200 * self.config.get("speed", 1.0)))
            self.engine.setProperty("volume", self.config.get("volume", 0.8))
        except ImportError:
            raise ImportError("pyttsx3 package not installed. Install with: pip install pyttsx3")

    def speak(self, text: str, voice: str = None, speed: float = 1.0) -> Optional[str]:
        """Convert text to speech using pyttsx3."""
        try:
            # Set voice if specified
            if voice:
                voices = self.engine.getProperty("voices")
                for v in voices:
                    if voice.lower() in v.name.lower():
                        self.engine.setProperty("voice", v.id)
                        break

            # Set speed
            self.engine.setProperty("rate", int(200 * speed))

            # Generate speech
            self.engine.say(text)
            self.engine.runAndWait()

            # pyttsx3 speaks directly, no file generated
            return None

        except Exception as e:
            print(f"pyttsx3 TTS error: {e}")
            return None

    def get_available_voices(self) -> List[str]:
        """Get available voices."""
        try:
            voices = self.engine.getProperty("voices")
            return [voice.name for voice in voices]
        except:
            return []


class GTTSEngine(TTSEngine):
    """Google Text-to-Speech engine."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Google TTS engine."""
        super().__init__(config)

        try:
            from gtts import gTTS

            self.gtts = gTTS
        except ImportError:
            raise ImportError("gtts package not installed. Install with: pip install gtts")

    def speak(self, text: str, voice: str = None, speed: float = 1.0) -> Optional[str]:
        """Convert text to speech using Google TTS."""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_file.close()

            # Generate speech
            tts = self.gtts(text=text, lang=self.language, slow=(speed < 1.0))
            tts.save(temp_file.name)

            return temp_file.name

        except Exception as e:
            print(f"Google TTS error: {e}")
            return None

    def get_available_voices(self) -> List[str]:
        """Google TTS supports many languages but not specific voices."""
        return [f"{self.language}_default"]


class ElevenLabsEngine(TTSEngine):
    """ElevenLabs text-to-speech engine."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize ElevenLabs engine."""
        super().__init__(config)
        self.api_key = self.config.get("api_key")
        self.voice_id = self.config.get("voice_id", "21m00Tcm4TlvDq8ikWAM")  # Default voice

        if not self.api_key:
            raise ValueError("ElevenLabs API key required")

        try:
            import requests

            self.requests = requests
        except ImportError:
            raise ImportError("requests package not installed")

    def speak(self, text: str, voice: str = None, speed: float = 1.0) -> Optional[str]:
        """Convert text to speech using ElevenLabs."""
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key,
            }

            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
            }

            response = self.requests.post(url, json=data, headers=headers)

            if response.status_code == 200:
                # Save audio to temporary file
                temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                temp_file.write(response.content)
                temp_file.close()
                return temp_file.name
            else:
                print(f"ElevenLabs API error: {response.status_code}")
                return None

        except Exception as e:
            print(f"ElevenLabs TTS error: {e}")
            return None

    def get_available_voices(self) -> List[str]:
        """Get available ElevenLabs voices."""
        # This would require an API call to get available voices
        return [self.voice_id]


class SystemTTSEngine(TTSEngine):
    """System text-to-speech using platform-specific commands."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize system TTS engine."""
        super().__init__(config)
        self.system = platform.system().lower()

    def speak(self, text: str, voice: str = None, speed: float = 1.0) -> Optional[str]:
        """Use system TTS commands."""
        try:
            if self.system == "darwin":  # macOS
                cmd = ["say", text]
                if voice:
                    cmd.extend(["-v", voice])
                if speed != 1.0:
                    cmd.extend(["-r", str(int(200 * speed))])
                subprocess.run(cmd, check=True)

            elif self.system == "linux":
                # Try espeak
                cmd = ["espeak", text]
                if voice:
                    cmd.extend(["-v", voice])
                if speed != 1.0:
                    cmd.extend(["-s", str(int(160 * speed))])
                subprocess.run(cmd, check=True)

            elif self.system == "windows":
                # Use PowerShell's speech synthesizer
                ps_cmd = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak("{text}")'
                subprocess.run(["powershell", "-Command", ps_cmd], check=True)

            return None  # System TTS speaks directly

        except subprocess.CalledProcessError as e:
            print(f"System TTS error: {e}")
            return None
        except FileNotFoundError:
            print(f"System TTS not available on {self.system}")
            return None

    def get_available_voices(self) -> List[str]:
        """Get system voices (simplified)."""
        if self.system == "darwin":
            try:
                result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
                voices = []
                for line in result.stdout.split("\n"):
                    if line.strip():
                        voices.append(line.split()[0])
                return voices
            except:
                return ["default"]
        elif self.system == "linux":
            return ["default"]  # espeak has limited voice info
        elif self.system == "windows":
            return ["default"]  # Windows TTS has default voice
        else:
            return []


class TextToSpeechManager:
    """Manages text-to-speech operations with multiple engines."""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize TTS manager."""
        self.config = config or {}
        self.engines = {}
        self.active_engine = None
        self.speech_queue = queue.Queue()
        self.is_active = False
        self.audio_player = None

        # Load available engines
        self._load_engines()

        # Start speech processing thread
        self.processing_thread = threading.Thread(target=self._process_speech_queue, daemon=True)
        self.processing_thread.start()

    def _load_engines(self):
        """Load available TTS engines."""
        engines_config = self.config.get("engines", {})

        # Try to load pyttsx3 (offline, preferred)
        if engines_config.get("pyttsx3", {}).get("enabled", True):
            try:
                self.engines["pyttsx3"] = PyTTSx3Engine(engines_config.get("pyttsx3", {}))
                if self.active_engine is None:
                    self.active_engine = "pyttsx3"
            except Exception as e:
                print(f"Failed to load pyttsx3 engine: {e}")

        # Try to load Google TTS
        if engines_config.get("google", {}).get("enabled", True):
            try:
                self.engines["google"] = GTTSEngine(engines_config.get("google", {}))
                if self.active_engine is None:
                    self.active_engine = "google"
            except Exception as e:
                print(f"Failed to load Google TTS engine: {e}")

        # Try to load ElevenLabs
        if engines_config.get("elevenlabs", {}).get("enabled", False):
            try:
                self.engines["elevenlabs"] = ElevenLabsEngine(engines_config.get("elevenlabs", {}))
                if self.active_engine is None:
                    self.active_engine = "elevenlabs"
            except Exception as e:
                print(f"Failed to load ElevenLabs engine: {e}")

        # Try to load system TTS
        if engines_config.get("system", {}).get("enabled", True):
            try:
                self.engines["system"] = SystemTTSEngine(engines_config.get("system", {}))
                if self.active_engine is None:
                    self.active_engine = "system"
            except Exception as e:
                print(f"Failed to load system TTS engine: {e}")

        if not self.engines:
            print("Warning: No text-to-speech engines available. Voice responses will not work.")
            print("Install optional dependencies: pip install pyttsx3 gtts requests")
            # Don't raise error, just continue with empty engines dict

    def speak_text(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        priority: int = 1,
        callback: Optional[Callable] = None,
    ) -> str:
        """Queue text for speech synthesis.

        Args:
            text: Text to speak
            voice: Voice to use
            speed: Speech speed
            priority: Priority (0=low, 1=normal, 2=high)
            callback: Callback function when speech is complete

        Returns:
            Request ID
        """
        request_id = f"tts_{int(time.time() * 1000)}"

        request = SpeechRequest(
            request_id=request_id,
            text=text,
            voice=voice or self.config.get("default_voice", "default"),
            speed=speed,
            priority=priority,
            timestamp=time.time(),
            callback=callback,
        )

        self.speech_queue.put(request)
        return request_id

    def speak_immediately(self, text: str, voice: Optional[str] = None, speed: float = 1.0) -> bool:
        """Speak text immediately (blocking).

        Args:
            text: Text to speak
            voice: Voice to use
            speed: Speech speed

        Returns:
            True if successful
        """
        if not self.active_engine or self.active_engine not in self.engines:
            return False

        engine = self.engines[self.active_engine]
        audio_file = engine.speak(text, voice, speed)

        if audio_file:
            # Play the audio file
            self._play_audio_file(audio_file)
            # Clean up temp file
            try:
                os.unlink(audio_file)
            except:
                pass
            return True
        else:
            # Engine speaks directly (no file)
            return True

    def _process_speech_queue(self):
        """Background thread for processing speech requests."""
        while True:
            try:
                # Get next speech request
                request = self.speech_queue.get(timeout=1)

                # Process the request
                result = self._process_speech_request(request)

                # Call callback if provided
                if request.callback:
                    try:
                        request.callback(result)
                    except Exception as e:
                        print(f"Error in speech callback: {e}")

                self.speech_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing speech request: {e}")

    def _process_speech_request(self, request: SpeechRequest) -> SpeechResult:
        """Process a single speech request."""
        start_time = time.time()

        try:
            if not self.active_engine or self.active_engine not in self.engines:
                return SpeechResult(
                    request_id=request.request_id,
                    success=False,
                    audio_file=None,
                    duration=time.time() - start_time,
                    error="No active TTS engine",
                )

            engine = self.engines[self.active_engine]
            audio_file = engine.speak(request.text, request.voice, request.speed)

            if audio_file:
                # Play the audio file
                self._play_audio_file(audio_file)
                # Clean up temp file after a delay
                threading.Timer(5.0, lambda: self._cleanup_audio_file(audio_file)).start()

            return SpeechResult(
                request_id=request.request_id,
                success=True,
                audio_file=audio_file,
                duration=time.time() - start_time,
                error=None,
            )

        except Exception as e:
            return SpeechResult(
                request_id=request.request_id,
                success=False,
                audio_file=None,
                duration=time.time() - start_time,
                error=str(e),
            )

    def _play_audio_file(self, audio_file: str):
        """Play an audio file using system audio player."""
        try:
            system = platform.system().lower()

            if system == "darwin":  # macOS
                subprocess.run(["afplay", audio_file], check=True)
            elif system == "linux":
                subprocess.run(["mpg123", audio_file], check=True)
            elif system == "windows":
                # Use PowerShell to play audio
                ps_cmd = f'(New-Object Media.SoundPlayer "{audio_file}").PlaySync()'
                subprocess.run(["powershell", "-Command", ps_cmd], check=True)
            else:
                print(f"Audio playback not supported on {system}")

        except subprocess.CalledProcessError as e:
            print(f"Error playing audio file: {e}")
        except Exception as e:
            print(f"Unexpected error playing audio: {e}")

    def _cleanup_audio_file(self, audio_file: str):
        """Clean up temporary audio file."""
        try:
            if os.path.exists(audio_file):
                os.unlink(audio_file)
        except Exception as e:
            print(f"Error cleaning up audio file {audio_file}: {e}")

    def get_available_engines(self) -> List[str]:
        """Get list of available TTS engines."""
        return list(self.engines.keys())

    def set_active_engine(self, engine_name: str) -> bool:
        """Set the active TTS engine."""
        if engine_name in self.engines:
            self.active_engine = engine_name
            return True
        return False

    def get_available_voices(self, engine_name: Optional[str] = None) -> List[str]:
        """Get available voices for an engine."""
        engine_name = engine_name or self.active_engine
        if engine_name and engine_name in self.engines:
            return self.engines[engine_name].get_available_voices()
        return []

    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about TTS engines."""
        return {
            "active_engine": self.active_engine,
            "available_engines": list(self.engines.keys()),
            "engine_details": {
                name: {
                    "type": type(engine).__name__,
                    "voices": engine.get_available_voices()[:5],  # First 5 voices
                }
                for name, engine in self.engines.items()
            },
        }

    def stop(self):
        """Stop the TTS manager."""
        self.is_active = False
        # Clear any remaining requests
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
                self.speech_queue.task_done()
            except:
                break
