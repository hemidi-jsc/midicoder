from __future__ import annotations


from .models import PlanItemRuntime


def _map_type(t: str) -> str:
    raw = t.lower().strip()
    return {
        "string": "str",
        "uuid": "UUID",
        "datetime": "datetime",
        "int": "int",
        "integer": "int",
        "boolean": "bool",
        "bool": "bool",
    }.get(raw, "str")


def _entity_block(plan_item: PlanItemRuntime) -> str:
    pseudo = plan_item.payload.get("pseudo_struct", {})
    entity = pseudo.get("entity", {})
    fields = entity.get("fields", []) if isinstance(entity, dict) else []
    lines = [f"# region {plan_item.ir_ref}", "class GeneratedModel(BaseModel):"]
    if not fields:
        lines.append("    pass")
    else:
        for field in fields:
            if not isinstance(field, dict):
                continue
            name = str(field.get("name", "field"))
            typ = _map_type(str(field.get("type", "string")))
            required = bool(field.get("required", False))
            if required:
                lines.append(f"    {name}: {typ}")
            else:
                lines.append(f"    {name}: {typ} | None = None")
    lines.append(f"# endregion {plan_item.ir_ref}")
    return "\n".join(lines) + "\n"


def _workflow_block(plan_item: PlanItemRuntime) -> str:
    workflow = (
        plan_item.payload.get("pseudo_struct", {}).get("workflow", {})
        if isinstance(plan_item.payload.get("pseudo_struct"), dict)
        else {}
    )
    transitions = workflow.get("transitions", []) if isinstance(workflow, dict) else []
    lines = [f"# region {plan_item.ir_ref}", "WORKFLOW_TRANSITIONS = ["]
    for transition in transitions:
        if not isinstance(transition, dict):
            continue
        lines.append(
            "    "
            + repr(
                {
                    "from_state": transition.get("from_state"),
                    "to_state": transition.get("to_state"),
                    "on_command": transition.get("on_command"),
                }
            )
            + ","
        )
    lines.append("]")
    lines.append(f"# endregion {plan_item.ir_ref}")
    return "\n".join(lines) + "\n"


def _service_block(plan_item: PlanItemRuntime) -> str:
    pseudo = plan_item.payload.get("pseudo_struct", {})
    inputs = pseudo.get("inputs", []) if isinstance(pseudo, dict) else []
    outputs = pseudo.get("outputs", []) if isinstance(pseudo, dict) else []
    args = ", ".join(
        f"{str(i.get('name', 'arg'))}: str" for i in inputs if isinstance(i, dict)
    )
    lines = [
        f"# region {plan_item.ir_ref}",
        f"def handle_{plan_item.ir_ref.replace('.', '_').lower()}({args}) -> dict[str, Any]:",
    ]
    lines.append("    return {")
    for output in outputs:
        if isinstance(output, dict):
            name = str(output.get("name", "value"))
            lines.append(f"        {name!r}: None,")
    lines.append("    }")
    lines.append(f"# endregion {plan_item.ir_ref}")
    return "\n".join(lines) + "\n"


def _schema_block(plan_item: PlanItemRuntime) -> str:
    routes = (
        plan_item.payload.get("pseudo_struct", {}).get("api", {}).get("routes", [])
        if isinstance(plan_item.payload.get("pseudo_struct"), dict)
        else []
    )
    lines = [f"# region {plan_item.ir_ref}"]
    for route in routes:
        if not isinstance(route, dict):
            continue
        rid = str(route.get("id", "route")).title().replace("_", "").replace("-", "")
        lines.append(f"class {rid}Request(BaseModel):")
        req = route.get("request_schema", [])
        if req:
            for field in req:
                if isinstance(field, dict):
                    lines.append(f"    {field.get('name', 'field')}: str")
        else:
            lines.append("    pass")
        lines.append("")
        lines.append(f"class {rid}Response(BaseModel):")
        resp = route.get("response_schema", [])
        if resp:
            for field in resp:
                if isinstance(field, dict):
                    lines.append(f"    {field.get('name', 'field')}: str | None = None")
        else:
            lines.append("    pass")
        lines.append("")
    lines.append(f"# endregion {plan_item.ir_ref}")
    return "\n".join(lines) + "\n"


def _controller_block(plan_item: PlanItemRuntime) -> str:
    routes = (
        plan_item.payload.get("pseudo_struct", {}).get("api", {}).get("routes", [])
        if isinstance(plan_item.payload.get("pseudo_struct"), dict)
        else []
    )
    lines = [f"# region {plan_item.ir_ref}"]
    for route in routes:
        if not isinstance(route, dict):
            continue
        method = str(route.get("method", "POST")).lower()
        path = str(route.get("path", "/"))
        fn_name = str(route.get("id", "handler")).lower().replace("-", "_")
        lines.append(f"@router.{method}({path!r})")
        lines.append(f"def {fn_name}() -> dict[str, Any]:")
        lines.append("    return {}")
        lines.append("")
    lines.append(f"# endregion {plan_item.ir_ref}")
    return "\n".join(lines) + "\n"


def _bootstrap_block(plan_item: PlanItemRuntime) -> str:
    return (
        f"# region {plan_item.ir_ref}\n"
        "app = FastAPI(title='Midicoder Generated App')\n"
        f"# endregion {plan_item.ir_ref}\n"
    )


def build_deterministic_block(plan_item: PlanItemRuntime, runtime_path: str) -> str:
    normalized = runtime_path.replace("\\", "/")
    if normalized.endswith("/model.py"):
        return _entity_block(plan_item)
    if normalized.endswith("/workflow.py"):
        return _workflow_block(plan_item)
    if normalized.endswith("/service.py"):
        return _service_block(plan_item)
    if normalized.endswith("/schema.py"):
        return _schema_block(plan_item)
    if normalized.endswith("/controller.py"):
        return _controller_block(plan_item)
    if normalized.endswith("/main.py"):
        return _bootstrap_block(plan_item)
    return f"# region {plan_item.ir_ref}\npass\n# endregion {plan_item.ir_ref}\n"


def base_file_content(runtime_path: str) -> str:
    normalized = runtime_path.replace("\\", "/")
    if normalized.endswith("/model.py"):
        return "from __future__ import annotations\n\nfrom datetime import datetime\nfrom uuid import UUID\n\nfrom pydantic import BaseModel\n\n"
    if normalized.endswith("/workflow.py"):
        return "from __future__ import annotations\n\n"
    if normalized.endswith("/service.py"):
        return "from __future__ import annotations\n\nfrom typing import Any\n\n"
    if normalized.endswith("/schema.py"):
        return (
            "from __future__ import annotations\n\nfrom pydantic import BaseModel\n\n"
        )
    if normalized.endswith("/controller.py"):
        return (
            "from __future__ import annotations\n\n"
            "from typing import Any\n\n"
            "from fastapi import APIRouter\n\n"
            "router = APIRouter()\n\n"
        )
    if normalized.endswith("/main.py"):
        return "from __future__ import annotations\n\nfrom fastapi import FastAPI\n\n"
    return "from __future__ import annotations\n\n"
