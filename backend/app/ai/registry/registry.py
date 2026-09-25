"""Model Registry and Metadata Management for FinMate AI Models.

Stores:
- Model metadata in model_registry.json
- Serialized pipelines/estimators in artifacts/
- Benchmark comparisons between candidate models and baselines
"""

import datetime
import json
import os
from typing import Dict, Any, List, Optional
import joblib


REGISTRY_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(os.path.dirname(REGISTRY_DIR), "artifacts")
REGISTRY_FILE = os.path.join(REGISTRY_DIR, "model_registry.json")

os.makedirs(ARTIFACTS_DIR, exist_ok=True)


class ModelRegistry:
    """Lightweight JSON-backed model registry."""

    def __init__(self, registry_file: str = REGISTRY_FILE):
        self.registry_file = registry_file
        self.registry_data = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"models": {}, "last_updated": None}

    def _save(self):
        self.registry_data["last_updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(self.registry_data, f, indent=2)

    def register_model(
        self,
        task: str,
        model_name: str,
        version: str,
        algorithm: str,
        hyperparameters: Dict[str, Any],
        metrics: Dict[str, Any],
        is_selected: bool,
        is_baseline: bool,
        artifact_path: Optional[str] = None,
        notes: str = ""
    ):
        """Registers or updates model metadata in the registry."""
        key = f"{task}::{model_name}::{version}"
        entry = {
            "task": task,
            "model_name": model_name,
            "version": version,
            "algorithm": algorithm,
            "hyperparameters": hyperparameters,
            "metrics": metrics,
            "is_selected": is_selected,
            "is_baseline": is_baseline,
            "artifact_path": artifact_path,
            "notes": notes,
            "registered_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self.registry_data["models"][key] = entry
        self._save()

    def get_selected_model_entry(self, task: str) -> Optional[Dict[str, Any]]:
        """Retrieves the active selected model metadata for a task."""
        for entry in self.registry_data["models"].values():
            if entry["task"] == task and entry.get("is_selected", False):
                return entry
        return None

    def list_models_for_task(self, task: str) -> List[Dict[str, Any]]:
        """Lists all registered models and baselines for a specific task."""
        return [
            entry for entry in self.registry_data["models"].values()
            if entry["task"] == task
        ]

    def get_all_models(self) -> List[Dict[str, Any]]:
        """Returns all registered models across all tasks."""
        return list(self.registry_data["models"].values())


def save_artifact(obj: Any, filename: str) -> str:
    """Serializes a model object using joblib into artifacts directory."""
    path = os.path.join(ARTIFACTS_DIR, filename)
    joblib.dump(obj, path)
    return path


def load_artifact(filename: str) -> Any:
    """Loads a serialized model object from artifacts directory."""
    path = os.path.join(ARTIFACTS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model artifact not found: {path}")
    return joblib.load(path)
