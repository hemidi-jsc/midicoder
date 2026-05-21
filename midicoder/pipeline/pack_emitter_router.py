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
    # CP03 – Auth (FastAPI)
    "cp03.auth.fastapi": (
        "midicoder.emitters.core.cp03_auth.fastapi",
        "FastAPIAuthEmitter",
        "cp03_auth",
    ),
    # CP03 – Auth (NestJS)
    "cp03.auth.nestjs": (
        "midicoder.emitters.core.cp03_auth.nestjs",
        "NestJSEmitter",
        "cp03_auth",
    ),
    # CP03 – Auth (Angular)
    "cp03.auth.angular": (
        "midicoder.emitters.core.cp03_auth.angular",
        "AngularEmitter",
        "cp03_auth",
    ),
    # CP03 – Auth (React)
    "cp03.auth.react": (
        "midicoder.emitters.core.cp03_auth.react",
        "ReactEmitter",
        "cp03_auth",
    ),
    # CP04 – RBAC (FastAPI)
    "cp04.rbac.fastapi": (
        "midicoder.emitters.core.cp04_rbac.fastapi",
        "FastAPIRBACEmitter",
        None,
    ),
    # CP04 – RBAC (NestJS)
    "cp04.rbac.nestjs": (
        "midicoder.emitters.core.cp04_rbac.nestjs",
        "NestJSRBACEmitter",
        None,
    ),
    # CP04 – RBAC (Angular)
    "cp04.rbac.angular": (
        "midicoder.emitters.core.cp04_rbac.angular",
        "AngularRBACEmitter",
        None,
    ),
    # CP04 – RBAC (React)
    "cp04.rbac.react": (
        "midicoder.emitters.core.cp04_rbac.react",
        "ReactRBACEmitter",
        None,
    ),
    # CP07 – Docker Compose (already used, kept for reference)
    "cp07.docker": (
        "midicoder.emitters.core.cp07_iac.docker",
        "DockerComposeGenerator",
        None,
    ),
    # CP08 – Database (FastAPI)
    "cp08.database.fastapi": (
        "midicoder.emitters.core.cp08_database.fastapi",
        "SQLAlchemyEmitter",
        "cp08_database",
    ),
    # CP08 – Database (NestJS)
    "cp08.database.nestjs": (
        "midicoder.emitters.core.cp08_database.nestjs",
        "TypeORMEmitter",
        "cp08_database",
    ),
    # CP10 – Search (FastAPI)
    "cp10.search.fastapi": (
        "midicoder.emitters.core.cp10_search.fastapi",
        "FastAPISearchEmitter",
        "cp10_search",
    ),
    # CP10 – Search (NestJS)
    "cp10.search.nestjs": (
        "midicoder.emitters.core.cp10_search.nestjs",
        "NestJSSearchEmitter",
        "cp10_search",
    ),
    # CP10 – Search (Angular)
    "cp10.search.angular": (
        "midicoder.emitters.core.cp10_search.angular",
        "AngularEmitter",
        "cp10_search",
    ),
    # CP10 – Search (React)
    "cp10.search.react": (
        "midicoder.emitters.core.cp10_search.react",
        "ReactEmitter",
        "cp10_search",
    ),
    # CP05 – Event (FastAPI)
    "cp05.event.fastapi": (
        "midicoder.emitters.core.cp05_event_driven.fastapi",
        "FastAPIEventEmitter",
        "cp05_event",
    ),
    # CP05 – Event (NestJS)
    "cp05.event.nestjs": (
        "midicoder.emitters.core.cp05_event_driven.nestjs",
        "NestJSEventEmitter",
        "cp05_event",
    ),
    # CP06 – API Gateway (FastAPI)
    "cp06.gateway.fastapi": (
        "midicoder.emitters.core.cp06_api_gateway.fastapi",
        "FastAPIGatewayEmitter",
        "cp06_gateway",
    ),
    # CP06 – API Gateway (NestJS)
    "cp06.gateway.nestjs": (
        "midicoder.emitters.core.cp06_api_gateway.nestjs",
        "NestJSGatewayEmitter",
        "cp06_gateway",
    ),
    # CP06 – API Gateway (Angular)
    "cp06.gateway.angular": (
        "midicoder.emitters.core.cp06_api_gateway.angular",
        "AngularGatewayEmitter",
        "cp06_gateway",
    ),
    # CP06 – API Gateway (React)
    "cp06.gateway.react": (
        "midicoder.emitters.core.cp06_api_gateway.react",
        "ReactGatewayEmitter",
        "cp06_gateway",
    ),
    # CP09 – Cache (FastAPI)
    "cp09.cache.fastapi": (
        "midicoder.emitters.core.cp09_cache.fastapi",
        "FastAPICacheEmitter",
        "cp09_cache",
    ),
    # CP09 – Cache (NestJS)
    "cp09.cache.nestjs": (
        "midicoder.emitters.core.cp09_cache.nestjs",
        "NestJSCacheEmitter",
        "cp09_cache",
    ),
    # CP09 – Cache (Angular)
    "cp09.cache.angular": (
        "midicoder.emitters.core.cp09_cache.angular",
        "AngularEmitter",
        "cp09_cache",
    ),
    # CP09 – Cache (React)
    "cp09.cache.react": (
        "midicoder.emitters.core.cp09_cache.react",
        "ReactEmitter",
        "cp09_cache",
    ),
    # CP18 – Frontend Framework (Angular)
    "cp18.frontend.angular": (
        "midicoder.emitters.core.cp18_frontend_framework.angular",
        "AngularComponentEmitter",
        "cp18_frontend",
    ),
    # CP18 – Frontend Framework (React)
    "cp18.frontend.react": (
        "midicoder.emitters.core.cp18_frontend_framework.react",
        "ReactComponentEmitter",
        "cp18_frontend",
    ),
    # CP18 – Frontend Framework (FastAPI backend config)
    "cp18.frontend.fastapi": (
        "midicoder.emitters.core.cp18_frontend_framework.fastapi",
        "FastAPIFrontendEmitter",
        "cp18_frontend",
    ),
    # CP18 – Frontend Framework (NestJS backend config)
    "cp18.frontend.nestjs": (
        "midicoder.emitters.core.cp18_frontend_framework.nestjs",
        "NestJSFrontendEmitter",
        "cp18_frontend",
    ),
    # CP19 – UI Components (Angular)
    "cp19.angular": (
        "midicoder.emitters.core.cp19_ui_components.angular",
        "AngularUIEmitter",
        "cp19_ui_component",
    ),
    # CP19 – UI Components (React)
    "cp19.react": (
        "midicoder.emitters.core.cp19_ui_components.react",
        "ReactUIEmitter",
        "cp19_ui_component",
    ),
    # CP19 – UI Components (FastAPI)
    "cp19.fastapi": (
        "midicoder.emitters.core.cp19_ui_components.fastapi",
        "FastAPIUIEmitter",
        "cp19_ui_component",
    ),
    # CP19 – UI Components (NestJS)
    "cp19.nestjs": (
        "midicoder.emitters.core.cp19_ui_components.nestjs",
        "NestJSUIEmitter",
        "cp19_ui_component",
    ),
    # CP22 – Real-time UI (React)
    "cp22.react": (
        "midicoder.emitters.core.cp22_realtime_ui.react",
        "RealtimeComponentEmitter",
        "cp22_realtime",
    ),
    # CP22 – Real-time UI (Angular)
    "cp22.angular": (
        "midicoder.emitters.core.cp22_realtime_ui.angular",
        "AngularRealtimeEmitter",
        "cp22_realtime",
    ),
    # CP24 – Quality & Security (FastAPI)
    "cp24.quality.fastapi": (
        "midicoder.emitters.core.cp24_quality_security.fastapi",
        "FastAPIQualityEmitter",
        "cp24_quality",
    ),
    # CP24 – Quality & Security (NestJS)
    "cp24.quality.nestjs": (
        "midicoder.emitters.core.cp24_quality_security.nestjs",
        "NestJSQualityEmitter",
        "cp24_quality",
    ),
    # CP24 – Quality & Security (Angular)
    "cp24.quality.angular": (
        "midicoder.emitters.core.cp24_quality_security.angular",
        "AngularQualityEmitter",
        "cp24_quality",
    ),
    # CP24 – Quality & Security (React)
    "cp24.quality.react": (
        "midicoder.emitters.core.cp24_quality_security.react",
        "ReactQualityEmitter",
        "cp24_quality",
    ),
    # CP34 – Report & Document (FastAPI)
    "cp34.report.fastapi": (
        "midicoder.emitters.core.cp34_reporting.fastapi",
        "FastAPIReportEmitter",
        "cp34_report",
    ),
    # CP34 – Report & Document (NestJS)
    "cp34.report.nestjs": (
        "midicoder.emitters.core.cp34_reporting.nestjs",
        "NestJSReportEmitter",
        "cp34_report",
    ),
    # CP34 – Report & Document (Angular)
    "cp34.report.angular": (
        "midicoder.emitters.core.cp34_reporting.angular",
        "AngularReportEmitter",
        "cp34_report",
    ),
    # CP34 – Report & Document (React)
    "cp34.report.react": (
        "midicoder.emitters.core.cp34_reporting.react",
        "ReactReportEmitter",
        "cp34_report",
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


def _parse_database_dict(raw: dict[str, Any]) -> Any:
    """Parse a raw database dict from MIR metadata into a CP08 DataModelCollection."""
    from midicoder.emitters.core.cp08_database.parser import DBParser
    parser = DBParser()
    return parser.parse_from_metadata(raw)


def _parse_auth_dict(raw: dict[str, Any]) -> Any:
    """Parse a raw auth dict from MIR metadata into a CP03 AuthIR dataclass."""
    from midicoder.emitters.core.cp03_auth.parser import AuthParser
    import yaml

    # AuthParser expects a file path, but we have raw dict — create a minimal
    # YAML structure and use the internal parse methods.
    yaml_safe = raw if "authentication" in raw else {
        "authentication": {"providers": raw.get("providers", [])},
    }
    yaml_str = yaml.dump(yaml_safe)

    # Use a temp file for AuthParser
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False, encoding="utf-8") as f:
        f.write(yaml_str)
        f.flush()
        parser = AuthParser(f.name)
        auth_ir = parser.parse()
    import os
    os.unlink(f.name)
    return auth_ir


