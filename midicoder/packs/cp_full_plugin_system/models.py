# coding: utf-8
"""
Mô-đun models cho Plugin System Generator (CP27).

Định nghĩa các dataclass biểu diễn:
- PluginStatus: Enum trạng thái plugin
- LifecycleEvent: Enum các sự kiện lifecycle
- PolicyType: Enum loại policy
- PluginSlot: Một slot plugin với events và priority range
- PluginContract: Contract định nghĩa slots, config schema, dependencies
- PluginPolicy: Policy an toàn và versioning cho plugin
- PluginManifest: Manifest metadata của plugin
- PluginContext: Context runtime cho plugin execution
- PluginInfo: Thông tin runtime của plugin
- PluginCollection: Collection chứa slots, contracts, policies, manifests

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class PluginStatus(str, Enum):
    """Enum trạng thái plugin."""
    DISABLED = "disabled"
    LOADING = "loading"
    ENABLED = "enabled"
    ERROR = "error"

    __test__ = False  # Prevent pytest collection


class LifecycleEvent(str, Enum):
    """Enum các sự kiện lifecycle của plugin."""
    ON_INIT = "on_init"
    ON_CONFIGURE = "on_configure"
    ON_READY = "on_ready"
    ON_REQUEST = "on_request"
    ON_SHUTDOWN = "on_shutdown"
    BEFORE_ACTION = "before_action"
    AFTER_ACTION = "after_action"

    __test__ = False  # Prevent pytest collection


class PolicyType(str, Enum):
    """Enum loại policy cho plugin."""
    SECURITY = "security"
    VERSIONING = "versioning"

    __test__ = False  # Prevent pytest collection


# ===========================================================================
# PluginSlot
# ===========================================================================


@dataclass
class PluginSlot:
    """
    Một slot plugin — điểm gắn kết plugin vào lifecycle.

    Attributes:
        id: Định danh duy nhất của slot
        name: Tên mô tả slot
        events: Danh sách các lifecycle events mà slot hỗ trợ
        priority_range: Khoảng priority (min, max) cho plugin trong slot
        is_tenant_aware: Slot có nhận biết tenant không
    """
    __test__ = False  # Prevent pytest collection

    id: str
    name: str = ""
    events: list[LifecycleEvent] = field(default_factory=list)
    priority_range: tuple[int, int] = (0, 100)
    is_tenant_aware: bool = True

    def __post_init__(self) -> None:
        """Validate slot sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.MDC-F11_EMPTY_SLOT_ID, field="slot.id")


# ===========================================================================
# PluginContract
# ===========================================================================


@dataclass
class PluginContract:
    """
    Contract định nghĩa yêu cầu của plugin — slots, config schema, dependencies.

    Attributes:
        id: Định danh duy nhất của contract
        slots: Danh sách slot IDs mà contract yêu cầu
        config_schema: Schema cấu hình (dict)
        dependencies: Danh sách dependency IDs
    """
    __test__ = False  # Prevent pytest collection

    id: str
    slots: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate contract sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.MDC-F11_PLUGIN_CONTRACT_VIOLATION, field="contract.id", reason="Contract ID không được để trống")


# ===========================================================================
# PluginPolicy
# ===========================================================================


@dataclass
class PluginPolicy:
    """
    Policy an toàn và versioning cho plugin.

    Attributes:
        id: Định danh duy nhất của policy
        policy_type: Loại policy (security, versioning)
        rule: Quy tắc policy (string expression)
        enforced: Policy có được thực thi không
        config: Cấu hình bổ sung cho policy
    """
    __test__ = False  # Prevent pytest collection

    id: str
    policy_type: PolicyType
    rule: str
    enforced: bool = True
    config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate policy sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.MDC-F11_EMPTY_POLICY_ID, field="policy.id")
        if not self.policy_type:
            EM.raise_error(ErrorCode.MDC-F11_INVALID_POLICY_TYPE, field="policy.policy_type")


# ===========================================================================
# PluginManifest
# ===========================================================================


