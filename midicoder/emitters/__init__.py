"""
Emitter module cho Midicoder.

Module này chứa các emitters để generate configuration files:
- Kong Gateway YAML emitter
- Consul HCL emitter
- Future: Other infrastructure emitters

Author: Midicoder Team
Version: 1.0.0
"""

from .kong_gateway import KongGatewayEmitter

__all__ = ["KongGatewayEmitter"]