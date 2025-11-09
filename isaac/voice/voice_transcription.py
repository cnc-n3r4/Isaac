"""
Voice Transcription - Convert audio recordings to text
Isaac's system for transcribing meetings, notes, and voice memos
"""

import os
import time
import threading
import json
import queue
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
import tempfile
import subprocess
try:
    import wave
    import audioop
except ImportError:
    wave = None
    audioop = None


@dataclass
class TranscriptionRequest:
    """Represents a transcription request."""
    request_id: str
    audio_file: str
    language: str
    model: str
    options: Dict[str, Any]
    timestamp: float
    callback: Optional[Callable] = None


@dataclass
class TranscriptionSegment:
    """Represents a segment of transcribed text."""
    start_time: float
    end_time: float
    text: str
    confidence: float
    speaker: Optional[str] = None


@dataclass
class TranscriptionResult:
    """Complete transcription result."""
    request_id: str
    success: bool
    full_text: str
    segments: List[TranscriptionSegment]
    language: str
    duration: float
    processing_time: float
    metadata: Dict[str, Any]
    error: Optional[str] = None


class AudioPreprocessor:
    """Preprocesses audio files for better transcription."""

    def __init__(self):
        """Initialize audio preprocessor."""
        self.supported_formats = ['wav', 'mp3', 'm4a', 'flac', 'ogg']

    def preprocess_audio(self, input_file: str, output_file: Optional[str] = None) -> Optional[str]:
        """Preprocess audio file for optimal transcription.

        Args:
            input_file: Input audio file path
            output_file: Output file path (optional)

        Returns:
            Path to processed audio file or None if failed
        """
        if not output_file:
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            output_file = temp_file.name
            temp_file.close()

        try:
            # Convert to WAV format with optimal settings for speech recognition
            # 16kHz, mono, 16-bit PCM
            self._convert_to_optimal_format(input_file, output_file)
            return output_file

        except Exception as e:
            print(f"Audio preprocessing failed: {e}")
            return None

    def _convert_to_optimal_format(self, input_file: str, output_file: str):
        """Convert audio to optimal format for transcription."""
        try:
            # Use ffmpeg for conversion
            cmd = [
                'ffmpeg', '-i', input_file,
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', '16000',         # 16kHz sample rate
                '-ac', '1',             # Mono
                '-y',                   # Overwrite output
                output_file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                raise Exception(f"ffmpeg conversion failed: {result.stderr}")

        except FileNotFoundError:
            # Fallback: try to use pydub if available
            try:
                from pydub import AudioSegment

                audio = AudioSegment.from_file(input_file)
                audio = audio.set_channels(1)  # Mono
                audio = audio.set_frame_rate(16000)  # 16kHz
                audio.export(output_file, format='wav')

            except ImportError:
                raise Exception("ffmpeg not found and pydub not available for audio conversion")

    def get_audio_info(self, audio_file: str) -> Dict[str, Any]:
        """Get information about an audio file.

        Args:
            audio_file: Path to audio file

        Returns:
            Audio file information
        """
        try:
            # Use ffprobe to get audio info
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', audio_file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                data = json.loads(result.stdout)
                return self._parse_audio_info(data)
            else:
                # Fallback for WAV files
                if audio_file.lower().endswith('.wav'):
                    return self._get_wav_info(audio_file)

        except Exception as e:
            print(f"Error getting audio info: {e}")

        return {}

    def _parse_audio_info(self, ffprobe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse ffprobe output."""
        info = {}

        if 'format' in ffprobe_data:
            fmt = ffprobe_data['format']
            info['duration'] = float(fmt.get('duration', 0))
            info['size'] = int(fmt.get('size', 0))
            info['bit_rate'] = int(fmt.get('bit_rate', 0))

        if 'streams' in ffprobe_data:
            for stream in ffprobe_data['streams']:
                if stream.get('codec_type') == 'audio':
                    info['codec'] = stream.get('codec_name', 'unknown')
                    info['sample_rate'] = int(stream.get('sample_rate', 0))
                    info['channels'] = int(stream.get('channels', 0))
                    info['bit_depth'] = int(stream.get('bits_per_sample', 0))
                    break

        return info

    def _get_wav_info(self, wav_file: str) -> Dict[str, Any]:
        """Get WAV file information."""
        try:
            with wave.open(wav_file, 'rb') as wf:
                return {
                    'duration': wf.getnframes() / wf.getframerate(),
                    'size': os.path.getsize(wav_file),
                    'codec': 'pcm',
                    'sample_rate': wf.getframerate(),
                    'channels': wf.getnchannels(),
                    'bit_depth': wf.getsampwidth() * 8
                }
        except:
            return {}


class TranscriptionEngine:
    """Base class for transcription engines."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize transcription engine."""
        self.config = config or {}
        self.language = self.config.get('language', 'en-US')

    def transcribe(self, audio_file: str, **kwargs) -> Optional[TranscriptionResult]:
        """Transcribe audio file to text.

        Args:
            audio_file: Path to audio file
            **kwargs: Additional options

        Returns:
            Transcription result or None if failed
        """
        raise NotImplementedError


class WhisperTranscriptionEngine(TranscriptionEngine):
    """OpenAI Whisper-based transcription engine."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Whisper engine."""
        super().__init__(config)
        self.model_size = self.config.get('model_size', 'base')

        try:
            import whisper
            self.whisper = whisper
            self.model = None
        except ImportError:
            raise ImportError("whisper package not installed. Install with: pip install openai-whisper")

    def _load_model(self):
        """Load Whisper model if not already loaded."""
        if self.model is None:
            print(f"Loading Whisper model ({self.model_size})...")
            self.model = self.whisper.load_model(self.model_size)
            print("Whisper model loaded successfully")

    def transcribe(self, audio_file: str, **kwargs) -> Optional[TranscriptionResult]:
        """Transcribe using Whisper."""
        try:
            self._load_model()

            start_time = time.time()

            # Transcribe with segments
            result = self.model.transcribe(
                audio_file,
                language=self.language.split('-')[0],
                verbose=True,
                **kwargs
            )

            processing_time = time.time() - start_time

            # Extract segments
            segments = []
            for segment_data in result.get('segments', []):
                segment = TranscriptionSegment(
                    start_time=segment_data['start'],
                    end_time=segment_data['end'],
                    text=segment_data['text'].strip(),
                    confidence=segment_data.get('confidence', 0.8)
                )
                segments.append(segment)

            # Create full text
            full_text = result.get('text', '').strip()

            return TranscriptionResult(
                request_id=f"whisper_{int(time.time() * 1000)}",
                success=True,
                full_text=full_text,
                segments=segments,
                language=self.language,
                duration=result.get('duration', 0),
                processing_time=processing_time,
                metadata={
                    'model': self.model_size,
                    'engine': 'whisper'
                }
            )

        except Exception as e:
            return TranscriptionResult(
                request_id=f"whisper_{int(time.time() * 1000)}",
                success=False,
                full_text="",
                segments=[],
                language=self.language,
                duration=0,
                processing_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )


class GoogleTranscriptionEngine(TranscriptionEngine):
    """Google Speech-to-Text transcription engine."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Google engine."""
        super().__init__(config)
        self.api_key = self.config.get('api_key')

        try:
            from google.cloud import speech
            self.speech_client = speech.SpeechClient()
        except ImportError:
            raise ImportError("google-cloud-speech package not installed")

    def transcribe(self, audio_file: str, **kwargs) -> Optional[TranscriptionResult]:
        """Transcribe using Google Speech-to-Text."""
        try:
            start_time = time.time()

            with open(audio_file, 'rb') as audio_file_obj:
                content = audio_file_obj.read()

            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=self.language,
                enable_word_time_offsets=True,
                enable_automatic_punctuation=True,
            )

            response = self.speech_client.recognize(config=config, audio=audio)
            processing_time = time.time() - start_time

            segments = []
            full_text = ""

            for result in response.results:
                alternative = result.alternatives[0]
                full_text += alternative.transcript + " "

                # Extract word-level timing if available
                if alternative.words:
                    for word_info in alternative.words:
                        segment = TranscriptionSegment(
                            start_time=word_info.start_time.total_seconds(),
                            end_time=word_info.end_time.total_seconds(),
                            text=word_info.word,
                            confidence=0.9  # Google doesn't provide word-level confidence easily
                        )
                        segments.append(segment)
                else:
                    # Create a single segment for the whole result
                    segment = TranscriptionSegment(
                        start_time=0,
                        end_time=result.result_end_time.total_seconds() if result.result_end_time else 0,
                        text=alternative.transcript,
                        confidence=alternative.confidence
                    )
                    segments.append(segment)

            return TranscriptionResult(
                request_id=f"google_{int(time.time() * 1000)}",
                success=True,
                full_text=full_text.strip(),
                segments=segments,
                language=self.language,
                duration=max([s.end_time for s in segments]) if segments else 0,
                processing_time=processing_time,
                metadata={
                    'engine': 'google',
                    'api_used': True
                }
            )

        except Exception as e:
            return TranscriptionResult(
                request_id=f"google_{int(time.time() * 1000)}",
                success=False,
                full_text="",
                segments=[],
                language=self.language,
                duration=0,
                processing_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )


class VoiceTranscriptionManager:
    """Manages voice transcription operations."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize transcription manager."""
        self.config = config or {}
        self.engines = {}
        self.active_engine = None
        self.preprocessor = AudioPreprocessor()
        self.transcription_queue = queue.Queue()
        self.is_active = False

        # Load available engines
        self._load_engines()

        # Start transcription processing thread
        self.processing_thread = threading.Thread(target=self._process_transcription_queue, daemon=True)
        self.processing_thread.start()

    def _load_engines(self):
        """Load available transcription engines."""
        engines_config = self.config.get('engines', {})

        # Try to load Whisper (preferred for offline use)
        if engines_config.get('whisper', {}).get('enabled', True):
            try:
                self.engines['whisper'] = WhisperTranscriptionEngine(engines_config.get('whisper', {}))
                if self.active_engine is None:
                    self.active_engine = 'whisper'
            except Exception as e:
                print(f"Failed to load Whisper engine: {e}")

        # Try to load Google STT
        if engines_config.get('google', {}).get('enabled', False):
            try:
                self.engines['google'] = GoogleTranscriptionEngine(engines_config.get('google', {}))
                if self.active_engine is None:
                    self.active_engine = 'google'
            except Exception as e:
                print(f"Failed to load Google STT engine: {e}")

        if not self.engines:
            print("Warning: No transcription engines available. Voice transcription will not work.")
            print("Install optional dependencies: pip install openai-whisper google-cloud-speech")
            # Don't raise error, just continue with empty engines dict

    def transcribe_audio(self, audio_file: str, language: Optional[str] = None, model: Optional[str] = None,
                        callback: Optional[Callable] = None, **options) -> str:
        """Queue audio file for transcription.

        Args:
            audio_file: Path to audio file
            language: Language code (optional)
            model: Model to use (optional)
            callback: Callback function when transcription is complete
            **options: Additional transcription options

        Returns:
            Request ID
        """
        request_id = f"transcribe_{int(time.time() * 1000)}"

        request = TranscriptionRequest(
            request_id=request_id,
            audio_file=audio_file,
            language=language or self.config.get('default_language', 'en-US'),
            model=model or 'default',
            options=options,
            timestamp=time.time(),
            callback=callback
        )

        self.transcription_queue.put(request)
        return request_id

    def transcribe_immediately(self, audio_file: str, language: Optional[str] = None,
                             model: Optional[str] = None, **options) -> Optional[TranscriptionResult]:
        """Transcribe audio file immediately (blocking).

        Args:
            audio_file: Path to audio file
            language: Language code
            model: Model to use
            **options: Additional options

        Returns:
            Transcription result or None if failed
        """
        if not self.active_engine or self.active_engine not in self.engines:
            return None

        try:
            # Preprocess audio if needed
            processed_file = self.preprocessor.preprocess_audio(audio_file)
            if not processed_file:
                processed_file = audio_file

            # Get audio info
            audio_info = self.preprocessor.get_audio_info(processed_file)

            # Transcribe
            engine = self.engines[self.active_engine]
            result = engine.transcribe(processed_file, **options)

            if result:
                result.metadata.update({
                    'original_file': audio_file,
                    'processed_file': processed_file,
                    'audio_info': audio_info
                })

            # Clean up processed file if different from original
            if processed_file != audio_file:
                try:
                    os.unlink(processed_file)
                except:
                    pass

            return result

        except Exception as e:
            return TranscriptionResult(
                request_id=f"error_{int(time.time() * 1000)}",
                success=False,
                full_text="",
                segments=[],
                language=language or 'en-US',
                duration=0,
                processing_time=0,
                metadata={},
                error=str(e)
            )

    def _process_transcription_queue(self):
        """Background thread for processing transcription requests."""
        while True:
            try:
                # Get next transcription request
                request = self.transcription_queue.get(timeout=1)

                # Process the request
                result = self.transcribe_immediately(
                    request.audio_file,
                    request.language,
                    request.model,
                    **request.options
                )

                # Call callback if provided
                if request.callback and result:
                    try:
                        request.callback(result)
                    except Exception as e:
                        print(f"Error in transcription callback: {e}")

                self.transcription_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing transcription request: {e}")

    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats."""
        return self.preprocessor.supported_formats

    def get_available_engines(self) -> List[str]:
        """Get list of available transcription engines."""
        return list(self.engines.keys())

    def set_active_engine(self, engine_name: str) -> bool:
        """Set the active transcription engine."""
        if engine_name in self.engines:
            self.active_engine = engine_name
            return True
        return False

    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about transcription engines."""
        return {
            'active_engine': self.active_engine,
            'available_engines': list(self.engines.keys()),
            'supported_formats': self.get_supported_formats(),
            'engine_details': {
                name: {
                    'type': type(engine).__name__,
                    'language': getattr(engine, 'language', 'unknown')
                }
                for name, engine in self.engines.items()
            }
        }

    def batch_transcribe(self, audio_files: List[str], **options) -> List[TranscriptionResult]:
        """Transcribe multiple audio files.

        Args:
            audio_files: List of audio file paths
            **options: Transcription options

        Returns:
            List of transcription results
        """
        results = []

        for audio_file in audio_files:
            result = self.transcribe_immediately(audio_file, **options)
            if result:
                results.append(result)

        return results

    def save_transcription(self, result: TranscriptionResult, output_file: str,
                          format: str = 'txt') -> bool:
        """Save transcription result to file.

        Args:
            result: Transcription result
            output_file: Output file path
            format: Output format ('txt', 'json', 'srt')

        Returns:
            True if successful
        """
        try:
            if format == 'txt':
                with open(output_file, 'w') as f:
                    f.write(f"Transcription Results\n")
                    f.write(f"Language: {result.language}\n")
                    f.write(f"Duration: {result.duration:.2f}s\n")
                    f.write(f"Processing Time: {result.processing_time:.2f}s\n\n")
                    f.write(result.full_text)

            elif format == 'json':
                with open(output_file, 'w') as f:
                    json.dump(asdict(result), f, indent=2)

            elif format == 'srt':
                with open(output_file, 'w') as f:
                    for i, segment in enumerate(result.segments, 1):
                        start_time = self._format_srt_time(segment.start_time)
                        end_time = self._format_srt_time(segment.end_time)
                        f.write(f"{i}\n")
                        f.write(f"{start_time} --> {end_time}\n")
                        f.write(f"{segment.text}\n\n")

            return True

        except Exception as e:
            print(f"Error saving transcription: {e}")
            return False

    def _format_srt_time(self, seconds: float) -> str:
        """Format time for SRT subtitle format."""
        int(seconds // 3600)
        int((seconds % 3600) // 60)
        int(seconds % 60)
        int((seconds % 1) * 1000)
        return "02d"

    def stop(self):
        """Stop the transcription manager."""
        self.is_active = False
        # Clear any remaining requests
        while not self.transcription_queue.empty():
            try:
                self.transcription_queue.get_nowait()
                self.transcription_queue.task_done()
            except:
                break