"""
Pack Emitter Router.

Routes FileSpecs to pack-specific emitters instead of raw Jinja2.
This is the dispatch layer between pipeline's code gen and structured
pack emitters (e.g., CP01 EntityEmitter, VOEmitter).

Usage in code.py:
    if pack_emitter := file_spec.metadata.get("pack_emitter"):
        files = PackEmitterRouter.dispatch(pack_emitter, file_spec, stack)
    else:
        # raw Jinja2 fallback
        content = Emitter.render(template, context)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from .config import get_config


# ---------------------------------------------------------------------------
# Registry: pack_emitter key → (module_path, class_name, parser_key | None)
#
# parser_key is an optional hint telling the router which parser to use
# to convert the raw MIR dict into a structured dataclass before passing
# it to the emitter.
# ---------------------------------------------------------------------------

EMITTER_REGISTRY: dict[str, tuple[str, str, str | None]] = {
    # CP01 – Entity (FastAPI)
    "cp01.entity.fastapi": (
        "midicoder.emitters.core.cp01_domain_model.entity_fastapi",
        "FastAPIEntityEmitter",
        "cp01_entity",
    ),
    # CP01 – Entity (NestJS)
    "cp01.entity.nestjs": (
        "midicoder.emitters.core.cp01_domain_model.entity_nestjs",
        "NestJSEntityEmitter",
        "cp01_entity",
    ),
    # CP01 – Value Object (FastAPI)
    "cp01.vo.fastapi": (
        "midicoder.emitters.core.cp01_domain_model.vo_fastapi",
        "FastAPIValueObjectEmitter",
        None,  # VO emitters accept raw dicts
    ),
    # CP01 – Value Object (NestJS)
    "cp01.vo.nestjs": (
        "midicoder.emitters.core.cp01_domain_model.vo_nestjs",
        "NestJSValueObjectEmitter",
        None,
    ),
    # CP07 – Docker Compose (already used, kept for reference)
    "cp07.docker": (
        "midicoder.emitters.core.cp07_iac.docker",
        "DockerComposeGenerator",
        None,
    ),
}


# ---------------------------------------------------------------------------
# Parser registry: parser_key → callable(raw_dict) → dataclass
# ---------------------------------------------------------------------------

def _parse_entity_dict(raw: dict[str, Any]) -> Any:
    """Parse a raw entity dict from MIR metadata into a CP01 Entity dataclass."""
    from midicoder.emitters.core.cp01_domain_model.entity_parser import EntityParser
    parser = EntityParser()

    # EntityParser expects a YAML-like dict with "entities" key.
    # MIR metadata stores entities as a flat list of dicts, so wrap it.
    import yaml
    yaml_safe = {
        "entities": [raw],
    }
    yaml_str = yaml.dump(yaml_safe)
    entities = parser.parse(yaml_str)
    return entities[0] if entities else None


PARSER_REGISTRY: dict[str, Any] = {
    "cp01_entity": _parse_entity_dict,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class PackEmitterRouter:
    """
    Dispatches FileSpecs to pack-specific emitters.

    The router resolves the stack-specific emitter class, instantiates it
    with the correct template directory, and calls its ``emit()`` method.
    If a parser key is registered, raw MIR dicts are converted to typed
    dataclasses before dispatch.
    """

    @staticmethod
    def dispatch(
        pack_emitter: str,
        file_spec: dict[str, Any],
        stack: str,
    ) -> list[dict[str, str]]:
        """
        Dispatch a single FileSpec to the appropriate pack emitter.

        Args:
            pack_emitter: Key in EMITTER_REGISTRY (e.g. "cp01.entity.fastapi")
            file_spec: FileSpec as dict (path, context, template, …)
            stack: Stack name ("fastapi", "nestjs", …)

        Returns:
            List of ``{"path": ..., "content": ...}`` — one entry per
            generated file.  Multi-file emitters (e.g. command emitter)
            may return more than one entry.
        """
        if pack_emitter not in EMITTER_REGISTRY:
            raise KeyError(
                f"Unknown pack_emitter '{pack_emitter}'. "
                f"Available: {list(EMITTER_REGISTRY.keys())}"
            )

        module_path, class_name, parser_key = EMITTER_REGISTRY[pack_emitter]

        # Resolve template directory
        stack_dir = _resolve_stack_dir(stack)

        # Import and instantiate emitter
        mod = importlib.import_module(module_path)
        emitter_cls = getattr(mod, class_name)
        emitter = emitter_cls(stack_dir=stack_dir)

        # Get raw data from FileSpec context
        context = file_spec.get("context", {})
        file_path = file_spec.get("path", "")
        file_type = file_spec.get("file_type", file_spec.get("type", ""))

        # Parse raw dict → dataclass if parser registered
        entity_data = context.get("entity")
        vo_data = context.get("vo")

        if entity_data and parser_key and parser_key in PARSER_REGISTRY:
            entity = PARSER_REGISTRY[parser_key](entity_data)
            if entity is None:
                return _fallback_placeholder(file_path, "Failed to parse entity dict")

            # Collect all entities for relationship resolution
            all_entities_raw = context.get("all_entities", [])
            all_entities = []
            for raw_e in all_entities_raw:
                parsed = PARSER_REGISTRY[parser_key](raw_e)
                if parsed:
                    all_entities.append(parsed)

            # --- Entity emitter dispatch ---
            # Entity emitters return a single string (the model code)
            try:
                if file_type in ("model", "schema"):
                    content = emitter.emit(entity, all_entities)
                else:
                    # repository, route — entity emitter only produces model code
                    # for model/schema types; fall through for others
                    return _fallback_placeholder(
                        file_path,
                        f"Entity emitter does not produce '{file_type}' files; "
                        f"use raw Jinja2 instead",
                    )
                return [{"path": file_path, "content": content}]
            except Exception as exc:
                return _fallback_placeholder(file_path, str(exc))

        elif vo_data:
            # --- Value Object emitter dispatch ---
            # VO emitters accept raw dicts directly
            try:
                content = emitter.render_value_object(vo_data)
                return [{"path": file_path, "content": content}]
            except Exception as exc:
                return _fallback_placeholder(file_path, str(exc))

        elif hasattr(emitter, "emit"):
            # Generic dispatch — emitter.emit(entity, all_entities) or
            # emitter.emit(command, output_dir) — try to call emit()
            try:
                if entity_data:
                    result = emitter.emit(entity_data, context.get("all_entities", []))
                else:
                    # Some emitters take (data, output_dir) — pass empty
                    result = emitter.emit(None, Path("."))
                if isinstance(result, str):
                    return [{"path": file_path, "content": result}]
                elif isinstance(result, dict):
                    return [{"path": k, "content": v} for k, v in result.items()]
                else:
                    return _fallback_placeholder(
                        file_path, f"Emitter returned unexpected type {type(result)}"
                    )
            except Exception as exc:
                return _fallback_placeholder(file_path, str(exc))

        else:
            return _fallback_placeholder(
                file_path,
                f"Cannot dispatch '{pack_emitter}' — no matching data in context",
            )


def _resolve_stack_dir(stack: str) -> Path:
    """
    Resolve the absolute template directory for a given stack.

    Mirrors the resolution logic in pipeline/emitter.py:
    ``package_dir / "stacks" / stack / "core"``
    """
    package_dir = Path(__file__).resolve().parent.parent  # midicoder/
    new_dir = package_dir / "stacks" / stack / "core"
    old_dir = package_dir / "stacks" / stack / "templates"

    if new_dir.exists():
        return new_dir
    elif old_dir.exists():
        return old_dir
    else:
        # Create empty dir so Jinja2 doesn't crash
        new_dir.mkdir(parents=True, exist_ok=True)
        return new_dir


def _fallback_placeholder(
    file_path: str, reason: str
) -> list[dict[str, str]]:
    """Return a single-file result with a placeholder / error comment."""
    content = (
        f"# Placeholder — pack emitter dispatch failed\n"
        f"# Reason: {reason}\n"
        f"# File: {file_path}\n"
        f"pass\n"
    )
    return [{"path": file_path, "content": content}]
