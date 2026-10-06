import json
import os
from typing import Dict, List, Optional

from backend.config import GITHUB_INTELLIGENCE_DIR
from backend.github.intelligence_models import RepositoryChangeSet, RepositoryRecord, RepositorySnapshot, utc_now


class RepositoryRegistry:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or GITHUB_INTELLIGENCE_DIR
        self.records_dir = os.path.join(self.base_dir, "records")
        self.snapshots_dir = os.path.join(self.base_dir, "snapshots")
        self.changes_dir = os.path.join(self.base_dir, "changes")
        os.makedirs(self.records_dir, exist_ok=True)
        os.makedirs(self.snapshots_dir, exist_ok=True)
        os.makedirs(self.changes_dir, exist_ok=True)

    def _repo_id(self, full_name: str) -> str:
        return full_name.lower().replace("/", "__")

    def _record_path(self, full_name: str) -> str:
        return os.path.join(self.records_dir, f"{self._repo_id(full_name)}.json")

    def get(self, full_name: str) -> Optional[RepositoryRecord]:
        path = self._record_path(full_name)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as handle:
            return RepositoryRecord.model_validate(json.load(handle))

    def save(self, record: RepositoryRecord) -> RepositoryRecord:
        record.updated_at = utc_now()
        with open(self._record_path(record.full_name), "w", encoding="utf-8") as handle:
            json.dump(record.model_dump(), handle, indent=2)
        return record

    def list_records(self) -> List[RepositoryRecord]:
        records: List[RepositoryRecord] = []
        for item in os.listdir(self.records_dir):
            if not item.endswith(".json"):
                continue
            with open(os.path.join(self.records_dir, item), "r", encoding="utf-8") as handle:
                records.append(RepositoryRecord.model_validate(json.load(handle)))
        return records

    def save_snapshot(self, snapshot: RepositorySnapshot) -> RepositorySnapshot:
        repo_dir = os.path.join(self.snapshots_dir, self._repo_id(snapshot.repository))
        os.makedirs(repo_dir, exist_ok=True)
        path = os.path.join(repo_dir, f"{snapshot.commit_sha}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(snapshot.model_dump(), handle, indent=2)
        with open(os.path.join(repo_dir, "latest.json"), "w", encoding="utf-8") as handle:
            json.dump(snapshot.model_dump(), handle, indent=2)
        return snapshot

    def latest_snapshot(self, full_name: str) -> Optional[RepositorySnapshot]:
        path = os.path.join(self.snapshots_dir, self._repo_id(full_name), "latest.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as handle:
            return RepositorySnapshot.model_validate(json.load(handle))

    def save_change_set(self, change_set: RepositoryChangeSet) -> RepositoryChangeSet:
        repo_dir = os.path.join(self.changes_dir, self._repo_id(change_set.repository))
        os.makedirs(repo_dir, exist_ok=True)
        path = os.path.join(repo_dir, f"{change_set.before_sha[:12]}_{change_set.after_sha[:12]}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(change_set.model_dump(), handle, indent=2)
        return change_set

    def mark_repository_rag_superseded(self, repository: str, active_commit: str) -> Dict[str, str]:
        marker_dir = os.path.join(self.base_dir, "rag_status", self._repo_id(repository))
        os.makedirs(marker_dir, exist_ok=True)
        marker = {
            "repository": repository,
            "active_commit_sha": active_commit,
            "superseded_at": utc_now(),
            "status": "SUPERSEDED_PREVIOUS_REPOSITORY_CONTEXT",
        }
        with open(os.path.join(marker_dir, "latest.json"), "w", encoding="utf-8") as handle:
            json.dump(marker, handle, indent=2)
        return marker
