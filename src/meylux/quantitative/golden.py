"""Deterministic golden-vector loader and exact runner."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping

from .numeric import serialize_decimal


def load_golden_vectors(path: str | Path) -> tuple[Mapping[str, Any], ...]:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise TypeError("golden vector file must contain a JSON array")
    vectors = tuple(payload)
    for index, vector in enumerate(vectors):
        if not isinstance(vector, Mapping):
            raise TypeError(f"golden vector {index} must be an object")
        for key in ("id", "function", "input", "expected"):
            if key not in vector:
                raise ValueError(f"golden vector {index} missing {key}")
    return vectors


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _canonical(value[k]) for k in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if hasattr(value, "value") and hasattr(value, "status"):
        return {
            "value": None if value.value is None else serialize_decimal(value.value),
            "status": value.status.value,
            "reason": value.reason,
        }
    if hasattr(value, "value") and hasattr(value, "reason"):
        return _canonical(value.value)
    if isinstance(value, str):
        return value
    return value


def run_golden_vectors(
    vectors: tuple[Mapping[str, Any], ...],
    functions: Mapping[str, Callable[..., Any]],
) -> None:
    for vector in vectors:
        function = functions.get(str(vector["function"]))
        if function is None:
            raise KeyError(f"unregistered golden function: {vector['function']}")
        args = vector["input"]
        if not isinstance(args, Mapping):
            raise TypeError(f"vector {vector['id']} input must be an object")
        actual = _canonical(function(**args))
        expected = _canonical(vector["expected"])
        if actual != expected:
            raise AssertionError(
                f"golden vector {vector['id']} mismatch: expected={expected!r} actual={actual!r}"
            )
