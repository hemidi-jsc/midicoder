"""Kiểm tra Queue Provider abstraction — CP13: Background Job & Workflow Generator.

Module này kiểm tra toàn bộ các thành phần của queue provider:
- QueueBackend enum
- QueueConfig dataclass
- QueueMessage dataclass
- MemoryQueueProvider (in-memory implementation)
- RedisQueueProvider (stub — NotImplementedError)
- RabbitMQQueueProvider (stub — NotImplementedError)
- SQSQueueProvider (stub — NotImplementedError)
- QueueProviderFactory
"""

import pytest
import asyncio
from midicoder.packs.cp_full_workflow_scheduler.queue_provider import (
    QueueBackend, QueueConfig, QueueMessage, QueueProvider,
    MemoryQueueProvider, RedisQueueProvider, RabbitMQQueueProvider, SQSQueueProvider,
    QueueProviderFactory,
)
from midicoder.errors import MidicoderError, ErrorCode


class TestQueueBackend:
    """Kiểm tra các giá trị enum của QueueBackend."""

    def test_redis_value(self):
        """Kiểm tra giá trị REDIS."""
        assert QueueBackend.REDIS.value == "redis"

    def test_rabbitmq_value(self):
        """Kiểm tra giá trị RABBITMQ."""
        assert QueueBackend.RABBITMQ.value == "rabbitmq"

    def test_sqs_value(self):
        """Kiểm tra giá trị SQS."""
        assert QueueBackend.SQS.value == "sqs"

    def test_in_memory_value(self):
        """Kiểm tra giá trị IN_MEMORY."""
        assert QueueBackend.IN_MEMORY.value == "in_memory"

    def test_kafka_value(self):
        """Kiểm tra giá trị KAFKA."""
        assert QueueBackend.KAFKA.value == "kafka"


class TestQueueConfig:
    """Kiểm tra QueueConfig dataclass."""

    def test_create_with_defaults(self):
        """Kiểm tra tạo QueueConfig với các giá trị mặc định."""
        config = QueueConfig()

        assert config.backend == QueueBackend.IN_MEMORY
        assert config.connection_url == ""
        assert config.max_retries == 3
        assert config.visibility_timeout == 30
        assert config.dlq_enabled is False
        assert config.dlq_max_messages == 1000
        assert config.dead_letter_queue_name == "dlq"

    def test_to_dict(self):
        """Kiểm tra chuyển QueueConfig sang dict."""
        config = QueueConfig(
            backend=QueueBackend.REDIS,
            connection_url="redis://localhost:6379",
            max_retries=5,
            visibility_timeout=60,
            dlq_enabled=True,
            dlq_max_messages=500,
            dead_letter_queue_name="custom-dlq",
        )

        d = config.to_dict()

        assert d["backend"] == "redis"
        assert d["connection_url"] == "redis://localhost:6379"
        assert d["max_retries"] == 5
        assert d["visibility_timeout"] == 60
        assert d["dlq_enabled"] is True
        assert d["dlq_max_messages"] == 500
        assert d["dead_letter_queue_name"] == "custom-dlq"

    def test_from_dict_roundtrip(self):
        """Kiểm tra roundtrip to_dict() -> from_dict()."""
        original = QueueConfig(
            backend=QueueBackend.RABBITMQ,
            connection_url="amqp://guest:guest@localhost",
            max_retries=10,
            visibility_timeout=45,
            dlq_enabled=True,
            dlq_max_messages=2000,
            dead_letter_queue_name="rabbit-dlq",
        )

        restored = QueueConfig.from_dict(original.to_dict())

        assert restored.backend == original.backend
        assert restored.connection_url == original.connection_url
        assert restored.max_retries == original.max_retries
        assert restored.visibility_timeout == original.visibility_timeout
        assert restored.dlq_enabled == original.dlq_enabled
        assert restored.dlq_max_messages == original.dlq_max_messages
        assert restored.dead_letter_queue_name == original.dead_letter_queue_name

    def test_from_dict_with_defaults(self):
        """Kiểm tra from_dict với dict rỗng — sử dụng giá trị mặc định."""
        config = QueueConfig.from_dict({})

        assert config.backend == QueueBackend.IN_MEMORY
        assert config.connection_url == ""
        assert config.max_retries == 3
        assert config.visibility_timeout == 30
        assert config.dlq_enabled is False
        assert config.dlq_max_messages == 1000
        assert config.dead_letter_queue_name == "dlq"


