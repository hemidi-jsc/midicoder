"""DSL schema package for Midicoder.

This package contains the Pydantic models that define the
contract/DSL schema used by Midicoder CLI.

`DSL_SCHEMA_VERSION` tracks the current schema version used for
these models. Backwards-compatible changes should keep the same
version; breaking changes should bump it and coexist with the
previous version.
"""

from __future__ import annotations

DSL_SCHEMA_VERSION = "v0"

__all__ = ["DSL_SCHEMA_VERSION"]