def _parse_search_dict(raw: dict[str, Any]) -> Any:
    """Parse raw MIR metadata into a CP10 SearchCollection."""
    from midicoder.emitters.core.cp10_search.parser import SearchParser
    parser = SearchParser()
    return parser.parse_from_metadata(raw)


def _parse_event_dict(raw: dict[str, Any]) -> Any:
    """Parse raw event dict from MIR metadata into a CP05 EventDefinition list."""
    from midicoder.emitters.core.cp05_event_driven.parser import EventParser
    parser = EventParser()
    # MIR metadata stores events as a list of dicts — pass directly
    if isinstance(raw, list):
        return parser.parse(raw)
    # If it's a single dict, wrap in list
    return parser.parse([raw])


def _parse_cache_dict(raw: dict[str, Any]) -> Any:
    """Parse raw MIR metadata into a CP09 CacheCollection."""
    from midicoder.emitters.core.cp09_cache.parser import CacheParser
    parser = CacheParser()
    return parser.parse_from_metadata(raw)


def _parse_gateway_dict(raw: dict[str, Any]) -> Any:
    """Parse raw MIR metadata into a CP06 RouteCollection."""
    from midicoder.emitters.core.cp06_api_gateway.route_parser import RouteParser
    parser = RouteParser()
    return parser.parse_from_metadata(
        routes_data=raw.get("routes"),
        graphql_data=raw.get("graphql"),
        webhooks_data=raw.get("webhooks"),
    )


