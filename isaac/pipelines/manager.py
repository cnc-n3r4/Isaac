"""
Pipeline Manager - Load, save, and manage pipeline definitions
Isaac's pipeline registry and storage system
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from isaac.pipelines.models import Pipeline


class PipelineManager:
    """Manages pipeline definitions and storage."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize pipeline manager.

        Args:
            storage_path: Directory to store pipeline definitions
        """
        if storage_path is None:
            isaac_dir = Path.home() / '.isaac'
            isaac_dir.mkdir(exist_ok=True)
            storage_path = isaac_dir / 'pipelines'

        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)

        # In-memory cache
        self._pipelines: Dict[str, Pipeline] = {}
        self._load_all_pipelines()

    def create_pipeline(self, pipeline: Pipeline) -> None:
        """Create a new pipeline.

        Args:
            pipeline: Pipeline to create

        Raises:
            ValueError: If pipeline ID already exists
        """
        if pipeline.id in self._pipelines:
            raise ValueError(f"Pipeline {pipeline.id} already exists")

        pipeline.updated_at = time.time()
        self._pipelines[pipeline.id] = pipeline
        self._save_pipeline(pipeline)

    def update_pipeline(self, pipeline: Pipeline) -> None:
        """Update an existing pipeline.

        Args:
            pipeline: Pipeline to update

        Raises:
            ValueError: If pipeline doesn't exist
        """
        if pipeline.id not in self._pipelines:
            raise ValueError(f"Pipeline {pipeline.id} does not exist")

        pipeline.updated_at = time.time()
        self._pipelines[pipeline.id] = pipeline
        self._save_pipeline(pipeline)

    def delete_pipeline(self, pipeline_id: str) -> bool:
        """Delete a pipeline.

        Args:
            pipeline_id: ID of pipeline to delete

        Returns:
            True if deleted, False if not found
        """
        if pipeline_id in self._pipelines:
            del self._pipelines[pipeline_id]
            pipeline_file = self.storage_path / f"{pipeline_id}.json"
            if pipeline_file.exists():
                pipeline_file.unlink()
            return True
        return False

    def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        """Get a pipeline by ID.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            Pipeline or None if not found
        """
        return self._pipelines.get(pipeline_id)

    def list_pipelines(self) -> List[Pipeline]:
        """List all pipelines.

        Returns:
            List of all pipelines
        """
        return list(self._pipelines.values())

    def search_pipelines(self, query: str) -> List[Pipeline]:
        """Search pipelines by name or description.

        Args:
            query: Search query

        Returns:
            Matching pipelines
        """
        query_lower = query.lower()
        return [
            pipeline for pipeline in self._pipelines.values()
            if query_lower in pipeline.name.lower() or query_lower in pipeline.description.lower()
        ]

    def get_pipeline_templates(self) -> List[Dict[str, Any]]:
        """Get available pipeline templates.

        Returns:
            List of template definitions
        """
        return [
            {
                'id': 'build',
                'name': 'Build Pipeline',
                'description': 'Compile and build project',
                'category': 'development',
                'steps': [
                    {'id': 'install_deps', 'name': 'Install Dependencies', 'type': 'command', 'config': {'command': 'pip install -r requirements.txt'}},
                    {'id': 'run_tests', 'name': 'Run Tests', 'type': 'command', 'config': {'command': 'pytest'}},
                    {'id': 'build', 'name': 'Build', 'type': 'command', 'config': {'command': 'python setup.py build'}}
                ]
            },
            {
                'id': 'deploy',
                'name': 'Deploy Pipeline',
                'description': 'Build and deploy application',
                'category': 'deployment',
                'steps': [
                    {'id': 'build', 'name': 'Build', 'type': 'command', 'config': {'command': 'docker build -t myapp .'}},
                    {'id': 'test', 'name': 'Test', 'type': 'command', 'config': {'command': 'docker run myapp pytest'}},
                    {'id': 'deploy', 'name': 'Deploy', 'type': 'command', 'config': {'command': 'docker push myapp && kubectl apply -f deployment.yaml'}}
                ]
            },
            {
                'id': 'ci_cd',
                'name': 'CI/CD Pipeline',
                'description': 'Complete CI/CD workflow',
                'category': 'ci_cd',
                'steps': [
                    {'id': 'lint', 'name': 'Lint Code', 'type': 'command', 'config': {'command': 'flake8 src/'}},
                    {'id': 'test', 'name': 'Run Tests', 'type': 'command', 'config': {'command': 'pytest --cov=src'}},
                    {'id': 'build', 'name': 'Build Package', 'type': 'command', 'config': {'command': 'python -m build'}},
                    {'id': 'publish', 'name': 'Publish', 'type': 'command', 'config': {'command': 'twine upload dist/*'}}
                ]
            }
        ]

    def create_pipeline_from_template(self, template_id: str, name: str,
                                    description: str = "") -> Pipeline:
        """Create a pipeline from a template.

        Args:
            template_id: Template ID
            name: Pipeline name
            description: Pipeline description

        Returns:
            Created pipeline

        Raises:
            ValueError: If template not found
        """
        templates = self.get_pipeline_templates()
        template = next((t for t in templates if t['id'] == template_id), None)

        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Convert template steps to PipelineStep objects
        from isaac.pipelines.models import PipelineStep, StepType
        steps = []
        for step_data in template['steps']:
            step = PipelineStep(
                id=step_data['id'],
                name=step_data['name'],
                type=StepType(step_data['type']),
                config=step_data.get('config', {})
            )
            steps.append(step)

        pipeline = Pipeline(
            id=name.lower().replace(' ', '_'),
            name=name,
            description=description or template['description'],
            steps=steps,
            metadata={'template': template_id}
        )

        self.create_pipeline(pipeline)
        return pipeline

    def _save_pipeline(self, pipeline: Pipeline) -> None:
        """Save pipeline to disk."""
        pipeline_file = self.storage_path / f"{pipeline.id}.json"
        with open(pipeline_file, 'w') as f:
            json.dump(pipeline.to_dict(), f, indent=2)

    def _load_all_pipelines(self) -> None:
        """Load all pipelines from disk."""
        for pipeline_file in self.storage_path.glob("*.json"):
            try:
                with open(pipeline_file, 'r') as f:
                    data = json.load(f)
                    pipeline = Pipeline.from_dict(data)
                    self._pipelines[pipeline.id] = pipeline
            except Exception as e:
                print(f"Error loading pipeline {pipeline_file}: {e}")

    def export_pipeline(self, pipeline_id: str, export_path: Path) -> bool:
        """Export pipeline to file.

        Args:
            pipeline_id: Pipeline to export
            export_path: Export file path

        Returns:
            True if exported successfully
        """
        pipeline = self.get_pipeline(pipeline_id)
        if not pipeline:
            return False

        with open(export_path, 'w') as f:
            json.dump(pipeline.to_dict(), f, indent=2)
        return True

    def import_pipeline(self, import_path: Path) -> Optional[Pipeline]:
        """Import pipeline from file.

        Args:
            import_path: Import file path

        Returns:
            Imported pipeline or None if failed
        """
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)
                pipeline = Pipeline.from_dict(data)

                # Generate new ID if it conflicts
                original_id = pipeline.id
                counter = 1
                while pipeline.id in self._pipelines:
                    pipeline.id = f"{original_id}_{counter}"
                    counter += 1

                self.create_pipeline(pipeline)
                return pipeline

        except Exception as e:
            print(f"Error importing pipeline: {e}")
            return None