import hashlib
import os
from pathlib import Path
from typing import Any, Iterable

from backend.events import event_bus
from backend.foundation.services import artifact_registry


def project_root(state) -> Path:
    root = Path("generated_projects") / state.project_name
    root.mkdir(parents=True, exist_ok=True)
    return root


def checksum_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_text_artifact(state, relative_path: str, content: str, artifact_type: str, agent: str, **metadata: Any) -> dict:
    return write_bytes_artifact(state, relative_path, content.encode("utf-8"), artifact_type, agent, text=True, **metadata)


def write_bytes_artifact(state, relative_path: str, content: bytes, artifact_type: str, agent: str, text: bool = False, **metadata: Any) -> dict:
    normalized = relative_path.replace("\\", "/").strip("/")
    if not normalized or Path(normalized).is_absolute() or ".." in Path(normalized).parts:
        raise ValueError(f"Unsafe artifact path: {relative_path}")

    root = project_root(state)
    target = (root / normalized).resolve()
    if os.path.commonpath([str(root.resolve()), str(target)]) != str(root.resolve()):
        raise ValueError(f"Artifact path escapes project root: {relative_path}")

    existed = target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)

    if not target.exists() or not target.is_file():
        raise RuntimeError(f"Artifact was not written: {normalized}")
    saved = target.read_bytes()
    if saved != content:
        raise RuntimeError(f"Artifact readback verification failed: {normalized}")

    artifact = artifact_registry.register_file(
        state.project_id,
        normalized,
        artifact_type,
        title=metadata.pop("title", normalized),
        agent_id=agent,
        project_name=state.project_name,
        checksum=checksum_bytes(saved),
        agent=agent,
        **metadata,
    )

    event_payload = {
        "project_id": state.project_id,
        "agent": agent,
        "agent_id": agent,
        "artifact_id": artifact.artifact_id,
        "path": normalized,
        "status": artifact.status,
        "summary": normalized,
        "artifact_type": artifact_type,
        "checksum": artifact.metadata.get("checksum"),
    }
    event_bus.emit_sync("FILE_UPDATED" if existed else "FILE_CREATED", event_payload)
    event_bus.emit_sync("FILE_UPDATED" if existed else "FILE_GENERATED", event_payload)
    event_bus.emit_sync("ARTIFACT_CREATED", event_payload)
    event_bus.emit_sync("ARTIFACT_REGISTERED", event_payload)
    return artifact.model_dump()


def write_many_text_artifacts(state, files: Iterable[tuple[str, str, str]], agent: str) -> list[dict]:
    artifacts = []
    for relative_path, content, artifact_type in files:
        artifacts.append(write_text_artifact(state, relative_path, content, artifact_type, agent))
    return artifacts