def _parse_frontend_dict(raw: dict[str, Any]) -> Any:
    """Parse raw frontend dict from DSL/MIR into CP18 FrontendApp dataclass."""
    from midicoder.emitters.core.cp18_frontend_framework.parser import FrontendFrameworkParser
    import yaml

    # FrontendFrameworkParser expects a YAML string — serialize the raw dict
    yaml_str = yaml.dump(raw)
    parser = FrontendFrameworkParser()
    result = parser.parse(yaml_str)
    return result.get("frontend_app")


def _parse_ui_component_dict(raw: dict[str, Any]) -> Any:
    """Parse raw UI component dict from DSL/MIR into CP19 ComponentSpec list."""
    from midicoder.emitters.core.cp19_ui_components.models import ComponentSpec

    # raw can be a single dict or a list of dicts
    if isinstance(raw, list):
        return [ComponentSpec.from_dict(item) for item in raw if isinstance(item, dict)]
    elif isinstance(raw, dict):
        # If it has a "components" key, unwrap it
        if "components" in raw:
            return [ComponentSpec.from_dict(item) for item in raw["components"]]
        # Otherwise treat as single ComponentSpec
        return [ComponentSpec.from_dict(raw)]
    return []


def _parse_realtime_dict(raw: dict[str, Any]) -> Any:
    """Parse raw realtime events dict from CP05/MIR into CP22 ChannelSpec list."""
    from midicoder.emitters.core.cp22_realtime_ui.parser import RealtimeParser
    parser = RealtimeParser()
    # raw can be list of event dicts, or a dict with 'events' key
    if isinstance(raw, list):
        return parser.parse(raw)
    elif isinstance(raw, dict):
        events = raw.get("events", raw.get("channels", []))
        return parser.parse(events) if events else []
    return []


