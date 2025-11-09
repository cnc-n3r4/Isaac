"""Team pipeline sharing for collaborative automation."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import ResourceType, SharedResource


class TeamPipelineSharing:
    """Share pipelines with teams."""

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize team pipeline sharing.

        Args:
            base_dir: Base directory for team pipelines (default: ~/.isaac/team_pipelines/)
        """
        self.base_dir = Path(base_dir or os.path.expanduser("~/.isaac/team_pipelines"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def share_pipeline(
        self,
        team_id: str,
        pipeline_data: Dict,
        shared_by: str,
        name: str = "",
        description: str = "",
    ) -> SharedResource:
        """Share a pipeline with a team.

        Args:
            team_id: Team ID
            pipeline_data: Pipeline data from pipeline system
            shared_by: User ID sharing the pipeline
            name: Pipeline name
            description: Pipeline description

        Returns:
            SharedResource object
        """
        # Generate resource ID
        import uuid

        pipeline_id = pipeline_data.get("pipeline_id", str(uuid.uuid4()))

        # Save pipeline data
        pipeline_file = self.base_dir / team_id / f"{pipeline_id}.json"
        pipeline_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pipeline_file, "w") as f:
            json.dump(pipeline_data, f, indent=2)

        # Create shared resource
        resource = SharedResource(
            resource_id=pipeline_id,
            resource_type=ResourceType.PIPELINE,
            team_id=team_id,
            shared_by=shared_by,
            name=name or pipeline_data.get("name", "Unnamed Pipeline"),
            description=description or pipeline_data.get("description", ""),
            metadata={
                "step_count": len(pipeline_data.get("steps", [])),
                "tags": pipeline_data.get("tags", []),
                "execution_count": pipeline_data.get("execution_count", 0),
            },
        )

        return resource

    def get_pipeline(self, team_id: str, pipeline_id: str) -> Optional[Dict]:
        """Get pipeline data.

        Args:
            team_id: Team ID
            pipeline_id: Pipeline ID

        Returns:
            Pipeline data dictionary or None if not found
        """
        pipeline_file = self.base_dir / team_id / f"{pipeline_id}.json"
        if not pipeline_file.exists():
            return None

        with open(pipeline_file) as f:
            return json.load(f)

    def import_pipeline(
        self, team_id: str, pipeline_id: str, pipeline_manager, user_id: str
    ) -> Optional[str]:
        """Import a team pipeline into local pipeline manager.

        Args:
            team_id: Team ID
            pipeline_id: Pipeline ID
            pipeline_manager: PipelineManager instance
            user_id: User ID importing the pipeline

        Returns:
            New local pipeline ID or None on error
        """
        pipeline_data = self.get_pipeline(team_id, pipeline_id)
        if not pipeline_data:
            return None

        try:
            # Generate new local ID
            import uuid

            local_id = str(uuid.uuid4())

            # Update metadata
            pipeline_data["pipeline_id"] = local_id
            pipeline_data["imported_from_team"] = team_id
            pipeline_data["imported_at"] = datetime.now().isoformat()
            pipeline_data["imported_by"] = user_id

            # Save to local pipeline manager
            pipeline_manager._save_pipeline(pipeline_data)

            return local_id
        except Exception:
            return None

    def list_pipelines(self, team_id: str, tags: Optional[List[str]] = None) -> List[Dict]:
        """List pipelines shared with a team.

        Args:
            team_id: Team ID
            tags: Optional tags to filter by

        Returns:
            List of pipeline metadata
        """
        pipelines = []
        team_dir = self.base_dir / team_id

        if not team_dir.exists():
            return pipelines

        for pipeline_file in team_dir.glob("*.json"):
            try:
                with open(pipeline_file) as f:
                    pipeline_data = json.load(f)

                # Apply tag filter
                if tags:
                    pipeline_tags = set(pipeline_data.get("tags", []))
                    if not pipeline_tags.intersection(tags):
                        continue

                pipelines.append(
                    {
                        "pipeline_id": pipeline_file.stem,
                        "name": pipeline_data.get("name", "Unnamed"),
                        "description": pipeline_data.get("description", ""),
                        "step_count": len(pipeline_data.get("steps", [])),
                        "tags": pipeline_data.get("tags", []),
                        "execution_count": pipeline_data.get("execution_count", 0),
                        "last_executed_at": pipeline_data.get("last_executed_at"),
                        "shared_at": pipeline_data.get("shared_at"),
                    }
                )
            except Exception:
                continue

        # Sort by execution count (most popular first)
        pipelines.sort(key=lambda p: p.get("execution_count", 0), reverse=True)

        return pipelines

    def update_pipeline(
        self, team_id: str, pipeline_id: str, pipeline_data: Dict, updated_by: str
    ) -> bool:
        """Update a shared pipeline.

        Args:
            team_id: Team ID
            pipeline_id: Pipeline ID
            pipeline_data: Updated pipeline data
            updated_by: User ID updating the pipeline

        Returns:
            True if updated, False on error
        """
        pipeline_file = self.base_dir / team_id / f"{pipeline_id}.json"

        # Add update metadata
        pipeline_data["last_updated_by"] = updated_by
        pipeline_data["last_updated_at"] = datetime.now().isoformat()
        pipeline_data["version"] = pipeline_data.get("version", 1) + 1

        try:
            with open(pipeline_file, "w") as f:
                json.dump(pipeline_data, f, indent=2)
            return True
        except Exception:
            return False

    def execute_pipeline(
        self, team_id: str, pipeline_id: str, pipeline_runner, executed_by: str
    ) -> Optional[Dict]:
        """Execute a team pipeline.

        Args:
            team_id: Team ID
            pipeline_id: Pipeline ID
            pipeline_runner: PipelineRunner instance
            executed_by: User ID executing the pipeline

        Returns:
            Execution result or None on error
        """
        pipeline_data = self.get_pipeline(team_id, pipeline_id)
        if not pipeline_data:
            return None

        try:
            # Execute pipeline
            result = pipeline_runner.run_pipeline(pipeline_data)

            # Update execution count
            pipeline_data["execution_count"] = pipeline_data.get("execution_count", 0) + 1
            pipeline_data["last_executed_at"] = datetime.now().isoformat()
            pipeline_data["last_executed_by"] = executed_by

            # Add to execution history
            if "execution_history" not in pipeline_data:
                pipeline_data["execution_history"] = []

            pipeline_data["execution_history"].append(
                {
                    "executed_by": executed_by,
                    "executed_at": datetime.now().isoformat(),
                    "success": result.get("success", False),
                    "duration": result.get("duration", 0),
                }
            )

            # Save updated pipeline
            self.update_pipeline(team_id, pipeline_id, pipeline_data, executed_by)

            return result
        except Exception:
            return None

    def search_pipelines(self, team_id: str, query: str) -> List[Dict]:
        """Search pipelines by name, description, or tags.

        Args:
            team_id: Team ID
            query: Search query

        Returns:
            List of matching pipelines
        """
        results = []
        team_dir = self.base_dir / team_id

        if not team_dir.exists():
            return results

        query_lower = query.lower()

        for pipeline_file in team_dir.glob("*.json"):
            try:
                with open(pipeline_file) as f:
                    pipeline_data = json.load(f)

                # Search in name, description, and tags
                searchable_text = (
                    f"{pipeline_data.get('name', '')} "
                    f"{pipeline_data.get('description', '')} "
                    f"{' '.join(pipeline_data.get('tags', []))}"
                ).lower()

                if query_lower in searchable_text:
                    results.append(
                        {
                            "pipeline_id": pipeline_file.stem,
                            "name": pipeline_data.get("name", "Unnamed"),
                            "description": pipeline_data.get("description", ""),
                            "step_count": len(pipeline_data.get("steps", [])),
                            "tags": pipeline_data.get("tags", []),
                        }
                    )
            except Exception:
                continue

        return results

    def delete_pipeline(self, team_id: str, pipeline_id: str) -> bool:
        """Delete a shared pipeline.

        Args:
            team_id: Team ID
            pipeline_id: Pipeline ID

        Returns:
            True if deleted, False if not found
        """
        pipeline_file = self.base_dir / team_id / f"{pipeline_id}.json"
        if pipeline_file.exists():
            pipeline_file.unlink()
            return True
        return False

    def get_pipeline_stats(self, team_id: str) -> Dict:
        """Get statistics about team pipelines.

        Args:
            team_id: Team ID

        Returns:
            Dictionary with pipeline statistics
        """
        pipelines = self.list_pipelines(team_id)

        stats = {
            "total_pipelines": len(pipelines),
            "total_executions": 0,
            "average_steps": 0,
            "popular_tags": {},
            "top_pipelines": [],
        }

        if not pipelines:
            return stats

        total_steps = 0
        for pipeline in pipelines:
            stats["total_executions"] += pipeline.get("execution_count", 0)
            total_steps += pipeline.get("step_count", 0)

            # Count tags
            for tag in pipeline.get("tags", []):
                stats["popular_tags"][tag] = stats["popular_tags"].get(tag, 0) + 1

        # Calculate average steps
        stats["average_steps"] = total_steps / len(pipelines) if pipelines else 0

        # Get top pipelines by execution count
        stats["top_pipelines"] = sorted(
            pipelines, key=lambda p: p.get("execution_count", 0), reverse=True
        )[:10]

        return stats
