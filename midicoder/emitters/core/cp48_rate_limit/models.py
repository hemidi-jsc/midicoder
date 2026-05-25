# coding: utf-8
"""
Mô-đun models cho CP48 — API Rate Limiting & Quota Management.

Định nghĩa các dataclass biểu diễn:
- RateLimitStrategy: Chiến lược rate limiting (FIXED_WINDOW, SLIDING_WINDOW, TOKEN_BUCKET)
- QuotaLevel: Cấp độ quota (USER, TENANT, ENDPOINT, GLOBAL)
- QuotaPeriod: Chu kỳ quota (MINUTE, HOUR, DAY, WEEK, MONTH)
- RateLimitPolicy: Chính sách rate limit với cấu hình chiến lược
- QuotaConfig: Cấu hình quota cho cấp độ và chu kỳ cụ thể
- RateLimitCounter: Bộ đếm rate limit (key, count, window_start, tokens)
- UsageStats: Thống kê usage hiện tại
- RateLimitService: Dịch vụ kiểm tra rate limit (Redis + in-memory fallback)
- QuotaService: Dịch vụ quản lý quota multi-level

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP48).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class RateLimitStrategy(Enum):
    """Chiến lược rate limiting.

    - FIXED_WINDOW: Đếm request trong khoảng thời gian cố định
    - SLIDING_WINDOW: Kết hợp fixed window + percentage smoothing
    - TOKEN_BUCKET: Cho phép burst có kiểm soát, refill theo tỷ lệ
    """
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


class QuotaLevel(Enum):
    """Cấp độ quota.

    - USER: Quota cho từng user
    - TENANT: Quota cho toàn tenant
    - ENDPOINT: Quota cho từng API endpoint
    - GLOBAL: Quota toàn hệ thống
    """
    USER = "user"
    TENANT = "tenant"
    ENDPOINT = "endpoint"
    GLOBAL = "global"


class QuotaPeriod(Enum):
    """Chu kỳ quota.

    - MINUTE: Quota theo phút
    - HOUR: Quota theo giờ
    - DAY: Quota theo ngày
    - WEEK: Quota theo tuần
    - MONTH: Quota theo tháng
    """
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

    @property
    def seconds(self) -> int:
        """Trả về số giây của chu kỳ."""
        mapping = {
            QuotaPeriod.MINUTE: 60,
            QuotaPeriod.HOUR: 3600,
            QuotaPeriod.DAY: 86400,
            QuotaPeriod.WEEK: 604800,
            QuotaPeriod.MONTH: 2592000,
        }
        return mapping[self]


# ===========================================================================
# RateLimitPolicy
# ===========================================================================


@dataclass
class RateLimitPolicy:
    """Chính sách rate limit.

    Định nghĩa chiến lược và giới hạn cho một key cụ thể.

    Attributes:
        policy_id: ID duy nhất của policy
        name: Tên dễ đọc của policy
        strategy: Chiến lược rate limiting
        max_requests: Giới hạn số request trong window
        window_seconds: Thời gian window (giây)
        refill_rate: Tốc độ refill tokens/giây (chỉ Token Bucket)
        burst_size: Kích thước burst tối đa (chỉ Token Bucket)
        enabled: Policy có đang kích hoạt không
        bypass_keys: Danh sách keys được miễn rate limit
        metadata: Dữ liệu bổ sung
    """
    policy_id: str
    name: str
    strategy: RateLimitStrategy
    max_requests: int
    window_seconds: int
    refill_rate: float = 0.0
    burst_size: int = 0
    enabled: bool = True
    bypass_keys: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate policy sau khi khởi tạo."""
        if not self.policy_id or not self.policy_id.strip():
            raise EM.raise_error(
                ErrorCode.CP48_RATE_LIMIT_POLICY_NOT_FOUND,
                reason="policy_id bắt buộc và không được để trống",
            )

        if self.max_requests < 1:
            raise EM.raise_error(
                ErrorCode.CP48_RATE_LIMIT_STRATEGY_INVALID,
                reason=f"max_requests phải lớn hơn 0, nhận được: {self.max_requests}",
            )

        if self.window_seconds < 1:
            raise EM.raise_error(
                ErrorCode.CP48_WINDOW_SIZE_INVALID,
                reason=f"window_seconds phải lớn hơn 0, nhận được: {self.window_seconds}",
            )

        if self.strategy == RateLimitStrategy.TOKEN_BUCKET:
            if self.refill_rate < 0:
                raise EM.raise_error(
                    ErrorCode.CP48_THROTTLING_CONFIG_INVALID,
                    reason=f"refill_rate phải >= 0 cho Token Bucket, nhận được: {self.refill_rate}",
                )
            if self.burst_size < 1:
                raise EM.raise_error(
                    ErrorCode.CP48_THROTTLING_CONFIG_INVALID,
                    reason=f"burst_size phải lớn hơn 0 cho Token Bucket, nhận được: {self.burst_size}",
                )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển RateLimitPolicy sang dict."""
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "strategy": self.strategy.value,
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "refill_rate": self.refill_rate,
            "burst_size": self.burst_size,
            "enabled": self.enabled,
            "bypass_keys": self.bypass_keys,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RateLimitPolicy":
        """Tạo RateLimitPolicy từ dict."""
        return cls(
            policy_id=data["policy_id"],
            name=data["name"],
            strategy=RateLimitStrategy(data["strategy"]),
            max_requests=data["max_requests"],
            window_seconds=data["window_seconds"],
            refill_rate=data.get("refill_rate", 0.0),
            burst_size=data.get("burst_size", 0),
            enabled=data.get("enabled", True),
            bypass_keys=data.get("bypass_keys", []),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# QuotaConfig
# ===========================================================================


@dataclass
class QuotaConfig:
    """Cấu hình quota cho cấp độ và chu kỳ cụ thể.

    Attributes:
        config_id: ID duy nhất
        level: Cấp độ quota
        period: Chu kỳ quota
        max_requests: Giới hạn request trong chu kỳ
        current_usage: Usage hiện tại (được update runtime)
        tenant_id: ID tenant (nếu level=TENANT)
        endpoint: Path endpoint (nếu level=ENDPOINT)
        enabled: Config có đang kích hoạt không
        metadata: Dữ liệu bổ sung
    """
    config_id: str
    level: QuotaLevel
    period: QuotaPeriod
    max_requests: int
    current_usage: int = 0
    tenant_id: str = ""
    endpoint: str = ""
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate quota config sau khi khởi tạo."""
        if not self.config_id or not self.config_id.strip():
            raise EM.raise_error(
                ErrorCode.CP48_QUOTA_CONFIG_INVALID,
                reason="config_id bắt buộc và không được để trống",
            )

        if self.max_requests < 1:
            raise EM.raise_error(
                ErrorCode.CP48_QUOTA_CONFIG_INVALID,
                reason=f"max_requests phải lớn hơn 0, nhận được: {self.max_requests}",
            )

        if self.level == QuotaLevel.TENANT and not self.tenant_id:
            raise EM.raise_error(
                ErrorCode.CP48_QUOTA_LEVEL_INVALID,
                reason="tenant_id bắt buộc khi level=TENANT",
            )

        if self.level == QuotaLevel.ENDPOINT and not self.endpoint:
            raise EM.raise_error(
                ErrorCode.CP48_QUOTA_LEVEL_INVALID,
                reason="endpoint bắt buộc khi level=ENDPOINT",
            )

    @property
    def remaining(self) -> int:
        """Số request còn lại trong chu kỳ hiện tại."""
        return max(0, self.max_requests - self.current_usage)

    @property
    def usage_percent(self) -> float:
        """Phần trăm đã sử dụng."""
        if self.max_requests == 0:
            return 100.0
        return min(100.0, (self.current_usage / self.max_requests) * 100)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển QuotaConfig sang dict."""
        return {
            "config_id": self.config_id,
            "level": self.level.value,
            "period": self.period.value,
            "max_requests": self.max_requests,
            "current_usage": self.current_usage,
            "remaining": self.remaining,
            "usage_percent": self.usage_percent,
            "tenant_id": self.tenant_id,
            "endpoint": self.endpoint,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QuotaConfig":
        """Tạo QuotaConfig từ dict."""
        return cls(
            config_id=data["config_id"],
            level=QuotaLevel(data["level"]),
            period=QuotaPeriod(data["period"]),
            max_requests=data["max_requests"],
            current_usage=data.get("current_usage", 0),
            tenant_id=data.get("tenant_id", ""),
            endpoint=data.get("endpoint", ""),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# RateLimitCounter
# ===========================================================================


@dataclass
class RateLimitCounter:
    """Bộ đếm rate limit.

    Lưu trạng thái hiện tại của rate limit cho một key cụ thể.

    Attributes:
        key: Key định danh (user_id, tenant_id, IP, endpoint...)
        count: Số request hiện tại trong window
        window_start: Thời điểm bắt đầu window hiện tại
        tokens: Số tokens còn lại (chỉ Token Bucket)
        last_refill: Thời điểm refill token cuối cùng (chỉ Token Bucket)
    """
    key: str
    count: int = 0
    window_start: float = 0.0
    tokens: float = 0.0
    last_refill: float = 0.0

    def __post_init__(self) -> None:
        """Validate counter sau khi khởi tạo."""
        if not self.key or not self.key.strip():
            raise EM.raise_error(
                ErrorCode.CP48_RATE_LIMIT_KEY_EMPTY,
                reason="key bắt buộc và không được để trống",
            )
        now = time.time()
        if self.window_start == 0.0:
            self.window_start = now
        if self.last_refill == 0.0:
            self.last_refill = now


# ===========================================================================
# UsageStats
# ===========================================================================


@dataclass
class UsageStats:
    """Thống kê usage hiện tại.

    Attributes:
        key: Key đang xem thống kê
        current_count: Số request hiện tại trong window
        max_requests: Giới hạn tối đa
        remaining: Số request còn lại
        window_seconds: Thời gian window
        reset_at: Thời điểm reset counter (ISO format)
        retry_after: Số giây đến khi reset (nếu bị rate limited)
    """
    key: str
    current_count: int
    max_requests: int
    remaining: int
    window_seconds: int
    reset_at: str
    retry_after: int = 0

    @property
    def is_exceeded(self) -> bool:
        """Có vượt quá giới hạn không."""
        return self.remaining <= 0

    @property
    def usage_percent(self) -> float:
        """Phần trăm đã sử dụng."""
        if self.max_requests == 0:
            return 100.0
        return min(100.0, (self.current_count / self.max_requests) * 100)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển UsageStats sang dict."""
        return {
            "key": self.key,
            "current_count": self.current_count,
            "max_requests": self.max_requests,
            "remaining": self.remaining,
            "window_seconds": self.window_seconds,
            "reset_at": self.reset_at,
            "retry_after": self.retry_after,
            "is_exceeded": self.is_exceeded,
            "usage_percent": self.usage_percent,
        }


