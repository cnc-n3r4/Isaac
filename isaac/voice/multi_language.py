"""
Multi-Language Support for Voice Systems
Isaac's internationalization system for voice commands and responses
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LanguageConfig:
    """Configuration for a language."""
    code: str
    name: str
    native_name: str
    voice_commands: Dict[str, List[str]] = field(default_factory=dict)
    responses: Dict[str, str] = field(default_factory=dict)
    tts_voice: Optional[str] = None
    stt_model: Optional[str] = None
    text_direction: str = "ltr"  # ltr or rtl
    enabled: bool = True


@dataclass
class TranslationRequest:
    """Represents a translation request."""
    text: str
    from_lang: str
    to_lang: str
    context: str = "general"  # general, command, response, error
    timestamp: float = field(default_factory=time.time)


@dataclass
class TranslationResult:
    """Result of a translation operation."""
    original_text: str
    translated_text: str
    from_lang: str
    to_lang: str
    confidence: float
    detected_lang: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)


class LanguageDetector:
    """Detects the language of input text."""

    def __init__(self):
        """Initialize language detector."""
        self.models = {}
        self._load_models()

    def _load_models(self):
        """Load language detection models."""
        try:
            # Try to load langdetect
            import langdetect
            self.models['langdetect'] = langdetect
        except ImportError:
            pass

        try:
            # Try to load fasttext
            import fasttext
            # Load pre-trained language identification model
            try:
                self.models['fasttext'] = fasttext.load_model('lid.176.bin')
            except:
                pass
        except ImportError:
            pass

    def detect_language(self, text: str) -> Optional[str]:
        """Detect the language of the given text.

        Args:
            text: Input text

        Returns:
            Language code or None if detection failed
        """
        if not text or not text.strip():
            return None

        # Try langdetect first (most accurate)
        if 'langdetect' in self.models:
            try:
                from langdetect import detect
                detected = detect(text)
                return self._normalize_lang_code(detected)
            except:
                pass

        # Try fasttext as fallback
        if 'fasttext' in self.models:
            try:
                predictions = self.models['fasttext'].predict(text.replace('\n', ' '), k=1)
                if predictions and len(predictions) > 0:
                    lang_code = predictions[0][0].replace('__label__', '')
                    return self._normalize_lang_code(lang_code)
            except:
                pass

        # Simple rule-based detection as last resort
        return self._rule_based_detection(text)

    def _normalize_lang_code(self, code: str) -> str:
        """Normalize language code to standard format."""
        # Convert common variations
        code = code.lower()
        mappings = {
            'zh-cn': 'zh-CN',
            'zh-tw': 'zh-TW',
            'zh': 'zh-CN',
            'en': 'en-US',
            'es': 'es-ES',
            'fr': 'fr-FR',
            'de': 'de-DE',
            'it': 'it-IT',
            'pt': 'pt-BR',
            'ja': 'ja-JP',
            'ko': 'ko-KR',
            'ru': 'ru-RU',
            'ar': 'ar-SA',
            'hi': 'hi-IN'
        }
        return mappings.get(code, code)

    def _rule_based_detection(self, text: str) -> Optional[str]:
        """Simple rule-based language detection."""
        text = text.lower()

        # Spanish indicators
        if any(word in text for word in ['el', 'la', 'los', 'las', 'es', 'son', 'está', 'muy']):
            return 'es-ES'

        # French indicators
        if any(word in text for word in ['le', 'la', 'les', 'et', 'est', 'sont', 'très']):
            return 'fr-FR'

        # German indicators
        if any(word in text for word in ['der', 'die', 'das', 'ist', 'sind', 'und', 'sehr']):
            return 'de-DE'

        # Default to English
        return 'en-US'


class Translator:
    """Handles text translation between languages."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize translator."""
        self.config = config or {}
        self.cache = {}
        self.cache_file = Path.home() / '.isaac' / 'translation_cache.json'
        self._load_cache()

        # Initialize translation services
        self.services = {}
        self._load_services()

    def _load_services(self):
        """Load available translation services."""
        # Try Google Translate
        try:
            from googletrans import Translator as GoogleTranslator
            self.services['google'] = GoogleTranslator()
        except ImportError:
            pass

        # Try DeepL
        try:
            import deepl
            api_key = self.config.get('deepl_api_key')
            if api_key:
                self.services['deepl'] = deepl.Translator(api_key)
        except ImportError:
            pass

        # Try Microsoft Translator
        try:
            from azure.ai.translation.text import TextTranslationClient
            from azure.core.credentials import AzureKeyCredential
            api_key = self.config.get('azure_translator_key')
            endpoint = self.config.get('azure_translator_endpoint')
            if api_key and endpoint:
                credential = AzureKeyCredential(api_key)
                self.services['azure'] = TextTranslationClient(
                    endpoint=endpoint, credential=credential)
        except ImportError:
            pass

    def translate(self, text: str, from_lang: Optional[str] = None, to_lang: str = 'en-US',
                  context: str = 'general') -> Optional[TranslationResult]:
        """Translate text from one language to another.

        Args:
            text: Text to translate
            from_lang: Source language (auto-detect if None)
            to_lang: Target language
            context: Translation context

        Returns:
            Translation result or None if failed
        """
        if not text or not text.strip():
            return None

        # Check cache first
        cache_key = f"{text}:{from_lang}:{to_lang}:{context}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return TranslationResult(**cached)

        # Detect language if not provided
        if not from_lang:
            detector = LanguageDetector()
            from_lang = detector.detect_language(text) or 'en-US'

        # Skip translation if source and target are the same
        if from_lang.split('-')[0] == to_lang.split('-')[0]:
            result = TranslationResult(
                original_text=text,
                translated_text=text,
                from_lang=from_lang,
                to_lang=to_lang,
                confidence=1.0,
                detected_lang=from_lang
            )
            self._cache_result(cache_key, result)
            return result

        # Try available translation services
        for service_name, service in self.services.items():
            try:
                result = self._translate_with_service(service_name, service, text, from_lang, to_lang)
                if result:
                    self._cache_result(cache_key, result)
                    return result
            except Exception as e:
                print(f"Translation failed with {service_name}: {e}")
                continue

        return None

    def _translate_with_service(self, service_name: str, service, text: str,
                               from_lang: str, to_lang: str) -> Optional[TranslationResult]:
        """Translate using a specific service."""
        try:
            if service_name == 'google':
                result = service.translate(text, src=from_lang.split('-')[0],
                                         dest=to_lang.split('-')[0])
                return TranslationResult(
                    original_text=text,
                    translated_text=result.text,
                    from_lang=from_lang,
                    to_lang=to_lang,
                    confidence=0.8,
                    detected_lang=result.src
                )

            elif service_name == 'deepl':
                result = service.translate_text(text, target_lang=to_lang.split('-')[0].upper())
                return TranslationResult(
                    original_text=text,
                    translated_text=result.text,
                    from_lang=from_lang,
                    to_lang=to_lang,
                    confidence=0.9
                )

            elif service_name == 'azure':
                response = service.translate(body=[text], to=[to_lang.split('-')[0]])
                if response and len(response) > 0:
                    translation = response[0]
                    if translation.translations and len(translation.translations) > 0:
                        translated = translation.translations[0]
                        return TranslationResult(
                            original_text=text,
                            translated_text=translated.text,
                            from_lang=from_lang,
                            to_lang=to_lang,
                            confidence=translated.confidence if hasattr(translated, 'confidence') else 0.8,
                            detected_lang=translation.detected_language.language if translation.detected_language else None
                        )

        except Exception as e:
            print(f"Error with {service_name} translation: {e}")

        return None

    def _load_cache(self):
        """Load translation cache from file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
        except Exception as e:
            print(f"Error loading translation cache: {e}")
            self.cache = {}

    def _save_cache(self):
        """Save translation cache to file."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving translation cache: {e}")

    def _cache_result(self, key: str, result: TranslationResult):
        """Cache a translation result."""
        self.cache[key] = {
            'original_text': result.original_text,
            'translated_text': result.translated_text,
            'from_lang': result.from_lang,
            'to_lang': result.to_lang,
            'confidence': result.confidence,
            'detected_lang': result.detected_lang,
            'alternatives': result.alternatives
        }

        # Save cache periodically (every 10 translations)
        if len(self.cache) % 10 == 0:
            self._save_cache()


