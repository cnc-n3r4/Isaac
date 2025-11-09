"""
Gesture API for AR/VR Input

Defines gesture types, recognition patterns, and handlers for
spatial input methods like hand tracking and controller gestures.
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

from isaac.arvr.spatial_api import Vector3D


class GestureType(Enum):
    """Types of recognized gestures"""
    # Hand gestures
    PINCH = "pinch"
    GRAB = "grab"
    POINT = "point"
    SWIPE = "swipe"
    TAP = "tap"
    WAVE = "wave"
    PALM_UP = "palm_up"
    PALM_DOWN = "palm_down"
    THUMBS_UP = "thumbs_up"
    PEACE_SIGN = "peace_sign"

    # Controller gestures
    TRIGGER_PRESS = "trigger_press"
    GRIP_PRESS = "grip_press"
    TOUCHPAD_SWIPE = "touchpad_swipe"
    BUTTON_PRESS = "button_press"

    # Spatial gestures
    DRAW_CIRCLE = "draw_circle"
    DRAW_LINE = "draw_line"
    PULL = "pull"
    PUSH = "push"
    ROTATE = "rotate"
    SCALE = "scale"

    # Custom
    CUSTOM = "custom"


class HandType(Enum):
    """Hand/controller identification"""
    LEFT = "left"
    RIGHT = "right"
    BOTH = "both"
    ANY = "any"


@dataclass
class GesturePoint:
    """Single point in a gesture sequence"""
    position: Vector3D
    timestamp: float
    velocity: Optional[Vector3D] = None
    pressure: float = 0.0  # For pinch/grab strength

    def to_dict(self) -> Dict[str, Any]:
        return {
            'position': self.position.to_dict(),
            'timestamp': self.timestamp,
            'velocity': self.velocity.to_dict() if self.velocity else None,
            'pressure': self.pressure
        }


@dataclass
class Gesture:
    """Complete gesture definition"""
    type: GestureType
    hand: HandType
    start_time: float
    end_time: Optional[float] = None
    points: List[GesturePoint] = field(default_factory=list)
    confidence: float = 1.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def duration(self) -> float:
        """Get gesture duration"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time

    def is_complete(self) -> bool:
        """Check if gesture is complete"""
        return self.end_time is not None

    def get_trajectory(self) -> List[Vector3D]:
        """Get trajectory of gesture"""
        return [point.position for point in self.points]

    def get_total_distance(self) -> float:
        """Calculate total distance traveled"""
        if len(self.points) < 2:
            return 0.0

        total = 0.0
        for i in range(1, len(self.points)):
            total += self.points[i-1].position.distance_to(self.points[i].position)
        return total

    def get_average_velocity(self) -> Optional[Vector3D]:
        """Calculate average velocity"""
        velocities = [p.velocity for p in self.points if p.velocity]
        if not velocities:
            return None

        avg_x = sum(v.x for v in velocities) / len(velocities)
        avg_y = sum(v.y for v in velocities) / len(velocities)
        avg_z = sum(v.z for v in velocities) / len(velocities)

        return Vector3D(avg_x, avg_y, avg_z)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type.value,
            'hand': self.hand.value,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'points': [p.to_dict() for p in self.points],
            'confidence': self.confidence,
            'metadata': self.metadata
        }


@dataclass
class GesturePattern:
    """Pattern definition for gesture recognition"""
    gesture_type: GestureType
    min_points: int = 2
    max_duration: float = 3.0  # seconds
    min_distance: float = 0.0  # meters
    required_hands: HandType = HandType.ANY
    velocity_threshold: Optional[float] = None
    pressure_threshold: Optional[float] = None

    def matches(self, gesture: Gesture) -> bool:
        """Check if gesture matches this pattern"""
        # Check type
        if gesture.type != self.gesture_type:
            return False

        # Check hand
        if self.required_hands != HandType.ANY and gesture.hand != self.required_hands:
            return False

        # Check points
        if len(gesture.points) < self.min_points:
            return False

        # Check duration
        if gesture.duration() > self.max_duration:
            return False

        # Check distance
        if gesture.get_total_distance() < self.min_distance:
            return False

        # Check velocity
        if self.velocity_threshold:
            avg_vel = gesture.get_average_velocity()
            if avg_vel and avg_vel.magnitude() < self.velocity_threshold:
                return False

        return True


GestureHandler = Callable[[Gesture], None]


