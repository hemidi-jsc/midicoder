"""
MCP Tools Package.

Export tất cả MCP tool functions cho auto-discovery bởi server.py.

Tool registry:
- MCP-B (DSL Schema): get_dsl_schema, get_dsl_section
- MCP-C (Packs): list_packs, get_pack
- MCP-D (Compiler): compile_contracts, validate_capability_graph
- MCP-E (SQLite): get_active_brief, get_clarifications, list_artifacts
- MCP-F (Context): get_project_context, list_symbols
- MCP-G (Contract Validation): validate_contract_yaml, cross_check_category, verify_structural_fidelity, get_generated_artifact
"""

from midicoder.mcp.tools.dsl_schema import get_dsl_schema, get_dsl_section
from midicoder.mcp.tools.packs import list_packs, get_pack
from midicoder.mcp.tools.compiler import compile_contracts, validate_capability_graph
from midicoder.mcp.tools.sqlite_tools import (
    get_active_brief,
    get_clarifications,
    list_artifacts,
)
from midicoder.mcp.tools.context import get_project_context, list_symbols
from midicoder.mcp.tools.contract_validation import (
    validate_contract_yaml,
    cross_check_category,
    verify_structural_fidelity,
    get_generated_artifact,
)

# Tool registry — mapping tool_name → callable
# Dùng bởi server.py để auto-register tools với MCP server
TOOLS = {
    # MCP-B: DSL Schema Tools
    "get_dsl_schema": {
        "function": get_dsl_schema,
        "description": "Trả về schema đầy đủ của DSL — tất cả node types, fields, required/optional. Source: midicoder.dsl.projection (TypedDict models).",
        "parameters": {},
        "group": "dsl_schema",
    },
    "get_dsl_section": {
        "function": get_dsl_section,
        "description": "Trả về schema cho một section cụ thể của DSL (entities, commands, render_context, infrastructure, ...). Bao gồm styles schema từ presets.",
        "parameters": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": "Tên section (vd: 'entities', 'commands', 'render_context', 'infrastructure', 'access_control', 'observability', 'api', 'supporting')",
                }
            },
            "required": ["section"],
        },
        "group": "dsl_schema",
    },
    # MCP-C: Pack Tools
    "list_packs": {
        "function": list_packs,
        "description": "Trả về danh sách tất cả packs với metadata (id, internal_id, name, status, category, description). Source: midicoder.contracts.registry + pack.yml files.",
        "parameters": {},
        "group": "packs",
    },
    "get_pack": {
        "function": get_pack,
        "description": "Trả về thông tin chi tiết cho một pack cụ thể: capabilities, file_contributions, emitter info, definitions, recipes, obligations.",
        "parameters": {
            "type": "object",
            "properties": {
                "pack_id": {
                    "type": "string",
                    "description": "Pack ID (vd: 'CP01', 'CP02', ... 'CP65')",
                }
            },
            "required": ["pack_id"],
        },
        "group": "packs",
    },
    # MCP-D: Compiler Tools
    "compile_contracts": {
        "function": compile_contracts,
        "description": "Kích hoạt biên dịch contracts từ brief. Đọc brief từ SQLite, load DSL files, build capability graph, và generate contracts output.",
        "parameters": {
            "type": "object",
            "properties": {
                "brief_id": {
                    "type": "string",
                    "description": "ID của brief để biên dịch",
                }
            },
            "required": ["brief_id"],
        },
        "group": "compiler",
    },
    "validate_capability_graph": {
        "function": validate_capability_graph,
        "description": "Kiểm tra tính liên thông (connectivity) của capability graph. Build graph từ pack dependencies và kiểm tra cycles, orphan nodes, connected components.",
        "parameters": {
            "type": "object",
            "properties": {
                "brief_id": {
                    "type": "string",
                    "description": "ID của brief (dùng để filter capabilities nếu cần)",
                }
            },
            "required": ["brief_id"],
        },
        "group": "compiler",
    },
    # MCP-E: SQLite Tools
    "get_active_brief": {
        "function": get_active_brief,
        "description": "Lấy active brief hiện tại từ SQLite database. Kiểm tra .midicoder/active_brief file, fallback đến brief mới nhất.",
        "parameters": {},
        "group": "sqlite",
    },
    "get_clarifications": {
        "function": get_clarifications,
        "description": "Lấy tất cả clarifications (Q&A) cho một brief. Group by round, tách memos.",
        "parameters": {
            "type": "object",
            "properties": {
                "brief_id": {
                    "type": "string",
                    "description": "ID của brief",
                }
            },
            "required": ["brief_id"],
        },
        "group": "sqlite",
    },
    "list_artifacts": {
        "function": list_artifacts,
        "description": "Lấy danh sách tất cả artifacts (contracts, generated files) cho một brief. Group by type và status.",
        "parameters": {
            "type": "object",
            "properties": {
                "brief_id": {
                    "type": "string",
                    "description": "ID của brief để filter artifacts. Nếu không có, trả về tất cả.",
                }
            },
            "required": [],
        },
        "group": "sqlite",
    },
    # MCP-F: Context Tools
    "get_project_context": {
        "function": get_project_context,
        "description": "Trả về project context — domain, stack configuration, số lượng entities/commands/queries, database status, output directory status.",
        "parameters": {},
        "group": "context",
    },
    "list_symbols": {
        "function": list_symbols,
        "description": "Trả về danh sách tất cả symbols (entities, commands, queries, events, value_objects) từ DSL files và SQLite context database.",
        "parameters": {},
        "group": "context",
    },
    # MCP-G: Contract Validation Tools
    "validate_contract_yaml": {
        "function": validate_contract_yaml,
        "description": "Validate YAML + DSL constraints của một category contract. Trả về errors/warnings chi tiết. Dùng để tự xác thực contract trước khi hoàn tất.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Tên category (entities, commands, queries, events, workflows, value_objects, guards, roles, ui_components)",
                },
                "yaml_content": {
                    "type": "string",
                    "description": "Raw YAML string cần validate",
                },
            },
            "required": ["category", "yaml_content"],
        },
        "group": "contract_validation",
    },
    "cross_check_category": {
        "function": cross_check_category,
        "description": "Cross-reference một category với các category đã generate. Kiểm tra references (entity, event, role) có tồn tại không.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Tên category đang check",
                },
                "yaml_content": {
                    "type": "string",
                    "description": "Raw YAML string của category này",
                },
            },
            "required": ["category", "yaml_content"],
        },
        "group": "contract_validation",
    },
    "verify_structural_fidelity": {
        "function": verify_structural_fidelity,
        "description": "So sánh contract YAML với analysis data để phát hiện structural drifts (missing fields, inputs, permissions, missing nodes).",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Tên category đang verify",
                },
                "yaml_content": {
                    "type": "string",
                    "description": "Raw YAML string của contract đang kiểm tra",
                },
            },
            "required": ["category", "yaml_content"],
        },
        "group": "contract_validation",
    },
    "get_generated_artifact": {
        "function": get_generated_artifact,
        "description": "Lấy nội dung artifact đã generate từ SQLite cho một category. Dùng để cross-check hoặc tham khảo category trước đó.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Tên category (entities, commands, queries, events, workflows, value_objects, guards, roles, ui_components)",
                }
            },
            "required": ["category"],
        },
        "group": "contract_validation",
    },
}

__all__ = [
    # Tool functions
    "get_dsl_schema",
    "get_dsl_section",
    "list_packs",
    "get_pack",
    "compile_contracts",
    "validate_capability_graph",
    "get_active_brief",
    "get_clarifications",
    "list_artifacts",
    "get_project_context",
    "list_symbols",
    "validate_contract_yaml",
    "cross_check_category",
    "verify_structural_fidelity",
    "get_generated_artifact",
    # Registry
    "TOOLS",
]
