import json
import os
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from application.ports.repository import Repository

T = TypeVar("T", bound=BaseModel)


class JsonRepository(Repository):
    """Small atomic JSON persistence adapter for local development and tests."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, entity: T) -> T:
        self.save_many([entity])
        return entity

    def save_many(self, entities: Sequence[T]) -> list[T]:
        prepared = []
        for entity in entities:
            entity_id = getattr(entity, "id", None)
            if not isinstance(entity_id, str) or not entity_id:
                raise ValueError("persisted models must expose a non-empty string id")
            prepared.append((type(entity).__name__, entity_id, entity.model_dump(mode="json")))

        if not prepared:
            return []
        data = self._read()
        for collection_name, entity_id, payload in prepared:
            collection = data["records"].setdefault(collection_name, {})
            collection[entity_id] = payload
        self._write(data)
        return list(entities)

    def get(self, model_type: type[T], entity_id: str) -> T | None:
        record = self._read()["records"].get(model_type.__name__, {}).get(entity_id)
        return model_type.model_validate(record) if record is not None else None

    def list(self, model_type: type[T]) -> list[T]:
        records = self._read()["records"].get(model_type.__name__, {})
        return [model_type.model_validate(item) for item in records.values()]

    def _read(self) -> dict:
        if not self.path.exists():
            return {"schema_version": 1, "records": {}}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"repository file is invalid JSON: {self.path}") from exc
        if (
            not isinstance(data, dict)
            or data.get("schema_version") != 1
            or not isinstance(data.get("records"), dict)
        ):
            raise ValueError("unsupported JSON repository format")
        return data

    def _write(self, data: dict) -> None:
        fd, temp_name = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
                json.dump(data, temp_file, ensure_ascii=False, indent=2)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
