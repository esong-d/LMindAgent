

import datetime as dt
import json
import uuid
from typing import Any, Callable, TypeVar


T = TypeVar("T")


def json_default(obj: Any) -> Any:
    if isinstance(obj, (dt.datetime, dt.date)):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    model_dump = getattr(obj, "model_dump", None)
    if callable(model_dump):
        return model_dump()
    to_dict = getattr(obj, "dict", None)
    if callable(to_dict):
        return to_dict()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def dumps_json(value: Any, *, default: Callable[[Any], Any] = json_default) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=default)


def loads_json(raw: str) -> Any:
    return json.loads(raw)


__all__ = [
    "T",
    "json_default",
    "dumps_json",
    "loads_json",
]
