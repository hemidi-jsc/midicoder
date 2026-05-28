"""Queue Provider Abstraction — CP13: Background Job & Workflow Generator.

Module này cung cấp lớp trừu tượng QueueProvider cho việc xử lý background jobs,
cùng với các implement cho các backend phổ biến (Redis/Celery, RabbitMQ, SQS,
in-memory) để hỗ trợ đa nền tảng.

Sử dụng:
    from midicoder.packs.cp_full_workflow_scheduler.queue_provider import (
        QueueBackend, QueueConfig, QueueProviderFactory
    )

    # Tạo provider từ config dict
    provider = QueueProviderFactory.create_from_dict({
        "backend": "in_memory",
        "max_retries": 3,
    })

    await provider.connect(config)
    msg_id = await provider.enqueue(message)
"""

from __future__ import annotations

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class QueueBackend(str, Enum):
    """Loại backend cho message queue.

    Attributes:
        REDIS: Redis/Celery backend
        RABBITMQ: RabbitMQ backend (aio-pika)
        SQS: AWS Simple Queue Service
        IN_MEMORY: In-memory queue (dùng asyncio.Queue)
        KAFKA: Apache Kafka backend
    """

    REDIS = "redis"
    RABBITMQ = "rabbitmq"
    SQS = "sqs"
    IN_MEMORY = "in_memory"
    KAFKA = "kafka"


