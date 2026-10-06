import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

from backend.knowledge.knowledge_service import KnowledgeService
from backend.knowledge.models import KnowledgeDocument, KnowledgeSource, PRODUCTION_KNOWLEDGE_STATUSES, validate_knowledge_source


KNOWLEDGE_ROOT = Path(__file__).resolve().parents[2] / "knowledge"


def resolve_knowledge_path(path: Path) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == KNOWLEDGE_ROOT.name:
        return KNOWLEDGE_ROOT.parent / path
    candidate = Path.cwd() / path
    if candidate.exists():
        return candidate
    return KNOWLEDGE_ROOT / path


def resolve_knowledge_root(root: Optional[Path] = None) -> Path:
    return resolve_knowledge_path(root) if root else KNOWLEDGE_ROOT


def document_id_for(path: Path) -> str:
    path = resolve_knowledge_path(path)
    relative = path.resolve().relative_to(KNOWLEDGE_ROOT.resolve()).as_posix()
    return hashlib.sha256(relative.encode("utf-8")).hexdigest()


def parse_frontmatter(text: str) -> tuple[Dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip()
    body = text[end + 4:].lstrip()
    metadata: Dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip().lower()] = value.strip().strip('"')
    return metadata, body


def title_from_body(body: str, fallback: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def discover_documents(root: Optional[Path] = None) -> List[Path]:
    base = resolve_knowledge_root(root)
    if not base.exists():
        raise FileNotFoundError(f"Knowledge directory not found: {base}")
    return sorted(path for path in base.rglob("*.md") if path.is_file())


def load_document(path: Path) -> KnowledgeDocument:
    path = resolve_knowledge_path(path)
    text = path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(text)
    relative = path.resolve().relative_to(KNOWLEDGE_ROOT.resolve()).as_posix()
    category = metadata.get("category") or relative.split("/")[0]
    topic = metadata.get("topic") or path.stem
    parts = relative.split("/")
    domain = metadata.get("domain") or (
        parts[1] if len(parts) > 2 and parts[0] == "domains" else "general"
    )
    status = metadata.get("status", "VALIDATED").upper()
    version_raw = metadata.get("version", "1")
    version_match = re.search(r"\d+", version_raw)
    version = int(version_match.group(0)) if version_match else 1
    source_type = metadata.get("source_type") or ("SEAM_CURATED" if metadata.get("source", "").lower().startswith("seam") else "SEAM_CURATED")
    source = KnowledgeSource(
        source_type=source_type,
        organization=metadata.get("organization") or metadata.get("source") or "SEAM curated knowledge repository",
        title=metadata.get("title") or title_from_body(body, path.stem.replace("_", " ").title()),
        url=metadata.get("url") or None,
        document_version=metadata.get("document_version") or metadata.get("version"),
        publication_date=metadata.get("publication_date"),
        accessed_date=metadata.get("accessed_date"),
        domain=domain,
        category=category,
        topic=topic,
        status=status,
        license=metadata.get("license"),
        authors=metadata.get("authors"),
        publication=metadata.get("publication"),
        year=metadata.get("year"),
        doi=metadata.get("doi"),
        project_name=metadata.get("project_name"),
        project_version=metadata.get("project_version"),
        validation_result=metadata.get("validation_result"),
    )
    validate_knowledge_source(source)
    return KnowledgeDocument(
        knowledge_id=document_id_for(path),
        title=source.title,
        source=relative,
        source_type=source.source_type,
        source_metadata=source,
        category=category,
        domain=domain,
        topic=topic,
        content=body,
        version=version,
        validated=status,
        sensitivity="internal",
        tags=[topic, category, domain],
    )


def index_knowledge(root: Optional[Path] = None, service: Optional[KnowledgeService] = None) -> Dict:
    docs = discover_documents(root)
    if not docs:
        raise ValueError(f"No markdown knowledge documents found under {root or KNOWLEDGE_ROOT}")
    ks = service or KnowledgeService()
    valid_sources = []
    chunks = 0
    indexed = []
    for path in docs:
        doc = load_document(path)
        if doc.validated not in PRODUCTION_KNOWLEDGE_STATUSES:
            continue
        valid_sources.append(doc.source)
        chunk_count = ks.ingest_document(doc) or 0
        chunks += chunk_count
        indexed.append({"document_id": doc.knowledge_id, "source_path": doc.source, "domain": doc.domain, "category": doc.category, "chunks": chunk_count})
    ks.repository.delete_missing_sources(valid_sources)
    return {
        "status": "indexed",
        "knowledge_root": str((root or KNOWLEDGE_ROOT).resolve()),
        "documents_discovered": len(docs),
        "documents_indexed": len(indexed),
        "chunks_indexed": chunks,
        "collection_count": ks.repository.count(),
        "documents": indexed,
    }
