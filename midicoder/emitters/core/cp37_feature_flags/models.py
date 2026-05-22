# coding: utf-8
"""
Mô-đun models cho CP37 — Feature Flags & Dynamic Config.

Định nghĩa các dataclass biểu diễn:
- FeatureFlag: Feature toggle với targeting rules và tenant overrides
- TargetingRule: Rule để evaluate flag theo condition
- FlagEvaluation: Kết quả evaluation của flag
- FeatureFlagEvaluator: Engine evaluate flags
- ABExperiment: A/B experiment với variants
- ABVariant: Variant trong experiment
- ABExperimentAssignment: Kết quả assignment
- ABExperimentEngine: Engine assign users vào variants
- DynamicConfig: Dynamic configuration key-value
- ConfigChange: Audit trail cho config change
- FlagStore: Abstract interface cho storage backend

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP37).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class FlagVariantType(str, Enum):
    """Loại flag variant.

    - BOOLEAN: Flag đơn giản on/off
    - PERCENTAGE: Flag theo tỷ lệ % traffic
    - TARGETED: Flag với targeting rules
    """
    BOOLEAN = "boolean"
    PERCENTAGE = "percentage"
    TARGETED = "targeted"


class ConditionType(str, Enum):
    """Loại condition cho targeting rule.

    - ROLE: Theo user role
    - ATTRIBUTE: Theo custom attribute
    - TENANT: Theo tenant_id
    - SEGMENT: Theo user segment
    """
    ROLE = "role"
    ATTRIBUTE = "attribute"
    TENANT = "tenant"
    SEGMENT = "segment"


class ConfigScope(str, Enum):
    """Scope của dynamic config.

    - GLOBAL: Config global, áp dụng cho tất cả
    - TENANT: Config scoped theo tenant
    - ENVIRONMENT: Config scoped theo environment
    """
    GLOBAL = "global"
    TENANT = "tenant"
    ENVIRONMENT = "environment"


class ConfigValueType(str, Enum):
    """Loại giá trị của config.

    - STRING: Giá trị string
    - NUMBER: Giá trị số
    - BOOLEAN: Giá trị boolean
    - JSON: Giá trị JSON object
    - ARRAY: Giá trị array
    """
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"
    ARRAY = "array"


# ===========================================================================
# Feature Flag
# ===========================================================================


@dataclass
class TargetingRule:
    """Rule để evaluate flag theo condition.

    Attributes:
        rule_id: ID duy nhất của rule trong flag
        condition_type: Loại condition (role, attribute, tenant, segment)
        condition: Dict key-value condition (vd: {"role": "admin"})
        value: Flag value khi rule match
        priority: Order of evaluation (thấp = ưu tiên cao)
    """
    rule_id: str
    condition_type: ConditionType
    condition: dict[str, Any]
    value: bool
    priority: int = 0

    def __post_init__(self) -> None:
        """Validate targeting rule sau khi khởi tạo."""
        if not self.rule_id or not self.rule_id.strip():
            EM.raise_error(
                ErrorCode.CP37_INVALID_TARGETING_RULE,
                reason="rule_id không được để trống"
            )
        if not self.condition:
            EM.raise_error(
                ErrorCode.CP37_INVALID_TARGETING_RULE,
                reason="condition không được để trống"
            )

    def matches(self, context: dict[str, Any]) -> bool:
        """Kiểm tra context có match với rule không.

        Args:
            context: Context dict (user_id, tenant_id, role, attributes)

        Returns:
            True nếu context match với condition của rule
        """
        match self.condition_type:
            case ConditionType.ROLE:
                expected = self.condition.get("role")
                return context.get("role") == expected
            case ConditionType.TENANT:
                expected = self.condition.get("tenant_id")
                return context.get("tenant_id") == expected
            case ConditionType.ATTRIBUTE:
                for key, value in self.condition.items():
                    if context.get("attributes", {}).get(key) != value:
                        return False
                return True
            case ConditionType.SEGMENT:
                expected = self.condition.get("segment")
                return expected in context.get("segments", [])
            case _:
                return False

    def to_dict(self) -> dict[str, Any]:
        """Chuyển TargetingRule sang dict."""
        return {
            "rule_id": self.rule_id,
            "condition_type": self.condition_type.value,
            "condition": self.condition,
            "value": self.value,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TargetingRule":
        """Tạo TargetingRule từ dict."""
        return cls(
            rule_id=data.get("rule_id", ""),
            condition_type=ConditionType(data.get("condition_type", "role")),
            condition=data.get("condition", {}),
            value=data.get("value", False),
            priority=data.get("priority", 0),
        )


@dataclass
class FeatureFlag:
    """Entity feature flag.

    Lưu trữ thông tin của một feature flag, bao gồm variant type,
    targeting rules, tenant overrides, và environment scope.

    Attributes:
        flag_key: Identifier duy nhất (snake_case, required)
        name: Tên hiển thị
        description: Mô tả flag
        variant_type: Loại flag (boolean, percentage, targeted)
        default_enabled: Giá trị mặc định
        percentage: Tỷ lệ % (chỉ dùng khi variant_type=percentage)
        targeting_rules: Danh sách targeting rules
        environments: Danh sách environments
        tenant_overrides: Override per tenant_id
        is_active: Flag có đang active không
        created_at: Thời điểm tạo
        updated_at: Thời điểm cập nhật cuối
    """
    flag_key: str
    name: str = ""
    description: str = ""
    variant_type: FlagVariantType = FlagVariantType.BOOLEAN
    default_enabled: bool = False
    percentage: int = 0
    targeting_rules: list[TargetingRule] = field(default_factory=list)
    environments: list[str] = field(default_factory=list)
    tenant_overrides: dict[str, bool] = field(default_factory=dict)
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate feature flag sau khi khởi tạo."""
        if not self.flag_key or not self.flag_key.strip():
            EM.raise_error(ErrorCode.CP37_EMPTY_FLAG_KEY, message="Flag key không được để trống")

        if not re.match(r'^[a-z][a-z0-9_]*$', self.flag_key):
            EM.raise_error(ErrorCode.CP37_EMPTY_FLAG_KEY, message=f"Flag key phải là snake_case: {self.flag_key}")

        if self.variant_type == FlagVariantType.PERCENTAGE:
            if self.percentage < 0 or self.percentage > 100:
                EM.raise_error(
                    ErrorCode.CP37_INVALID_PERCENTAGE,
                    percentage=self.percentage,
                    message=f"Percentage phải trong khoảng 0-100: {self.percentage}"
                )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    def to_dict(self) -> dict[str, Any]:
        """Chuyển FeatureFlag sang dict format."""
        return {
            "flag_key": self.flag_key,
            "name": self.name,
            "description": self.description,
            "variant_type": self.variant_type.value,
            "default_enabled": self.default_enabled,
            "percentage": self.percentage,
            "targeting_rules": [r.to_dict() for r in self.targeting_rules],
            "environments": self.environments,
            "tenant_overrides": self.tenant_overrides,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FeatureFlag":
        """Tạo FeatureFlag từ dict."""
        rules_data = data.get("targeting_rules", [])
        rules = [TargetingRule.from_dict(r) for r in rules_data]
        return cls(
            flag_key=data.get("flag_key", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            variant_type=FlagVariantType(data.get("variant_type", "boolean")),
            default_enabled=data.get("default_enabled", False),
            percentage=data.get("percentage", 0),
            targeting_rules=rules,
            environments=data.get("environments", []),
            tenant_overrides=data.get("tenant_overrides", {}),
            is_active=data.get("is_active", True),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


# ===========================================================================
# Flag Evaluation
# ===========================================================================


@dataclass
class FlagEvaluation:
    """Kết quả evaluation của flag.

    Attributes:
        flag_key: Flag được evaluate
        user_id: User được evaluate
        tenant_id: Tenant được evaluate
        evaluated_value: Kết quả boolean
        reason: Lý do evaluate ra giá trị này
        evaluated_at: Thời điểm evaluate
    """
    flag_key: str
    user_id: str = ""
    tenant_id: str = ""
    evaluated_value: bool = False
    reason: str = ""
    evaluated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Set timestamp nếu chưa có."""
        if self.evaluated_at is None:
            self.evaluated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển FlagEvaluation sang dict."""
        return {
            "flag_key": self.flag_key,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "evaluated_value": self.evaluated_value,
            "reason": self.reason,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
        }


class FeatureFlagEvaluator:
    """Engine evaluate feature flags.

    Evaluation order (ưu tiên giảm dần):
    1. Tenant override
    2. Targeting rule (theo priority)
    3. Percentage rollout
    4. Default value

    Attributes:
        flags: Danh sách tất cả flags
    """
    def __init__(self, flags: list[FeatureFlag] | None = None):
        self.flags: dict[str, FeatureFlag] = {}
        if flags:
            for f in flags:
                self.flags[f.flag_key] = f

    def add_flag(self, flag: FeatureFlag) -> None:
        """Thêm flag vào evaluator."""
        self.flags[flag.flag_key] = flag

    def remove_flag(self, flag_key: str) -> None:
        """Xóa flag khỏi evaluator."""
        self.flags.pop(flag_key, None)

    def evaluate(self, flag_key: str, context: dict[str, Any]) -> FlagEvaluation:
        """Evaluate một flag cho context cụ thể.

        Args:
            flag_key: Flag key để evaluate
            context: Context dict (user_id, tenant_id, role, attributes, segments, environment)

        Returns:
            FlagEvaluation với kết quả và lý do

        Raises:
            MidicoderError: Nếu flag không tồn tại
        """
        flag = self.flags.get(flag_key)
        if not flag:
            return FlagEvaluation(
                flag_key=flag_key,
                user_id=context.get("user_id", ""),
                tenant_id=context.get("tenant_id", ""),
                evaluated_value=False,
                reason=f"flag_not_found: {flag_key}",
            )

        # 1. Kiểm tra flag active
        if not flag.is_active:
            return FlagEvaluation(
                flag_key=flag_key,
                user_id=context.get("user_id", ""),
                tenant_id=context.get("tenant_id", ""),
                evaluated_value=False,
                reason="flag_inactive",
            )

        # 2. Tenant override (ưu tiên cao nhất)
        tenant_id = context.get("tenant_id", "")
        if tenant_id and tenant_id in flag.tenant_overrides:
            override_value = flag.tenant_overrides[tenant_id]
            return FlagEvaluation(
                flag_key=flag_key,
                user_id=context.get("user_id", ""),
                tenant_id=tenant_id,
                evaluated_value=override_value,
                reason=f"tenant_override: {tenant_id}",
            )

        # 3. Targeting rules (theo priority)
        if flag.variant_type == FlagVariantType.TARGETED and flag.targeting_rules:
            sorted_rules = sorted(flag.targeting_rules, key=lambda r: r.priority)
            for rule in sorted_rules:
                if rule.matches(context):
                    return FlagEvaluation(
                        flag_key=flag_key,
                        user_id=context.get("user_id", ""),
                        tenant_id=context.get("tenant_id", ""),
                        evaluated_value=rule.value,
                        reason=f"targeting_rule: {rule.rule_id}",
                    )

        # 4. Percentage rollout
        if flag.variant_type == FlagVariantType.PERCENTAGE:
            user_id = context.get("user_id", "")
            if user_id:
                bucket = int(hashlib.sha256(user_id.encode()).hexdigest(), 16) % 100
                matched = bucket < flag.percentage
                return FlagEvaluation(
                    flag_key=flag_key,
                    user_id=user_id,
                    tenant_id=context.get("tenant_id", ""),
                    evaluated_value=matched,
                    reason=f"percentage_rollout: {flag.percentage}%, bucket={bucket}",
                )

        # 5. Default value
        return FlagEvaluation(
            flag_key=flag_key,
            user_id=context.get("user_id", ""),
            tenant_id=context.get("tenant_id", ""),
            evaluated_value=flag.default_enabled,
            reason="default_value",
        )

    def evaluate_all(self, context: dict[str, Any]) -> dict[str, bool]:
        """Evaluate tất cả flags cho context.

        Args:
            context: Context dict

        Returns:
            Dict flag_key -> boolean
        """
        result = {}
        for flag_key in self.flags:
            eval_result = self.evaluate(flag_key, context)
            result[flag_key] = eval_result.evaluated_value
        return result


# ===========================================================================
# A/B Testing
# ===========================================================================


@dataclass
class ABVariant:
    """Variant trong A/B experiment.

    Attributes:
        variant_key: ID duy nhất trong experiment
        name: Tên hiển thị
        weight: Trọng số (tổng weight = 100%)
        metadata: Custom config cho variant
    """
    variant_key: str
    name: str = ""
    weight: float = 50.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate variant."""
        if not self.variant_key or not self.variant_key.strip():
            EM.raise_error(ErrorCode.CP37_INVALID_VARIANT_WEIGHT,
                           total_weight=0, message="Variant key không được để trống")
        if self.weight < 0:
            EM.raise_error(ErrorCode.CP37_INVALID_VARIANT_WEIGHT,
                           total_weight=self.weight, message="Weight không được âm")

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ABVariant sang dict."""
        return {
            "variant_key": self.variant_key,
            "name": self.name,
            "weight": self.weight,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ABVariant":
        """Tạo ABVariant từ dict."""
        return cls(
            variant_key=data.get("variant_key", ""),
            name=data.get("name", ""),
            weight=data.get("weight", 50.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ABExperiment:
    """A/B experiment.

    Attributes:
        experiment_key: Identifier duy nhất
        name: Tên hiển thị
        description: Mô tả experiment
        variants: Danh sách variants (>= 2)
        start_date: Ngày bắt đầu
        end_date: Ngày kết thúc (nullable)
        is_active: Có đang active không
        traffic_percentage: Bao nhiêu % traffic vào experiment
        targeting: TargetingRule cho ai tham gia (optional)
        success_metric: Metric để đo lường
    """
    experiment_key: str
    name: str = ""
    description: str = ""
    variants: list[ABVariant] = field(default_factory=list)
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool = True
    traffic_percentage: float = 100.0
    targeting: TargetingRule | None = None
    success_metric: str = "conversion_rate"

    def __post_init__(self) -> None:
        """Validate experiment."""
        if not self.experiment_key or not self.experiment_key.strip():
            EM.raise_error(ErrorCode.CP37_EMPTY_EXPERIMENT_KEY,
                           message="Experiment key không được để trống")

        if len(self.variants) < 2:
            EM.raise_error(ErrorCode.CP37_TOO_FEW_VARIANTS,
                           count=len(self.variants),
                           message=f"Experiment cần ít nhất 2 variants, nhận được: {len(self.variants)}")

        total_weight = sum(v.weight for v in self.variants)
        if abs(total_weight - 100.0) > 0.01:
            EM.raise_error(ErrorCode.CP37_INVALID_VARIANT_WEIGHT,
                           total_weight=total_weight,
                           message=f"Tổng weight phải bằng 100, nhận được: {total_weight}")

        if self.start_date is None:
            self.start_date = datetime.now(timezone.utc)

    @property
    def is_running(self) -> bool:
        """Trả về True nếu experiment đang chạy."""
        if not self.is_active:
            return False
        now = datetime.now(timezone.utc)
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ABExperiment sang dict."""
        return {
            "experiment_key": self.experiment_key,
            "name": self.name,
            "description": self.description,
            "variants": [v.to_dict() for v in self.variants],
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_active": self.is_active,
            "traffic_percentage": self.traffic_percentage,
            "targeting": self.targeting.to_dict() if self.targeting else None,
            "success_metric": self.success_metric,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ABExperiment":
        """Tạo ABExperiment từ dict."""
        variants_data = data.get("variants", [])
        variants = [ABVariant.from_dict(v) for v in variants_data]
        targeting_data = data.get("targeting")
        targeting = TargetingRule.from_dict(targeting_data) if targeting_data else None
        return cls(
            experiment_key=data.get("experiment_key", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            variants=variants,
            start_date=datetime.fromisoformat(data["start_date"]) if data.get("start_date") else None,
            end_date=datetime.fromisoformat(data["end_date"]) if data.get("end_date") else None,
            is_active=data.get("is_active", True),
            traffic_percentage=data.get("traffic_percentage", 100.0),
            targeting=targeting,
            success_metric=data.get("success_metric", "conversion_rate"),
        )


@dataclass
class ABExperimentAssignment:
    """Kết quả assignment của user vào variant.

    Attributes:
        experiment_key: Experiment được assign
        user_id: User được assign
        tenant_id: Tenant của user
        assigned_variant: Variant được assign
        assigned_at: Thời điểm assign
    """
    experiment_key: str
    user_id: str
    tenant_id: str = ""
    assigned_variant: str = ""
    assigned_at: datetime | None = None

    def __post_init__(self) -> None:
        """Set timestamp nếu chưa có."""
        if self.assigned_at is None:
            self.assigned_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ABExperimentAssignment sang dict."""
        return {
            "experiment_key": self.experiment_key,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "assigned_variant": self.assigned_variant,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
        }


class ABExperimentEngine:
    """Engine quản lý và assign A/B experiments.

    Attributes:
        experiments: Danh sách experiments
    """
    def __init__(self, experiments: list[ABExperiment] | None = None):
        self.experiments: dict[str, ABExperiment] = {}
        if experiments:
            for exp in experiments:
                self.experiments[exp.experiment_key] = exp

    def add_experiment(self, experiment: ABExperiment) -> None:
        """Thêm experiment vào engine."""
        if experiment.experiment_key in self.experiments:
            EM.raise_error(
                ErrorCode.CP37_DUPLICATE_EXPERIMENT_KEY,
                experiment_key=experiment.experiment_key,
                message=f"Experiment key đã tồn tại: {experiment.experiment_key}"
            )
        self.experiments[experiment.experiment_key] = experiment

    def get_experiment(self, experiment_key: str) -> ABExperiment | None:
        """Lấy experiment theo key."""
        return self.experiments.get(experiment_key)

    def get_active_experiments(self) -> list[ABExperiment]:
        """Lấy danh sách experiments đang chạy."""
        return [exp for exp in self.experiments.values() if exp.is_running]

    def assign(self, experiment_key: str, user_id: str) -> ABVariant | None:
        """Assign user vào variant của experiment (deterministic).

        Args:
            experiment_key: Experiment key
            user_id: User ID để assign

        Returns:
            ABVariant được assign, hoặc None nếu experiment không chạy

        Raises:
            MidicoderError: Nếu experiment không tồn tại
        """
        experiment = self.experiments.get(experiment_key)
        if not experiment:
            EM.raise_error(
                ErrorCode.CP37_EXPERIMENT_NOT_FOUND,
                experiment_key=experiment_key,
                message=f"Không tìm thấy experiment: {experiment_key}"
            )

        if not experiment.is_running:
            return None

        # Kiểm tra traffic percentage
        bucket = int(hashlib.sha256(user_id.encode()).hexdigest(), 16) % 100
        if bucket >= experiment.traffic_percentage:
            return None

        # Deterministic variant selection
        user_hash = int(hashlib.sha256(f"{experiment_key}:{user_id}".encode()).hexdigest(), 16)
        variant_bucket = user_hash % 100
        cumulative = 0.0
        for variant in experiment.variants:
            cumulative += variant.weight
            if variant_bucket < cumulative:
                return variant

        return experiment.variants[-1]

    def create_assignment(self, experiment_key: str, user_id: str, tenant_id: str = "") -> ABExperimentAssignment | None:
        """Tạo assignment record cho user.

        Args:
            experiment_key: Experiment key
            user_id: User ID
            tenant_id: Tenant ID

        Returns:
            ABExperimentAssignment hoặc None
        """
        variant = self.assign(experiment_key, user_id)
        if variant is None:
            return None
        return ABExperimentAssignment(
            experiment_key=experiment_key,
            user_id=user_id,
            tenant_id=tenant_id,
            assigned_variant=variant.variant_key,
        )


# ===========================================================================
# Dynamic Configuration
# ===========================================================================


@dataclass
class ConfigChange:
    """Audit trail cho config change.

    Attributes:
        config_key: Config key được thay đổi
        old_value: Giá trị cũ
        new_value: Giá trị mới
        changed_by: Người thay đổi
        changed_at: Thời điểm thay đổi
        reason: Lý do thay đổi
    """
    config_key: str
    old_value: Any = None
    new_value: Any = None
    changed_by: str = ""
    changed_at: datetime | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        """Set timestamp nếu chưa có."""
        if self.changed_at is None:
            self.changed_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển ConfigChange sang dict."""
        return {
            "config_key": self.config_key,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "changed_by": self.changed_by,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConfigChange":
        """Tạo ConfigChange từ dict."""
        return cls(
            config_key=data.get("config_key", ""),
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            changed_by=data.get("changed_by", ""),
            changed_at=datetime.fromisoformat(data["changed_at"]) if data.get("changed_at") else None,
            reason=data.get("reason", ""),
        )


@dataclass
class DynamicConfig:
    """Dynamic configuration key-value.

    Attributes:
        config_key: Key duy nhất, hierarchical (section.subsection.key)
        value: Giá trị (JSON serializable)
        value_type: Loại giá trị
        scope: Scope (global, tenant, environment)
        tenant_id: Tenant ID (nullable, chỉ dùng khi scope=tenant)
        environment: Environment (nullable)
        is_encrypted: Có encrypt value không
        audit_trail: Lịch sử thay đổi
        created_at: Thời điểm tạo
        updated_at: Thời điểm cập nhật cuối
    """
    config_key: str
    value: Any = None
    value_type: ConfigValueType = ConfigValueType.STRING
    scope: ConfigScope = ConfigScope.GLOBAL
    tenant_id: str | None = None
    environment: str | None = None
    is_encrypted: bool = False
    audit_trail: list[ConfigChange] = field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate dynamic config."""
        if not self.config_key or not self.config_key.strip():
            EM.raise_error(ErrorCode.CP37_EMPTY_CONFIG_KEY, message="Config key không được để trống")

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    def update_value(self, new_value: Any, changed_by: str, reason: str) -> None:
        """Cập nhật giá trị config và ghi audit trail.

        Args:
            new_value: Giá trị mới
            changed_by: Người thay đổi
            reason: Lý do thay đổi
        """
        change = ConfigChange(
            config_key=self.config_key,
            old_value=self.value,
            new_value=new_value,
            changed_by=changed_by,
            reason=reason,
        )
        self.value = new_value
        self.updated_at = datetime.now(timezone.utc)
        self.audit_trail.append(change)

    def to_dict(self) -> dict[str, Any]:
        """Chuyển DynamicConfig sang dict."""
        return {
            "config_key": self.config_key,
            "value": self.value,
            "value_type": self.value_type.value,
            "scope": self.scope.value,
            "tenant_id": self.tenant_id,
            "environment": self.environment,
            "is_encrypted": self.is_encrypted,
            "audit_trail": [c.to_dict() for c in self.audit_trail],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DynamicConfig":
        """Tạo DynamicConfig từ dict."""
        audit_data = data.get("audit_trail", [])
        audit_trail = [ConfigChange.from_dict(c) for c in audit_data]
        return cls(
            config_key=data.get("config_key", ""),
            value=data.get("value"),
            value_type=ConfigValueType(data.get("value_type", "string")),
            scope=ConfigScope(data.get("scope", "global")),
            tenant_id=data.get("tenant_id"),
            environment=data.get("environment"),
            is_encrypted=data.get("is_encrypted", False),
            audit_trail=audit_trail,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


# ===========================================================================
# Storage Interface
# ===========================================================================


class FlagStore(ABC):
    """Abstract interface cho storage backend của flag/experiment/config.

    Các implement: RedisFlagStore, DatabaseFlagStore
    """

    @abstractmethod
    def get_all_flags(self) -> list[FeatureFlag]:
        """Lấy tất cả flags."""
        ...

    @abstractmethod
    def get_flag(self, flag_key: str) -> FeatureFlag | None:
        """Lấy flag theo key."""
        ...

    @abstractmethod
    def save_flag(self, flag: FeatureFlag) -> None:
        """Lưu flag."""
        ...

    @abstractmethod
    def delete_flag(self, flag_key: str) -> None:
        """Xóa flag."""
        ...

    @abstractmethod
    def get_all_experiments(self) -> list[ABExperiment]:
        """Lấy tất cả experiments."""
        ...

    @abstractmethod
    def get_experiment(self, experiment_key: str) -> ABExperiment | None:
        """Lấy experiment theo key."""
        ...

    @abstractmethod
    def save_experiment(self, experiment: ABExperiment) -> None:
        """Lưu experiment."""
        ...

    @abstractmethod
    def get_config(self, config_key: str) -> DynamicConfig | None:
        """Lấy config theo key."""
        ...

    @abstractmethod
    def save_config(self, config: DynamicConfig) -> None:
        """Lưu config."""
        ...


# ===========================================================================
# Exports
# ===========================================================================

__all__ = [
    # Enums
    "FlagVariantType",
    "ConditionType",
    "ConfigScope",
    "ConfigValueType",
    # Feature Flags
    "FeatureFlag",
    "TargetingRule",
    "FlagEvaluation",
    "FeatureFlagEvaluator",
    # A/B Testing
    "ABExperiment",
    "ABVariant",
    "ABExperimentAssignment",
    "ABExperimentEngine",
    # Dynamic Config
    "DynamicConfig",
    "ConfigChange",
    # Storage
    "FlagStore",
]
