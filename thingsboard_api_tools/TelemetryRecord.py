from typing import Any
from datetime import datetime
from pydantic import field_serializer

try:
    from .TbModel import TbModel
except (ModuleNotFoundError, ImportError):
    from TbModel import TbModel


class TelemetryRecord(TbModel):

    values: dict[str, Any]
    ts: datetime | None

    @field_serializer("ts")
    def format_ts(ts):
        return int(ts.timestamp() * 1000)       # type: ignore


    def __str__(self):
        max_len = 20

        v = str(self.values)
        val_str = v[:max_len]
        if len(v) > max_len:
            val_str += "..."

        if self.ts is None:
            return ""       # Warning: Not sure what to do here because I'm not sure when this would happen.

        return f"ts: {int(self.ts.timestamp() * 1000)}, values: {val_str}"


    def __repr__(self):
        return self.__str__()
