"""
Smart Drag-Drop System for Isaac
"""

from .batch_processor import BatchProcessor, StreamingBatchProcessor
from .interactive_decision import (
    ActionOption,
    ActionType,
    DecisionResult,
    InteractiveDecisionMaker,
)
from .multi_file_detector import (
    BatchAnalysis,
    FileAnalysis,
    FileCategory,
    MultiFileDetector,
)
from .progress import (
    BatchProgressManager,
    ProgressCallback,
    ProgressIndicator,
    ProgressStyle,
    create_progress_indicator,
    with_progress,
)
from .smart_router import SmartFileRouter
from .types import BatchConfig, BatchResult, RoutingResult

__all__ = [
    "MultiFileDetector",
    "FileAnalysis",
    "BatchAnalysis",
    "FileCategory",
    "InteractiveDecisionMaker",
    "ActionType",
    "ActionOption",
    "DecisionResult",
    "SmartFileRouter",
    "RoutingResult",
    "ProgressIndicator",
    "BatchProgressManager",
    "ProgressCallback",
    "ProgressStyle",
    "create_progress_indicator",
    "with_progress",
    "BatchProcessor",
    "StreamingBatchProcessor",
    "BatchConfig",
    "BatchResult",
]