def _parse_quality_dict(raw: dict[str, Any]) -> Any:
    """Parse raw quality config dict from DSL/MIR into CP24 QualityCollection."""
    from midicoder.emitters.core.cp24_quality_security.parser import QualityProfileParser
    parser = QualityProfileParser()
    return parser.parse_from_metadata(raw)


def _parse_report_dict(raw: dict[str, Any]) -> Any:
    """Parse raw report dict from DSL/MIR into CP34 ReportCollection."""
    from midicoder.emitters.core.cp34_reporting.parser import ReportParser
    parser = ReportParser()
    return parser.parse_from_metadata(raw)


PARSER_REGISTRY: dict[str, Any] = {
    "cp01_entity": _parse_entity_dict,
    "cp08_database": _parse_database_dict,
    "cp03_auth": _parse_auth_dict,
    "cp10_search": _parse_search_dict,
    "cp05_event": _parse_event_dict,
    "cp09_cache": _parse_cache_dict,
    "cp06_gateway": _parse_gateway_dict,
    "cp18_frontend": _parse_frontend_dict,
    "cp19_ui_component": _parse_ui_component_dict,
    "cp22_realtime": _parse_realtime_dict,
    "cp24_quality": _parse_quality_dict,
    "cp34_report": _parse_report_dict,
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

        # CP19 emitters accept (ui_framework=...) not (stack_dir=...)
        if pack_emitter.startswith("cp19.") or pack_emitter.startswith("cp22."):
            emitter = emitter_cls()
        else:
            emitter = emitter_cls(stack_dir=stack_dir)

        # Get raw data from FileSpec context
        context = file_spec.get("context", {})
        file_path = file_spec.get("path", "")
        file_type = file_spec.get("file_type", file_spec.get("type", ""))

        # Parse raw dict → dataclass if parser registered
        entity_data = context.get("entity")
        vo_data = context.get("vo")

        # ── CP19: UI Component emitter (must be FIRST — uses raw entity dict) ──
        if parser_key == "cp19_ui_component" or pack_emitter.startswith("cp19."):
            # --- UI Component emitter dispatch ---
            # CP19 emitters take (list[ComponentSpec], output_dir) and return
            # list[GeneratedFile] with path/content attributes.
            try:
                from midicoder.emitters.core.cp19_ui_components.models import ComponentSpec

                entity = context.get("entity")
                components = []

                # Case 1: components is a list of strings (component_type names) from per_ui_component expansion
                components_raw = context.get("components")
                if isinstance(components_raw, list) and components_raw and isinstance(components_raw[0], str):
                    if entity:
                        type_to_factory = {
                            "form_field": ComponentSpec.generate_form,
                            "data_table": ComponentSpec.generate_table,
                            "card_list": ComponentSpec.generate_card_list,
                            "dialog": ComponentSpec.generate_dialog,
                        }
                        for ct in components_raw:
                            factory = type_to_factory.get(ct)
                            if factory:
                                try:
                                    components.append(factory(entity))
                                except Exception:
                                    pass

                # Case 2: components is a list of dicts (explicit ComponentSpec from MIR)
                elif components_raw:
                    components = _parse_ui_component_dict(components_raw)

                # Case 3: fallback — ui_components key
                elif context.get("ui_components"):
                    components = _parse_ui_component_dict(context["ui_components"])

                # Case 4: single entity, no components — generate all 4 types
                elif entity and not components:
                    components = [
                        ComponentSpec.generate_form(entity),
                        ComponentSpec.generate_table(entity),
                        ComponentSpec.generate_card_list(entity),
                        ComponentSpec.generate_dialog(entity),
                    ]

                import tempfile
                with tempfile.TemporaryDirectory() as tmp:
                    output_dir = Path(tmp)
                    generated = emitter.generate(components, output_dir)
                    results = []
                    for gf in generated:
                        if hasattr(gf, "content"):
                            content = gf.content
                        elif hasattr(gf, "path") and gf.path.exists():
                            content = gf.path.read_text(encoding="utf-8")
                        else:
                            continue
                        rel = str(getattr(gf, "path", Path(file_path)))
                        if tmp in rel:
                            try:
                                rel = str(Path(rel).relative_to(tmp))
                            except ValueError:
                                pass
                        results.append({"path": rel, "content": content})
                    return results if results else _fallback_placeholder(
                        file_path, "UI Component emitter produced no files"
                    )
            except Exception as exc:
                return _fallback_placeholder(file_path, str(exc))

        elif entity_data and parser_key and parser_key in PARSER_REGISTRY:
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

        elif parser_key == "cp10_search" or pack_emitter.startswith("cp10."):
            # --- Search emitter dispatch ---
            # Search emitters take (SearchCollection, output_dir) and return
            # list[GeneratedFile] with path/content attributes.
            try:
                collection = PARSER_REGISTRY["cp10_search"](context)
                import tempfile
                with tempfile.TemporaryDirectory() as tmp:
                    output_dir = Path(tmp)
                    generated = emitter.emit(collection, output_dir)
                    results = []
                    for gf in generated:
                        # GeneratedFile can have .content str or need file read
                        if hasattr(gf, "content"):
                            content = gf.content
                        elif hasattr(gf, "path") and gf.path.exists():
                            content = gf.path.read_text(encoding="utf-8")
                        else:
                            continue
                        # Build relative path from output_dir
                        rel = str(getattr(gf, "path", Path(file_path)))
                        if tmp in rel:
                            try:
                                rel = str(Path(rel).relative_to(tmp))
                            except ValueError:
                                pass
                        results.append({"path": rel, "content": content})
                    return results if results else _fallback_placeholder(
                        file_path, "Search emitter produced no files"
                    )
            except Exception as exc:
                return _fallback_placeholder(file_path, str(exc))

        elif parser_key == "cp06_gateway" or pack_emitter.startswith("cp06."):
            # --- Gateway emitter dispatch ---
            # Gateway emitters take (RouteCollection) via generate() and return
            # dict[file_path, content].
            try:
                collection = PARSER_REGISTRY["cp06_gateway"](context)
                if hasattr(emitter, "generate"):
                    result = emitter.generate(collection)
                    if isinstance(result, dict):
                        return [{"path": k, "content": v} for k, v in result.items()]
                    elif isinstance(result, list):
                        return result
                return _fallback_placeholder(
                    file_path, "Gateway emitter returned unexpected type"
                )
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
