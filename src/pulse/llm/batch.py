"""Batching and the per-item result cache (D-022 rules 1 and 3)."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence, TypeVar

from .base import LLMError
from .client import LLM

T = TypeVar("T")


class ResultCache:
    """JSON file per task, mapping item id to its result.

    Bump the task name (for example "themes-v2") when the prompt or schema
    changes, so old results are not reused.
    """

    def __init__(self, directory: Path | str) -> None:
        self.directory = Path(directory)

    def _path(self, task: str) -> Path:
        return self.directory / (re.sub(r"[^A-Za-z0-9._-]", "_", task) + ".json")

    def _load(self, task: str) -> dict[str, Any]:
        path = self._path(task)
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def get_many(self, task: str, ids: Iterable[str]) -> dict[str, Any]:
        stored = self._load(task)
        return {i: stored[i] for i in ids if i in stored}

    def put_many(self, task: str, results: dict[str, Any]) -> None:
        stored = self._load(task)
        stored.update(results)
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self._path(task)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(stored, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)


def chunks(items: Sequence[T], size: int) -> list[Sequence[T]]:
    if size < 1:
        raise ValueError("batch size must be at least 1")
    return [items[i : i + size] for i in range(0, len(items), size)]


def run_batched(
    llm: LLM,
    task: str,
    items: Sequence[T],
    *,
    item_id: Callable[[T], str],
    make_prompt: Callable[[Sequence[T]], str],
    schema: dict,
    extract: Callable[[Any, Sequence[T]], dict[str, Any]],
    cache: ResultCache | None = None,
    batch_size: int = 50,
) -> dict[str, Any]:
    """Run `items` through the LLM in batches and return {item id: result}.

    Items already in the cache are skipped, and each finished batch is saved
    straight away, so an interrupted run resumes where it stopped.
    """
    ids = [item_id(i) for i in items]
    if len(set(ids)) != len(ids):
        raise ValueError("item ids must be unique")

    results: dict[str, Any] = cache.get_many(task, ids) if cache else {}
    todo = [i for i in items if item_id(i) not in results]

    for batch in chunks(todo, batch_size):
        data = llm.complete(make_prompt(batch), schema)
        got = extract(data, batch)
        wanted = {item_id(i) for i in batch}
        missing = wanted - got.keys()
        if missing:
            raise LLMError(f"model skipped {len(missing)} of {len(wanted)} items in a batch")
        fresh = {k: v for k, v in got.items() if k in wanted}
        if cache:
            cache.put_many(task, fresh)
        results.update(fresh)
    return results
