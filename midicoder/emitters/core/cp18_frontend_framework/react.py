"""React Component Emitter (P2-002-E).

Module này cung cấp ReactComponentEmitter để emit UI components
cho React frontend với features:
- CRUD Components: ListView, DetailView, FormView
- Dashboard Component với widgets
- Layout Component với sidebar navigation
- Support 5 UI Frameworks: material, tailwind, bootstrap, antd, carbon

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.emitters.core.cp18_frontend_framework.models import RouteDefinition, StateStoreConfig

# Resolve template directory relative to this package
_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_TEMPLATE_DIR = _PACKAGE_DIR / "stacks" / "react" / "core" / "cp18_frontend_framework"


@dataclass
class GeneratedFile:
    """File đã generate."""
    path: Path
    content: str
    template: str


class ReactComponentEmitter:
    """Emitter cho React Functional Components.

    Generate code cho:
    - ListView: Data table với pagination/filtering
    - DetailView: Chi tiết entity
    - FormView: CRUD form với validation
    - Dashboard: Stats widgets
    - Layout: App shell với sidebar navigation

    Usage:
        emitter = ReactComponentEmitter(ui_framework="antd")
        files = emitter.emit(entities, output_dir)
    """

    SUPPORTED_UI_FRAMEWORKS = ["material", "tailwind", "bootstrap", "antd", "carbon"]

    def __init__(self, ui_framework: str = "antd") -> None:
        self.ui_framework = ui_framework
        if ui_framework not in self.SUPPORTED_UI_FRAMEWORKS:
            raise ValueError("UI framework '" + ui_framework + "' không được hỗ trợ.")

        # Initialize Jinja2 environment for CP18 templates
        self._template_env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Register custom filter to strip leading slash from route paths
        self._template_env.filters["lstrip_slash"] = lambda s: s.lstrip("/")  # type: ignore[assignment]

    def _render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a jinja2 template with the given context."""
        try:
            template = self._template_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            return f"// {template_name} - template not found\n"

    def _serialize_route(self, route: RouteDefinition) -> dict[str, Any]:
        """Serialize RouteDefinition to dict for jinja2 template."""
        return {
            "path": route.path,
            "component": route.component,
            "children": [self._serialize_route(c) for c in route.children],
        }

    def emit(
        self,
        entities: list[dict[str, Any]],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit React components.

        Args:
            entities: Danh sách entities với id và fields
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []
        components_dir = output_dir / "components"
        components_dir.mkdir(parents=True, exist_ok=True)

        for entity in entities:
            files.extend(self._emit_entity_components(entity, components_dir, output_dir))

        files.extend(self._emit_layout_component(components_dir, output_dir))
        files.extend(self._emit_dashboard_component(components_dir, entities, output_dir))

        return files

    # ------------------------------------------------------------------
    # CP18 additions: routes & state store
    # ------------------------------------------------------------------

    def emit_routes(
        self,
        routes: list[RouteDefinition],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Generate react-router config từ RouteDefinition.

        Template: routes.tsx.jinja2

        Args:
            routes: Danh sách RouteDefinition.
            output_dir: Output directory.

        Returns:
            List of GeneratedFile instances.
        """
        content = self._render_template("routes.tsx.jinja2", {
            "routes": [self._serialize_route(r) for r in routes],
        })
        return [self._write_file("routes.tsx", content, output_dir, output_dir)]

    def emit_state_store(
        self,
        store_config: StateStoreConfig,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Generate Zustand store từ StateStoreConfig.

        Template: store.ts.jinja2

        Args:
            store_config: Config state store.
            output_dir: Output directory.

        Returns:
            List of GeneratedFile instances.
        """
        content = self._render_template("store.ts.jinja2", {
            "entities": store_config.entities,
            "selectors": store_config.selectors,
            "actions": store_config.actions,
        })
        return [self._write_file("store.ts", content, output_dir, output_dir)]

    def _emit_entity_components(
        self, entity: dict[str, Any], output_dir: Path, root_dir: Path
    ) -> list[GeneratedFile]:
        """Emit List/Detail/Form cho 1 entity."""
        entity_id = entity["id"]
        entity_lower = entity_id.lower()
        entity_dir = output_dir / entity_id
        entity_dir.mkdir(parents=True, exist_ok=True)

        files: list[GeneratedFile] = []
        files.extend(self._emit_list_view(entity_id, entity_lower, entity_dir, root_dir))
        files.extend(self._emit_detail_view(entity_id, entity_lower, entity.get("fields", []), entity_dir, root_dir))
        files.extend(self._emit_form_view(entity_id, entity_lower, entity.get("fields", []), entity_dir, root_dir))
        return files

    def _emit_list_view(
        self, entity_id: str, entity_lower: str, output_dir: Path, root_dir: Path
    ) -> list[GeneratedFile]:
        """Emit ListView Component."""
        import_stmt = self._get_ui_import()
        table_code = self._get_table_component(entity_id, entity_lower)

        content = (
            '/** ' + entity_id + ' ListView - Danh sách ' + entity_lower + 's với table, pagination, filtering. */\n'
            '\n'
            'import React, { useState, useEffect } from "react";\n'
            'import { useGet' + entity_id + 'sQuery } from "../../services/' + entity_lower + '-api";\n'
            + import_stmt + '\n'
            '\n'
            'export interface ' + entity_id + 'ListProps {\n'
            '  filter?: Record<string, unknown>;\n'
            '  onItemSelected?: (item: ' + entity_id + ') => void;\n'
            '}\n'
            '\n'
            'export const ' + entity_id + 'List: React.FC<' + entity_id + 'ListProps> = ({\n'
            '  filter = {},\n'
            '  onItemSelected,\n'
            '}) => {\n'
            '  const [page, setPage] = useState(1);\n'
            '  const [limit] = useState(20);\n'
            '\n'
            '  const { data, isLoading, error } = useGet' + entity_id + 'sQuery({\n'
            '    filter,\n'
            '    page,\n'
            '    limit,\n'
            '  });\n'
            '\n'
            '  const items = data?.items ?? [];\n'
            '  const total = data?.total ?? 0;\n'
            '\n'
            '  return (\n'
            '    <div>\n'
            '      <h1>' + entity_id + 's List</h1>\n'
            '      {isLoading && <p>Loading...</p>}\n'
            '      {error && <p>Error loading data</p>}\n'
            '      {!isLoading && !error && (\n'
            + table_code + '\n'
            '      )}\n'
            '    </div>\n'
            '  );\n'
            '};\n'
        )
        return [self._write_file(entity_lower + '-list.tsx', content, output_dir, root_dir)]

    def _emit_detail_view(
        self, entity_id: str, entity_lower: str, fields: list[dict], output_dir: Path, root_dir: Path
    ) -> list[GeneratedFile]:
        """Emit DetailView Component."""
        fields_jsx = self._generate_fields_jsx(fields)

        content = (
            '/** ' + entity_id + ' DetailView - Hiển thị chi tiết ' + entity_lower + '. */\n'
            '\n'
            'import React from "react";\n'
            'import { useGet' + entity_id + 'ByIdQuery } from "../../services/' + entity_lower + '-api";\n'
            '\n'
            'export interface ' + entity_id + 'DetailProps {\n'
            '  id: string;\n'
            '}\n'
            '\n'
            'export const ' + entity_id + 'Detail: React.FC<' + entity_id + 'DetailProps> = ({ id }) => {\n'
            '  const { data, isLoading, error } = useGet' + entity_id + 'ByIdQuery(id);\n'
            '\n'
            '  if (isLoading) return <p>Loading...</p>;\n'
            '  if (error) return <p>Error loading data</p>;\n'
            '  if (!data) return <p>Not found</p>;\n'
            '\n'
            '  return (\n'
            '    <div>\n'
            '      <h1>' + entity_id + ' Detail</h1>\n'
            '      <div className="detail-card">\n'
            + fields_jsx + '\n'
            '      </div>\n'
            '    </div>\n'
            '  );\n'
            '};\n'
        )
        return [self._write_file(entity_lower + '-detail.tsx', content, output_dir, root_dir)]

    def _emit_form_view(
        self, entity_id: str, entity_lower: str, fields: list[dict], output_dir: Path, root_dir: Path
    ) -> list[GeneratedFile]:
        """Emit FormView Component với validation."""
        form_fields = self._generate_form_fields(fields)

        content = (
            '/** ' + entity_id + ' FormView - Form tạo/sửa ' + entity_lower + ' với validation. */\n'
            '\n'
            'import React, { useState } from "react";\n'
            'import {\n'
            '  useCreate' + entity_id + 'Mutation,\n'
            '  useUpdate' + entity_id + 'Mutation,\n'
            '} from "../../services/' + entity_lower + '-api";\n'
            '\n'
            'export interface ' + entity_id + 'FormProps {\n'
            '  item?: { id: string };\n'
            '  isEdit?: boolean;\n'
            '  onSave?: (item: any) => void;\n'
            '  onCancel?: () => void;\n'
            '}\n'
            '\n'
            'export const ' + entity_id + 'Form: React.FC<' + entity_id + 'FormProps> = ({\n'
            '  item,\n'
            '  isEdit = false,\n'
            '  onSave,\n'
            '  onCancel,\n'
            '}) => {\n'
            '  const [createItem, { isLoading: creating }] = useCreateOrderMutation();\n'
            '  const [updateItem, { isLoading: updating }] = useUpdateOrderMutation();\n'
            '  const [formData, setFormData] = useState(item ?? {});\n'
            '  const [errors, setErrors] = useState<Record<string, string>>({});\n'
            '\n'
            '  const validate = (): boolean => {\n'
            '    const newErrors: Record<string, string> = {};\n'
            '    // Validation rules cho từng field\n'
            '    setErrors(newErrors);\n'
            '    return Object.keys(newErrors).length === 0;\n'
            '  };\n'
            '\n'
            '  const handleSubmit = async (e: React.FormEvent) => {\n'
            '    e.preventDefault();\n'
            '    if (!validate()) return;\n'
            '    try {\n'
            '      let result;\n'
            '      if (isEdit && item) {\n'
            '        result = await updateItem({ id: item.id, data: formData }).unwrap();\n'
            '      } else {\n'
            '        result = await createItem(formData).unwrap();\n'
            '      }\n'
            '      onSave?.(result);\n'
            '    } catch (error) {\n'
            '      console.error("Lỗi khi submit form:", error);\n'
            '    }\n'
            '  };\n'
            '\n'
            '  return (\n'
            '    <form onSubmit={handleSubmit}>\n'
            '      <h2>{isEdit ? "Edit" : "Create"} Order</h2>\n'
            + form_fields + '\n'
            '      <div className="form-actions">\n'
            '        <button type="submit" disabled={creating || updating}>Save</button>\n'
            '        <button type="button" onClick={onCancel}>Cancel</button>\n'
            '      </div>\n'
            '    </form>\n'
            '  );\n'
            '};\n'
        )
        return [self._write_file(entity_lower + '-form.tsx', content, output_dir, root_dir)]

    def _emit_layout_component(self, output_dir: Path, root_dir: Path) -> list[GeneratedFile]:
        """Emit Layout Component với sidebar navigation."""
        import_stmt = self._get_ui_import()
        content = (
            '/** Layout Component - App shell với sidebar, topbar, breadcrumbs. */\n'
            '\n'
            'import React from "react";\n'
            'import { Link, Outlet, useNavigate } from "react-router-dom";\n'
            + import_stmt + '\n'
            '\n'
            'export const Layout: React.FC = () => {\n'
            '  const navigate = useNavigate();\n'
            '\n'
            '  const handleLogout = () => {\n'
            "    localStorage.removeItem('auth_token');\n"
            "    localStorage.removeItem('auth_user');\n"
            "    navigate('/login');\n"
            '  };\n'
            '\n'
            '  return (\n'
            '    <div style={{ display: "flex", height: "100vh" }}>\n'
            '      {/* Sidebar Navigation */}\n'
            '      <nav style={{ width: 250, background: "#1a1a2e", color: "white" }}>\n'
            '        <div style={{ padding: "1rem" }}>\n'
            '          <h1>App Name</h1>\n'
            '        </div>\n'
            '        <ul style={{ listStyle: "none", padding: 0 }}>\n'
            '          <li><Link to="/dashboard">Dashboard</Link></li>\n'
            '          <li><Link to="/orders">Orders</Link></li>\n'
            '          <li><Link to="/products">Products</Link></li>\n'
            '        </ul>\n'
            '      </nav>\n'
            '\n'
            '      {/* Main Content */}\n'
            '      <main style={{ flex: 1, display: "flex", flexDirection: "column" }}>\n'
            '        <header style={{\n'
            '          display: "flex", justifyContent: "space-between",\n'
            '          padding: "1rem", borderBottom: "1px solid #eee"\n'
            '        }}>\n'
            '          <nav>Breadcrumbs</nav>\n'
            '          <div><button onClick={handleLogout}>Logout</button></div>\n'
            '        </header>\n'
            '        <div style={{ flex: 1, padding: "1rem" }}>\n'
            '          <Outlet />\n'
            '        </div>\n'
            '      </main>\n'
            '    </div>\n'
            '  );\n'
            '};\n'
        )
        return [self._write_file("layout.tsx", content, output_dir, root_dir)]

    def _emit_dashboard_component(
        self, output_dir: Path, entities: list[dict], root_dir: Path
    ) -> list[GeneratedFile]:
        """Emit Dashboard Component với stats widgets."""
        stat_cards = ''.join(
            '        <StatCard title="' + e["id"] + 's" value={' + e["id"].lower() + 'sCount} />\n'
            for e in entities
        )
        content = (
            '/** Dashboard Component - Bảng điều khiển với stats widgets. */\n'
            '\n'
            'import React from "react";\n'
            '\n'
            'interface StatCardProps {\n'
            '  title: string;\n'
            '  value: number;\n'
            '}\n'
            '\n'
            'const StatCard: React.FC<StatCardProps> = ({ title, value }) => (\n'
            '  <div style={{\n'
            '    background: "white", padding: "1.5rem", borderRadius: 8,\n'
            '    boxShadow: "0 2px 4px rgba(0,0,0,0.1)"\n'
            '  }}>\n'
            '    <h3>{title}</h3>\n'
            '    <span style={{ fontSize: "2rem", fontWeight: "bold" }}>{value}</span>\n'
            '  </div>\n'
            ');\n'
            '\n'
            'export const Dashboard: React.FC = () => {\n'
            '  return (\n'
            '    <div style={{ padding: "1rem" }}>\n'
            '      <h1>Dashboard</h1>\n'
            '      <div style={{\n'
            '        display: "grid",\n'
            '        gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",\n'
            '        gap: "1rem", marginBottom: "2rem"\n'
            '      }}>\n'
            + stat_cards + '\n'
            '      </div>\n'
            '      <div style={{\n'
            '        display: "grid",\n'
            '        gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",\n'
            '        gap: "1rem"\n'
            '      }}>\n'
            '        <div style={{ background: "white", padding: "1.5rem", borderRadius: 8 }}>\n'
            '          <h3>Recent Activity</h3>\n'
            '          <p>Widget placeholder cho activity log</p>\n'
            '        </div>\n'
            '        <div style={{ background: "white", padding: "1.5rem", borderRadius: 8 }}>\n'
            '          <h3>Chart</h3>\n'
            '          <p>Widget placeholder cho chart visualization</p>\n'
            '        </div>\n'
            '      </div>\n'
            '    </div>\n'
            '  );\n'
            '};\n'
        )
        return [self._write_file("dashboard.tsx", content, output_dir, root_dir)]

    def _get_ui_import(self) -> str:
        """Lấy import statement theo UI framework."""
        imports = {
            "material": 'import { Table, TableBody, TableCell, TableHead, TableRow, Paper } from "@mui/material";',
            "tailwind": '',
            "bootstrap": 'import { Table, Container, Row, Col } from "react-bootstrap";',
            "antd": 'import { Table, Card, Typography } from "antd";',
            "carbon": 'import { Table, TableBody, TableHeader, TableRow, DataTable } from "@carbon/react";',
        }
        return imports.get(self.ui_framework, '')

    def _get_table_component(self, entity_id: str, entity_lower: str) -> str:
        """Generate table code dựa theo UI framework."""
        if self.ui_framework == "antd":
            return (
                '      <Table\n'
                '        dataSource={items}\n'
                '        rowKey="id"\n'
                '        columns={columns}\n'
                '        pagination={{\n'
                '          current: page,\n'
                '          pageSize: limit,\n'
                '          total,\n'
                '          onChange: setPage,\n'
                '        }}\n'
                '        onRow={{ click: (record) => onItemSelected?.(record) }}\n'
                '      />'
            )
        if self.ui_framework == "material":
            return (
                '      <Paper>\n'
                '        <Table>\n'
                '          <TableHead>\n'
                '            <TableRow>\n'
                '              <TableCell>Col</TableCell>\n'
                '              <TableCell>Col</TableCell>\n'
                '              <TableCell>Col</TableCell>\n'
                '            </TableRow>\n'
                '          </TableHead>\n'
                '          <TableBody>\n'
                '            {items.map((item) => (\n'
                '              <TableRow key={item.id} onClick={() => onItemSelected?.(item)}>\n'
                '                <TableCell>val</TableCell>\n'
                '                <TableCell>val</TableCell>\n'
                '                <TableCell>val</TableCell>\n'
                '              </TableRow>\n'
                '            ))}\n'
                '          </TableBody>\n'
                '        </Table>\n'
                '      </Paper>'
            )
        return (
            '      <table>\n'
            '        <thead>\n'
            '          <tr><th>Header</th><th>Header</th><th>Header</th></tr>\n'
            '        </thead>\n'
            '        <tbody>\n'
            '          {items.map((item) => (\n'
            '            <tr key={item.id} onClick={() => onItemSelected?.(item)}>\n'
            '              <td>value</td>\n'
            '              <td>value</td>\n'
            '              <td>value</td>\n'
            '            </tr>\n'
            '          ))}\n'
            '        </tbody>\n'
            '      </table>'
        )

    def _generate_fields_jsx(self, fields: list[dict]) -> str:
        """Generate field display JSX."""
        lines = []
        for f in fields:
            lines.append('        <div><strong>' + f['name'] + ':</strong> <span>{ data.' + f['name'] + ' }</span></div>')
        return '\n'.join(lines)

    def _generate_form_fields(self, fields: list[dict]) -> str:
        """Generate form input fields."""
        lines = []
        for f in fields:
            name = f['name']
            ftype = f.get('type', 'str')
            input_type = 'number' if ftype in ('int', 'float') else 'text'
            lines.append('      <div>')
            lines.append('        <label>' + name + '</label>')
            lines.append('        <input')
            lines.append('          type="' + input_type + '"')
            lines.append('          value={{formData.' + name + ' ?? ""}}')
            lines.append('          onChange={(e) => setFormData(prev => ({...prev, ' + name + ': e.target.value}))}')
            lines.append('        />')
            lines.append('        {{errors.' + name + ' && <span style={{color: \'red\'}}>{{errors.' + name + '}}</span>}}')
            lines.append('      </div>')
        return '\n'.join(lines)

    def _write_file(
        self, filename: str, content: str, output_dir: Path, root_dir: Path | None = None
    ) -> GeneratedFile:
        """Write file và trả về GeneratedFile.

        Args:
            filename: Tên file
            content: Nội dung file
            output_dir: Directory chứa file
            root_dir: Root directory để tính relative path
        """
        file_path = output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        rel_to = root_dir if root_dir is not None else output_dir.parent
        try:
            rel_path = file_path.relative_to(rel_to)
        except ValueError:
            rel_path = file_path

        return GeneratedFile(
            path=rel_path,
            content=content,
            template="component/react/" + filename,
        )

    # ------------------------------------------------------------------
    # CP18 helper: build react-router config
    # ------------------------------------------------------------------

    def _build_routes_jsx(
        self,
        routes: list[RouteDefinition],
        output_dir: Path,
    ) -> list[str]:
        """Build React routes.tsx content."""
        lines: list[str] = []
        lines.append("/** Auto-generated React routes config. */")
        lines.append("")
        lines.append('import React from "react";')
        lines.append('import { createBrowserRouter, RouteObject } from "react-router-dom";')
        lines.append("")
        lines.append('import { Layout } from "./components/layout";')
        lines.append("")

        # Build route elements
        for route in routes:
            comp = route.component
            lines.append(
                f"const {comp} = React.lazy(() => "
                f"import('./components/{comp.lower()}/{comp.lower()}.tsx'));"
            )
        lines.append("")

        lines.append("const routeElements: RouteObject[] = [")
        lines.append('  {')
        lines.append('    path: "/",')
        lines.append('    element: <Layout />,')
        lines.append('    children: [')

        for route in routes:
            lines.extend(self._route_to_jsx(route, 3))

        lines.append("    ],")
        lines.append("  },")
        lines.append("];")
        lines.append("")
        lines.append("const router = createBrowserRouter(routeElements);")
        lines.append("")
        lines.append("export default router;")
        lines.append("")
        return lines

    def _route_to_jsx(self, route: RouteDefinition, indent: int) -> list[str]:
        """Convert a single RouteDefinition to React route entry."""
        spaces = "  " * indent
        lines: list[str] = []

        lines.append(f"{spaces}{{")
        lines.append(f'{spaces}  path: "{route.path.lstrip("/")}",')
        lines.append(f"{spaces}  element: <{route.component} />,")

        if route.children:
            lines.append(f"{spaces}  children: [")
            for child in route.children:
                lines.extend(self._route_to_jsx(child, indent + 1))
            lines.append(f"{spaces}  ],")

        lines.append(f"{spaces}}},")
        return lines

    # ------------------------------------------------------------------
    # CP18 helper: build Zustand store
    # ------------------------------------------------------------------

    def _build_zustand_store(
        self,
        store_config: StateStoreConfig,
        output_dir: Path,
    ) -> list[str]:
        """Build Zustand store content."""
        lines: list[str] = []
        lines.append("/** Auto-generated Zustand store. */")
        lines.append("")
        lines.append('import { create } from "zustand";')
        lines.append("")

        # Build state interface
        lines.append("// State interface")
        lines.append("interface StoreState {")
        for entity in store_config.entities:
            entity_lower = entity.lower()
            entity_plural = entity_lower + "s"
            lines.append(f"  {entity_plural}: {entity}[];")
            lines.append(f"  {entity_plural}Loading: boolean;")
            lines.append(f"  {entity_plural}Error: string | null;")
        lines.append("}")
        lines.append("")

        # Build actions interface
        lines.append("// Actions interface")
        lines.append("interface StoreActions {")
        for entity in store_config.entities:
            entity_plural = entity.lower() + "s"
            lines.append(f"  set{entity_plural}State: (data: {entity}[]) => void;")
            lines.append(f"  add{entity}: (item: {entity}) => void;")
            lines.append(f"  update{entity}: (id: string, changes: Partial<{entity}>) => void;")
            lines.append(f"  remove{entity}: (id: string) => void;")
        lines.append("}")
        lines.append("")

        # Create store
        lines.append("export const useStore = create<StoreState & StoreActions>()((set) => ({")

        # Initial state
        for entity in store_config.entities:
            entity_plural = entity.lower() + "s"
            lines.append(f"  {entity_plural}: [],")
            lines.append(f"  {entity_plural}Loading: false,")
            lines.append(f"  {entity_plural}Error: null,")

        # Actions
        for entity in store_config.entities:
            entity_plural = entity.lower() + "s"
            lines.append(f"  set{entity_plural}State: (data) => set(() => ({{ {entity_plural}: data }})),")
            lines.append(f"  add{entity}: (item) => set((state) => ({{ {entity_plural}: [...state.{entity_plural}, item] }})),")
            lines.append(
                f"  update{entity}: (id, changes) => set((state) => ({{"
                f" {entity_plural}: state.{entity_plural}.map((e) => e.id === id ? {{ ...e, ...changes }} : e) }})), "
            )
            lines.append(
                f"  remove{entity}: (id) => set((state) => ({{"
                f" {entity_plural}: state.{entity_plural}.filter((e) => e.id !== id) }})), "
            )

        lines.append("}));")
        lines.append("")

        # Selectors
        if store_config.entities:
            lines.append("// Derived selectors")
            for entity in store_config.entities:
                entity_plural = entity.lower() + "s"
                lines.append(
                    f"export const use{entity}Count = () =>"
                    f" useStore((state) => state.{entity_plural}.length);"
                )
            lines.append("")

        # User-defined selectors
        if store_config.selectors:
            lines.append("// User-defined selectors")
            for selector in store_config.selectors:
                lines.append(f"export const {selector} = () => {{")
                lines.append(f"  // TODO: implement {selector}")
                lines.append(f"  return useStore((state) => state);")
                lines.append(f"}}")
                lines.append("")

        # User-defined actions
        if store_config.actions:
            lines.append("// User-defined actions")
            for action in store_config.actions:
                lines.append(f"export function {action}() {{")
                lines.append(f"  // TODO: implement {action}")
                lines.append(f"}}")
                lines.append("")

        return lines


__all__ = ["ReactComponentEmitter", "GeneratedFile"]