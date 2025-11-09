"""
Smart File Router for Drag-Drop System
Routes files to appropriate handlers based on user decisions.
"""

import subprocess
import shlex
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from .interactive_decision import DecisionResult, ActionType
from .multi_file_detector import BatchAnalysis
from .progress import BatchProgressManager, ProgressStyle
from .batch_processor import BatchProcessor
from .types import RoutingResult
from ..images import CloudImageStorage


class SmartFileRouter:
    """
    Routes files to appropriate handlers based on user decisions.
    """

    def __init__(self):
        self._handlers = {
            ActionType.UPLOAD_IMAGES: self._handle_upload_images,
            ActionType.ANALYZE_CODE: self._handle_analyze_code,
            ActionType.PROCESS_DOCUMENTS: self._handle_process_documents,
            ActionType.EXTRACT_ARCHIVE: self._handle_extract_archive,
            ActionType.VIEW_TEXT: self._handle_view_text,
            ActionType.CUSTOM_COMMAND: self._handle_custom_command,
            ActionType.SKIP: self._handle_skip,
        }
        self._progress_manager = BatchProgressManager(ProgressStyle.PERCENTAGE)
        self._batch_processor = BatchProcessor()

    def route_files(self, decision: DecisionResult, analysis: BatchAnalysis,
                   progress_callback: Optional[Callable[[str], None]] = None) -> RoutingResult:
        """
        Route files based on user decision.

        Args:
            decision: User's decision result
            analysis: Original file analysis
            progress_callback: Optional callback for progress updates

        Returns:
            RoutingResult with operation outcome
        """
        if decision.selected_action not in self._handlers:
            return RoutingResult(
                success=False,
                message=f"Unknown action: {decision.selected_action}",
                processed_files=[],
                failed_files=[analysis.files[i].path for i in decision.selected_files]
            )

        # Use batch processor for large batches (>20 files)
        if len(decision.selected_files) > 20:
            return self._batch_processor.process_batch(decision, analysis, progress_callback)

        # Use progress manager if no callback provided
        use_progress_manager = progress_callback is None
        if use_progress_manager:
            operation_name = decision.selected_action.value.replace('_', ' ').title()
            progress_callback = self._progress_manager.start_batch(
                operation_name, len(decision.selected_files)
            )

        handler = self._handlers[decision.selected_action]
        result = handler(decision, analysis, progress_callback)

        # Complete the batch if we used the progress manager
        if use_progress_manager:
            self._progress_manager.complete_batch(result.success, result.message)

        return result

    def _handle_upload_images(self, decision: DecisionResult, analysis: BatchAnalysis,
                            progress_callback: Optional[Callable[[str], None]] = None) -> RoutingResult:
        """Handle image upload to cloud storage."""
        if progress_callback:
            progress_callback("Initializing cloud storage...")

        try:
            storage = CloudImageStorage()
        except Exception as e:
            return RoutingResult(
                success=False,
                message=f"Failed to initialize cloud storage: {e}",
                processed_files=[],
                failed_files=[analysis.files[i].path for i in decision.selected_files]
            )

        processed_files = []
        failed_files = []

        for i, file_index in enumerate(decision.selected_files):
            file_analysis = analysis.files[file_index]
            file_path = file_analysis.path

            if progress_callback:
                progress_callback(f"Uploading {file_path.name}... ({i+1}/{len(decision.selected_files)})")

            try:
                result = storage.upload_image(file_path)
                if result:
                    processed_files.append(file_path)
                    if progress_callback:
                        progress_callback(f"✅ Uploaded: {result.filename}")
                else:
                    failed_files.append(file_path)
                    if progress_callback:
                        progress_callback(f"❌ Failed: {file_path.name}")
            except Exception as e:
                failed_files.append(file_path)
                if progress_callback:
                    progress_callback(f"❌ Error uploading {file_path.name}: {e}")

        success = len(processed_files) > 0
        message = f"Uploaded {len(processed_files)} of {len(decision.selected_files)} images"
        if failed_files:
            message += f" ({len(failed_files)} failed)"

        return RoutingResult(
            success=success,
            message=message,
            processed_files=processed_files,
            failed_files=failed_files
        )

    def _handle_analyze_code(self, decision: DecisionResult, analysis: BatchAnalysis,
                           progress_callback: Optional[Callable[[str], None]] = None) -> RoutingResult:
        """Handle code file analysis."""
        processed_files = []
        failed_files = []
        analysis_results = {}

        for i, file_index in enumerate(decision.selected_files):
            file_analysis = analysis.files[file_index]
            file_path = file_analysis.path

            if progress_callback:
                progress_callback(f"Analyzing {file_path.name}... ({i+1}/{len(decision.selected_files)})")

            try:
                # Basic code analysis - count lines, detect language, etc.
                analysis_result = self._analyze_code_file(file_path)
                analysis_results[str(file_path)] = analysis_result
                processed_files.append(file_path)

                if progress_callback:
                    progress_callback(f"✅ Analyzed: {file_path.name} ({analysis_result.get('lines', 0)} lines)")

            except Exception as e:
                failed_files.append(file_path)
                if progress_callback:
                    progress_callback(f"❌ Error analyzing {file_path.name}: {e}")

        success = len(processed_files) > 0
        message = f"Analyzed {len(processed_files)} code files"

        return RoutingResult(
            success=success,
            message=message,
            processed_files=processed_files,
            failed_files=failed_files,
            output={"analysis_results": analysis_results}
        )

    def _handle_process_documents(self, decision: DecisionResult, analysis: BatchAnalysis,
                                progress_callback: Optional[Callable[[str], None]] = None) -> RoutingResult:
        """Handle document processing."""
        processed_files = []
        failed_files = []

        for i, file_index in enumerate(decision.selected_files):
            file_analysis = analysis.files[file_index]
            file_path = file_analysis.path

            if progress_callback:
                progress_callback(f"Processing {file_path.name}... ({i+1}/{len(decision.selected_files)})")

            try:
                # For now, just attempt OCR if it's a PDF or image-based document
                if file_analysis.extension.lower() in ['.pdf']:
                    # Could integrate PDF text extraction here
                    processed_files.append(file_path)
                    if progress_callback:
                        progress_callback(f"✅ Processed document: {file_path.name}")
                else:
                    # For other documents, just acknowledge
                    processed_files.append(file_path)
                    if progress_callback:
                        progress_callback(f"✅ Processed: {file_path.name}")

            except Exception as e:
                failed_files.append(file_path)
                if progress_callback:
                    progress_callback(f"❌ Error processing {file_path.name}: {e}")

        success = len(processed_files) > 0
        message = f"Processed {len(processed_files)} documents"

        return RoutingResult(
            success=success,
            message=message,
            processed_files=processed_files,
            failed_files=failed_files
        )

    def _handle_extract_archive(self, decision: DecisionResult, analysis: BatchAnalysis,
                              progress_callback: Optional[Callable[[str], None]] = None) -> RoutingResult:
        """Handle archive extraction."""
        processed_files = []
        failed_files = []
        extracted_files = []

        for i, file_index in enumerate(decision.selected_files):
            file_analysis = analysis.files[file_index]
            file_path = file_analysis.path

            if progress_callback:
                progress_callback(f"Extracting {file_path.name}... ({i+1}/{len(decision.selected_files)})")

            try:
                extracted = self._extract_archive_file(file_path)
                if extracted:
                    processed_files.append(file_path)
                    extracted_files.extend(extracted)
                    if progress_callback:
                        progress_callback(f"✅ Extracted {len(extracted)} files from {file_path.name}")
                else:
                    failed_files.append(file_path)
                    if progress_callback:
                        progress_callback(f"❌ Failed to extract: {file_path.name}")

            except Exception as e:
                failed_files.append(file_path)
                if progress_callback:
                    progress_callback(f"❌ Error extracting {file_path.name}: {e}")

        success = len(processed_files) > 0
        message = f"Extracted {len(processed_files)} archives ({len(extracted_files)} total files)"

        return RoutingResult(
            success=success,
            message=message,
            processed_files=processed_files,
            failed_files=failed_files,
            output={"extracted_files": extracted_files}
        )

    def _handle_view_text(self, decision: DecisionResult, analysis: BatchAnalysis,
                        progress_callback: Optional[Callable[[str], None]] = None) -> RoutingResult:
        """Handle text file viewing."""
        processed_files = []
        failed_files = []
        text_contents = {}

        for i, file_index in enumerate(decision.selected_files):
            file_analysis = analysis.files[file_index]
            file_path = file_analysis.path

            if progress_callback:
                progress_callback(f"Reading {file_path.name}... ({i+1}/{len(decision.selected_files)})")

            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    text_contents[str(file_path)] = content
                    processed_files.append(file_path)

                    # Show preview
                    lines = content.split('\n')
                    preview = '\n'.join(lines[:5])  # First 5 lines
                    if len(lines) > 5:
                        preview += f"\n... ({len(lines)} total lines)"

                    if progress_callback:
                        progress_callback(f"✅ Read {file_path.name} ({len(lines)} lines)")

            except Exception as e:
                failed_files.append(file_path)
                if progress_callback:
                    progress_callback(f"❌ Error reading {file_path.name}: {e}")

        success = len(processed_files) > 0
        message = f"Viewed {len(processed_files)} text files"

        return RoutingResult(
            success=success,
            message=message,
            processed_files=processed_files,
            failed_files=failed_files,
            output={"text_contents": text_contents}
        )

    def _handle_custom_command(self, decision: DecisionResult, analysis: BatchAnalysis,
                             progress_callback: Optional[Callable[[str], None]] = None) -> RoutingResult:
        """Handle custom command execution."""
        command_template = decision.custom_params.get("command", "") if decision.custom_params else ""
        if not command_template:
            return RoutingResult(
                success=False,
                message="No command specified",
                processed_files=[],
                failed_files=[analysis.files[i].path for i in decision.selected_files]
            )

        processed_files = []
        failed_files = []
        command_outputs = {}

        for i, file_index in enumerate(decision.selected_files):
            file_analysis = analysis.files[file_index]
            file_path = file_analysis.path

            # Replace {} placeholder with file path
            command = command_template.replace("{}", str(file_path))

            if progress_callback:
                progress_callback(f"Running: {command}")

            try:
                # Use shlex.split() to safely parse the command and disable shell=True
                result = subprocess.run(
                    shlex.split(command),
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=30,  # 30 second timeout
                    check=False
                )

                command_outputs[str(file_path)] = {
                    "command": command,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }

                if result.returncode == 0:
                    processed_files.append(file_path)
                    if progress_callback:
                        progress_callback(f"✅ Command succeeded for {file_path.name}")
                else:
                    failed_files.append(file_path)
                    if progress_callback:
                        progress_callback(f"❌ Command failed for {file_path.name} (exit code {result.returncode})")

            except subprocess.TimeoutExpired:
                failed_files.append(file_path)
                if progress_callback:
                    progress_callback(f"❌ Command timed out for {file_path.name}")
            except Exception as e:
                failed_files.append(file_path)
                if progress_callback:
                    progress_callback(f"❌ Error running command for {file_path.name}: {e}")

        success = len(processed_files) > 0
        message = f"Executed custom command on {len(processed_files)} files"

        return RoutingResult(
            success=success,
            message=message,
            processed_files=processed_files,
            failed_files=failed_files,
            output={"command_outputs": command_outputs}
        )

    def _handle_skip(self, decision: DecisionResult, analysis: BatchAnalysis,
                   progress_callback: Optional[Callable[[str], None]] = None) -> RoutingResult:
        """Handle skipping files."""
        skipped_files = [analysis.files[i].path for i in decision.selected_files]

        if progress_callback:
            for file_path in skipped_files:
                progress_callback(f"⏭️  Skipped: {file_path.name}")

        return RoutingResult(
            success=True,
            message=f"Skipped {len(skipped_files)} files",
            processed_files=skipped_files,  # Consider skipped as "processed"
            failed_files=[]
        )

    def _analyze_code_file(self, file_path: Path) -> Dict[str, Any]:
        """Perform basic code analysis on a file."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            lines = content.split('\n')
            total_lines = len(lines)

            # Count non-empty lines
            non_empty_lines = sum(1 for line in lines if line.strip())

            # Detect language from extension
            extension = file_path.suffix.lower()
            language_map = {
                '.py': 'Python',
                '.js': 'JavaScript',
                '.ts': 'TypeScript',
                '.java': 'Java',
                '.cpp': 'C++',
                '.c': 'C',
                '.cs': 'C#',
                '.php': 'PHP',
                '.rb': 'Ruby',
                '.go': 'Go',
                '.rs': 'Rust',
                '.html': 'HTML',
                '.css': 'CSS',
                '.sh': 'Shell',
                '.md': 'Markdown'
            }
            language = language_map.get(extension, 'Unknown')

            return {
                "lines": total_lines,
                "non_empty_lines": non_empty_lines,
                "language": language,
                "size_bytes": len(content.encode('utf-8'))
            }

        except Exception as e:
            return {"error": str(e)}

    def _extract_archive_file(self, file_path: Path) -> Optional[List[Path]]:
        """Extract an archive file."""
        import zipfile
        import tarfile

        extract_dir = file_path.parent / f"{file_path.stem}_extracted"
        extract_dir.mkdir(exist_ok=True)

        extracted_files = []

        try:
            if file_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                    extracted_files = [extract_dir / name for name in zip_ref.namelist()]

            elif file_path.suffix.lower() in ['.tar', '.gz', '.bz2', '.xz']:
                with tarfile.open(file_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_dir)
                    extracted_files = [extract_dir / member.name for member in tar_ref.getmembers()
                                     if member.isfile()]

            else:
                return None  # Unsupported archive type

            return extracted_files

        except Exception:
            # Clean up failed extraction
            import shutil
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            return None