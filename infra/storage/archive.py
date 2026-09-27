from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from urllib.parse import quote

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class ArchiveError(Exception):
    """Base exception for storage-layer errors."""


class SchemaParseError(ArchiveError):
    """Raised when raw data cannot be validated against the requested schema."""


class RecordNotFoundError(ArchiveError):
    """Raised when a required record does not exist."""


class JsonArchive:
    """
    JSON-file storage. No database.
    Layout: <base_dir>/<collection>/<record_id>.json
    """

    def __init__(self, base_dir: Union[str, Path] = "data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ---------- parsing ----------

    def parse_json_to_schema(
        self,
        data: Union[Dict[str, Any], str],
        model: Type[T],
    ) -> T:
        """Validate raw dict or JSON string into the given Pydantic model."""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as exc:
                raise SchemaParseError(
                    f"Invalid JSON for {model.__name__}: {exc}"
                ) from exc

        try:
            return model.model_validate(data)
        except ValidationError as exc:
            raise SchemaParseError(
                f"Data does not match schema {model.__name__}: {exc}"
            ) from exc

    # ---------- path helpers ----------

    def _collection_dir(self, collection: str) -> Path:
        path = self.base_dir / collection
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _record_path(self, collection: str, record_id: str) -> Path:
        safe_id = quote(record_id, safe="")
        return self._collection_dir(collection) / f"{safe_id}.json"

    # ---------- save / load one record ----------

    def save(self, collection: str, record_id: str, record: BaseModel) -> None:
        path = self._record_path(collection, record_id)
        payload = record.model_dump(mode="json")
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    def load(
        self, collection: str, record_id: str, model: Type[T]
    ) -> Optional[T]:
        path = self._record_path(collection, record_id)
        if not path.exists():
            return None
        return self.parse_json_to_schema(path.read_text(encoding="utf-8"), model)

    def require(self, collection: str, record_id: str, model: Type[T]) -> T:
        record = self.load(collection, record_id, model)
        if record is None:
            raise RecordNotFoundError(f"{collection}/{record_id} not found")
        return record

    def delete(self, collection: str, record_id: str) -> bool:
        path = self._record_path(collection, record_id)
        if path.exists():
            path.unlink()
            return True
        return False

    # ---------- bulk ----------

    def load_all(self, collection: str, model: Type[T]) -> List[T]:
        records: List[T] = []
        for file in sorted(self._collection_dir(collection).glob("*.json")):
            try:
                records.append(
                    self.parse_json_to_schema(
                        file.read_text(encoding="utf-8"), model
                    )
                )
            except SchemaParseError:
                # File hỏng hoặc lệch schema -> bỏ qua, không sập cả hệ thống
                continue
        return records

    def query(self, collection: str, model: Type[T], **filters: Any) -> List[T]:
        """Ví dụ: archive.query('predictions', Prediction, thesis_id='t1', status=PredictionStatus.ACTIVE)"""
        def matches(record: T) -> bool:
            return all(getattr(record, key, None) == value for key, value in filters.items())

        return [r for r in self.load_all(collection, model) if matches(r)]

    # ---------- append-only log (dùng cho Event / event_log) ----------

    def append_jsonl(self, stream_name: str, record: BaseModel) -> None:
        path = self.base_dir / f"{stream_name}.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.model_dump(mode="json"), default=str, ensure_ascii=False) + "\n")

    def load_jsonl(self, stream_name: str, model: Type[T]) -> List[T]:
        path = self.base_dir / f"{stream_name}.jsonl"
        if not path.exists():
            return []
        records: List[T] = []
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(self.parse_json_to_schema(line, model))
        return records