import os
import json
import sqlite3
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager
from threading import RLock

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Configuration for SEAM database persistence.
    
    Architecture:
      - Local Development: SQLite (.seam/runtime/seam.db)
      - Production: PostgreSQL (via SEAM_POSTGRESQL_URL or DATABASE_URL)
      - RAG Semantic Knowledge: ChromaDB
      - Distributed Cache / Coordination: Redis
    """
    def __init__(self):
        self.backend = os.getenv("SEAM_DATABASE_BACKEND", "sqlite").lower()
        self.sqlite_path = Path(os.getenv("SEAM_SQLITE_PATH", Path(__file__).resolve().parents[2] / ".seam" / "runtime" / "seam.db"))
        self.postgres_url = os.getenv("SEAM_POSTGRESQL_URL", os.getenv("DATABASE_URL", ""))
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    def get_safe_url(self) -> str:
        """Returns connection string with masked password for audit logging."""
        if self.backend == "sqlite":
            return f"sqlite:///{self.sqlite_path}"
        if not self.postgres_url:
            return "postgresql://[NOT_CONFIGURED]"
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.postgres_url)
            netloc = parsed.hostname or "localhost"
            if parsed.port:
                netloc += f":{parsed.port}"
            if parsed.username:
                netloc = f"{parsed.username}:***@{netloc}"
            return f"{parsed.scheme}://{netloc}{parsed.path}"
        except Exception:
            return "postgresql://***:***@masked/db"

    @property
    def is_postgres_configured(self) -> bool:
        return bool(self.postgres_url.strip() and self.postgres_url.startswith("postgres"))


class DatabaseEngine:
    """Unified Database Persistence Abstraction for SEAM.
    
    Provides thread-safe transactional persistence for projects, events, and artifacts
    supporting both local development (SQLite) and production (PostgreSQL).
    """
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._lock = RLock()
        self._init_schema()

    def _get_connection(self):
        if self.config.backend == "postgresql":
            if not self.config.is_postgres_configured:
                raise ConnectionError("PostgreSQL requested but SEAM_POSTGRESQL_URL is not configured.")
            try:
                import psycopg2
                return psycopg2.connect(self.config.postgres_url)
            except ImportError:
                raise ImportError("psycopg2 package required for production PostgreSQL backend.")
        else:
            conn = sqlite3.connect(str(self.config.sqlite_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

    def _init_schema(self):
        """Initializes canonical relational tables through deterministic migrations."""
        if self.config.backend == "postgresql" and not self.config.is_postgres_configured:
            logger.info("PostgreSQL persistence not configured locally; skipping schema initialization.")
            return
        self.run_migrations()

    def run_migrations(self) -> List[str]:
        """Executes deterministic schema migrations in transactional order."""
        if self.config.backend == "postgresql" and not self.config.is_postgres_configured:
            logger.info("PostgreSQL persistence not configured locally; skipping migrations.")
            return []

        applied_now = []
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                # 0. Migration tracking table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version TEXT PRIMARY KEY,
                        description TEXT,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()

                cur.execute("SELECT version FROM schema_migrations;")
                already_applied = {row[0] for row in cur.fetchall()}

                # Migration 001: Canonical schema
                if "001_initial_schema" not in already_applied:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS projects (
                            project_id TEXT PRIMARY KEY,
                            project_name TEXT,
                            domain TEXT,
                            user_requirement TEXT,
                            workflow_status TEXT DEFAULT 'pending',
                            state_json TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS events (
                            event_id TEXT PRIMARY KEY,
                            sequence_number INTEGER,
                            project_id TEXT,
                            conversation_id TEXT,
                            task_id TEXT,
                            agent_id TEXT,
                            event_type TEXT,
                            payload_json TEXT,
                            timestamp TEXT
                        );
                    """)
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_project ON events(project_id);")
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_seq ON events(sequence_number);")

                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS artifacts (
                            artifact_id TEXT PRIMARY KEY,
                            project_id TEXT,
                            path TEXT,
                            type TEXT,
                            status TEXT,
                            metadata_json TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    cur.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_project ON artifacts(project_id);")

                    param_ph = "%s" if self.config.backend == "postgresql" else "?"
                    cur.execute(f"INSERT INTO schema_migrations (version, description) VALUES ({param_ph}, {param_ph});",
                                ("001_initial_schema", "Canonical schema for projects, events, and artifacts"))
                    conn.commit()
                    applied_now.append("001_initial_schema")

                return applied_now
            finally:
                conn.close()

    def get_applied_migrations(self) -> List[str]:
        """Returns list of all applied migration version strings."""
        if self.config.backend == "postgresql" and not self.config.is_postgres_configured:
            return []
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                if self.config.backend == "postgresql":
                    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='schema_migrations';")
                else:
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations';")
                if not cur.fetchone():
                    return []
                cur.execute("SELECT version FROM schema_migrations ORDER BY version ASC;")
                return [r[0] for r in cur.fetchall()]
            finally:
                conn.close()

    @contextmanager
    def transaction(self):
        """Transaction context manager with automatic rollback on error."""
        with self._lock:
            conn = self._get_connection()
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database transaction error: {e}")
                raise
            finally:
                conn.close()

    def validate_connection(self) -> Dict[str, Any]:
        """Probes and validates database connectivity."""
        result = {
            "backend": self.config.backend,
            "url": self.config.get_safe_url(),
            "status": "NOT_CONFIGURED",
            "writable": False,
            "error": None
        }
        if self.config.backend == "postgresql":
            if not self.config.is_postgres_configured:
                result["status"] = "NOT_CONFIGURED"
                result["error"] = "SEAM_POSTGRESQL_URL is not set"
                return result
            try:
                with self.transaction() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT 1;")
                    result["status"] = "PASS"
                    result["writable"] = True
            except Exception as e:
                result["status"] = "ERROR"
                result["error"] = str(e)
            return result
        else:
            try:
                with self.transaction() as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT 1;")
                    result["status"] = "PASS"
                    result["writable"] = True
            except Exception as e:
                result["status"] = "ERROR"
                result["error"] = str(e)
            return result

    def validate_schema(self) -> Dict[str, Any]:
        """Validates canonical tables exist and conform to schema contract."""
        required_tables = ["projects", "events", "artifacts"]
        present_tables = []
        try:
            with self._lock:
                conn = self._get_connection()
                cur = conn.cursor()
                if self.config.backend == "postgresql":
                    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
                    present_tables = [row[0] for row in cur.fetchall()]
                else:
                    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    present_tables = [row[0] for row in cur.fetchall()]
                conn.close()

            missing = [t for t in required_tables if t not in present_tables]
            return {
                "valid": len(missing) == 0,
                "required_tables": required_tables,
                "present_tables": present_tables,
                "missing_tables": missing
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    # Projects CRUD
    def save_project(self, project_id: str, project_name: str, domain: str, user_requirement: str, state_dict: Dict[str, Any], workflow_status: str = "pending") -> None:
        with self.transaction() as conn:
            cur = conn.cursor()
            state_json = json.dumps(state_dict)
            if self.config.backend == "postgresql":
                cur.execute("""
                    INSERT INTO projects (project_id, project_name, domain, user_requirement, workflow_status, state_json, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (project_id) DO UPDATE SET
                        project_name = EXCLUDED.project_name,
                        domain = EXCLUDED.domain,
                        user_requirement = EXCLUDED.user_requirement,
                        workflow_status = EXCLUDED.workflow_status,
                        state_json = EXCLUDED.state_json,
                        updated_at = CURRENT_TIMESTAMP;
                """, (project_id, project_name, domain, user_requirement, workflow_status, state_json))
            else:
                cur.execute("""
                    INSERT INTO projects (project_id, project_name, domain, user_requirement, workflow_status, state_json, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(project_id) DO UPDATE SET
                        project_name = excluded.project_name,
                        domain = excluded.domain,
                        user_requirement = excluded.user_requirement,
                        workflow_status = excluded.workflow_status,
                        state_json = excluded.state_json,
                        updated_at = CURRENT_TIMESTAMP;
                """, (project_id, project_name, domain, user_requirement, workflow_status, state_json))

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                if self.config.backend == "postgresql":
                    cur.execute("SELECT project_id, project_name, domain, user_requirement, workflow_status, state_json FROM projects WHERE project_id = %s;", (project_id,))
                else:
                    cur.execute("SELECT project_id, project_name, domain, user_requirement, workflow_status, state_json FROM projects WHERE project_id = ?;", (project_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "project_id": row[0],
                    "project_name": row[1],
                    "domain": row[2],
                    "user_requirement": row[3],
                    "workflow_status": row[4],
                    "state": json.loads(row[5]) if row[5] else {}
                }
            finally:
                conn.close()

    def list_projects(self) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute("SELECT project_id, project_name, domain, workflow_status FROM projects ORDER BY updated_at DESC;")
                rows = cur.fetchall()
                return [{"project_id": r[0], "project_name": r[1], "domain": r[2], "workflow_status": r[3]} for r in rows]
            finally:
                conn.close()

    # Events CRUD
    def append_event(self, event_dict: Dict[str, Any]) -> int:
        with self.transaction() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(MAX(sequence_number), 0) + 1 FROM events;")
            seq = cur.fetchone()[0]
            event_id = event_dict.get("event_id") or f"evt_{seq}_{event_dict.get('timestamp')}"
            payload_json = json.dumps(event_dict)
            if self.config.backend == "postgresql":
                cur.execute("""
                    INSERT INTO events (event_id, sequence_number, project_id, conversation_id, task_id, agent_id, event_type, payload_json, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    event_id,
                    seq,
                    event_dict.get("project_id"),
                    event_dict.get("conversation_id"),
                    event_dict.get("task_id"),
                    event_dict.get("agent_id"),
                    event_dict.get("event", event_dict.get("event_type", "UNKNOWN")),
                    payload_json,
                    event_dict.get("timestamp")
                ))
            else:
                cur.execute("""
                    INSERT INTO events (event_id, sequence_number, project_id, conversation_id, task_id, agent_id, event_type, payload_json, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    event_id,
                    seq,
                    event_dict.get("project_id"),
                    event_dict.get("conversation_id"),
                    event_dict.get("task_id"),
                    event_dict.get("agent_id"),
                    event_dict.get("event", event_dict.get("event_type", "UNKNOWN")),
                    payload_json,
                    event_dict.get("timestamp")
                ))
            return seq

    def list_events(self, project_id: Optional[str] = None, since_seq: Optional[int] = None) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                query = "SELECT payload_json FROM events WHERE 1=1"
                params = []
                param_placeholder = "%s" if self.config.backend == "postgresql" else "?"
                if project_id:
                    query += f" AND project_id = {param_placeholder}"
                    params.append(project_id)
                if since_seq is not None:
                    query += f" AND sequence_number > {param_placeholder}"
                    params.append(since_seq)
                query += " ORDER BY sequence_number ASC;"
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                return [json.loads(r[0]) for r in rows]
            finally:
                conn.close()

    # Artifacts CRUD
    def save_artifact(self, artifact_id: str, project_id: str, path: str, artifact_type: str, status: str, metadata_dict: Dict[str, Any]) -> None:
        with self.transaction() as conn:
            cur = conn.cursor()
            meta_json = json.dumps(metadata_dict)
            if self.config.backend == "postgresql":
                cur.execute("""
                    INSERT INTO artifacts (artifact_id, project_id, path, type, status, metadata_json, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (artifact_id) DO UPDATE SET
                        project_id = EXCLUDED.project_id,
                        path = EXCLUDED.path,
                        type = EXCLUDED.type,
                        status = EXCLUDED.status,
                        metadata_json = EXCLUDED.metadata_json,
                        updated_at = CURRENT_TIMESTAMP;
                """, (artifact_id, project_id, path, artifact_type, status, meta_json))
            else:
                cur.execute("""
                    INSERT INTO artifacts (artifact_id, project_id, path, type, status, metadata_json, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(artifact_id) DO UPDATE SET
                        project_id = excluded.project_id,
                        path = excluded.path,
                        type = excluded.type,
                        status = excluded.status,
                        metadata_json = excluded.metadata_json,
                        updated_at = CURRENT_TIMESTAMP;
                """, (artifact_id, project_id, path, artifact_type, status, meta_json))

    def get_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                param_placeholder = "%s" if self.config.backend == "postgresql" else "?"
                cur.execute(f"SELECT artifact_id, project_id, path, type, status, metadata_json FROM artifacts WHERE artifact_id = {param_placeholder};", (artifact_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "artifact_id": row[0],
                    "project_id": row[1],
                    "path": row[2],
                    "type": row[3],
                    "status": row[4],
                    "metadata": json.loads(row[5]) if row[5] else {}
                }
            finally:
                conn.close()

    def list_artifacts(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                query = "SELECT artifact_id, project_id, path, type, status, metadata_json FROM artifacts"
                params = []
                if project_id:
                    param_placeholder = "%s" if self.config.backend == "postgresql" else "?"
                    query += f" WHERE project_id = {param_placeholder}"
                    params.append(project_id)
                query += " ORDER BY created_at DESC;"
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                return [{
                    "artifact_id": r[0],
                    "project_id": r[1],
                    "path": r[2],
                    "type": r[3],
                    "status": r[4],
                    "metadata": json.loads(r[5]) if r[5] else {}
                } for r in rows]
            finally:
                conn.close()

# Global default instance
db_engine = DatabaseEngine()

