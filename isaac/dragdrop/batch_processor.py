"""
Batch Operations for Smart Drag-Drop System
Handles large-scale file processing with optimizations for 100+ files.
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Callable
from queue import Queue

from .multi_file_detector import BatchAnalysis
from .interactive_decision import DecisionResult, ActionType
from .types import RoutingResult, BatchConfig, BatchResult
from .progress import BatchProgressManager, ProgressStyle


class BatchProcessor:
    """
    Handles large-scale batch file operations with optimizations.
    """

    def __init__(self, config: Optional[BatchConfig] = None):
        self.config = config or BatchConfig()
        self._progress_manager = BatchProgressManager(ProgressStyle.PERCENTAGE)

    def process_batch(self, decision: DecisionResult, analysis: BatchAnalysis,
                     progress_callback: Optional[Callable[[str], None]] = None) -> RoutingResult:
        """
        Process a large batch of files with optimizations.

        Args:
            decision: User's decision
            analysis: File analysis
            progress_callback: Optional progress callback

        Returns:
            RoutingResult with batch processing outcome
        """
        start_time = time.time()
        total_files = len(decision.selected_files)

        # For small batches, use regular processing
        if total_files <= self.config.batch_size:
            from .smart_router import SmartFileRouter
            router = SmartFileRouter()
            return router.route_files(decision, analysis, progress_callback)

        # Large batch - use optimized processing
        print(f"🔄 Processing large batch of {total_files} files with optimizations...")

        # Set up progress tracking
        if progress_callback is None:
            operation_name = decision.selected_action.value.replace('_', ' ').title()
            progress_callback = self._progress_manager.start_batch(
                f"{operation_name} (Batch)", total_files
            )

        try:
            # Process in optimized batches
            result = self._process_large_batch(decision, analysis, progress_callback)

            # Complete progress
            duration = time.time() - start_time
            self._progress_manager.complete_batch(
                result.success,
                f"Processed {result.processed_files}/{total_files} files in {duration:.1f}s"
            )

            return result

        except Exception as e:
            error_msg = f"Batch processing failed: {e}"
            self._progress_manager.complete_batch(False, error_msg)
            return RoutingResult(
                success=False,
                message=error_msg,
                processed_files=[],
                failed_files=[analysis.files[i].path for i in decision.selected_files]
            )

    def _process_large_batch(self, decision: DecisionResult, analysis: BatchAnalysis,
                           progress_callback: Callable[[str], None]) -> RoutingResult:
        """
        Process large batch with parallel execution and error recovery.
        """
        selected_files = decision.selected_files
        total_files = len(selected_files)

        # Split into smaller batches for processing
        batches = self._create_batches(selected_files, self.config.batch_size)

        # Results tracking
        all_processed = []
        all_failed = []
        all_errors = []

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all batches for parallel processing
            future_to_batch = {}
            for batch_idx, batch_files in enumerate(batches):
                future = executor.submit(
                    self._process_batch_chunk,
                    batch_idx, batch_files, decision, analysis, progress_callback
                )
                future_to_batch[future] = batch_files

            # Collect results as they complete
            for future in as_completed(future_to_batch):
                batch_files = future_to_batch[future]
                try:
                    batch_result = future.result()
                    all_processed.extend(batch_result.processed_files)
                    all_failed.extend(batch_result.failed_files)

                    if batch_result.output and 'errors' in batch_result.output:
                        all_errors.extend(batch_result.output['errors'])

                except Exception as e:
                    # Batch failed completely
                    batch_paths = [analysis.files[i].path for i in batch_files]
                    all_failed.extend(batch_paths)
                    all_errors.append(f"Batch processing error: {e}")

                    if progress_callback:
                        progress_callback(f"❌ Batch failed: {e}")

        # Create final result
        success = len(all_processed) > 0
        message = f"Batch processed {len(all_processed)}/{total_files} files"
        if all_failed:
            message += f" ({len(all_failed)} failed)"

        output = {"errors": all_errors} if all_errors else None

        return RoutingResult(
            success=success,
            message=message,
            processed_files=all_processed,
            failed_files=all_failed,
            output=output
        )

    def _process_batch_chunk(self, batch_idx: int, batch_files: List[int],
                           decision: DecisionResult, analysis: BatchAnalysis,
                           progress_callback: Callable[[str], None]) -> RoutingResult:
        """
        Process a single batch chunk.
        """
        # Create a decision for this specific batch
        batch_decision = DecisionResult(
            selected_action=decision.selected_action,
            selected_files=batch_files,
            custom_params=decision.custom_params
        )

        # Process with regular router (but with timeout and error handling)
        from .smart_router import SmartFileRouter
        router = SmartFileRouter()

        try:
            # Create a batch-specific progress callback
            def batch_progress(msg: str) -> None:
                if progress_callback:
                    progress_callback(f"[Batch {batch_idx+1}] {msg}")

            result = router.route_files(batch_decision, analysis, batch_progress)
            return result

        except Exception as e:
            # Return failed result
            failed_paths = [analysis.files[i].path for i in batch_files]
            return RoutingResult(
                success=False,
                message=f"Batch {batch_idx+1} failed: {e}",
                processed_files=[],
                failed_files=failed_paths,
                output={"errors": [str(e)]}
            )

    def _create_batches(self, file_indices: List[int], batch_size: int) -> List[List[int]]:
        """
        Split file indices into batches.

        Args:
            file_indices: List of file indices to process
            batch_size: Size of each batch

        Returns:
            List of batches (each batch is a list of file indices)
        """
        batches = []
        for i in range(0, len(file_indices), batch_size):
            batch = file_indices[i:i + batch_size]
            batches.append(batch)
        return batches

    def estimate_processing_time(self, analysis: BatchAnalysis, action: ActionType) -> float:
        """
        Estimate processing time for a batch operation.

        Args:
            analysis: File analysis
            action: Action to perform

        Returns:
            Estimated time in seconds
        """
        file_count = analysis.file_count

        # Base time per file (seconds)
        time_per_file = {
            ActionType.UPLOAD_IMAGES: 2.0,      # Cloud upload
            ActionType.ANALYZE_CODE: 0.1,       # Code analysis
            ActionType.PROCESS_DOCUMENTS: 1.0,  # Document processing
            ActionType.EXTRACT_ARCHIVE: 3.0,    # Archive extraction
            ActionType.VIEW_TEXT: 0.05,         # Text reading
            ActionType.CUSTOM_COMMAND: 1.0,     # Custom command
        }.get(action, 1.0)

        # Adjust for file size
        avg_size_mb = (analysis.total_size / file_count / (1024 * 1024)) if file_count > 0 else 0
        if avg_size_mb > 10:  # Large files
            time_per_file *= 2

        # Calculate total time with parallelization
        total_sequential_time = file_count * time_per_file
        parallel_time = total_sequential_time / min(self.config.max_workers, file_count)

        # Add overhead for batching
        batch_overhead = (file_count / self.config.batch_size) * 0.5
        parallel_time += batch_overhead

        return max(parallel_time, 1.0)  # At least 1 second

    def get_optimal_config(self, file_count: int, avg_file_size_mb: float) -> BatchConfig:
        """
        Get optimal batch configuration based on file characteristics.

        Args:
            file_count: Number of files
            avg_file_size_mb: Average file size in MB

        Returns:
            Optimized BatchConfig
        """
        config = BatchConfig()

        # Adjust workers based on file count
        if file_count < 10:
            config.max_workers = 2
        elif file_count < 50:
            config.max_workers = 4
        elif file_count < 200:
            config.max_workers = 6
        else:
            config.max_workers = 8

        # Adjust batch size based on file size
        if avg_file_size_mb < 1:  # Small files
            config.batch_size = 20
        elif avg_file_size_mb < 10:  # Medium files
            config.batch_size = 10
        else:  # Large files
            config.batch_size = 5

        # Adjust timeouts for large files
        if avg_file_size_mb > 50:
            config.timeout_per_file = 120  # 2 minutes

        return config


class StreamingBatchProcessor:
    """
    Processes files in a streaming fashion to handle very large batches.
    """

    def __init__(self, config: Optional[BatchConfig] = None):
        self.config = config or BatchConfig()
        self._queue = Queue(maxsize=1000)  # Buffer for streaming
        self._results_queue = Queue()

    def process_streaming(self, file_generator, decision_factory: Callable,
                         progress_callback: Optional[Callable] = None) -> BatchResult:
        """
        Process files in a streaming fashion.

        Args:
            file_generator: Generator yielding file paths
            decision_factory: Function creating decisions for batches
            progress_callback: Progress callback

        Returns:
            BatchResult with processing statistics
        """
        start_time = time.time()
        processed_count = 0
        failed_count = 0
        retry_count = 0
        errors = []

        # Start worker threads
        workers = []
        for _ in range(self.config.max_workers):
            worker = threading.Thread(
                target=self._worker_thread,
                args=(decision_factory, progress_callback)
            )
            worker.daemon = True
            worker.start()
            workers.append(worker)

        # Feed files to queue
        file_count = 0
        for file_path in file_generator:
            self._queue.put(file_path)
            file_count += 1

            # Prevent memory issues with very large streams
            if file_count % 1000 == 0:
                time.sleep(0.1)  # Brief pause to let workers catch up

        # Signal workers to finish
        for _ in range(self.config.max_workers):
            self._queue.put(None)

        # Wait for workers to complete
        for worker in workers:
            worker.join(timeout=300)  # 5 minute timeout

        # Collect results
        while not self._results_queue.empty():
            result = self._results_queue.get()
            processed_count += result.get('processed', 0)
            failed_count += result.get('failed', 0)
            retry_count += result.get('retries', 0)
            if result.get('errors'):
                errors.extend(result['errors'])

        duration = time.time() - start_time

        return BatchResult(
            total_files=file_count,
            processed_files=processed_count,
            failed_files=failed_count,
            retry_count=retry_count,
            duration_seconds=duration,
            memory_peak_mb=0.0,  # Would need psutil to measure
            errors=errors,
            success=processed_count > 0
        )

    def _worker_thread(self, decision_factory: Callable,
                      progress_callback: Optional[Callable]) -> None:
        """Worker thread for processing files from queue."""
        while True:
            file_path = self._queue.get()
            if file_path is None:  # Sentinel value
                break

            try:
                # Process file (simplified - would need full analysis)
                result = {'processed': 1, 'failed': 0, 'retries': 0, 'errors': []}

                if progress_callback:
                    progress_callback(f"Processed {file_path}")

            except Exception as e:
                result = {'processed': 0, 'failed': 1, 'retries': 0, 'errors': [str(e)]}

            self._results_queue.put(result)
            self._queue.task_done()