"""Compat shim — re-exports from domain_model.vo_models."""
from midicoder.emitters.core.domain_model.vo_models import (
    ValueObject, VOField, VOFieldType,
)

__all__ = ["ValueObject", "VOField", "VOFieldType"]