class MultiLanguageManager:
    """Manages multi-language support for Isaac's voice systems."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize multi-language manager."""
        self.config = config or {}
        self.languages = {}
        self.current_language = 'en-US'
        self.translator = Translator(self.config.get('translation', {}))
        self.detector = LanguageDetector()

        # Load language configurations
        self._load_language_configs()

        # Voice command patterns for different languages
        self._load_voice_patterns()

    def _load_language_configs(self):
        """Load language configurations."""
        # Default language configurations
        default_configs = {
            'en-US': LanguageConfig(
                code='en-US',
                name='English (US)',
                native_name='English',
                voice_commands={
                    'help': ['help', 'assist', 'what can you do'],
                    'status': ['status', 'how are you', 'system status'],
                    'run_tests': ['run tests', 'execute tests', 'test'],
                    'stop': ['stop', 'cancel', 'quit'],
                    'workspace': ['workspace', 'project', 'folder']
                },
                responses={
                    'greeting': 'Hello! How can I help you?',
                    'processing': 'Processing your request...',
                    'error': 'Sorry, I encountered an error.',
                    'success': 'Task completed successfully.'
                },
                tts_voice='en-US',
                stt_model='en-US'
            ),

            'es-ES': LanguageConfig(
                code='es-ES',
                name='Spanish (Spain)',
                native_name='Español',
                voice_commands={
                    'help': ['ayuda', 'asistencia', 'qué puedes hacer'],
                    'status': ['estado', 'cómo estás', 'estado del sistema'],
                    'run_tests': ['ejecutar pruebas', 'correr tests', 'probar'],
                    'stop': ['parar', 'cancelar', 'salir'],
                    'workspace': ['espacio de trabajo', 'proyecto', 'carpeta']
                },
                responses={
                    'greeting': '¡Hola! ¿Cómo puedo ayudarte?',
                    'processing': 'Procesando tu solicitud...',
                    'error': 'Lo siento, encontré un error.',
                    'success': 'Tarea completada exitosamente.'
                },
                tts_voice='es-ES',
                stt_model='es-ES'
            ),

            'fr-FR': LanguageConfig(
                code='fr-FR',
                name='French (France)',
                native_name='Français',
                voice_commands={
                    'help': ['aide', 'assistance', 'que peux-tu faire'],
                    'status': ['statut', 'comment ça va', 'état système'],
                    'run_tests': ['lancer tests', 'exécuter tests', 'tester'],
                    'stop': ['arrêter', 'annuler', 'quitter'],
                    'workspace': ['espace de travail', 'projet', 'dossier']
                },
                responses={
                    'greeting': 'Bonjour ! Comment puis-je vous aider ?',
                    'processing': 'Traitement de votre demande...',
                    'error': 'Désolé, j\'ai rencontré une erreur.',
                    'success': 'Tâche terminée avec succès.'
                },
                tts_voice='fr-FR',
                stt_model='fr-FR'
            ),

            'de-DE': LanguageConfig(
                code='de-DE',
                name='German (Germany)',
                native_name='Deutsch',
                voice_commands={
                    'help': ['hilfe', 'unterstützung', 'was kannst du'],
                    'status': ['status', 'wie geht\'s', 'systemstatus'],
                    'run_tests': ['tests ausführen', 'tests laufen', 'testen'],
                    'stop': ['stopp', 'abbrechen', 'beenden'],
                    'workspace': ['arbeitsbereich', 'projekt', 'ordner']
                },
                responses={
                    'greeting': 'Hallo! Wie kann ich Ihnen helfen?',
                    'processing': 'Bearbeite Ihre Anfrage...',
                    'error': 'Entschuldigung, es ist ein Fehler aufgetreten.',
                    'success': 'Aufgabe erfolgreich abgeschlossen.'
                },
                tts_voice='de-DE',
                stt_model='de-DE'
            ),

            'zh-CN': LanguageConfig(
                code='zh-CN',
                name='Chinese (Simplified)',
                native_name='中文',
                voice_commands={
                    'help': ['帮助', '协助', '你能做什么'],
                    'status': ['状态', '你怎么样', '系统状态'],
                    'run_tests': ['运行测试', '执行测试', '测试'],
                    'stop': ['停止', '取消', '退出'],
                    'workspace': ['工作区', '项目', '文件夹']
                },
                responses={
                    'greeting': '你好！我可以怎么帮助你？',
                    'processing': '正在处理您的请求...',
                    'error': '抱歉，遇到错误。',
                    'success': '任务成功完成。'
                },
                tts_voice='zh-CN',
                stt_model='zh-CN',
                text_direction='ltr'
            ),

            'ja-JP': LanguageConfig(
                code='ja-JP',
                name='Japanese',
                native_name='日本語',
                voice_commands={
                    'help': ['ヘルプ', '助けて', '何ができる'],
                    'status': ['ステータス', '調子はどう', 'システム状態'],
                    'run_tests': ['テスト実行', 'テストを走らせる', 'テスト'],
                    'stop': ['停止', 'キャンセル', '終了'],
                    'workspace': ['ワークスペース', 'プロジェクト', 'フォルダ']
                },
                responses={
                    'greeting': 'こんにちは！お手伝いできることはありますか？',
                    'processing': 'リクエストを処理しています...',
                    'error': '申し訳ありませんが、エラーが発生しました。',
                    'success': 'タスクが正常に完了しました。'
                },
                tts_voice='ja-JP',
                stt_model='ja-JP'
            )
        }

        # Load custom configurations if available
        config_dir = Path.home() / '.isaac' / 'languages'
        if config_dir.exists():
            for config_file in config_dir.glob('*.json'):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        custom_config = json.load(f)
                        code = custom_config.get('code')
                        if code:
                            default_configs[code] = LanguageConfig(**custom_config)
                except Exception as e:
                    print(f"Error loading language config {config_file}: {e}")

        self.languages = default_configs

    def _load_voice_patterns(self):
        """Load voice command patterns for language recognition."""
        # This would load more sophisticated pattern matching
        # For now, using simple keyword matching

    def detect_language(self, text: str) -> Optional[str]:
        """Detect the language of input text."""
        return self.detector.detect_language(text)

    def translate_text(self, text: str, to_lang: Optional[str] = None,
                      from_lang: Optional[str] = None) -> Optional[str]:
        """Translate text to target language."""
        if not to_lang:
            to_lang = self.current_language

        result = self.translator.translate(text, from_lang, to_lang)
        return result.translated_text if result else None

    def get_voice_commands(self, language: Optional[str] = None) -> Dict[str, List[str]]:
        """Get voice commands for a language."""
        lang_code = language or self.current_language
        config = self.languages.get(lang_code)
        return config.voice_commands if config else {}

    def get_response(self, response_key: str, language: Optional[str] = None) -> str:
        """Get a localized response."""
        lang_code = language or self.current_language
        config = self.languages.get(lang_code)
        if config and response_key in config.responses:
            return config.responses[response_key]

        # Fallback to English
        en_config = self.languages.get('en-US')
        if en_config and response_key in en_config.responses:
            return en_config.responses[response_key]

        return f"[{response_key}]"  # Placeholder if not found

    def process_voice_command(self, command_text: str) -> Dict[str, Any]:
        """Process a voice command in any supported language.

        Args:
            command_text: Raw voice command text

        Returns:
            Processed command information
        """
        # Detect language
        detected_lang = self.detect_language(command_text)
        if not detected_lang:
            detected_lang = self.current_language

        # Translate to English for processing if needed
        processing_text = command_text
        if detected_lang != 'en-US':
            translation = self.translate_text(command_text, 'en-US', detected_lang)
            if translation:
                processing_text = translation

        # Match against voice commands
        matched_command = None
        confidence = 0.0

        voice_commands = self.get_voice_commands('en-US')  # Use English patterns for matching

        for cmd, patterns in voice_commands.items():
            for pattern in patterns:
                # Simple string matching (could be enhanced with NLP)
                if pattern.lower() in processing_text.lower():
                    matched_command = cmd
                    confidence = 0.8  # Basic confidence
                    break
            if matched_command:
                break

        return {
            'original_text': command_text,
            'detected_language': detected_lang,
            'processed_text': processing_text,
            'matched_command': matched_command,
            'confidence': confidence,
            'needs_translation': detected_lang != self.current_language
        }

    def set_current_language(self, language_code: str) -> bool:
        """Set the current language for responses."""
        if language_code in self.languages:
            self.current_language = language_code
            return True
        return False

    def get_current_language(self) -> str:
        """Get the current language."""
        return self.current_language

    def get_available_languages(self) -> List[Dict[str, Any]]:
        """Get list of available languages."""
        return [
            {
                'code': config.code,
                'name': config.name,
                'native_name': config.native_name,
                'enabled': config.enabled
            }
            for config in self.languages.values()
            if config.enabled
        ]

    def add_custom_language(self, config: LanguageConfig) -> bool:
        """Add a custom language configuration."""
        try:
            self.languages[config.code] = config

            # Save to file
            config_dir = Path.home() / '.isaac' / 'languages'
            config_dir.mkdir(parents=True, exist_ok=True)

            config_file = config_dir / f"{config.code}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'code': config.code,
                    'name': config.name,
                    'native_name': config.native_name,
                    'voice_commands': config.voice_commands,
                    'responses': config.responses,
                    'tts_voice': config.tts_voice,
                    'stt_model': config.stt_model,
                    'text_direction': config.text_direction,
                    'enabled': config.enabled
                }, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"Error adding custom language: {e}")
            return False

    def get_tts_voice(self, language: Optional[str] = None) -> Optional[str]:
        """Get TTS voice for a language."""
        lang_code = language or self.current_language
        config = self.languages.get(lang_code)
        return config.tts_voice if config else None

    def get_stt_model(self, language: Optional[str] = None) -> Optional[str]:
        """Get STT model for a language."""
        lang_code = language or self.current_language
        config = self.languages.get(lang_code)
        return config.stt_model if config else None

    def is_rtl_language(self, language: Optional[str] = None) -> bool:
        """Check if a language uses right-to-left text direction."""
        lang_code = language or self.current_language
        config = self.languages.get(lang_code)
        return config.text_direction == 'rtl' if config else False