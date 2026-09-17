import json
from pathlib import Path
from threading import RLock
from typing import Callable, Dict, Generic, Iterable, List, Optional, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class JsonTable(Generic[T]):
    def __init__(self, path: Path, model: Type[T], key_field: str):
        self.path = path
        self.model = model
        self.key_field = key_field
        self._lock = RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def list(self) -> List[T]:
        with self._lock:
            return [self.model(**item) for item in self._read_raw()]

    def get(self, key: str) -> Optional[T]:
        for item in self.list():
            if getattr(item, self.key_field) == key:
                return item
        return None

    def upsert(self, record: T) -> T:
        with self._lock:
            raw = self._read_raw()
            key = getattr(record, self.key_field)
            replaced = False
            for index, item in enumerate(raw):
                if item.get(self.key_field) == key:
                    raw[index] = record.model_dump(mode="json")
                    replaced = True
                    break
            if not replaced:
                raw.append(record.model_dump(mode="json"))
            self._write_raw(raw)
            return record

    def update(self, key: str, updater: Callable[[T], T]) -> Optional[T]:
        with self._lock:
            record = self.get(key)
            if not record:
                return None
            return self.upsert(updater(record))

    def filter(self, **criteria: str) -> List[T]:
        def matches(record: T) -> bool:
            return all(getattr(record, field) == value for field, value in criteria.items() if value is not None)

        return [record for record in self.list() if matches(record)]

    def _read_raw(self) -> List[Dict]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def _write_raw(self, rows: Iterable[Dict]) -> None:
        self.path.write_text(json.dumps(list(rows), indent=2), encoding="utf-8")


runtime_dir = Path(__file__).resolve().parents[3] / ".seam" / "runtime"