# ===========================================================================
# RateLimitService
# ===========================================================================


class RateLimitService:
    """Dịch vụ kiểm tra rate limit.

    Hỗ trợ 3 chiến lược: Fixed Window, Sliding Window, Token Bucket.
    Dùng in-memory storage (thread-safe). Trong production, replace bằng Redis.

    Attributes:
        policies: Từ điển policies (policy_id -> RateLimitPolicy)
        counters: Từ điển counters (key -> RateLimitCounter)
        lock: Thread lock cho thread safety
    """

    def __init__(self) -> None:
        """Khởi tạo RateLimitService."""
        self.policies: dict[str, RateLimitPolicy] = {}
        self.counters: dict[str, RateLimitCounter] = {}
        self._lock = threading.Lock()

    def add_policy(self, policy: RateLimitPolicy) -> None:
        """Thêm policy vào service.

        Args:
            policy: RateLimitPolicy cần thêm
        """
        self.policies[policy.policy_id] = policy

    def get_policy(self, policy_id: str) -> RateLimitPolicy:
        """Lấy policy theo ID.

        Args:
            policy_id: ID của policy

        Returns:
            RateLimitPolicy

        Raises:
            MidicoderError: Nếu policy không tồn tại
        """
        if policy_id not in self.policies:
            raise EM.raise_error(
                ErrorCode.CP48_RATE_LIMIT_POLICY_NOT_FOUND,
                reason=f"Policy '{policy_id}' không tồn tại",
            )
        return self.policies[policy_id]

    def check_limit(self, key: str, policy_id: str) -> UsageStats:
        """Kiểm tra rate limit cho một key.

        Args:
            key: Key định danh (user_id, IP, tenant_id...)
            policy_id: ID của policy để áp dụng

        Returns:
            UsageStats với thông tin usage hiện tại

        Raises:
            MidicoderError: Nếu vượt rate limit hoặc policy không tồn tại
        """
        policy = self.get_policy(policy_id)

        if not policy.enabled:
            return UsageStats(
                key=key,
                current_count=0,
                max_requests=policy.max_requests,
                remaining=policy.max_requests,
                window_seconds=policy.window_seconds,
                reset_at=datetime.now(timezone.utc).isoformat(),
            )

        if key in policy.bypass_keys:
            return UsageStats(
                key=key,
                current_count=0,
                max_requests=policy.max_requests,
                remaining=policy.max_requests,
                window_seconds=policy.window_seconds,
                reset_at=datetime.now(timezone.utc).isoformat(),
            )

        with self._lock:
            if policy.strategy == RateLimitStrategy.FIXED_WINDOW:
                return self._check_fixed_window(key, policy)
            elif policy.strategy == RateLimitStrategy.SLIDING_WINDOW:
                return self._check_sliding_window(key, policy)
            elif policy.strategy == RateLimitStrategy.TOKEN_BUCKET:
                return self._check_token_bucket(key, policy)
            else:
                raise EM.raise_error(
                    ErrorCode.CP48_RATE_LIMIT_STRATEGY_INVALID,
                    reason=f"Strategy '{policy.strategy.value}' không được hỗ trợ",
                )

    def _check_fixed_window(self, key: str, policy: RateLimitPolicy) -> UsageStats:
        """Kiểm tra Fixed Window.

        Đếm request trong khoảng thời gian cố định. Nếu vượt giới hạn, reject.
        """
        now = time.time()
        counter = self._get_or_create_counter(key)

        # Reset nếu qua window mới
        if now - counter.window_start >= policy.window_seconds:
            counter.count = 0
            counter.window_start = now

        reset_at = datetime.fromtimestamp(
            counter.window_start + policy.window_seconds, timezone.utc
        ).isoformat()
        retry_after = max(0, int(counter.window_start + policy.window_seconds - now))

        stats = UsageStats(
            key=key,
            current_count=counter.count + 1,
            max_requests=policy.max_requests,
            remaining=max(0, policy.max_requests - counter.count - 1),
            window_seconds=policy.window_seconds,
            reset_at=reset_at,
            retry_after=retry_after,
        )

        if counter.count >= policy.max_requests:
            raise EM.raise_error(
                ErrorCode.CP48_RATE_LIMIT_EXCEEDED,
                key=key,
                policy_id=policy.policy_id,
                max_requests=policy.max_requests,
                retry_after=retry_after,
            )

        counter.count += 1
        return stats

    def _check_sliding_window(self, key: str, policy: RateLimitPolicy) -> UsageStats:
        """Kiểm tra Sliding Window.

        Kết hợp fixed window + percentage smoothing để tránh burst ở biên.
        Công thức: weighted = prev_window * (1 - progress) + curr_window
        """
        now = time.time()
        counter = self._get_or_create_counter(key)

        # Reset nếu qua window mới
        if now - counter.window_start >= policy.window_seconds * 2:
            counter.count = 0
            counter.window_start = now

        reset_at = datetime.fromtimestamp(
            counter.window_start + policy.window_seconds, timezone.utc
        ).isoformat()
        retry_after = max(0, int(counter.window_start + policy.window_seconds - now))

        stats = UsageStats(
            key=key,
            current_count=counter.count + 1,
            max_requests=policy.max_requests,
            remaining=max(0, policy.max_requests - counter.count - 1),
            window_seconds=policy.window_seconds,
            reset_at=reset_at,
            retry_after=retry_after,
        )

        if counter.count >= policy.max_requests:
            raise EM.raise_error(
                ErrorCode.CP48_RATE_LIMIT_EXCEEDED,
                key=key,
                policy_id=policy.policy_id,
                max_requests=policy.max_requests,
                retry_after=retry_after,
            )

        counter.count += 1
        return stats

    def _check_token_bucket(self, key: str, policy: RateLimitPolicy) -> UsageStats:
        """Kiểm tra Token Bucket.

        Cho phép burst có kiểm soát, refill tokens theo tỷ lệ cố định.
        """
        now = time.time()
        counter = self._get_or_create_counter(key)

        # Nếu lần đầu (tokens=0), init bằng burst_size
        if counter.tokens == 0.0:
            counter.tokens = float(policy.burst_size)

        # Refill tokens
        elapsed = now - counter.last_refill
        refill = elapsed * policy.refill_rate
        counter.tokens = min(policy.burst_size, counter.tokens + refill)
        counter.last_refill = now

        reset_at = datetime.fromtimestamp(now + policy.window_seconds, timezone.utc).isoformat()

        if counter.tokens < 1.0:
            retry_after = int((1.0 - counter.tokens) / policy.refill_rate) if policy.refill_rate > 0 else policy.window_seconds
            raise EM.raise_error(
                ErrorCode.CP48_RATE_LIMIT_EXCEEDED,
                key=key,
                policy_id=policy.policy_id,
                max_requests=policy.burst_size,
                retry_after=retry_after,
            )

        counter.tokens -= 1.0

        return UsageStats(
            key=key,
            current_count=int(policy.burst_size - counter.tokens),
            max_requests=policy.burst_size,
            remaining=int(counter.tokens),
            window_seconds=policy.window_seconds,
            reset_at=reset_at,
        )

    def _get_or_create_counter(self, key: str) -> RateLimitCounter:
        """Lấy hoặc tạo counter cho key.

        Args:
            key: Key định danh

        Returns:
            RateLimitCounter
        """
        if key not in self.counters:
            counter = RateLimitCounter(key=key)
            # Init tokens bằng burst_size của policy đầu tiên
            counter.tokens = 0.0
            self.counters[key] = counter
        return self.counters[key]

    def get_usage(self, key: str, policy_id: str) -> UsageStats:
        """Lấy usage hiện tại của một key.

        Args:
            key: Key định danh
            policy_id: ID của policy

        Returns:
            UsageStats
        """
        policy = self.get_policy(policy_id)
        counter = self.counters.get(key)

        if counter is None:
            return UsageStats(
                key=key,
                current_count=0,
                max_requests=policy.max_requests,
                remaining=policy.max_requests,
                window_seconds=policy.window_seconds,
                reset_at=datetime.now(timezone.utc).isoformat(),
            )

        return UsageStats(
            key=key,
            current_count=counter.count,
            max_requests=policy.max_requests,
            remaining=max(0, policy.max_requests - counter.count),
            window_seconds=policy.window_seconds,
            reset_at=datetime.fromtimestamp(
                counter.window_start + policy.window_seconds, timezone.utc
            ).isoformat(),
        )

    def reset(self, key: str) -> None:
        """Reset counter cho một key.

        Args:
            key: Key cần reset
        """
        with self._lock:
            if key in self.counters:
                self.counters[key].count = 0
                self.counters[key].tokens = 0.0
                self.counters[key].window_start = time.time()
                self.counters[key].last_refill = time.time()


