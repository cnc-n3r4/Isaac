"""
Multimodal Input Handler

Combines voice commands and gesture controls for natural AR/VR interaction.
Supports simultaneous voice + gesture inputs for complex operations.
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

from isaac.arvr.gesture_api import Gesture, GestureType, GestureAPI


class InputModality(Enum):
    """Types of input modalities"""
    VOICE = "voice"
    GESTURE = "gesture"
    COMBINED = "combined"  # Voice + Gesture simultaneously
    GAZE = "gaze"
    CONTROLLER = "controller"


@dataclass
class VoiceCommand:
    """Voice command data"""
    text: str
    confidence: float
    timestamp: float
    language: str = "en"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'confidence': self.confidence,
            'timestamp': self.timestamp,
            'language': self.language,
            'metadata': self.metadata
        }


@dataclass
class MultimodalInput:
    """Combined multimodal input event"""
    modality: InputModality
    timestamp: float
    voice_command: Optional[VoiceCommand] = None
    gesture: Optional[Gesture] = None
    gaze_target: Optional[str] = None  # Object ID being looked at
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_combined(self) -> bool:
        """Check if this is a combined input"""
        active_modalities = sum([
            self.voice_command is not None,
            self.gesture is not None,
            self.gaze_target is not None
        ])
        return active_modalities > 1

    def get_intent(self) -> str:
        """Try to determine user intent from the input"""
        # Simple intent extraction
        if self.voice_command and self.gesture:
            return f"{self.voice_command.text}_{self.gesture.type.value}"
        elif self.voice_command:
            return self.voice_command.text
        elif self.gesture:
            return self.gesture.type.value
        return "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'modality': self.modality.value,
            'timestamp': self.timestamp,
            'voice_command': self.voice_command.to_dict() if self.voice_command else None,
            'gesture': self.gesture.to_dict() if self.gesture else None,
            'gaze_target': self.gaze_target,
            'confidence': self.confidence,
            'metadata': self.metadata
        }


@dataclass
class InputPattern:
    """Pattern for multimodal input recognition"""
    name: str
    required_modalities: List[InputModality]
    voice_keywords: List[str] = field(default_factory=list)
    gesture_types: List[GestureType] = field(default_factory=list)
    requires_gaze: bool = False
    time_window: float = 2.0  # seconds - inputs must occur within this window

    def matches(self, inputs: List[MultimodalInput]) -> bool:
        """Check if a sequence of inputs matches this pattern"""
        if not inputs:
            return False

        # Check time window
        time_span = inputs[-1].timestamp - inputs[0].timestamp
        if time_span > self.time_window:
            return False

        # Check required modalities
        present_modalities = set()
        for inp in inputs:
            if inp.voice_command:
                present_modalities.add(InputModality.VOICE)
            if inp.gesture:
                present_modalities.add(InputModality.GESTURE)
            if inp.gaze_target:
                present_modalities.add(InputModality.GAZE)

        for required in self.required_modalities:
            if required not in present_modalities:
                return False

        # Check voice keywords
        if self.voice_keywords:
            voice_texts = [inp.voice_command.text.lower()
                          for inp in inputs if inp.voice_command]
            matched = any(
                any(keyword.lower() in text for keyword in self.voice_keywords)
                for text in voice_texts
            )
            if not matched:
                return False

        # Check gesture types
        if self.gesture_types:
            gesture_types = [inp.gesture.type
                            for inp in inputs if inp.gesture]
            matched = any(gt in self.gesture_types for gt in gesture_types)
            if not matched:
                return False

        # Check gaze requirement
        if self.requires_gaze:
            has_gaze = any(inp.gaze_target for inp in inputs)
            if not has_gaze:
                return False

        return True


MultimodalHandler = Callable[[MultimodalInput], None]


class MultimodalInputHandler:
    """Handles and coordinates multiple input modalities"""

    def __init__(self):
        self.gesture_api = GestureAPI()
        self.patterns: Dict[str, InputPattern] = {}
        self.handlers: Dict[str, List[MultimodalHandler]] = {}
        self.recent_inputs: List[MultimodalInput] = []
        self.input_buffer_size = 10
        self.input_history: List[MultimodalInput] = []
        self._initialize_default_patterns()

    def _initialize_default_patterns(self) -> None:
        """Initialize common multimodal patterns"""
        # "Move this" - voice + point + grab
        self.add_pattern(InputPattern(
            name="move_object",
            required_modalities=[InputModality.VOICE, InputModality.GESTURE],
            voice_keywords=["move", "drag", "reposition"],
            gesture_types=[GestureType.GRAB, GestureType.PINCH],
            requires_gaze=True
        ))

        # "Delete this" - voice + point
        self.add_pattern(InputPattern(
            name="delete_object",
            required_modalities=[InputModality.VOICE, InputModality.GESTURE],
            voice_keywords=["delete", "remove", "dismiss"],
            gesture_types=[GestureType.POINT],
            requires_gaze=True
        ))

        # "Scale up/down" - voice + pinch
        self.add_pattern(InputPattern(
            name="scale_object",
            required_modalities=[InputModality.VOICE, InputModality.GESTURE],
            voice_keywords=["scale", "resize", "bigger", "smaller"],
            gesture_types=[GestureType.SCALE, GestureType.PINCH]
        ))

        # "Show details" - voice + tap
        self.add_pattern(InputPattern(
            name="show_details",
            required_modalities=[InputModality.VOICE, InputModality.GESTURE],
            voice_keywords=["show", "details", "info", "open"],
            gesture_types=[GestureType.TAP, GestureType.POINT],
            requires_gaze=True
        ))

    def add_pattern(self, pattern: InputPattern) -> None:
        """Add a multimodal input pattern"""
        self.patterns[pattern.name] = pattern

    def register_handler(self, pattern_name: str, handler: MultimodalHandler) -> None:
        """Register handler for a pattern"""
        if pattern_name not in self.handlers:
            self.handlers[pattern_name] = []
        self.handlers[pattern_name].append(handler)

    def process_voice_input(
        self,
        text: str,
        confidence: float = 1.0,
        gaze_target: Optional[str] = None
    ) -> MultimodalInput:
        """Process voice input"""
        voice_cmd = VoiceCommand(
            text=text,
            confidence=confidence,
            timestamp=time.time()
        )

        multimodal_input = MultimodalInput(
            modality=InputModality.VOICE,
            timestamp=time.time(),
            voice_command=voice_cmd,
            gaze_target=gaze_target,
            confidence=confidence
        )

        self._add_input(multimodal_input)
        return multimodal_input

    def process_gesture_input(
        self,
        gesture: Gesture,
        gaze_target: Optional[str] = None
    ) -> MultimodalInput:
        """Process gesture input"""
        multimodal_input = MultimodalInput(
            modality=InputModality.GESTURE,
            timestamp=time.time(),
            gesture=gesture,
            gaze_target=gaze_target,
            confidence=gesture.confidence
        )

        self._add_input(multimodal_input)
        return multimodal_input

    def process_combined_input(
        self,
        voice_text: Optional[str] = None,
        gesture: Optional[Gesture] = None,
        gaze_target: Optional[str] = None
    ) -> MultimodalInput:
        """Process combined input (voice + gesture simultaneously)"""
        voice_cmd = None
        if voice_text:
            voice_cmd = VoiceCommand(
                text=voice_text,
                confidence=1.0,
                timestamp=time.time()
            )

        confidence = 1.0
        if gesture:
            confidence = min(confidence, gesture.confidence)

        multimodal_input = MultimodalInput(
            modality=InputModality.COMBINED,
            timestamp=time.time(),
            voice_command=voice_cmd,
            gesture=gesture,
            gaze_target=gaze_target,
            confidence=confidence
        )

        self._add_input(multimodal_input)
        return multimodal_input

    def _add_input(self, multimodal_input: MultimodalInput) -> None:
        """Add input to buffers and check for pattern matches"""
        self.recent_inputs.append(multimodal_input)
        self.input_history.append(multimodal_input)

        # Keep buffer size limited
        if len(self.recent_inputs) > self.input_buffer_size:
            self.recent_inputs.pop(0)

        # Check for pattern matches
        self._check_patterns()

    def _check_patterns(self) -> None:
        """Check if recent inputs match any patterns"""
        for pattern_name, pattern in self.patterns.items():
            if pattern.matches(self.recent_inputs):
                self._trigger_pattern_handlers(pattern_name)

    def _trigger_pattern_handlers(self, pattern_name: str) -> None:
        """Trigger handlers for a matched pattern"""
        handlers = self.handlers.get(pattern_name, [])

        # Create combined input from recent inputs
        voice_cmd = None
        gesture = None
        gaze_target = None

        for inp in self.recent_inputs:
            if inp.voice_command and not voice_cmd:
                voice_cmd = inp.voice_command
            if inp.gesture and not gesture:
                gesture = inp.gesture
            if inp.gaze_target and not gaze_target:
                gaze_target = inp.gaze_target

        combined = MultimodalInput(
            modality=InputModality.COMBINED,
            timestamp=time.time(),
            voice_command=voice_cmd,
            gesture=gesture,
            gaze_target=gaze_target,
            metadata={'pattern': pattern_name}
        )

        for handler in handlers:
            try:
                handler(combined)
            except Exception as e:
                print(f"Error in multimodal handler: {e}")

    def simulate_interaction(
        self,
        voice_text: str,
        gesture_type: GestureType,
        gaze_target: Optional[str] = None,
        delay: float = 0.5
    ) -> List[MultimodalInput]:
        """Simulate a multimodal interaction for testing"""
        inputs = []

        # Voice input
        voice_input = self.process_voice_input(voice_text, gaze_target=gaze_target)
        inputs.append(voice_input)

        time.sleep(delay)

        # Gesture input
        from isaac.arvr.gesture_api import HandType
        gesture = Gesture(
            type=gesture_type,
            hand=HandType.RIGHT,
            start_time=time.time() - 0.1,
            end_time=time.time()
        )
        gesture_input = self.process_gesture_input(gesture, gaze_target=gaze_target)
        inputs.append(gesture_input)

        return inputs

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about multimodal input usage"""
        total = len(self.input_history)
        if total == 0:
            return {'total_inputs': 0}

        modality_counts = {}
        for inp in self.input_history:
            modality = inp.modality.value
            modality_counts[modality] = modality_counts.get(modality, 0) + 1

        combined_count = sum(1 for inp in self.input_history if inp.is_combined())
        pattern_matches = sum(
            1 for inp in self.input_history
            if 'pattern' in inp.metadata
        )

        return {
            'total_inputs': total,
            'modality_counts': modality_counts,
            'combined_inputs': combined_count,
            'pattern_matches': pattern_matches,
            'patterns_registered': len(self.patterns)
        }

    def clear_history(self) -> None:
        """Clear input history"""
        self.input_history.clear()
        self.recent_inputs.clear()

    def on_pattern(self, pattern_name: str) -> Callable:
        """Decorator for registering pattern handlers"""
        def decorator(func: MultimodalHandler) -> MultimodalHandler:
            self.register_handler(pattern_name, func)
            return func
        return decorator