class GestureRecognizer:
    """Recognizes and processes gestures"""

    def __init__(self):
        self.patterns: Dict[str, GesturePattern] = {}
        self.handlers: Dict[GestureType, List[GestureHandler]] = {}
        self.active_gestures: Dict[str, Gesture] = {}  # gesture_id -> Gesture
        self._initialize_default_patterns()

    def _initialize_default_patterns(self) -> None:
        """Initialize default gesture patterns"""
        # Pinch gesture
        self.add_pattern("pinch", GesturePattern(
            gesture_type=GestureType.PINCH,
            min_points=1,
            max_duration=2.0,
            pressure_threshold=0.5
        ))

        # Swipe gesture
        self.add_pattern("swipe", GesturePattern(
            gesture_type=GestureType.SWIPE,
            min_points=3,
            max_duration=1.0,
            min_distance=0.1,
            velocity_threshold=0.3
        ))

        # Tap gesture
        self.add_pattern("tap", GesturePattern(
            gesture_type=GestureType.TAP,
            min_points=2,
            max_duration=0.3
        ))

        # Wave gesture
        self.add_pattern("wave", GesturePattern(
            gesture_type=GestureType.WAVE,
            min_points=5,
            max_duration=2.0,
            min_distance=0.2
        ))

    def add_pattern(self, name: str, pattern: GesturePattern) -> None:
        """Add a gesture pattern"""
        self.patterns[name] = pattern

    def register_handler(self, gesture_type: GestureType, handler: GestureHandler) -> None:
        """Register a handler for a gesture type"""
        if gesture_type not in self.handlers:
            self.handlers[gesture_type] = []
        self.handlers[gesture_type].append(handler)

    def start_gesture(
        self,
        gesture_id: str,
        gesture_type: GestureType,
        hand: HandType,
        initial_position: Vector3D
    ) -> Gesture:
        """Start tracking a new gesture"""
        gesture = Gesture(
            type=gesture_type,
            hand=hand,
            start_time=time.time(),
            points=[GesturePoint(position=initial_position, timestamp=time.time())]
        )
        self.active_gestures[gesture_id] = gesture
        return gesture

    def update_gesture(
        self,
        gesture_id: str,
        position: Vector3D,
        velocity: Optional[Vector3D] = None,
        pressure: float = 0.0
    ) -> Optional[Gesture]:
        """Update an active gesture with new point"""
        if gesture_id not in self.active_gestures:
            return None

        gesture = self.active_gestures[gesture_id]
        point = GesturePoint(
            position=position,
            timestamp=time.time(),
            velocity=velocity,
            pressure=pressure
        )
        gesture.points.append(point)
        return gesture

    def end_gesture(self, gesture_id: str) -> Optional[Gesture]:
        """End a gesture and trigger recognition"""
        if gesture_id not in self.active_gestures:
            return None

        gesture = self.active_gestures[gesture_id]
        gesture.end_time = time.time()

        # Recognize gesture
        recognized = self.recognize(gesture)
        if recognized:
            self._trigger_handlers(recognized)

        del self.active_gestures[gesture_id]
        return recognized

    def recognize(self, gesture: Gesture) -> Optional[Gesture]:
        """Recognize a gesture against known patterns"""
        best_match = None
        best_confidence = 0.0

        for pattern_name, pattern in self.patterns.items():
            if pattern.matches(gesture):
                # Calculate confidence based on how well it matches
                confidence = self._calculate_confidence(gesture, pattern)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = gesture
                    best_match.confidence = confidence

        return best_match

    def _calculate_confidence(self, gesture: Gesture, pattern: GesturePattern) -> float:
        """Calculate confidence score for a gesture match"""
        confidence = 1.0

        # Penalize for too many points (might be noisy)
        if len(gesture.points) > pattern.min_points * 3:
            confidence *= 0.9

        # Penalize for duration close to max
        duration_ratio = gesture.duration() / pattern.max_duration
        if duration_ratio > 0.8:
            confidence *= 0.95

        # Reward for smooth trajectory (low velocity variance)
        velocities = [p.velocity.magnitude() for p in gesture.points if p.velocity]
        if len(velocities) > 1:
            import statistics
            variance = statistics.variance(velocities)
            if variance < 0.1:
                confidence *= 1.1

        return min(confidence, 1.0)

    def _trigger_handlers(self, gesture: Gesture) -> None:
        """Trigger all handlers for a recognized gesture"""
        handlers = self.handlers.get(gesture.type, [])
        for handler in handlers:
            try:
                handler(gesture)
            except Exception as e:
                print(f"Error in gesture handler: {e}")

    def get_active_gestures(self) -> List[Gesture]:
        """Get all currently active gestures"""
        return list(self.active_gestures.values())


class GestureAPI:
    """High-level API for gesture control"""

    def __init__(self):
        self.recognizer = GestureRecognizer()
        self.gesture_history: List[Gesture] = []
        self.max_history = 100

    def create_custom_gesture(
        self,
        name: str,
        gesture_type: GestureType = GestureType.CUSTOM,
        **pattern_params
    ) -> str:
        """Create a custom gesture pattern"""
        pattern = GesturePattern(gesture_type=gesture_type, **pattern_params)
        self.recognizer.add_pattern(name, pattern)
        return name

    def on_gesture(self, gesture_type: GestureType) -> Callable:
        """Decorator for registering gesture handlers"""
        def decorator(func: GestureHandler) -> GestureHandler:
            self.recognizer.register_handler(gesture_type, func)
            return func
        return decorator

    def simulate_gesture(
        self,
        gesture_type: GestureType,
        hand: HandType,
        trajectory: List[Vector3D],
        duration: float = 1.0
    ) -> Optional[Gesture]:
        """Simulate a gesture for testing"""
        gesture_id = f"sim_{time.time()}"

        # Start gesture
        gesture = self.recognizer.start_gesture(
            gesture_id, gesture_type, hand, trajectory[0]
        )

        # Add trajectory points
        time_per_point = duration / len(trajectory)
        for i, position in enumerate(trajectory[1:], 1):
            time.sleep(time_per_point)
            velocity = (position - trajectory[i-1]) * (1.0 / time_per_point)
            self.recognizer.update_gesture(gesture_id, position, velocity)

        # Complete the gesture
        gesture.end_time = time.time()

        # End gesture and try recognition
        recognized = self.recognizer.end_gesture(gesture_id)

        # Return recognized gesture or original gesture
        return recognized if recognized else gesture

    def get_gesture_stats(self) -> Dict[str, Any]:
        """Get statistics about gesture usage"""
        type_counts = {}
        for gesture in self.gesture_history:
            type_name = gesture.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        total = len(self.gesture_history)
        avg_confidence = (
            sum(g.confidence for g in self.gesture_history) / total
            if total > 0 else 0.0
        )

        return {
            'total_gestures': total,
            'type_counts': type_counts,
            'average_confidence': avg_confidence,
            'active_gestures': len(self.recognizer.active_gestures)
        }

    def clear_history(self) -> None:
        """Clear gesture history"""
        self.gesture_history.clear()