class TestQueueMessage:
    """Kiểm tra QueueMessage dataclass."""

    def test_create_with_auto_generated_message_id(self):
        """Kiểm tra tự động generate message_id khi để rỗng."""
        message = QueueMessage(body={"task": "test"})

        assert message.message_id != ""
        assert len(message.message_id) == 36  # UUID-4 format

    def test_create_with_explicit_message_id(self):
        """Kiểm tra sử dụng message_id do người dùng cung cấp."""
        explicit_id = "custom-message-id-123"
        message = QueueMessage(message_id=explicit_id, body={"task": "test"})

        assert message.message_id == explicit_id

    def test_create_with_defaults(self):
        """Kiểm tra tạo QueueMessage với các giá trị mặc định."""
        message = QueueMessage()

        assert message.message_id != ""
        assert message.body == {}
        assert message.queue_name == "default"
        assert message.priority == 0
        assert message.delay_seconds == 0
        assert message.headers == {}
        assert message.tenant_id == ""

    def test_to_dict_roundtrip(self):
        """Kiểm tra roundtrip to_dict() -> from_dict()."""
        original = QueueMessage(
            message_id="test-id-456",
            body={"action": "process", "data": [1, 2, 3]},
            queue_name="test-queue",
            priority=5,
            delay_seconds=10,
            headers={"content-type": "application/json"},
            tenant_id="tenant-abc",
        )

        d = original.to_dict()
        restored = QueueMessage.from_dict(d)

        assert restored.message_id == original.message_id
        assert restored.body == original.body
        assert restored.queue_name == original.queue_name
        assert restored.priority == original.priority
        assert restored.delay_seconds == original.delay_seconds
        assert restored.headers == original.headers
        assert restored.tenant_id == original.tenant_id

    def test_from_dict_generates_id_when_empty(self):
        """Kiểm tra from_dict tự generate ID khi message_id rỗng."""
        data = {"body": {"task": "no-id"}}
        message = QueueMessage.from_dict(data)

        assert message.message_id != ""
        assert message.body == {"task": "no-id"}


