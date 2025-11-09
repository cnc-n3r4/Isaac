"""
Shared types for Smart Drag-Drop System
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class RoutingResult:
    """Result of routing operation"""
    success: bool
    message: str
    processed_files: List[Path]
    failed_files: List[Path]
    output: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.output is None:
            self.output = {}


@dataclass
class BatchConfig:
    """Configuration for batch operations"""
    max_workers: int = 4  # Concurrent processing threads
    batch_size: int = 10  # Files per batch
    retry_attempts: int = 3  # Retry failed operations
    retry_delay: float = 1.0  # Delay between retries (seconds)
    memory_limit_mb: int = 100  # Memory usage limit
    timeout_per_file: int = 30  # Timeout per file operation (seconds)


@dataclass
class BatchResult:
    """Result of a batch operation"""
    total_files: int
    processed_files: int
    failed_files: int
    retry_count: int
    duration_seconds: float
    memory_peak_mb: float
    errors: List[str]
    success: bool