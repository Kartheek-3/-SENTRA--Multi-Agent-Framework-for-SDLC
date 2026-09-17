import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.api.projects import projects_db

router = APIRouter(prefix="/api/projects", tags=["filesystem"])


class SaveFileRequest(BaseModel):
    path: str
    content: str


class CreateEntryRequest(BaseModel):
    path: str
    type: str = "file"
    content: str = ""


class RenameEntryRequest(BaseModel):
    source_path: str
    target_path: str


class DeleteEntryRequest(BaseModel):
    path: str


def _project_root(project_id: str) -> Path:
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    state = projects_db[project_id]
    root = Path("generated_projects") / state.project_name
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def _safe_path(project_id: str, relative_path: str, allow_root: bool = False) -> Path:
    if relative_path is None:
        raise HTTPException(status_code=400, detail="Path is required")
    normalized = relative_path.replace("\\", "/").strip("/")
    if not normalized and not allow_root:
        raise HTTPException(status_code=400, detail="Path is required")
    if Path(normalized).is_absolute() or ".." in Path(normalized).parts:
        raise HTTPException(status_code=403, detail="Unsafe path")

    root = _project_root(project_id)
    target = (root / normalized).resolve()
    try:
        common = os.path.commonpath([str(root), str(target)])
    except ValueError:
        raise HTTPException(status_code=403, detail="Unsafe path")
    if common != str(root):
        raise HTTPException(status_code=403, detail="Path escapes project root")
    return target


def _entry(path: Path, root: Path):
    stat = path.stat()
    return {
        "name": path.name,
        "path": path.relative_to(root).as_posix(),
        "type": "directory" if path.is_dir() else "file",
        "modified": stat.st_mtime,
        "size": stat.st_size if path.is_file() else 0,
    }


@router.get("/{project_id}/filesystem/tree")
def get_file_tree(project_id: str, path: str = "", depth: int = 3):
    root = _project_root(project_id)
    base = _safe_path(project_id, path, allow_root=True)
    if not base.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    if not base.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    def walk(folder: Path, remaining_depth: int):
        children = []
        for child in sorted(folder.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
            if child.name in {"node_modules", ".git", "__pycache__"}:
                continue
            node = _entry(child, root)
            if child.is_dir() and remaining_depth > 0:
                node["children"] = walk(child, remaining_depth - 1)
            children.append(node)
        return children

    return {
        "root": root.as_posix(),
        "path": base.relative_to(root).as_posix() if base != root else "",
        "children": walk(base, max(0, min(depth, 8))),
    }


@router.get("/{project_id}/filesystem/file")
def read_file(project_id: str, path: str):
    target = _safe_path(project_id, path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if not target.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    try:
        return {"path": path.replace("\\", "/").strip("/"), "content": target.read_text(encoding="utf-8")}
    except UnicodeDecodeError:
        raise HTTPException(status_code=415, detail="File is not UTF-8 text")


@router.put("/{project_id}/filesystem/file")
def save_file(project_id: str, request: SaveFileRequest):
    target = _safe_path(project_id, request.path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(request.content, encoding="utf-8")
    return {"status": "saved", "path": request.path.replace("\\", "/").strip("/")}


@router.post("/{project_id}/filesystem/entry")
def create_entry(project_id: str, request: CreateEntryRequest):
    target = _safe_path(project_id, request.path)
    if target.exists():
        raise HTTPException(status_code=409, detail="Path already exists")
    if request.type == "directory":
        target.mkdir(parents=True, exist_ok=False)
    elif request.type == "file":
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(request.content, encoding="utf-8")
    else:
        raise HTTPException(status_code=400, detail="Type must be file or directory")
    return {"status": "created", "path": request.path.replace("\\", "/").strip("/"), "type": request.type}


@router.patch("/{project_id}/filesystem/entry")
def rename_entry(project_id: str, request: RenameEntryRequest):
    source = _safe_path(project_id, request.source_path)
    target = _safe_path(project_id, request.target_path)
    if not source.exists():
        raise HTTPException(status_code=404, detail="Source not found")
    if target.exists():
        raise HTTPException(status_code=409, detail="Target already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    source.rename(target)
    return {"status": "renamed", "path": request.target_path.replace("\\", "/").strip("/")}


@router.delete("/{project_id}/filesystem/entry")
def delete_entry(project_id: str, request: DeleteEntryRequest):
    target = _safe_path(project_id, request.path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    if target.is_dir():
        if any(target.iterdir()):
            raise HTTPException(status_code=400, detail="Directory is not empty")
        target.rmdir()
    else:
        target.unlink()
    return {"status": "deleted", "path": request.path.replace("\\", "/").strip("/")}