class TestMemoryQueueProvider:
    """Kiểm tra MemoryQueueProvider — in-memory implementation."""

    @pytest.mark.asyncio
    async def test_connect_succeeds(self):
        """Kiểm tra connect() thành công với backend IN_MEMORY."""
        provider = MemoryQueueProvider()
        config = QueueConfig(backend=QueueBackend.IN_MEMORY)

        await provider.connect(config)

        assert provider._connected is True
        assert provider._config == config

    @pytest.mark.asyncio
    async def test_connect_raises_for_wrong_backend(self):
        """Kiểm tra connect() raise lỗi khi backend không phải IN_MEMORY."""
        provider = MemoryQueueProvider()
        config = QueueConfig(backend=QueueBackend.REDIS)

        with pytest.raises(MidicoderError):
            await provider.connect(config)

    @pytest.mark.asyncio
    async def test_create_queue(self):
        """Kiểm tra create_queue() tạo queue mới."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        await provider.create_queue("new-queue")

        assert "new-queue" in provider._queues

    @pytest.mark.asyncio
    async def test_create_queue_idempotent(self):
        """Kiểm tra create_queue() không tạo queue trùng lặp."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        await provider.create_queue("same-queue")
        await provider.create_queue("same-queue")

        assert "same-queue" in provider._queues

    @pytest.mark.asyncio
    async def test_enqueue_returns_message_id(self):
        """Kiểm tra enqueue() thêm message và trả về message_id."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        message = QueueMessage(message_id="msg-001", body={"task": "enqueue-test"})
        returned_id = await provider.enqueue(message)

        assert returned_id == "msg-001"
        size = await provider.get_queue_size(message.queue_name)
        assert size == 1

    @pytest.mark.asyncio
    async def test_enqueue_creates_queue_automatically(self):
        """Kiểm tra enqueue() tự động tạo queue nếu chưa tồn tại."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        message = QueueMessage(queue_name="auto-created-queue", body={"task": "test"})
        await provider.enqueue(message)

        assert "auto-created-queue" in provider._queues

    @pytest.mark.asyncio
    async def test_enqueue_raises_when_not_connected(self):
        """Kiểm tra enqueue() raise lỗi khi chưa connect."""
        provider = MemoryQueueProvider()

        message = QueueMessage(body={"task": "test"})

        with pytest.raises(MidicoderError):
            await provider.enqueue(message)

    @pytest.mark.asyncio
    async def test_dequeue_returns_message_in_fifo_order(self):
        """Kiểm tra dequeue() trả về message theo thứ tự FIFO."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        msg1 = QueueMessage(message_id="first", body={"order": 1})
        msg2 = QueueMessage(message_id="second", body={"order": 2})
        msg3 = QueueMessage(message_id="third", body={"order": 3})

        await provider.enqueue(msg1)
        await provider.enqueue(msg2)
        await provider.enqueue(msg3)

        d1 = await provider.dequeue("default", timeout=1)
        d2 = await provider.dequeue("default", timeout=1)
        d3 = await provider.dequeue("default", timeout=1)

        assert d1.message_id == "first"
        assert d2.message_id == "second"
        assert d3.message_id == "third"

    @pytest.mark.asyncio
    async def test_dequeue_returns_none_when_empty(self):
        """Kiểm tra dequeue() trả về None khi queue rỗng (timeout)."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        result = await provider.dequeue("default", timeout=0)

        assert result is None

    @pytest.mark.asyncio
    async def test_dequeue_returns_none_for_nonexistent_queue(self):
        """Kiểm tra dequeue() trả về None khi queue không tồn tại."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        result = await provider.dequeue("nonexistent", timeout=1)

        assert result is None

    @pytest.mark.asyncio
    async def test_ack_removes_message_from_pending(self):
        """Kiểm tra ack() loại message khỏi pending."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        msg = QueueMessage(message_id="ack-test", body={"task": "ack"})
        await provider.enqueue(msg)
        dequeued = await provider.dequeue("default", timeout=1)

        assert dequeued is not None
        assert "ack-test" in provider._pending

        await provider.ack("ack-test")

        assert "ack-test" not in provider._pending

    @pytest.mark.asyncio
    async def test_nack_with_requeue_puts_message_back(self):
        """Kiểm tra nack() với requeue=True đưa message quay lại queue."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        msg = QueueMessage(message_id="requeue-test", body={"task": "nack-requeue"})
        await provider.enqueue(msg)
        dequeued = await provider.dequeue("default", timeout=1)

        assert dequeued is not None

        await provider.nack("requeue-test", requeue=True)

        size = await provider.get_queue_size("default")
        assert size == 1

        re_dequeued = await provider.dequeue("default", timeout=1)
        assert re_dequeued.message_id == "requeue-test"

    @pytest.mark.asyncio
    async def test_nack_without_requeue_discards_message(self):
        """Kiểm tra nack() với requeue=False loại bỏ message."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        msg = QueueMessage(message_id="discard-test", body={"task": "nack-discard"})
        await provider.enqueue(msg)
        dequeued = await provider.dequeue("default", timeout=1)

        assert dequeued is not None

        await provider.nack("discard-test", requeue=False)

        size = await provider.get_queue_size("default")
        assert size == 0

    @pytest.mark.asyncio
    async def test_get_queue_size_returns_correct_count(self):
        """Kiểm tra get_queue_size() trả về số message chính xác."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        assert await provider.get_queue_size("default") == 0

        for i in range(5):
            await provider.enqueue(QueueMessage(body={"index": i}))

        assert await provider.get_queue_size("default") == 5

    @pytest.mark.asyncio
    async def test_get_queue_size_returns_zero_for_unknown_queue(self):
        """Kiểm tra get_queue_size() trả về 0 cho queue không tồn tại."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        size = await provider.get_queue_size("unknown-queue")

        assert size == 0

    @pytest.mark.asyncio
    async def test_purge_queue_clears_all_messages(self):
        """Kiểm tra purge_queue() xóa tất cả message trong queue."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        for i in range(3):
            await provider.enqueue(QueueMessage(body={"index": i}))

        assert await provider.get_queue_size("default") == 3

        await provider.purge_queue("default")

        assert await provider.get_queue_size("default") == 0

    @pytest.mark.asyncio
    async def test_delete_queue_removes_queue(self):
        """Kiểm tra delete_queue() xóa queue khỏi bộ nhớ."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        await provider.create_queue("to-delete")
        assert "to-delete" in provider._queues

        await provider.delete_queue("to-delete")

        assert "to-delete" not in provider._queues

    @pytest.mark.asyncio
    async def test_delete_queue_removes_pending_messages(self):
        """Kiểm tra delete_queue() cũng xóa các pending messages của queue."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        msg = QueueMessage(message_id="pending-msg", body={"task": "test"}, queue_name="del-queue")
        await provider.create_queue("del-queue")
        await provider.enqueue(msg)
        dequeued = await provider.dequeue("del-queue", timeout=1)

        assert dequeued is not None
        assert "pending-msg" in provider._pending

        await provider.delete_queue("del-queue")

        assert "pending-msg" not in provider._pending

    @pytest.mark.asyncio
    async def test_close_cleans_up(self):
        """Kiểm tra close() xóa tất cả queues và pending messages."""
        provider = MemoryQueueProvider()
        await provider.connect(QueueConfig())

        await provider.create_queue("test-q")
        await provider.enqueue(QueueMessage(body={"task": "cleanup"}))

        await provider.close()

        assert provider._connected is False
        assert len(provider._queues) == 0
        assert len(provider._pending) == 0


class TestRedisQueueProvider:
    """Kiểm tra RedisQueueProvider — stub NotImplementedError."""

    @pytest.mark.asyncio
    async def test_connect_raises_not_implemented(self):
        """Kiểm tra connect() raise NotImplementedError."""
        provider = RedisQueueProvider()
        config = QueueConfig(backend=QueueBackend.REDIS)

        with pytest.raises(NotImplementedError, match=r"celery\[redis\]"):
            await provider.connect(config)

    @pytest.mark.asyncio
    async def test_enqueue_raises_not_implemented(self):
        """Kiểm tra enqueue() raise NotImplementedError."""
        provider = RedisQueueProvider()
        message = QueueMessage(body={"task": "test"})

        with pytest.raises(NotImplementedError, match=r"celery\[redis\]"):
            await provider.enqueue(message)

    @pytest.mark.asyncio
    async def test_dequeue_raises_not_implemented(self):
        """Kiểm tra dequeue() raise NotImplementedError."""
        provider = RedisQueueProvider()

        with pytest.raises(NotImplementedError, match=r"celery\[redis\]"):
            await provider.dequeue("queue")

    @pytest.mark.asyncio
    async def test_ack_raises_not_implemented(self):
        """Kiểm tra ack() raise NotImplementedError."""
        provider = RedisQueueProvider()

        with pytest.raises(NotImplementedError, match=r"celery\[redis\]"):
            await provider.ack("msg-id")

    @pytest.mark.asyncio
    async def test_nack_raises_not_implemented(self):
        """Kiểm tra nack() raise NotImplementedError."""
        provider = RedisQueueProvider()

        with pytest.raises(NotImplementedError, match=r"celery\[redis\]"):
            await provider.nack("msg-id")

    @pytest.mark.asyncio
    async def test_create_queue_raises_not_implemented(self):
        """Kiểm tra create_queue() raise NotImplementedError."""
        provider = RedisQueueProvider()

        with pytest.raises(NotImplementedError, match=r"celery\[redis\]"):
            await provider.create_queue("queue")

    @pytest.mark.asyncio
    async def test_delete_queue_raises_not_implemented(self):
        """Kiểm tra delete_queue() raise NotImplementedError."""
        provider = RedisQueueProvider()

        with pytest.raises(NotImplementedError, match=r"celery\[redis\]"):
            await provider.delete_queue("queue")

    @pytest.mark.asyncio
    async def test_get_queue_size_raises_not_implemented(self):
        """Kiểm tra get_queue_size() raise NotImplementedError."""
        provider = RedisQueueProvider()

        with pytest.raises(NotImplementedError, match=r"celery\[redis\]"):
            await provider.get_queue_size("queue")

    @pytest.mark.asyncio
    async def test_purge_queue_raises_not_implemented(self):
        """Kiểm tra purge_queue() raise NotImplementedError."""
        provider = RedisQueueProvider()

        with pytest.raises(NotImplementedError, match=r"celery\[redis\]"):
            await provider.purge_queue("queue")

    @pytest.mark.asyncio
    async def test_close_does_not_raise(self):
        """Kiểm tra close() không raise lỗi — chỉ reset state."""
        provider = RedisQueueProvider()

        await provider.close()

        assert provider._connected is False


class TestRabbitMQQueueProvider:
    """Kiểm tra RabbitMQQueueProvider — stub NotImplementedError."""

    @pytest.mark.asyncio
    async def test_connect_raises_not_implemented(self):
        """Kiểm tra connect() raise NotImplementedError."""
        provider = RabbitMQQueueProvider()
        config = QueueConfig(backend=QueueBackend.RABBITMQ)

        with pytest.raises(NotImplementedError, match="aio-pika"):
            await provider.connect(config)

    @pytest.mark.asyncio
    async def test_enqueue_raises_not_implemented(self):
        """Kiểm tra enqueue() raise NotImplementedError."""
        provider = RabbitMQQueueProvider()
        message = QueueMessage(body={"task": "test"})

        with pytest.raises(NotImplementedError, match="aio-pika"):
            await provider.enqueue(message)

    @pytest.mark.asyncio
    async def test_dequeue_raises_not_implemented(self):
        """Kiểm tra dequeue() raise NotImplementedError."""
        provider = RabbitMQQueueProvider()

        with pytest.raises(NotImplementedError, match="aio-pika"):
            await provider.dequeue("queue")

    @pytest.mark.asyncio
    async def test_ack_raises_not_implemented(self):
        """Kiểm tra ack() raise NotImplementedError."""
        provider = RabbitMQQueueProvider()

        with pytest.raises(NotImplementedError, match="aio-pika"):
            await provider.ack("msg-id")

    @pytest.mark.asyncio
    async def test_nack_raises_not_implemented(self):
        """Kiểm tra nack() raise NotImplementedError."""
        provider = RabbitMQQueueProvider()

        with pytest.raises(NotImplementedError, match="aio-pika"):
            await provider.nack("msg-id")

    @pytest.mark.asyncio
    async def test_create_queue_raises_not_implemented(self):
        """Kiểm tra create_queue() raise NotImplementedError."""
        provider = RabbitMQQueueProvider()

        with pytest.raises(NotImplementedError, match="aio-pika"):
            await provider.create_queue("queue")

    @pytest.mark.asyncio
    async def test_delete_queue_raises_not_implemented(self):
        """Kiểm tra delete_queue() raise NotImplementedError."""
        provider = RabbitMQQueueProvider()

        with pytest.raises(NotImplementedError, match="aio-pika"):
            await provider.delete_queue("queue")

    @pytest.mark.asyncio
    async def test_get_queue_size_raises_not_implemented(self):
        """Kiểm tra get_queue_size() raise NotImplementedError."""
        provider = RabbitMQQueueProvider()

        with pytest.raises(NotImplementedError, match="aio-pika"):
            await provider.get_queue_size("queue")

    @pytest.mark.asyncio
    async def test_purge_queue_raises_not_implemented(self):
        """Kiểm tra purge_queue() raise NotImplementedError."""
        provider = RabbitMQQueueProvider()

        with pytest.raises(NotImplementedError, match="aio-pika"):
            await provider.purge_queue("queue")

    @pytest.mark.asyncio
    async def test_close_does_not_raise(self):
        """Kiểm tra close() không raise lỗi — chỉ reset state."""
        provider = RabbitMQQueueProvider()

        await provider.close()

        assert provider._connected is False


class TestSQSQueueProvider:
    """Kiểm tra SQSQueueProvider — stub NotImplementedError."""

    @pytest.mark.asyncio
    async def test_connect_raises_not_implemented(self):
        """Kiểm tra connect() raise NotImplementedError."""
        provider = SQSQueueProvider()
        config = QueueConfig(backend=QueueBackend.SQS)

        with pytest.raises(NotImplementedError, match="boto3"):
            await provider.connect(config)

    @pytest.mark.asyncio
    async def test_enqueue_raises_not_implemented(self):
        """Kiểm tra enqueue() raise NotImplementedError."""
        provider = SQSQueueProvider()
        message = QueueMessage(body={"task": "test"})

        with pytest.raises(NotImplementedError, match="boto3"):
            await provider.enqueue(message)

    @pytest.mark.asyncio
    async def test_dequeue_raises_not_implemented(self):
        """Kiểm tra dequeue() raise NotImplementedError."""
        provider = SQSQueueProvider()

        with pytest.raises(NotImplementedError, match="boto3"):
            await provider.dequeue("queue")

    @pytest.mark.asyncio
    async def test_ack_raises_not_implemented(self):
        """Kiểm tra ack() raise NotImplementedError."""
        provider = SQSQueueProvider()

        with pytest.raises(NotImplementedError, match="boto3"):
            await provider.ack("msg-id")

    @pytest.mark.asyncio
    async def test_nack_raises_not_implemented(self):
        """Kiểm tra nack() raise NotImplementedError."""
        provider = SQSQueueProvider()

        with pytest.raises(NotImplementedError, match="boto3"):
            await provider.nack("msg-id")

    @pytest.mark.asyncio
    async def test_create_queue_raises_not_implemented(self):
        """Kiểm tra create_queue() raise NotImplementedError."""
        provider = SQSQueueProvider()

        with pytest.raises(NotImplementedError, match="boto3"):
            await provider.create_queue("queue")

    @pytest.mark.asyncio
    async def test_delete_queue_raises_not_implemented(self):
        """Kiểm tra delete_queue() raise NotImplementedError."""
        provider = SQSQueueProvider()

        with pytest.raises(NotImplementedError, match="boto3"):
            await provider.delete_queue("queue")

    @pytest.mark.asyncio
    async def test_get_queue_size_raises_not_implemented(self):
        """Kiểm tra get_queue_size() raise NotImplementedError."""
        provider = SQSQueueProvider()

        with pytest.raises(NotImplementedError, match="boto3"):
            await provider.get_queue_size("queue")

    @pytest.mark.asyncio
    async def test_purge_queue_raises_not_implemented(self):
        """Kiểm tra purge_queue() raise NotImplementedError."""
        provider = SQSQueueProvider()

        with pytest.raises(NotImplementedError, match="boto3"):
            await provider.purge_queue("queue")

    @pytest.mark.asyncio
    async def test_close_does_not_raise(self):
        """Kiểm tra close() không raise lỗi — chỉ reset state."""
        provider = SQSQueueProvider()

        await provider.close()

        assert provider._connected is False


class TestQueueProviderFactory:
    """Kiểm tra QueueProviderFactory."""

    def test_create_in_memory_returns_memory_provider(self):
        """Kiểm tra create(IN_MEMORY) trả về MemoryQueueProvider."""
        config = QueueConfig(backend=QueueBackend.IN_MEMORY)
        provider = QueueProviderFactory.create(QueueBackend.IN_MEMORY, config)

        assert isinstance(provider, MemoryQueueProvider)

    def test_create_redis_returns_redis_provider(self):
        """Kiểm tra create(REDIS) trả về RedisQueueProvider."""
        config = QueueConfig(backend=QueueBackend.REDIS)
        provider = QueueProviderFactory.create(QueueBackend.REDIS, config)

        assert isinstance(provider, RedisQueueProvider)

    def test_create_rabbitmq_returns_rabbitmq_provider(self):
        """Kiểm tra create(RABBITMQ) trả về RabbitMQQueueProvider."""
        config = QueueConfig(backend=QueueBackend.RABBITMQ)
        provider = QueueProviderFactory.create(QueueBackend.RABBITMQ, config)

        assert isinstance(provider, RabbitMQQueueProvider)

    def test_create_sqs_returns_sqs_provider(self):
        """Kiểm tra create(SQS) trả về SQSQueueProvider."""
        config = QueueConfig(backend=QueueBackend.SQS)
        provider = QueueProviderFactory.create(QueueBackend.SQS, config)

        assert isinstance(provider, SQSQueueProvider)

    def test_create_kafka_returns_rabbitmq_stub(self):
        """Kiểm tra create(KAFKA) trả về stub (dùng RabbitMQQueueProvider)."""
        config = QueueConfig(backend=QueueBackend.KAFKA)
        provider = QueueProviderFactory.create(QueueBackend.KAFKA, config)

        assert isinstance(provider, RabbitMQQueueProvider)

    def test_create_from_dict_in_memory(self):
        """Kiểm tra create_from_dict() tạo MemoryQueueProvider từ dict."""
        provider = QueueProviderFactory.create_from_dict({"backend": "in_memory"})

        assert isinstance(provider, MemoryQueueProvider)

    def test_create_from_dict_redis(self):
        """Kiểm tra create_from_dict() tạo RedisQueueProvider từ dict."""
        provider = QueueProviderFactory.create_from_dict({
            "backend": "redis",
            "connection_url": "redis://localhost:6379",
        })

        assert isinstance(provider, RedisQueueProvider)

    def test_create_from_dict_with_full_config(self):
        """Kiểm tra create_from_dict() với đầy đủ cấu hình."""
        provider = QueueProviderFactory.create_from_dict({
            "backend": "rabbitmq",
            "connection_url": "amqp://localhost",
            "max_retries": 5,
            "visibility_timeout": 60,
            "dlq_enabled": True,
            "dlq_max_messages": 500,
            "dead_letter_queue_name": "custom-dlq",
        })

        assert isinstance(provider, RabbitMQQueueProvider)