@dataclass
class PluginManifest:
    """
    Manifest metadata của plugin — định danh, version, slots, dependencies.

    Attributes:
        id: Định danh duy nhất của plugin
        name: Tên plugin
        version: Version của plugin (semver string)
        description: Mô tả plugin
        author: Tác giả plugin
        slots: Danh sách slot IDs mà plugin implement
        min_platform_version: Phiên bản platform tối thiểu
        dependencies: Danh sách plugin dependency IDs
        config_schema: Schema cấu hình plugin
        signature: Chữ ký xác thực plugin (optional)
    """
    __test__ = False  # Prevent pytest collection

    id: str
    name: str = ""
    version: str = "0.0.0"
    description: str = ""
    author: str = ""
    slots: list[str] = field(default_factory=list)
    min_platform_version: str = "0.0.0"
    dependencies: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)
    signature: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate manifest sau khi khởi tạo."""
        if not self.id or not self.id.strip():
            EM.raise_error(ErrorCode.MDC-F11_PLUGIN_NOT_FOUND, field="manifest.id", reason="Manifest ID không được để trống")


# ===========================================================================
# PluginContext
# ===========================================================================


@dataclass
class PluginContext:
    """
    Context runtime cho plugin execution — tenant, user, request, config, event_bus.

    Attributes:
        tenant_id: Tenant ID (đa thuê bao)
        user_id: User ID thực thi
        request_id: Request ID cho tracing
        app_config: Cấu hình ứng dụng (dict)
        event_bus: Event bus instance (optional)
    """
    __test__ = False  # Prevent pytest collection

    tenant_id: str = ""
    user_id: str = ""
    request_id: str = ""
    app_config: dict[str, Any] = field(default_factory=dict)
    event_bus: Any = None


# ===========================================================================
# PluginInfo
# ===========================================================================


@dataclass
class PluginInfo:
    """
    Thông tin runtime của plugin — trạng thái, config, thời gian loaded.

    Attributes:
        id: Định danh plugin
        name: Tên plugin
        version: Version plugin
        status: Trạng thái plugin (PluginStatus)
        slots: Danh sách slots mà plugin đang gắn vào
        config: Cấu hình runtime
        loaded_at: Thời điểm plugin được loaded (optional)
        error: Lỗi nếu plugin gặp sự cố (optional)
    """
    __test__ = False  # Prevent pytest collection

    id: str
    name: str
    version: str
    status: PluginStatus = PluginStatus.DISABLED
    slots: list[str] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    loaded_at: Optional[datetime] = None
    error: Optional[str] = None


# ===========================================================================
# PluginCollection
# ===========================================================================


@dataclass
class PluginCollection:
    """
    Collection chứa tất cả slots, contracts, policies, manifests.

    Dùng làm output của Plugin Parser và input cho Plugin Generator.

    Attributes:
        slots: Danh sách plugin slots
        contracts: Danh sách plugin contracts
        policies: Danh sách plugin policies
        manifests: Danh sách plugin manifests
    """
    __test__ = False  # Prevent pytest collection

    slots: list[PluginSlot] = field(default_factory=list)
    contracts: list[PluginContract] = field(default_factory=list)
    policies: list[PluginPolicy] = field(default_factory=list)
    manifests: list[PluginManifest] = field(default_factory=list)

    def add_slot(self, slot: PluginSlot) -> None:
        """Thêm plugin slot vào collection."""
        self.slots.append(slot)

    def add_contract(self, contract: PluginContract) -> None:
        """Thêm plugin contract vào collection."""
        if self.get_contract_by_id(contract.id):
            EM.raise_error(ErrorCode.MDC-F11_PLUGIN_CONTRACT_VIOLATION, id=contract.id, reason="Duplicate contract ID")
        self.contracts.append(contract)

    def add_policy(self, policy: PluginPolicy) -> None:
        """Thêm plugin policy vào collection."""
        if self.get_policy_by_id(policy.id):
            EM.raise_error(ErrorCode.MDC-F11_PLUGIN_POLICY_VIOLATION, id=policy.id, reason="Duplicate policy ID")
        self.policies.append(policy)

    def add_manifest(self, manifest: PluginManifest) -> None:
        """Thêm plugin manifest vào collection."""
        self.manifests.append(manifest)

    def get_slot_by_id(self, slot_id: str) -> Optional[PluginSlot]:
        """Tìm slot theo ID."""
        for slot in self.slots:
            if slot.id == slot_id:
                return slot
        return None

    def get_contract_by_id(self, contract_id: str) -> Optional[PluginContract]:
        """Tìm contract theo ID."""
        for contract in self.contracts:
            if contract.id == contract_id:
                return contract
        return None

    def get_policy_by_id(self, policy_id: str) -> Optional[PluginPolicy]:
        """Tìm policy theo ID."""
        for policy in self.policies:
            if policy.id == policy_id:
                return policy
        return None

    def has_duplicate_slots(self) -> bool:
        """Kiểm tra có slot ID trùng lặp không."""
        seen: set[str] = set()
        for slot in self.slots:
            if slot.id in seen:
                return True
            seen.add(slot.id)
        return False

    def to_dict(self) -> dict[str, Any]:
        """Chuyển collection sang dict format."""
        return {
            "slots": [
                {
                    "id": s.id,
                    "name": s.name,
                    "events": [e.value for e in s.events],
                    "priority_range": list(s.priority_range),
                    "is_tenant_aware": s.is_tenant_aware,
                }
                for s in self.slots
            ],
            "contracts": [
                {
                    "id": c.id,
                    "slots": c.slots,
                    "config_schema": c.config_schema,
                    "dependencies": c.dependencies,
                }
                for c in self.contracts
            ],
            "policies": [
                {
                    "id": p.id,
                    "policy_type": p.policy_type.value,
                    "rule": p.rule,
                    "enforced": p.enforced,
                    "config": p.config,
                }
                for p in self.policies
            ],
            "manifests": [
                {
                    "id": m.id,
                    "name": m.name,
                    "version": m.version,
                    "description": m.description,
                    "author": m.author,
                    "slots": m.slots,
                    "min_platform_version": m.min_platform_version,
                    "dependencies": m.dependencies,
                    "config_schema": m.config_schema,
                    "signature": m.signature,
                }
                for m in self.manifests
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PluginCollection":
        """Tạo PluginCollection từ dict."""
        collection = cls()

        for slot_data in data.get("slots", []):
            slot = PluginSlot(
                id=slot_data["id"],
                name=slot_data["name"],
                events=[LifecycleEvent(e) for e in slot_data.get("events", [])],
                priority_range=tuple(slot_data.get("priority_range", [0, 100])),
                is_tenant_aware=slot_data.get("is_tenant_aware", False),
            )
            collection.add_slot(slot)

        for contract_data in data.get("contracts", []):
            contract = PluginContract(
                id=contract_data["id"],
                slots=contract_data.get("slots", []),
                config_schema=contract_data.get("config_schema", {}),
                dependencies=contract_data.get("dependencies", []),
            )
            collection.add_contract(contract)

        for policy_data in data.get("policies", []):
            policy = PluginPolicy(
                id=policy_data["id"],
                policy_type=PolicyType(policy_data["policy_type"]),
                rule=policy_data["rule"],
                enforced=policy_data.get("enforced", True),
                config=policy_data.get("config", {}),
            )
            collection.add_policy(policy)

        for manifest_data in data.get("manifests", []):
            manifest = PluginManifest(
                id=manifest_data["id"],
                name=manifest_data["name"],
                version=manifest_data["version"],
                description=manifest_data.get("description", ""),
                author=manifest_data.get("author", ""),
                slots=manifest_data.get("slots", []),
                min_platform_version=manifest_data.get("min_platform_version", "0.0.0"),
                dependencies=manifest_data.get("dependencies", []),
                config_schema=manifest_data.get("config_schema", {}),
                signature=manifest_data.get("signature"),
            )
            collection.add_manifest(manifest)

        return collection
