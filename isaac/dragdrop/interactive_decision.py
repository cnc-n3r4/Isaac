"""
Interactive Decision Maker for Smart Drag-Drop System
Handles user interaction for file processing decisions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .multi_file_detector import BatchAnalysis, FileCategory


class ActionType(Enum):
    """Types of actions that can be taken on files"""

    UPLOAD_IMAGES = "upload_images"
    ANALYZE_CODE = "analyze_code"
    PROCESS_DOCUMENTS = "process_documents"
    EXTRACT_ARCHIVE = "extract_archive"
    VIEW_TEXT = "view_text"
    CUSTOM_COMMAND = "custom_command"
    SKIP = "skip"
    CANCEL = "cancel"


@dataclass
class ActionOption:
    """An action option presented to the user"""

    action_type: ActionType
    title: str
    description: str
    shortcut: str  # Single character for quick selection
    applicable_files: List[int]  # Indices of files this applies to
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DecisionResult:
    """Result of user decision making"""

    selected_action: ActionType
    selected_files: List[int]  # Indices of selected files
    custom_params: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}


class InteractiveDecisionMaker:
    """
    Handles interactive decision making for drag-drop operations.
    Presents options to user and captures their choices.
    """

    def __init__(self):
        self._last_analysis = None

    def get_decision_options(self, analysis: BatchAnalysis) -> List[ActionOption]:
        """
        Generate decision options based on file analysis.

        Args:
            analysis: BatchAnalysis result

        Returns:
            List of ActionOption objects
        """
        self._last_analysis = analysis
        options = []

        # Always offer cancel
        options.append(
            ActionOption(
                action_type=ActionType.CANCEL,
                title="Cancel",
                description="Cancel this operation",
                shortcut="c",
                applicable_files=[],
            )
        )

        # Image upload option
        if analysis.has_images:
            image_indices = [
                i for i, f in enumerate(analysis.files) if f.category == FileCategory.IMAGE
            ]
            options.append(
                ActionOption(
                    action_type=ActionType.UPLOAD_IMAGES,
                    title="Upload Images",
                    description=f"Upload {len(image_indices)} image(s) to cloud storage",
                    shortcut="u",
                    applicable_files=image_indices,
                )
            )

        # Code analysis option
        if analysis.has_code:
            code_indices = [
                i for i, f in enumerate(analysis.files) if f.category == FileCategory.CODE
            ]
            options.append(
                ActionOption(
                    action_type=ActionType.ANALYZE_CODE,
                    title="Analyze Code",
                    description=f"Analyze {len(code_indices)} code file(s)",
                    shortcut="a",
                    applicable_files=code_indices,
                )
            )

        # Document processing option
        if analysis.has_documents:
            doc_indices = [
                i for i, f in enumerate(analysis.files) if f.category == FileCategory.DOCUMENT
            ]
            options.append(
                ActionOption(
                    action_type=ActionType.PROCESS_DOCUMENTS,
                    title="Process Documents",
                    description=f"Process {len(doc_indices)} document(s)",
                    shortcut="d",
                    applicable_files=doc_indices,
                )
            )

        # Archive extraction (if supported archives present)
        archive_files = [
            f for f in analysis.files if f.category == FileCategory.ARCHIVE and f.is_supported
        ]
        if archive_files:
            archive_indices = [
                i
                for i, f in enumerate(analysis.files)
                if f.category == FileCategory.ARCHIVE and f.is_supported
            ]
            options.append(
                ActionOption(
                    action_type=ActionType.EXTRACT_ARCHIVE,
                    title="Extract Archive",
                    description=f"Extract {len(archive_files)} archive(s)",
                    shortcut="e",
                    applicable_files=archive_indices,
                )
            )

        # Text viewing (for text files)
        text_files = [f for f in analysis.files if f.category == FileCategory.TEXT]
        if text_files:
            text_indices = [
                i for i, f in enumerate(analysis.files) if f.category == FileCategory.TEXT
            ]
            options.append(
                ActionOption(
                    action_type=ActionType.VIEW_TEXT,
                    title="View Text Files",
                    description=f"View contents of {len(text_files)} text file(s)",
                    shortcut="v",
                    applicable_files=text_indices,
                )
            )

        # Custom command option (always available)
        options.append(
            ActionOption(
                action_type=ActionType.CUSTOM_COMMAND,
                title="Custom Command",
                description="Run a custom command on selected files",
                shortcut="x",
                applicable_files=list(range(len(analysis.files))),  # All files
            )
        )

        # Skip option (for unsupported files)
        if analysis.unsupported_count > 0:
            unsupported_indices = [i for i, f in enumerate(analysis.files) if not f.is_supported]
            options.append(
                ActionOption(
                    action_type=ActionType.SKIP,
                    title="Skip Unsupported",
                    description=f"Skip {analysis.unsupported_count} unsupported file(s)",
                    shortcut="s",
                    applicable_files=unsupported_indices,
                )
            )

        return options

    def present_options(self, analysis: BatchAnalysis) -> None:
        """
        Present decision options to the user.

        Args:
            analysis: BatchAnalysis result
        """
        print(f"\n📁 Detected {analysis.file_count} file(s) ({analysis.total_size} bytes total)")
        print(
            f"📊 Categories: {', '.join(f'{count} {cat.value}' for cat, count in analysis.categories.items())}"
        )

        if analysis.duplicates:
            print(f"⚠️  {len(analysis.duplicates)} duplicate file(s) detected")

        if analysis.unsupported_count > 0:
            print(f"❌ {analysis.unsupported_count} unsupported file(s)")

        print("\n📋 Available actions:")
        options = self.get_decision_options(analysis)

        for i, option in enumerate(options, 1):
            applicable_count = len(option.applicable_files)
            print(f"  {i}. [{option.shortcut}] {option.title}")
            print(f"     {option.description}")
            if applicable_count > 0:
                print(f"     Applies to {applicable_count} file(s)")
            print()

        print("💡 Quick selection: Press the shortcut key or number")
        print("💡 For custom command: Select files first, then choose action")

    def get_user_decision(self, analysis: BatchAnalysis) -> DecisionResult:
        """
        Get user decision interactively.

        Args:
            analysis: BatchAnalysis result

        Returns:
            DecisionResult with user's choice
        """
        options = self.get_decision_options(analysis)

        while True:
            try:
                # Present options
                self.present_options(analysis)

                # Get user input
                choice = input("\nYour choice: ").strip().lower()

                if not choice:
                    print("Please make a selection.")
                    continue

                # Check for shortcut or number
                selected_option = None

                # Check shortcuts
                for option in options:
                    if choice == option.shortcut:
                        selected_option = option
                        break

                # Check numbers
                if selected_option is None and choice.isdigit():
                    index = int(choice) - 1
                    if 0 <= index < len(options):
                        selected_option = options[index]

                if selected_option is None:
                    print(f"Invalid choice: {choice}")
                    continue

                # Handle different action types
                if selected_option.action_type == ActionType.CANCEL:
                    return DecisionResult(ActionType.CANCEL, [])

                elif selected_option.action_type == ActionType.CUSTOM_COMMAND:
                    return self._handle_custom_command(analysis)

                else:
                    # Standard action with pre-selected files
                    return DecisionResult(
                        selected_option.action_type, selected_option.applicable_files
                    )

            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return DecisionResult(ActionType.CANCEL, [])
            except Exception as e:
                print(f"Error getting user input: {e}")
                continue

    def _handle_custom_command(self, analysis: BatchAnalysis) -> DecisionResult:
        """
        Handle custom command selection.

        Args:
            analysis: BatchAnalysis result

        Returns:
            DecisionResult for custom command
        """
        print("\n🔧 Custom Command Setup")

        # Let user select files
        selected_files = self._select_files_interactively(analysis)

        if not selected_files:
            print("No files selected.")
            return DecisionResult(ActionType.CANCEL, [])

        # Get command
        command = input("Enter command to run (use {} for file path): ").strip()

        if not command:
            print("No command entered.")
            return DecisionResult(ActionType.CANCEL, [])

        return DecisionResult(ActionType.CUSTOM_COMMAND, selected_files, {"command": command})

    def _select_files_interactively(self, analysis: BatchAnalysis) -> List[int]:
        """
        Let user select specific files interactively.

        Args:
            analysis: BatchAnalysis result

        Returns:
            List of selected file indices
        """
        print("\n📂 Select files:")
        for i, file_analysis in enumerate(analysis.files):
            status = "✓" if file_analysis.is_supported else "❌"
            print(f"  {i+1}. {status} {file_analysis.path.name} ({file_analysis.category.value})")

        print("\nEnter file numbers separated by commas (or 'all' for all files):")

        while True:
            choice = input("Files: ").strip().lower()

            if choice == "all":
                return list(range(len(analysis.files)))

            if not choice:
                return []

            try:
                indices = []
                for part in choice.split(","):
                    part = part.strip()
                    if part.isdigit():
                        index = int(part) - 1
                        if 0 <= index < len(analysis.files):
                            indices.append(index)
                        else:
                            print(f"Invalid file number: {part}")
                            indices = []
                            break
                    else:
                        print(f"Invalid input: {part}")
                        indices = []
                        break

                if indices:
                    return sorted(set(indices))  # Remove duplicates and sort

            except ValueError:
                print("Invalid input format.")

    def get_quick_decision(self, analysis: BatchAnalysis) -> Optional[DecisionResult]:
        """
        Get a quick decision without full interaction (for automation).

        Args:
            analysis: BatchAnalysis result

        Returns:
            DecisionResult if automatic decision possible, None otherwise
        """
        # If all files are images, auto-upload
        if (
            analysis.file_count > 0
            and analysis.categories.get(FileCategory.IMAGE, 0) == analysis.file_count
            and analysis.unsupported_count == 0
        ):
            return DecisionResult(ActionType.UPLOAD_IMAGES, list(range(analysis.file_count)))

        # If all files are code, auto-analyze
        if (
            analysis.file_count > 0
            and analysis.categories.get(FileCategory.CODE, 0) == analysis.file_count
            and analysis.unsupported_count == 0
        ):
            return DecisionResult(ActionType.ANALYZE_CODE, list(range(analysis.file_count)))

        # If mixed or unsupported files, require interaction
        return None
