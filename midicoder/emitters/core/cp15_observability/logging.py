# coding: utf-8
"""
Mô-đun logging runtime engine (CP15).

Cung cấp:
- LogEntry: Log entry — immutable sau khi tạo, có SHA-256 hash cho tamper-evidence
- StructuredLogger: Structured JSON logger

Obligation: mỗi entry có immutable hash (SHA-256)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from midicoder.emitters.core.cp15_observability.models import LogLevel


@dataclass(frozen=True)
class LogEntry:
    """Log entry — immutable sau khi tạo.

    Attributes:
        timestamp: Thời gian tạo log
        level: Mức độ log
        message: Nội dung log
        service_name: Tên service
        trace_id: Trace ID (nếu có)
        span_id: Span ID (nếu có)
        fields: Fields bổ sung
        immutable_hash: SHA-256 hash cho tamper-evidence
    """

    timestamp: datetime
    level: str
    message: str
    service_name: str
    trace_id: str
    span_id: str
    fields: dict
    immutable_hash: str

    def verify_hash(self) -> bool:
        """Xác minh hash không bị thay đổi.

        Tính lại hash từ tất cả fields (trừ immutable_hash) và so sánh
        với hash đã lưu.

        Returns:
            True nếu hash khớp, False nếu bị thay đổi
        """
        data = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "message": self.message,
            "service_name": self.service_name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "fields": self.fields,
        }
        computed = hashlib.sha256(
            json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        return computed == self.immutable_hash

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary chứa tất cả attributes của LogEntry
        """
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "message": self.message,
            "service_name": self.service_name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "fields": self.fields,
            "immutable_hash": self.immutable_hash,
        }

    def to_json(self) -> str:
        """Convert to JSON string.

        Returns:
            Chuỗi JSON của LogEntry
        """
        return json.dumps(self.to_dict(), sort_keys=True, default=str)


class StructuredLogger:
    """Structured JSON logger.

    Cung cấp:
    - log(level, message, fields) -> ghi log entry
    - debug/info/warning/error/critical -> shorthand methods
    - entries() -> lấy tất cả entries
    - export_json() -> export tất cả entries làm JSON lines

    Obligation: mỗi entry có immutable hash (SHA-256)
    """

    def __init__(
        self,
        service_name: str = "midicoder",
        include_trace_id: bool = True,
        include_span_id: bool = True,
    ) -> None:
        """Khởi tạo StructuredLogger.

        Args:
            service_name: Tên service
            include_trace_id: Có include trace_id không
            include_span_id: Có include span_id không
        """
        self._service_name: str = service_name
        self._include_trace_id: bool = include_trace_id
        self._include_span_id: bool = include_span_id
        self._entries: list[LogEntry] = []

    def log(self, level: str, message: str, fields: Optional[dict] = None) -> LogEntry:
        """Ghi log entry. Returns entry.

        Tự động tạo timestamp và tính SHA-256 hash cho entry.

        Args:
            level: Mức độ log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Nội dung log
            fields: Các fields bổ sung (tùy chọn)

        Returns:
            LogEntry vừa tạo
        """
        if fields is None:
            fields = {}

        timestamp = datetime.now(timezone.utc)
        trace_id = ""
        span_id = ""

        if self._include_trace_id:
            trace_id = fields.get("trace_id", "")
        if self._include_span_id:
            span_id = fields.get("span_id", "")

        # Tính hash từ tất cả fields trừ immutable_hash
        hash_data = {
            "timestamp": timestamp.isoformat(),
            "level": level,
            "message": message,
            "service_name": self._service_name,
            "trace_id": trace_id,
            "span_id": span_id,
            "fields": fields,
        }
        immutable_hash = hashlib.sha256(
            json.dumps(hash_data, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()

        entry = LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            service_name=self._service_name,
            trace_id=trace_id,
            span_id=span_id,
            fields=dict(fields),
            immutable_hash=immutable_hash,
        )
        self._entries.append(entry)
        return entry

    def debug(self, message: str, fields: Optional[dict] = None) -> LogEntry:
        """Shorthand cho log(DEBUG, ...).

        Args:
            message: Nội dung log
            fields: Các fields bổ sung (tùy chọn)

        Returns:
            LogEntry vừa tạo
        """
        return self.log(LogLevel.DEBUG.value, message, fields)

    def info(self, message: str, fields: Optional[dict] = None) -> LogEntry:
        """Shorthand cho log(INFO, ...).

        Args:
            message: Nội dung log
            fields: Các fields bổ sung (tùy chọn)

        Returns:
            LogEntry vừa tạo
        """
        return self.log(LogLevel.INFO.value, message, fields)

    def warning(self, message: str, fields: Optional[dict] = None) -> LogEntry:
        """Shorthand cho log(WARNING, ...).

        Args:
            message: Nội dung log
            fields: Các fields bổ sung (tùy chọn)

        Returns:
            LogEntry vừa tạo
        """
        return self.log("WARNING", message, fields)

    def error(self, message: str, fields: Optional[dict] = None) -> LogEntry:
        """Shorthand cho log(ERROR, ...).

        Args:
            message: Nội dung log
            fields: Các fields bổ sung (tùy chọn)

        Returns:
            LogEntry vừa tạo
        """
        return self.log("ERROR", message, fields)

    def critical(self, message: str, fields: Optional[dict] = None) -> LogEntry:
        """Shorthand cho log(CRITICAL, ...).

        Args:
            message: Nội dung log
            fields: Các fields bổ sung (tùy chọn)

        Returns:
            LogEntry vừa tạo
        """
        return self.log("CRITICAL", message, fields)

    def entries(self) -> list[LogEntry]:
        """Lấy tất cả entries.

        Returns:
            Danh sách tất cả LogEntry đã ghi
        """
        return list(self._entries)

    def export_json(self) -> str:
        """Export entries làm JSON lines (mỗi entry một dòng JSON).

        Returns:
            Chuỗi JSON lines — mỗi dòng là một LogEntry
        """
        lines: list[str] = []
        for entry in self._entries:
            lines.append(entry.to_json())
        return "\n".join(lines) + "\n" if lines else ""
