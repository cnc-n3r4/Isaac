# isaac/runtime/manifest_loader.py

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import jsonschema


class ManifestLoader:
    """Loads and validates command.yaml manifests"""

    def __init__(self):
        self.schema = self._load_json_schema()
        self.cache = {}  # path → (manifest, mtime)

    def _load_json_schema(self) -> Dict:
        """Load the JSON schema for manifest validation"""
        schema = {
            "type": "object",
            "required": ["name", "version", "summary", "triggers"],
            "properties": {
                "name": {"type": "string", "pattern": "^[a-z][a-z0-9_-]*$"},
                "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
                "summary": {"type": "string", "maxLength": 100},
                "description": {"type": "string"},
                "triggers": {
                    "type": "array",
                    "items": {"type": "string", "pattern": "^/[a-z][a-z0-9_-]*$"},
                    "minItems": 1
                },
                "aliases": {
                    "type": "array",
                    "items": {"type": "string", "pattern": "^/[a-z][a-z0-9_-]*$"}
                },
                "args": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "type"],
                        "properties": {
                            "name": {"type": "string", "pattern": "^[a-z][a-z0-9_-]*$"},
                            "type": {"enum": ["string", "int", "bool", "enum"]},
                            "required": {"type": "boolean"},
                            "help": {"type": "string"},
                            "pattern": {"type": "string"},
                            "enum": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "stdin": {"type": "boolean"},
                "stdout": {
                    "type": "object",
                    "properties": {
                        "type": {"enum": ["text", "json", "binary"]}
                    }
                },
                "security": {
                    "type": "object",
                    "properties": {
                        "scope": {"enum": ["user", "system"]},
                        "allow_remote": {"type": "boolean"},
                        "resources": {
                            "type": "object",
                            "properties": {
                                "timeout_ms": {"type": "integer", "minimum": 100},
                                "max_stdout_kib": {"type": "integer", "minimum": 1}
                            }
                        }
                    }
                },
                "runtime": {
                    "type": "object",
                    "required": ["entry"],
                    "properties": {
                        "entry": {"type": "string"},
                        "interpreter": {"type": "string"}
                    }
                },
                "telemetry": {
                    "type": "object",
                    "properties": {
                        "log_invocation": {"type": "boolean"},
                        "log_output": {"type": "boolean"},
                        "redact_patterns": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "examples": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        return schema

    def load_manifest(self, yaml_path: Path) -> Optional[Dict]:
        """Load and validate a command.yaml manifest"""
        try:
            # Check cache first
            stat = yaml_path.stat()
            cache_key = str(yaml_path)
            if cache_key in self.cache:
                cached_manifest, cached_mtime = self.cache[cache_key]
                if cached_mtime == stat.st_mtime:
                    return cached_manifest

            # Load YAML
            with open(yaml_path, 'r', encoding='utf-8') as f:
                manifest = yaml.safe_load(f)

            # Validate against schema
            is_valid, errors = self.validate_manifest(manifest)
            if not is_valid:
                print(f"Invalid manifest {yaml_path}: {errors}")
                return None

            # Cache the result
            self.cache[cache_key] = (manifest, stat.st_mtime)
            return manifest

        except Exception as e:
            print(f"Error loading manifest {yaml_path}: {e}")
            return None

    def validate_manifest(self, manifest: Dict) -> Tuple[bool, List[str]]:
        """Validate manifest against JSON schema"""
        try:
            jsonschema.validate(instance=manifest, schema=self.schema)
            return True, []
        except jsonschema.ValidationError as e:
            return False, [str(e)]
        except Exception as e:
            return False, [f"Validation error: {e}"]

    def hot_reload(self, yaml_path: Path):
        """Reload a changed manifest (for future hot-reload feature)"""
        cache_key = str(yaml_path)
        if cache_key in self.cache:
            del self.cache[cache_key]
        # Re-load will happen on next access