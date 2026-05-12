"""Compat shim — re-exports from domain_model.command_nestjs."""
from midicoder.emitters.core.domain_model.command_nestjs import NestJSCommandEmitter, _to_snake_case

__all__ = ["NestJSCommandEmitter", "_to_snake_case"]
