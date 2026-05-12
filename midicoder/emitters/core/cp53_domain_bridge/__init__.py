# coding: utf-8
"""
Domain Pack Runtime Bridge (CP53)

Hệ thống runtime bridge để generic CPs có thể invoke domain-specific
semantics của Domain Packs. Cung cấp:
- DomainPackDescriptor: Metadata và discovery của domain pack
- BridgeBinding: Ánh xạ CP capability → DP handler
- RuntimeInvoker: Dispatch/routing để invoke DP capability tại runtime

Sử dụng:
    from midicoder.emitters.core.domain_bridge import (
        DomainPackDescriptor,
        BridgeBinding,
        RuntimeInvoker,
        FastAPIDomainBridgeEmitter,
        NestJSDomainBridgeEmitter,
    )

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from midicoder.emitters.core.domain_bridge.models import (
    DomainPackDescriptor,
    BridgeBinding,
    RuntimeInvoker,
)
from midicoder.emitters.core.domain_bridge.fastapi import FastAPIDomainBridgeEmitter
from midicoder.emitters.core.domain_bridge.nestjs import NestJSDomainBridgeEmitter

__all__ = [
    # Models
    "DomainPackDescriptor",
    "BridgeBinding",
    "RuntimeInvoker",
    # Emitters
    "FastAPIDomainBridgeEmitter",
    "NestJSDomainBridgeEmitter",
]