@dataclass
class QueueConfig:
    """Cấu hình cho message queue provider.

    Attributes:
        backend: Loại backend sử dụng.
        connection_url: URL kết nối đến queue server.
        max_retries: Số lần retry tối đa cho message.
        visibility_timeout: Thời gian visibility timeout (giây).
        dlq_enabled: Có bật dead-letter queue không.
        dlq_max_messages: Số message tối đa trong DLQ.
        dead_letter_queue_name: Tên của dead-letter queue.
    """

    backend: QueueBackend = QueueBackend.IN_MEMORY
    connection_url: str = ""
    max_retries: int = 3
    visibility_timeout: int = 30
    dlq_enabled: bool = False
    dlq_max_messages: int = 1000
    dead_letter_queue_name: str = "dlq"

    def to_dict(self) -> dict[str, Any]:
        """Chuyển QueueConfig sang dict."""
        return {
            "backend": self.backend.value,
            "connection_url": self.connection_url,
            "max_retries": self.max_retries,
            "visibility_timeout": self.visibility_timeout,
            "dlq_enabled": self.dlq_enabled,
            "dlq_max_messages": self.dlq_max_messages,
            "dead_letter_queue_name": self.dead_letter_queue_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueueConfig:
        """Tạo QueueConfig từ dict."""
        backend_val = data.get("backend", "in_memory")
        backend = QueueBackend(backend_val) if isinstance(backend_val, str) else backend_val

        return cls(
            backend=backend,
            connection_url=data.get("connection_url", ""),
            max_retries=data.get("max_retries", 3),
            visibility_timeout=data.get("visibility_timeout", 30),
            dlq_enabled=data.get("dlq_enabled", False),
            dlq_max_messages=data.get("dlq_max_messages", 1000),
            dead_letter_queue_name=data.get("dead_letter_queue_name", "dlq"),
        )


@dataclass
class QueueMessage:
    """Message trong queue — đại diện cho một job/task cần xử lý.

    Attributes:
        message_id: ID duy nhất của message.
        body: Nội dung message (dict).
        queue_name: Tên queue chứa message.
        priority: Mức độ ưu tiên (càng nhỏ càng ưu tiên cao).
        delay_seconds: Số giây trì hoãn trước khi message có thể dequeue.
        headers: Metadata bổ sung.
        tenant_id: Tenant ID cho multi-tenant isolation.
    """

    message_id: str = ""
    body: dict[str, Any] = field(default_factory=dict)
    queue_name: str = "default"
    priority: int = 0
    delay_seconds: int = 0
    headers: dict[str, Any] = field(default_factory=dict)
    tenant_id: str = ""

    def __post_init__(self) -> None:
        """Tự động generate message_id nếu chưa có."""
        if not self.message_id or not self.message_id.strip():
            self.message_id = str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        """Chuyển QueueMessage sang dict."""
        return {
            "message_id": self.message_id,
            "body": self.body,
            "queue_name": self.queue_name,
            "priority": self.priority,
            "delay_seconds": self.delay_seconds,
            "headers": self.headers,
            "tenant_id": self.tenant_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueueMessage:
        """Tạo QueueMessage từ dict."""
        return cls(
            message_id=data.get("message_id", ""),
            body=data.get("body", {}),
            queue_name=data.get("queue_name", "default"),
            priority=data.get("priority", 0),
            delay_seconds=data.get("delay_seconds", 0),
            headers=data.get("headers", {}),
            tenant_id=data.get("tenant_id", ""),
        )


class QueueProvider(ABC):
    """Lớp trừu tượng cho queue provider — định nghĩa interface chung.

    Cung cấp các phương thức cơ bản để thao tác với message queue:
    enqueue, dequeue, ack/nack, và quản lý queue lifecycle.
    """

    @abstractmethod
    async def connect(self, config: QueueConfig) -> None:
        """Thiết lập kết nối đến queue backend.

        Args:
            config: Cấu hình kết nối queue.

        Raises:
            MidicoderError: Nếu không thể kết nối đến queue backend.
        """

    @abstractmethod
    async def enqueue(self, message: QueueMessage) -> str:
        """Đưa message vào queue.

        Args:
            message: Message cần enqueue.

        Returns:
            Message ID của message đã enqueue.

        Raises:
            MidicoderError: Nếu enqueue thất bại.
        """

    @abstractmethod
    async def dequeue(self, queue_name: str, timeout: int = 5) -> QueueMessage | None:
        """Lấy message từ queue.

        Args:
            queue_name: Tên queue để dequeue.
            timeout: Thời gian chờ tối đa (giây).

        Returns:
            QueueMessage nếu có message, None nếu timeout.
        """

    @abstractmethod
    async def ack(self, message_id: str) -> None:
        """Xác nhận message đã được xử lý thành công.

        Args:
            message_id: ID của message cần xác nhận.
        """

    @abstractmethod
    async def nack(self, message_id: str, requeue: bool = True) -> None:
        """Bác bỏ message — xử lý thất bại.

        Args:
            message_id: ID của message cần bác bỏ.
            requeue: Có đưa message quay lại queue không.
        """

    @abstractmethod
    async def create_queue(self, queue_name: str, config: dict[str, Any] | None = None) -> None:
        """Tạo queue mới.

        Args:
            queue_name: Tên queue cần tạo.
            config: Cấu hình thêm cho queue (optional).
        """

    @abstractmethod
    async def delete_queue(self, queue_name: str) -> None:
        """Xóa queue.

        Args:
            queue_name: Tên queue cần xóa.
        """

    @abstractmethod
    async def get_queue_size(self, queue_name: str) -> int:
        """Lấy số message đang chờ trong queue.

        Args:
            queue_name: Tên queue.

        Returns:
            Số message trong queue.
        """

    @abstractmethod
    async def purge_queue(self, queue_name: str) -> None:
        """Xóa tất cả message trong queue.

        Args:
            queue_name: Tên queue cần purge.
        """

    @abstractmethod
    async def close(self) -> None:
        """Đóng kết nối đến queue backend."""


class MemoryQueueProvider(QueueProvider):
    """In-memory queue provider — dùng asyncio.Queue.

    Phù hợp cho development, testing, và các scenario không cần
    persistent queue. Không hỗ trợ multi-process.
    """

    def __init__(self) -> None:
        """Khởi tạo MemoryQueueProvider."""
        self._queues: dict[str, asyncio.Queue[QueueMessage]] = {}
        self._pending: dict[str, QueueMessage] = {}  # message_id -> message (dequeued, not acked)
        self._config: QueueConfig | None = None
        self._connected: bool = False

    async def connect(self, config: QueueConfig) -> None:
        """Thiết lập kết nối (in-memory không cần kết nối thực sự).

        Args:
            config: Cấu hình queue.

        Raises:
            MidicoderError: Nếu backend không phải IN_MEMORY.
        """
        if config.backend != QueueBackend.IN_MEMORY:
            EM.raise_error(
                ErrorCode.MDC-F20_JOB_SCHEDULE_FAILED,
                backend=config.backend.value,
                expected_backend=QueueBackend.IN_MEMORY.value,
                reason="MemoryQueueProvider chỉ hỗ trợ backend IN_MEMORY",
            )
        self._config = config
        self._connected = True
        # Tạo default queue nếu chưa có
        if "default" not in self._queues:
            self._queues["default"] = asyncio.Queue()

    async def enqueue(self, message: QueueMessage) -> str:
        """Đưa message vào queue trong bộ nhớ.

        Args:
            message: Message cần enqueue.

        Returns:
            Message ID.
        """
        if not self._connected:
            EM.raise_error(
                ErrorCode.MDC-F20_JOB_SCHEDULE_FAILED,
                reason="Provider chưa được connect. Gọi connect() trước khi enqueue.",
            )

        # Đảm bảo queue tồn tại
        if message.queue_name not in self._queues:
            self._queues[message.queue_name] = asyncio.Queue()

        await self._queues[message.queue_name].put(message)
        return message.message_id

    async def dequeue(self, queue_name: str, timeout: int = 5) -> QueueMessage | None:
        """Lấy message từ queue trong bộ nhớ.

        Args:
            queue_name: Tên queue.
            timeout: Thời gian chờ (giây).

        Returns:
            QueueMessage hoặc None nếu timeout.
        """
        if queue_name not in self._queues:
            return None

        try:
            message = await asyncio.wait_for(
                self._queues[queue_name].get(),
                timeout=timeout,
            )
            self._pending[message.message_id] = message
            return message
        except asyncio.TimeoutError:
            return None

    async def ack(self, message_id: str) -> None:
        """Xác nhận message đã xử lý xong — loại khỏi pending.

        Args:
            message_id: ID của message.
        """
        self._pending.pop(message_id, None)

    async def nack(self, message_id: str, requeue: bool = True) -> None:
        """Bác bỏ message — nếu requeue thì đưa lại vào queue.

        Args:
            message_id: ID của message.
            requeue: Có đưa lại vào queue không.
        """
        message = self._pending.pop(message_id, None)
        if message and requeue:
            if message.queue_name in self._queues:
                await self._queues[message.queue_name].put(message)

    async def create_queue(self, queue_name: str, config: dict[str, Any] | None = None) -> None:
        """Tạo queue mới trong bộ nhớ.

        Args:
            queue_name: Tên queue.
            config: Cấu hình thêm (bị bỏ qua cho in-memory).
        """
        if queue_name not in self._queues:
            self._queues[queue_name] = asyncio.Queue()

    async def delete_queue(self, queue_name: str) -> None:
        """Xóa queue khỏi bộ nhớ.

        Args:
            queue_name: Tên queue.
        """
        self._queues.pop(queue_name, None)
        # also remove any pending messages from this queue
        to_remove = [
            mid for mid, msg in self._pending.items() if msg.queue_name == queue_name
        ]
        for mid in to_remove:
            del self._pending[mid]

    async def get_queue_size(self, queue_name: str) -> int:
        """Lấy số message trong queue.

        Args:
            queue_name: Tên queue.

        Returns:
            Số message.
        """
        queue = self._queues.get(queue_name)
        return queue.qsize() if queue else 0

    async def purge_queue(self, queue_name: str) -> None:
        """Xóa tất cả message trong queue.

        Args:
            queue_name: Tên queue.
        """
        if queue_name in self._queues:
            q = self._queues[queue_name]
            while not q.empty():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    break

    async def close(self) -> None:
        """Đóng provider — xóa tất cả queues và pending messages."""
        self._queues.clear()
        self._pending.clear()
        self._connected = False


class RedisQueueProvider(QueueProvider):
    """Redis/Celery queue provider — stub implementation.

    Yêu cầu cài đặt `celery[redis]` để hoạt động đầy đủ.
    """

    def __init__(self) -> None:
        """Khởi tạo RedisQueueProvider."""
        self._config: QueueConfig | None = None
        self._connected: bool = False

    async def connect(self, config: QueueConfig) -> None:
        """Thiết lập kết nối đến Redis.

        Raises:
            NotImplementedError: Redis backend yêu cầu celery[redis].
        """
        raise NotImplementedError("Redis backend requires celery[redis] installed")

    async def enqueue(self, message: QueueMessage) -> str:
        """Đưa message vào Redis queue.

        Raises:
            NotImplementedError: Redis backend yêu cầu celery[redis].
        """
        raise NotImplementedError("Redis backend requires celery[redis] installed")

    async def dequeue(self, queue_name: str, timeout: int = 5) -> QueueMessage | None:
        """Lấy message từ Redis queue.

        Raises:
            NotImplementedError: Redis backend yêu cầu celery[redis].
        """
        raise NotImplementedError("Redis backend requires celery[redis] installed")

    async def ack(self, message_id: str) -> None:
        """Xác nhận message từ Redis.

        Raises:
            NotImplementedError: Redis backend yêu cầu celery[redis].
        """
        raise NotImplementedError("Redis backend requires celery[redis] installed")

    async def nack(self, message_id: str, requeue: bool = True) -> None:
        """Bác bỏ message từ Redis.

        Raises:
            NotImplementedError: Redis backend yêu cầu celery[redis].
        """
        raise NotImplementedError("Redis backend requires celery[redis] installed")

    async def create_queue(self, queue_name: str, config: dict[str, Any] | None = None) -> None:
        """Tạo queue trong Redis.

        Raises:
            NotImplementedError: Redis backend yêu cầu celery[redis].
        """
        raise NotImplementedError("Redis backend requires celery[redis] installed")

    async def delete_queue(self, queue_name: str) -> None:
        """Xóa queue trong Redis.

        Raises:
            NotImplementedError: Redis backend yêu cầu celery[redis].
        """
        raise NotImplementedError("Redis backend requires celery[redis] installed")

    async def get_queue_size(self, queue_name: str) -> int:
        """Lấy kích thước queue trong Redis.

        Raises:
            NotImplementedError: Redis backend yêu cầu celery[redis].
        """
        raise NotImplementedError("Redis backend requires celery[redis] installed")

    async def purge_queue(self, queue_name: str) -> None:
        """Xóa tất cả message trong Redis queue.

        Raises:
            NotImplementedError: Redis backend yêu cầu celery[redis].
        """
        raise NotImplementedError("Redis backend requires celery[redis] installed")

    async def close(self) -> None:
        """Đóng kết nối Redis."""
        self._connected = False


class RabbitMQQueueProvider(QueueProvider):
    """RabbitMQ queue provider — stub implementation.

    Yêu cầu cài đặt `aio-pika` để hoạt động đầy đủ.
    """

    def __init__(self) -> None:
        """Khởi tạo RabbitMQQueueProvider."""
        self._config: QueueConfig | None = None
        self._connected: bool = False

    async def connect(self, config: QueueConfig) -> None:
        """Thiết lập kết nối đến RabbitMQ.

        Raises:
            NotImplementedError: RabbitMQ backend yêu cầu aio-pika.
        """
        raise NotImplementedError("RabbitMQ backend requires aio-pika installed")

    async def enqueue(self, message: QueueMessage) -> str:
        """Đưa message vào RabbitMQ queue.

        Raises:
            NotImplementedError: RabbitMQ backend yêu cầu aio-pika.
        """
        raise NotImplementedError("RabbitMQ backend requires aio-pika installed")

    async def dequeue(self, queue_name: str, timeout: int = 5) -> QueueMessage | None:
        """Lấy message từ RabbitMQ queue.

        Raises:
            NotImplementedError: RabbitMQ backend yêu cầu aio-pika.
        """
        raise NotImplementedError("RabbitMQ backend requires aio-pika installed")

    async def ack(self, message_id: str) -> None:
        """Xác nhận message từ RabbitMQ.

        Raises:
            NotImplementedError: RabbitMQ backend yêu cầu aio-pika.
        """
        raise NotImplementedError("RabbitMQ backend requires aio-pika installed")

    async def nack(self, message_id: str, requeue: bool = True) -> None:
        """Bác bỏ message từ RabbitMQ.

        Raises:
            NotImplementedError: RabbitMQ backend yêu cầu aio-pika.
        """
        raise NotImplementedError("RabbitMQ backend requires aio-pika installed")

    async def create_queue(self, queue_name: str, config: dict[str, Any] | None = None) -> None:
        """Tạo queue trong RabbitMQ.

        Raises:
            NotImplementedError: RabbitMQ backend yêu cầu aio-pika.
        """
        raise NotImplementedError("RabbitMQ backend requires aio-pika installed")

    async def delete_queue(self, queue_name: str) -> None:
        """Xóa queue trong RabbitMQ.

        Raises:
            NotImplementedError: RabbitMQ backend yêu cầu aio-pika.
        """
        raise NotImplementedError("RabbitMQ backend requires aio-pika installed")

    async def get_queue_size(self, queue_name: str) -> int:
        """Lấy kích thước queue trong RabbitMQ.

        Raises:
            NotImplementedError: RabbitMQ backend yêu cầu aio-pika.
        """
        raise NotImplementedError("RabbitMQ backend requires aio-pika installed")

    async def purge_queue(self, queue_name: str) -> None:
        """Xóa tất cả message trong RabbitMQ queue.

        Raises:
            NotImplementedError: RabbitMQ backend yêu cầu aio-pika.
        """
        raise NotImplementedError("RabbitMQ backend requires aio-pika installed")

    async def close(self) -> None:
        """Đóng kết nối RabbitMQ."""
        self._connected = False


class SQSQueueProvider(QueueProvider):
    """AWS SQS queue provider — stub implementation.

    Yêu cầu cài đặt `boto3` để hoạt động đầy đủ.
    """

    def __init__(self) -> None:
        """Khởi tạo SQSQueueProvider."""
        self._config: QueueConfig | None = None
        self._connected: bool = False

    async def connect(self, config: QueueConfig) -> None:
        """Thiết lập kết nối đến AWS SQS.

        Raises:
            NotImplementedError: SQS backend yêu cầu boto3.
        """
        raise NotImplementedError("SQS backend requires boto3 installed")

    async def enqueue(self, message: QueueMessage) -> str:
        """Đưa message vào AWS SQS queue.

        Raises:
            NotImplementedError: SQS backend yêu cầu boto3.
        """
        raise NotImplementedError("SQS backend requires boto3 installed")

    async def dequeue(self, queue_name: str, timeout: int = 5) -> QueueMessage | None:
        """Lấy message từ AWS SQS queue.

        Raises:
            NotImplementedError: SQS backend yêu cầu boto3.
        """
        raise NotImplementedError("SQS backend requires boto3 installed")

    async def ack(self, message_id: str) -> None:
        """Xác nhận message từ AWS SQS.

        Raises:
            NotImplementedError: SQS backend yêu cầu boto3.
        """
        raise NotImplementedError("SQS backend requires boto3 installed")

    async def nack(self, message_id: str, requeue: bool = True) -> None:
        """Bác bỏ message từ AWS SQS.

        Raises:
            NotImplementedError: SQS backend yêu cầu boto3.
        """
        raise NotImplementedError("SQS backend requires boto3 installed")

    async def create_queue(self, queue_name: str, config: dict[str, Any] | None = None) -> None:
        """Tạo queue trong AWS SQS.

        Raises:
            NotImplementedError: SQS backend yêu cầu boto3.
        """
        raise NotImplementedError("SQS backend requires boto3 installed")

    async def delete_queue(self, queue_name: str) -> None:
        """Xóa queue trong AWS SQS.

        Raises:
            NotImplementedError: SQS backend yêu cầu boto3.
        """
        raise NotImplementedError("SQS backend requires boto3 installed")

    async def get_queue_size(self, queue_name: str) -> int:
        """Lấy kích thước queue trong AWS SQS.

        Raises:
            NotImplementedError: SQS backend yêu cầu boto3.
        """
        raise NotImplementedError("SQS backend requires boto3 installed")

    async def purge_queue(self, queue_name: str) -> None:
        """Xóa tất cả message trong AWS SQS queue.

        Raises:
            NotImplementedError: SQS backend yêu cầu boto3.
        """
        raise NotImplementedError("SQS backend requires boto3 installed")

    async def close(self) -> None:
        """Đóng kết nối AWS SQS."""
        self._connected = False


class QueueProviderFactory:
    """Factory class để tạo QueueProvider theo backend.

    Sử dụng:
        provider = QueueProviderFactory.create(QueueBackend.IN_MEMORY, config)
        provider = QueueProviderFactory.create_from_dict({"backend": "redis", ...})
    """

    _BACKEND_MAP: dict[QueueBackend, type[QueueProvider]] = {
        QueueBackend.REDIS: RedisQueueProvider,
        QueueBackend.RABBITMQ: RabbitMQQueueProvider,
        QueueBackend.SQS: SQSQueueProvider,
        QueueBackend.IN_MEMORY: MemoryQueueProvider,
        QueueBackend.KAFKA: RabbitMQQueueProvider,  # Kafka chưa có implementation, dùng stub
    }

    @classmethod
    def create(cls, backend: QueueBackend, config: QueueConfig) -> QueueProvider:
        """Tạo QueueProvider theo backend type.

        Args:
            backend: Loại backend.
            config: Cấu hình queue.

        Returns:
            Instance của QueueProvider phù hợp.

        Raises:
            MidicoderError: Nếu backend không được hỗ trợ.
        """
        provider_class = cls._BACKEND_MAP.get(backend)
        if provider_class is None:
            EM.raise_error(
                ErrorCode.MDC-F20_JOB_SCHEDULE_FAILED,
                backend=backend.value,
                supported_backends=[b.value for b in cls._BACKEND_MAP.keys()],
                reason=f"Backend {backend.value} chưa được hỗ trợ",
            )
        return provider_class()

    @classmethod
    def create_from_dict(cls, config_dict: dict[str, Any]) -> QueueProvider:
        """Tạo QueueProvider từ dict configuration.

        Args:
            config_dict: Dict chứa cấu hình queue (phải có key 'backend').

        Returns:
            Instance của QueueProvider phù hợp.
        """
        config = QueueConfig.from_dict(config_dict)
        return cls.create(config.backend, config)