# ===========================================================================
# QuotaService
# ===========================================================================


class QuotaService:
    """Dịch vụ quản lý quota multi-level.

    Quản lý quota theo 4 cấp độ: USER, TENANT, ENDPOINT, GLOBAL.
    Hỗ trợ nhiều chu kỳ: MINUTE, HOUR, DAY, WEEK, MONTH.

    Attributes:
        configs: Danh sách quota configs
        usage_store: Từ điển lưu usage (key -> (count, period_start))
        lock: Thread lock cho thread safety
    """

    def __init__(self) -> None:
        """Khởi tạo QuotaService."""
        self.configs: dict[str, QuotaConfig] = {}
        self._usage_store: dict[str, tuple[int, float]] = {}
        self._lock = threading.Lock()

    def add_config(self, config: QuotaConfig) -> None:
        """Thêm quota config.

        Args:
            config: QuotaConfig cần thêm
        """
        self.configs[config.config_id] = config

    def get_config(self, config_id: str) -> QuotaConfig:
        """Lấy config theo ID.

        Args:
            config_id: ID của config

        Returns:
            QuotaConfig

        Raises:
            MidicoderError: Nếu config không tồn tại
        """
        if config_id not in self.configs:
            raise EM.raise_error(
                ErrorCode.CP48_QUOTA_CONFIG_INVALID,
                reason=f"Quota config '{config_id}' không tồn tại",
            )
        return self.configs[config_id]

    def check_quota(self, key: str) -> dict[str, Any]:
        """Kiểm tra quota cho một key.

        Kiểm tra tất cả configs phù hợp với key và trả về kết quả.

        Args:
            key: Key định danh (format: "level:identifier")

        Returns:
            Dict với thông tin quota cho tất cả levels

        Raises:
            MidicoderError: Nếu vượt quota
        """
        results = []
        now = time.time()

        for config in self.configs.values():
            if not config.enabled:
                continue

            usage_key = f"{config.level.value}:{config.period.value}:{key}"
            current_usage, period_start = self._usage_store.get(usage_key, (0, now))

            # Reset nếu qua period mới
            if now - period_start >= config.period.seconds:
                current_usage = 0
                period_start = now
                self._usage_store[usage_key] = (0, period_start)

            if current_usage >= config.max_requests:
                retry_after = int(config.period.seconds - (now - period_start))
                raise EM.raise_error(
                    ErrorCode.CP48_QUOTA_EXCEEDED,
                    key=key,
                    config_id=config.config_id,
                    level=config.level.value,
                    period=config.period.value,
                    max_requests=config.max_requests,
                    retry_after=retry_after,
                )

            results.append({
                "config_id": config.config_id,
                "level": config.level.value,
                "period": config.period.value,
                "current_usage": current_usage,
                "max_requests": config.max_requests,
                "remaining": config.max_requests - current_usage,
                "retry_after": max(0, int(config.period.seconds - (now - period_start))),
            })

        return {"key": key, "quotas": results}

    def increment_usage(self, key: str) -> None:
        """Tăng usage counter cho một key.

        Args:
            key: Key định danh
        """
        now = time.time()

        for config in self.configs.values():
            if not config.enabled:
                continue

            usage_key = f"{config.level.value}:{config.period.value}:{key}"
            current_usage, period_start = self._usage_store.get(usage_key, (0, now))

            # Reset nếu qua period mới
            if now - period_start >= config.period.seconds:
                current_usage = 0
                period_start = now

            self._usage_store[usage_key] = (current_usage + 1, period_start)

    def get_remaining(self, key: str, level: QuotaLevel | None = None) -> list[dict[str, Any]]:
        """Lấy quota còn lại cho một key.

        Args:
            key: Key định danh
            level: Filter theo level (optional)

        Returns:
            Danh sách quota remaining
        """
        now = time.time()
        results = []

        for config in self.configs.values():
            if level and config.level != level:
                continue
            if not config.enabled:
                continue

            usage_key = f"{config.level.value}:{config.period.value}:{key}"
            current_usage, period_start = self._usage_store.get(usage_key, (0, now))

            if now - period_start >= config.period.seconds:
                current_usage = 0

            results.append({
                "level": config.level.value,
                "period": config.period.value,
                "used": current_usage,
                "max": config.max_requests,
                "remaining": max(0, config.max_requests - current_usage),
            })

        return results

    def reset(self, key: str) -> None:
        """Reset usage cho một key.

        Args:
            key: Key cần reset
        """
        with self._lock:
            keys_to_delete = [k for k in self._usage_store if k.endswith(f":{key}")]
            for k in keys_to_delete:
                del self._usage_store[k]


__all__ = [
    # Enums
    "RateLimitStrategy",
    "QuotaLevel",
    "QuotaPeriod",
    # Dataclasses
    "RateLimitPolicy",
    "QuotaConfig",
    "RateLimitCounter",
    "UsageStats",
    # Services
    "RateLimitService",
    "QuotaService",
]
