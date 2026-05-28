"""Angular Component Emitter (P2-002-E).

Module này cung cấp AngularComponentEmitter để emit UI components
cho Angular frontend với features:
- CRUD Components: List, Detail, Form
- Dashboard Component với widgets
- Shell/Layout Component với sidebar navigation
- Support 5 UI Frameworks: material, tailwind, bootstrap, antd, carbon

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.packs.cp_full_frontend_framework.models import RouteDefinition, StateStoreConfig

# Resolve template directory relative to this package
_PACKAGE_DIR = Path(__file__).resolve().parent.parent.parent.parent
_TEMPLATE_DIR = _PACKAGE_DIR / "stacks" / "angular" / "core" / "cp_full_frontend_framework"


@dataclass
class GeneratedFile:
    """File đã generate."""
    path: Path
    content: str
    template: str


class AngularComponentEmitter:
    """Emitter cho Angular Standalone Components (v17+).

    Generate code cho:
    - ListComponent: Data table với pagination/filtering
    - DetailComponent: Chi tiết entity
    - FormComponent: CRUD form với validation
    - DashboardComponent: Stats widgets
    - ShellComponent: Layout với sidebar navigation

    Usage:
        emitter = AngularComponentEmitter(ui_framework="material")
        files = emitter.emit(entities, output_dir)
    """

    # UI Frameworks hỗ trợ
    SUPPORTED_UI_FRAMEWORKS = ["material", "tailwind", "bootstrap", "antd", "carbon"]

    def __init__(self, ui_framework: str = "material") -> None:
        """Khởi tạo AngularComponentEmitter.

        Args:
            ui_framework: UI framework (material, tailwind, bootstrap, antd, carbon)
        """
        if ui_framework not in self.SUPPORTED_UI_FRAMEWORKS:
            raise ValueError("UI framework '" + ui_framework + "' không được hỗ trợ. "
                           "Chọn từ: " + str(self.SUPPORTED_UI_FRAMEWORKS))
        self.ui_framework = ui_framework

        # Initialize Jinja2 environment for CP18 templates
        self._template_env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

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
        """Emit Angular components.

        Args:
            entities: Danh sách entities với id và fields
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []
        components_dir = output_dir / "components"
        components_dir.mkdir(parents=True, exist_ok=True)

        # Emit entity components (pass output_dir as root for relative path)
        for entity in entities:
            files.extend(self._emit_entity_components(entity, components_dir, output_dir))

        # Emit shared shell component
        files.extend(self._emit_shell_component(components_dir, output_dir))

        # Emit dashboard component
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
        """Generate Angular routes config từ RouteDefinition.

        Template: app.routes.ts.jinja2

        Args:
            routes: Danh sách RouteDefinition.
            output_dir: Output directory.

        Returns:
            List of GeneratedFile instances.
        """
        content = self._render_template("app.routes.ts.jinja2", {
            "routes": [self._serialize_route(r) for r in routes],
        })
        return [self._write_file("app.routes.ts", content, output_dir)]

    def emit_state_store(
        self,
        store_config: StateStoreConfig,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Generate Angular Signals store từ StateStoreConfig.

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
        return [self._write_file("store.ts", content, output_dir)]

    def _emit_entity_components(
        self,
        entity: dict[str, Any],
        output_dir: Path,
        root_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit List/Detail/Form components cho 1 entity."""
        entity_id = entity["id"]
        entity_lower = entity_id.lower()
        entity_plural = entity_lower + "s"
        entity_dir = output_dir / entity_plural
        entity_dir.mkdir(parents=True, exist_ok=True)

        files: list[GeneratedFile] = []
        files.extend(self._emit_list_component(entity_id, entity_lower, entity_plural, entity_dir, root_dir))
        files.extend(self._emit_detail_component(entity_id, entity_lower, entity_plural, entity.get("fields", []), entity_dir, root_dir))
        files.extend(self._emit_form_component(entity_id, entity_lower, entity_plural, entity.get("fields", []), entity_dir, root_dir))

        return files

    def _emit_list_component(
        self,
        entity_id: str,
        entity_lower: str,
        entity_plural: str,
        output_dir: Path,
        root_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit List Component với data table."""
        import_statement = self._get_ui_import()

        lines = []
        lines.append(f'/** {entity_id} List Component - Danh sách {entity_plural} với table, pagination, filtering. */')
        lines.append('')
        lines.append('import { Component, Input, Output, EventEmitter } from "@angular/core";')
        lines.append('import { CommonModule } from "@angular/common";')
        lines.append(f'import {{ {import_statement} }} from "{self._get_framework_package()}";')
        lines.append(f"import {{ {entity_id} }} from '../../models/{entity_lower}.model';")
        lines.append(f"import {{ {entity_id}Service }} from '../../services/{entity_lower}-service';")
        lines.append('')
        lines.append('@Component({')
        lines.append(f"  selector: 'app-{entity_lower}-list',")
        lines.append(f"  standalone: true,")
        lines.append(f'  imports: [CommonModule, {import_statement}],')
        lines.append(f"  templateUrl: './{entity_lower}-list.component.html',")
        lines.append(f"  styleUrls: ['./{entity_lower}-list.component.css'],")
        lines.append('})')
        lines.append(f"export class {entity_id}ListComponent {{")
        lines.append(f"  @Input() filter: any = {{}};")
        lines.append(f"  @Output() itemSelected = new EventEmitter<{entity_id}>();")
        lines.append(f"  items: {entity_id}[] = [];")
        lines.append(f"  page = 1;")
        lines.append(f"  limit = 20;")
        lines.append(f"  total = 0;")
        lines.append(f"  loading = false;")
        lines.append('')
        lines.append('  constructor(private readonly service: OrderService) {}')
        lines.append('')
        lines.append('  ngOnInit() {')
        lines.append('    this.loadItems();')
        lines.append('  }')
        lines.append('')
        lines.append('  loadItems() {')
        lines.append('    this.loading = true;')
        lines.append('    this.service.list(this.filter, this.page, this.limit).subscribe({')
        lines.append('      next: (data) => {')
        lines.append('        this.items = data.items;')
        lines.append('        this.total = data.total;')
        lines.append('        this.loading = false;')
        lines.append('      },')
        lines.append('      error: () => this.loading = false,')
        lines.append('    });')
        lines.append('  }')
        lines.append('')
        lines.append('  selectItem(item: Order) {')
        lines.append('    this.itemSelected.emit(item);')
        lines.append('  }')
        lines.append('')
        lines.append('  pageChanged(page: number) {')
        lines.append('    this.page = page;')
        lines.append('    this.loadItems();')
        lines.append('  }')
        lines.append('}}')

        content = '\n'.join(lines)
        return [self._write_file(entity_lower + "-list.component.ts", content, output_dir, root_dir)]

    def _emit_detail_component(
        self,
        entity_id: str,
        entity_lower: str,
        entity_plural: str,
        fields: list[dict[str, Any]],
        output_dir: Path,
        root_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit Detail Component."""
        import_statement = self._get_ui_import()
        fields_display = self._generate_fields_display(fields)

        lines = []
        lines.append(f'/** {entity_id} Detail Component - Hiển thị chi tiết {entity_lower}. */')
        lines.append('')
        lines.append('import { Component, Input, OnInit } from "@angular/core";')
        lines.append('import { CommonModule } from "@angular/common";')
        lines.append(f'import {{ {import_statement} }} from "{self._get_framework_package()}";')
        lines.append(f"import {{ {entity_id} }} from '../../models/{entity_lower}.model';")
        lines.append('')
        lines.append('@Component({')
        lines.append(f"  selector: 'app-{entity_lower}-detail',")
        lines.append(f"  standalone: true,")
        lines.append(f'  imports: [CommonModule, {import_statement}],')
        lines.append(f"  templateUrl: './{entity_lower}-detail.component.html',")
        lines.append(f"  styleUrls: ['./{entity_lower}-detail.component.css'],")
        lines.append('})')
        lines.append(f"export class {entity_id}DetailComponent implements OnInit {{")
        lines.append(f"  @Input() item!: {entity_id};")
        lines.append(f"  @Input() id!: string;")
        lines.append('')
        lines.append('  ngOnInit() {')
        lines.append('    // Load detail nếu item chưa được cung cấp')
        lines.append('  }')
        lines.append('}}')

        content = '\n'.join(lines)
        return [self._write_file(entity_lower + "-detail.component.ts", content, output_dir, root_dir)]

    def _emit_form_component(
        self,
        entity_id: str,
        entity_lower: str,
        entity_plural: str,
        fields: list[dict[str, Any]],
        output_dir: Path,
        root_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit Form Component với validation."""
        import_statement = self._get_ui_import()
        form_controls = self._generate_form_controls(fields)

        lines = []
        lines.append(f'/** {entity_id} Form Component - Form tạo/sửa {entity_lower} với validation. */')
        lines.append('')
        lines.append('import { Component, Input, Output, EventEmitter, OnInit } from "@angular/core";')
        lines.append('import { CommonModule } from "@angular/common";')
        lines.append('import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from "@angular/forms";')
        lines.append(f'import {{ {import_statement} }} from "{self._get_framework_package()}";')
        lines.append(f"import {{ {entity_id} }} from '../../models/{entity_lower}.model';")
        lines.append(f"import {{ {entity_id}Service }} from '../../services/{entity_lower}-service';")
        lines.append('')
        lines.append('@Component({')
        lines.append(f"  selector: 'app-{entity_lower}-form',")
        lines.append(f"  standalone: true,")
        lines.append(f'  imports: [CommonModule, ReactiveFormsModule, {import_statement}],')
        lines.append(f"  templateUrl: './{entity_lower}-form.component.html',")
        lines.append(f"  styleUrls: ['./{entity_lower}-form.component.css'],")
        lines.append('})')
        lines.append(f"export class {entity_id}FormComponent implements OnInit {{")
        lines.append(f"  @Input() item?: {entity_id};")
        lines.append(f"  @Input() isEdit = false;")
        lines.append(f"  @Output() saved = new EventEmitter<{entity_id}>();")
        lines.append(f"  @Output() cancel = new EventEmitter<void>();")
        lines.append(f"  form: FormGroup;")
        lines.append(f"  loading = false;")
        lines.append('')
        lines.append('  constructor(private fb: FormBuilder, private service: OrderService) {')
        lines.append('    this.form = this.fb.group({')
        lines.append(form_controls)
        lines.append('    });')
        lines.append('  }')
        lines.append('')
        lines.append('  ngOnInit() {')
        lines.append('    if (this.isEdit && this.item) {')
        lines.append('      this.form.patchValue(this.item);')
        lines.append('    }')
        lines.append('  }')
        lines.append('')
        lines.append('  submit() {')
        lines.append('    if (this.form.invalid) return;')
        lines.append('    this.loading = true;')
        lines.append('    const data = this.form.value;')
        lines.append('    const obs = this.isEdit')
        lines.append("      ? this.service.update(this.item!.id, data)")
        lines.append('      : this.service.create(data);')
        lines.append('    obs.subscribe({')
        lines.append('      next: (item) => {')
        lines.append('        this.saved.emit(item);')
        lines.append('        this.loading = false;')
        lines.append('      },')
        lines.append('      error: () => this.loading = false,')
        lines.append('    });')
        lines.append('  }')
        lines.append('')
        lines.append('  onCancel() {')
        lines.append('    this.cancel.emit();')
        lines.append('  }')
        lines.append('}}')

        content = '\n'.join(lines)
        return [self._write_file(entity_lower + "-form.component.ts", content, output_dir, root_dir)]

    def _emit_shell_component(
        self,
        output_dir: Path,
        root_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit App Shell Component với sidebar navigation."""
        lines = []
        lines.append('/** App Shell Component - Layout chính với sidebar, topbar, breadcrumbs. */')
        lines.append('')
        lines.append('import { Component } from "@angular/core";')
        lines.append('import { CommonModule } from "@angular/common";')
        lines.append('import { RouterModule } from "@angular/router";')
        lines.append('')
        lines.append('@Component({')
        lines.append("  selector: 'app-shell',")
        lines.append("  standalone: true,")
        lines.append('  imports: [CommonModule, RouterModule],')
        lines.append("  template: `")
        lines.append('    <div class="app-shell">')
        lines.append('      <!-- Sidebar Navigation -->')
        lines.append('      <nav class="sidebar">')
        lines.append('        <div class="sidebar-header">')
        lines.append('          <h1>App Name</h1>')
        lines.append('        </div>')
        lines.append('        <ul class="nav-menu">')
        lines.append('          <li><a routerLink="/dashboard" routerLinkActive="active">Dashboard</a></li>')
        lines.append('          <li><a routerLink="/orders" routerLinkActive="active">Orders</a></li>')
        lines.append('          <li><a routerLink="/products" routerLinkActive="active">Products</a></li>')
        lines.append('        </ul>')
        lines.append('      </nav>')
        lines.append('')
        lines.append('      <!-- Main Content -->')
        lines.append('      <main class="main-content">')
        lines.append('        <!-- Top Bar -->')
        lines.append('        <header class="top-bar">')
        lines.append('          <nav class="breadcrumbs">')
        lines.append('            <ng-content select="[app-breadcrumbs]"></ng-content>')
        lines.append('          </nav>')
        lines.append('          <div class="user-menu">')
        lines.append('            <button (click)="logout()">Logout</button>')
        lines.append('          </div>')
        lines.append('        </header>')
        lines.append('')
        lines.append('        <!-- Router Outlet -->')
        lines.append('        <div class="content-area">')
        lines.append('          <router-outlet></router-outlet>')
        lines.append('        </div>')
        lines.append('      </main>')
        lines.append('    </div>')
        lines.append('  `,')
        lines.append("  styles: [`")
        lines.append('    .app-shell { display: flex; height: 100vh; }')
        lines.append('    .sidebar { width: 250px; background: #1a1a2e; color: white; }')
        lines.append('    .main-content { flex: 1; display: flex; flex-direction: column; }')
        lines.append('    .top-bar { display: flex; justify-content: space-between; padding: 1rem; border-bottom: 1px solid #eee; }')
        lines.append('    .content-area { flex: 1; padding: 1rem; }')
        lines.append('    .nav-menu { list-style: none; padding: 0; }')
        lines.append('    .nav-menu li a { display: block; padding: 0.75rem 1rem; color: white; text-decoration: none; }')
        lines.append('    .nav-menu li a.active { background: #16213e; }')
        lines.append('  `]')
        lines.append('})')
        lines.append('export class ShellComponent {')
        lines.append('  logout() {')
        lines.append("    localStorage.removeItem('auth_token');")
        lines.append("    localStorage.removeItem('auth_user');")
        lines.append("    window.location.href = '/login';")
        lines.append('  }')
        lines.append('}')

        content = '\n'.join(lines)
        return [self._write_file("shell.component.ts", content, output_dir, root_dir)]

    def _emit_dashboard_component(
        self,
        output_dir: Path,
        entities: list[dict[str, Any]],
        root_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit Dashboard Component với stats widgets."""
        entity_names = [e["id"] for e in entities]

        lines = []
        lines.append('/** Dashboard Component - Bảng điều khiển với stats widgets. */')
        lines.append('')
        lines.append('import { Component, OnInit } from "@angular/core";')
        lines.append('import { CommonModule } from "@angular/common";')
        lines.append('')
        lines.append('@Component({')
        lines.append("  selector: 'app-dashboard',")
        lines.append("  standalone: true,")
        lines.append('  imports: [CommonModule],')
        lines.append("  template: `")
        lines.append('    <div class="dashboard">')
        lines.append('      <h1>Dashboard</h1>')
        lines.append('')
        lines.append('      <!-- Stats Cards -->')
        lines.append('      <div class="stats-grid">')
        for entity in entity_names:
            lines.append(f'        <div class="stat-card">')
            lines.append(f'          <h3>{entity}s</h3>')
            lines.append(f'          <span class="stat-value">{{ {entity.lower()}sCount }}</span>')
            lines.append(f'        </div>')
        lines.append('      </div>')
        lines.append('')
        lines.append('      <!-- Widgets Grid -->')
        lines.append('      <div class="widgets-grid">')
        lines.append('        <div class="widget">')
        lines.append('          <h3>Recent Activity</h3>')
        lines.append('          <p>Widget placeholder cho activity log</p>')
        lines.append('        </div>')
        lines.append('        <div class="widget">')
        lines.append('          <h3>Chart</h3>')
        lines.append('          <p>Widget placeholder cho chart visualization</p>')
        lines.append('        </div>')
        lines.append('      </div>')
        lines.append('    </div>')
        lines.append('  `,')
        lines.append("  styles: [`")
        lines.append('    .dashboard { padding: 1rem; }')
        lines.append('    .stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }')
        lines.append('    .stat-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }')
        lines.append('    .stat-value { font-size: 2rem; font-weight: bold; color: #333; }')
        lines.append('    .widgets-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }')
        lines.append('    .widget { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }')
        lines.append('  `]')
        lines.append('})')
        lines.append('export class DashboardComponent implements OnInit {')
        lines.append('  ordersCount = 0;')
        lines.append('  productsCount = 0;')
        lines.append('')
        lines.append('  ngOnInit() {')
        lines.append('    // Load stats data từ API')
        lines.append('  }')
        lines.append('}')

        content = '\n'.join(lines)
        return [self._write_file("dashboard.component.ts", content, output_dir, root_dir)]

    def _get_ui_import(self) -> str:
        """Lấy import statement theo UI framework."""
        imports = {
            "material": "MatTableModule, MatPaginatorModule, MatSortModule",
            "tailwind": "",
            "bootstrap": "NgBootstrapModule",
            "antd": "NgZorroAntdModule",
            "carbon": "CarbonComponentsAngularModule",
        }
        return imports.get(self.ui_framework, "")

    def _get_framework_package(self) -> str:
        """Lấy package name theo UI framework."""
        packages = {
            "material": "@angular/material",
            "tailwind": "",
            "bootstrap": "ng-bootstrap",
            "antd": "ng-zorro-antd",
            "carbon": "@carbon/angular",
        }
        return packages.get(self.ui_framework, "@angular/material")

    def _generate_form_controls(self, fields: list[dict[str, Any]]) -> str:
        """Generate FormBuilder controls."""
        controls = []
        for f in fields:
            name = f['name']
            ftype = f.get('type', 'str')
            validators = ''
            default = 'false' if ftype == 'bool' else ''
            if ftype in ('int', 'float'):
                validators = ', [Validators.required, Validators.min(0)]'
            elif ftype == 'str':
                validators = ', [Validators.required]'
            controls.append('      ' + name + ': [' + default + validators + ']')
        return ',\n'.join(controls)

    def _generate_fields_display(self, fields: list[dict[str, Any]]) -> str:
        """Generate field display lines."""
        lines = []
        for f in fields:
            lines.append(f"  <div class=\"field\"><label>{f['name']}</label><span>{{ item.{f['name']} }}</span></div>")
        return '\n'.join(lines)

    def _write_file(
        self,
        filename: str,
        content: str,
        output_dir: Path,
        root_dir: Path | None = None,
    ) -> GeneratedFile:
        """Write file và trả về GeneratedFile.

        Args:
            filename: Tên file
            content: Nội dung file
            output_dir: Directory chứa file
            root_dir: Root directory để tính relative path (default: output_dir.parent)
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
            template="component/angular/" + filename,
        )

    # ------------------------------------------------------------------
    # CP18 helper: build Angular routes config
    # ------------------------------------------------------------------

    def _build_routes_ts(
        self,
        routes: list[RouteDefinition],
        output_dir: Path,
    ) -> list[str]:
        """Build Angular app.routes.ts content."""
        lines: list[str] = []
        lines.append("/** Auto-generated Angular routes config. */")
        lines.append("")
        lines.append('import { Routes } from "@angular/router";')
        lines.append("")
        lines.append("const routes: Routes = [")

        for route in routes:
            lines.extend(self._route_to_ts(route, 2))

        lines.append("];")
        lines.append("")
        lines.append("export default routes;")
        lines.append("")
        return lines

    def _route_to_ts(self, route: RouteDefinition, indent: int) -> list[str]:
        """Convert a single RouteDefinition to Angular route entry."""
        spaces = "  " * indent
        lines: list[str] = []
        child_lines = []

        lines.append(f"{spaces}{{")
        lines.append(f'{spaces}  path: {self._ts_string(route.path)},')
        lines.append(
            f"{spaces}  loadComponent: "
            f"() => import('./components/{route.component.lower()}/' "
            f"\"{route.component.lower()}.component.ts\") "
            f"then(m => m.default)"
        )

        if route.children:
            child_lines.append(f"{spaces}  children: [")
            for child in route.children:
                child_lines.extend(self._route_to_ts(child, indent + 1))
            child_lines.append(f"{spaces}  ]")

        lines.extend(child_lines)

        # Trailing comma (safe to have)
        if child_lines:
            lines[-1] = lines[-1].rstrip() + ","
        else:
            lines.append(f"{spaces}}},")

        return lines

    def _ts_string(self, s: str) -> str:
        """Wrap a string in TypeScript quotes, replacing :id with ':id'."""
        # Angular uses literal ':id' not ':id'
        return f"'{s}'"

    # ------------------------------------------------------------------
    # CP18 helper: build Angular Signals store
    # ------------------------------------------------------------------

    def _build_signals_store(
        self,
        store_config: StateStoreConfig,
        output_dir: Path,
    ) -> list[str]:
        """Build Angular Signals store content."""
        lines: list[str] = []
        lines.append("/** Auto-generated Angular Signals store. */")
        lines.append("")
        lines.append('import { signal, computed } from "@angular/core";')
        lines.append("")

        # Generate entity store sections
        for entity in store_config.entities:
            entity_lower = entity.lower()
            entity_plural = entity_lower + "s"

            lines.append(f"// {entity} store")
            lines.append(f"export const {entity_plural}State = signal<{entity}[]>([]);")
            lines.append(f"export const {entity_plural}Loading = signal<boolean>(false);")
            lines.append(f"export const {entity_plural}Error = signal<string | null>(null);")
            lines.append("")

            # Computed signals
            lines.append(f"export const {entity_plural}Count = computed(() => {entity_plural}State().length);")
            lines.append(f"export const {entity_plural}Ids = computed(() => {entity_plural}State().map(e => e.id));")
            lines.append("")

            # Actions
            lines.append(f"export function set{entity_plural}State(data: {entity}[]) {{")
            lines.append(f"  {entity_plural}State.set(data);")
            lines.append(f"}}")
            lines.append("")
            lines.append(f"export function add{entity}(item: {entity}) {{")
            lines.append(f"  {entity_plural}State.update(prev => [...prev, item]);")
            lines.append(f"}}")
            lines.append("")
            lines.append(f"export function update{entity}(id: string, changes: Partial<{entity}>) {{")
            lines.append(f"  {entity_plural}State.update(prev => prev.map(e => e.id === id ? {{ ...e, ...changes }} : e));")
            lines.append(f"}}")
            lines.append("")
            lines.append(f"export function remove{entity}(id: string) {{")
            lines.append(f"  {entity_plural}State.update(prev => prev.filter(e => e.id !== id));")
            lines.append(f"}}")
            lines.append("")

        # Global computed selectors
        if store_config.entities:
            lines.append("// Global selectors")
            lines.append("export const totalItems = computed(() => {")
            for entity in store_config.entities:
                entity_plural = entity.lower() + "s"
                lines.append(f"  +{entity_plural}Count()")
            lines.append("  return 0; // fallback")
            lines.append("});")
            lines.append("")

        # Export user-defined selectors placeholder
        if store_config.selectors:
            lines.append("// User-defined selectors")
            for selector in store_config.selectors:
                lines.append(f"export function {selector}() {{")
                lines.append(f"  // TODO: implement {selector}")
                lines.append(f"  return signal(null);")
                lines.append(f"}}")
                lines.append("")

        # Export user-defined actions placeholder
        if store_config.actions:
            lines.append("// User-defined actions")
            for action in store_config.actions:
                lines.append(f"export function {action}() {{")
                lines.append(f"  // TODO: implement {action}")
                lines.append(f"}}")
                lines.append("")

        return lines


__all__ = ["AngularComponentEmitter", "GeneratedFile"]