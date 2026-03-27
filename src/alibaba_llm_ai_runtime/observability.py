import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class JsonlEventLogger:
    def __init__(self, *, service_name: str, environment: str, log_path: str | Path):
        self._service_name = service_name
        self._environment = environment
        self._log_path = Path(log_path)
        self._logger = logging.getLogger(f"{service_name}.runtime")

    def emit(self, *, event_type: str, payload: dict[str, Any]) -> None:
        record = {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "service": self._service_name,
            "environment": self._environment,
            "event_type": event_type,
            "payload": payload,
        }
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
        self._logger.info("%s %s", event_type, json.dumps(payload, ensure_ascii=True))
