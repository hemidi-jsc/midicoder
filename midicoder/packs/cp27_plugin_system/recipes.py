# coding: utf-8
"""
Recipe module cho CP27 Plugin System Generator.

Recipes cung cấp auto-generate plugin slots, contracts, policies từ MIR metadata
(entities, commands) khi không có DSL plugin nodes explicit.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.packs.cp27_plugin_system.models import (
    LifecycleEvent,
    PluginCollection,
    PluginContract,
    PluginPolicy,
    PluginSlot,
    PolicyType,
)


# ===========================================================================
# Helper: chuyển command ID sang định dạng snake_case
# ===========================================================================


def _to_snake_case(name: str) -> str:
    """
    Chuyển tên entity/command sang snake_case.

    Ví dụ:
        "CreateUser" -> "create_user"
        "GetOrdersList" -> "get_orders_list"
        "updateSettings" -> "update_settings"

    Args:
        name: Tên đầu vào (PascalCase, camelCase, hoặc snake_case)

    Returns:
        Tên đã chuyển sang snake_case
    """
    # Xử lý PascalCase: chèn _ trước ký tự viết hoa (trừ ký tự đầu)
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            # Kiểm tra nếu ký tự trước là chữ thường hoặc
            # nếu ký tự sau là chữ thường (để xử lý chuỗi viết hoa liên tiếp)
            if name[i - 1].islower() or (i + 1 < len(name) and name[i + 1].islower()):
                result.append("_")
        result.append(char.lower())
    return "".join(result)


# ===========================================================================
# Sinh default lifecycle slots
# ===========================================================================


def generate_default_slots(
    entities: list[dict],
    commands: list[dict] | None = None,
) -> list[PluginSlot]:
    """
    Sinh danh sách các lifecycle slots mặc định từ entities và commands.

    Tạo ra:
    - 5 lifecycle slots cố định: on_init, on_configure, on_ready, on_request, on_shutdown
    - before_{command_snake} cho từng command (dùng BEFORE_ACTION event)
    - after_{command_snake} cho từng command (dùng AFTER_ACTION event)

    Args:
        entities: Danh sách entity dict từ MIR metadata
        commands: Danh sách command dict từ MIR metadata (optional)

    Returns:
        Danh sách các PluginSlot đã sinh ra
    """
    slots: list[PluginSlot] = []

    # 5 lifecycle slots cố định
    lifecycle_slots = [
        {
            "id": "slot_on_init",
            "name": "on_init",
            "event": LifecycleEvent.ON_INIT,
            "priority_range": (0, 100),
            "tenant_aware": False,
        },
        {
            "id": "slot_on_configure",
            "name": "on_configure",
            "event": LifecycleEvent.ON_CONFIGURE,
            "priority_range": (0, 100),
            "tenant_aware": False,
        },
        {
            "id": "slot_on_ready",
            "name": "on_ready",
            "event": LifecycleEvent.ON_READY,
            "priority_range": (0, 100),
            "tenant_aware": False,
        },
        {
            "id": "slot_on_request",
            "name": "on_request",
            "event": LifecycleEvent.ON_REQUEST,
            "priority_range": (0, 100),
            "tenant_aware": True,
        },
        {
            "id": "slot_on_shutdown",
            "name": "on_shutdown",
            "event": LifecycleEvent.ON_SHUTDOWN,
            "priority_range": (0, 100),
            "tenant_aware": False,
        },
    ]

    for slot_def in lifecycle_slots:
        slots.append(PluginSlot(
            id=slot_def["id"],
            name=slot_def["name"],
            events=[slot_def["event"]],
            priority_range=slot_def["priority_range"],
            is_tenant_aware=slot_def["tenant_aware"],
        ))

    # Sinh before/after slots cho từng command
    if commands:
        for command in commands:
            cmd_id = command.get("id", command.get("name", "unknown"))
            cmd_snake = _to_snake_case(cmd_id)

            # before_{command_snake}
            before_id = f"slot_before_{cmd_snake}"
            slots.append(PluginSlot(
                id=before_id,
                name=f"before_{cmd_snake}",
                events=[LifecycleEvent.BEFORE_ACTION],
                priority_range=(0, 100),
                is_tenant_aware=True,
            ))

            # after_{command_snake}
            after_id = f"slot_after_{cmd_snake}"
            slots.append(PluginSlot(
                id=after_id,
                name=f"after_{cmd_snake}",
                events=[LifecycleEvent.AFTER_ACTION],
                priority_range=(0, 100),
                is_tenant_aware=True,
            ))

    return slots


# ===========================================================================
# Sinh default contracts
# ===========================================================================


def generate_default_contracts(
    slots: list[PluginSlot] | None = None,
) -> list[PluginContract]:
    """
    Sinh contract mặc định bao gồm tất cả các slots đã sinh.

    Tạo ra 1 contract chính "default" với tất cả slot IDs được liệt kê.

    Args:
        slots: Danh sách PluginSlot đã sinh (nếu None, tạo contract rỗng)

    Returns:
        Danh sách các PluginContract đã sinh ra
    """
    contracts: list[PluginContract] = []

    slot_ids = [s.id for s in (slots or [])]

    contracts.append(PluginContract(
        id="contract_default",
        slots=slot_ids,
        config_schema={},
        dependencies=[],
    ))

    return contracts


# ===========================================================================
# Sinh default policies
# ===========================================================================


def generate_default_policies() -> list[PluginPolicy]:
    """
    Sinh danh sách các policies mặc định cho plugin system.

    Tạo ra 3 policies:
    - signature_check (security): xác thực chữ ký SHA-256 của plugin
    - version_gate (versioning): kiểm tra phiên bản semver của plugin
    - origin_whitelist (security): whitelist các nguồn plugin được phép

    Returns:
        Danh sách các PluginPolicy đã sinh ra
    """
    policies: list[PluginPolicy] = []

    # Policy 1: kiểm tra chữ ký SHA-256
    policies.append(PluginPolicy(
        id="policy_signature_check",
        policy_type=PolicyType.SECURITY,
        rule="verify_sha256",
        enforced=True,
        config={
            "algorithm": "sha256",
            "require_signature": True,
            "allow_unsigned_dev": True,
        },
    ))

    # Policy 2: kiểm tra phiên bản semver
    policies.append(PluginPolicy(
        id="policy_version_gate",
        policy_type=PolicyType.VERSIONING,
        rule="semver_range",
        enforced=True,
        config={
            "min_version": "0.1.0",
            "max_version": "2.0.0",
            "compatible_ranges": [">=1.0.0 <2.0.0"],
        },
    ))

    # Policy 3: whitelist nguồn plugin
    policies.append(PluginPolicy(
        id="policy_origin_whitelist",
        policy_type=PolicyType.SECURITY,
        rule="allowed_origins",
        enforced=True,
        config={
            "allowed_origins": [
                "midicoder://official",
                "midicoder://verified",
            ],
            "allow_local_dev": True,
            "reject_unknown": True,
        },
    ))

    return policies


# ===========================================================================
# Master recipe: auto-generate PluginCollection từ MIR metadata
# ===========================================================================


def auto_generate_plugins_from_mir(metadata: dict) -> PluginCollection:
    """
    Auto-generate toàn bộ PluginCollection từ MIR metadata.

    Đây là fallback khi không có DSL plugin nodes explicit.
    Hàm này đọc entities và commands từ metadata, sau đó sinh ra:
    - Default lifecycle slots + before/after hooks cho mỗi command
    - Default contract bao gồm tất cả slots
    - Default policies (signature, version, origin)

    Args:
        metadata: MIR metadata dict, chứa các keys:
            - "entities": list[dict] — danh sách entity metadata
            - "commands": list[dict] — danh sách command metadata

    Returns:
        PluginCollection chứa slots, contracts, policies đã sinh
    """
    collection = PluginCollection()

    # Đọc entities và commands từ metadata
    entities = metadata.get("entities", [])
    commands = metadata.get("commands", [])

    # Bước 1: sinh các slots mặc định
    slots = generate_default_slots(entities, commands)
    for slot in slots:
        collection.add_slot(slot)

    # Bước 2: sinh contracts từ danh sách slots
    contracts = generate_default_contracts(slots)
    for contract in contracts:
        collection.add_contract(contract)

    # Bước 3: sinh các policies mặc định
    policies = generate_default_policies()
    for policy in policies:
        collection.add_policy(policy)

    return collection


__all__ = [
    "auto_generate_plugins_from_mir",
    "generate_default_slots",
    "generate_default_contracts",
    "generate_default_policies",
]
