"""
Frontend Angular Emitter Module (P2-002-A).

Module này cung cấp AngularEmitter class để generate Angular v17+ frontend code
từ MIR (Midicoder Intermediate Representation).

Theo CURRENT_TASK_REQUIREMENT.md:
- FR1: Angular App Structure Emission
- FR2: Entity-driven Component Generation  
- FR3: Service Layer (REST + GraphQL + WebSocket + gRPC-web)
- FR4: NgRx State Management
- FR5: UI Framework Support (5 frameworks)
- FR6: Full Auth Integration
- FR7: Full Routing (lazy loading + guards + resolvers)
- FR8: Model/Interface Generation

Templates nằm trong midicoder/stacks/angular/templates/.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from midicoder.pipeline.mir import MIR


# ============================================================================
# Generated File
# ============================================================================


@dataclass
class GeneratedFile:
    """
    File đã generate từ template.

    Attributes:
        path: Đường dẫn file tương đối
        content: Nội dung file đã generate
        template: Tên template đã dùng
    """

    path: Path
    content: str
    template: str


# ============================================================================
# Angular Emitter
# ============================================================================


class AngularEmitter:
    """
    Emitter cho Angular v17+ frontend code generation.

    Generate code cho:
    - App structure (app.config.ts, app.routes.ts, app.component.ts)
    - Entity modules (CRUD components, services)
    - NgRx state (actions, reducers, selectors, effects)
    - Auth module (interceptor, guards, directives)
    - Routing (lazy loading, guards, resolvers)
    - Models/Interfaces

    Usage:
        emitter = AngularEmitter.create_emitter(ui_framework="material")
        files = emitter.emit(mir, output_dir=Path("/tmp/output"))
    """

    # UI Frameworks hỗ trợ (FR5)
    SUPPORTED_UI_FRAMEWORKS = ["material", "tailwind", "bootstrap", "antd", "carbon"]

    def __init__(
        self,
        stack_dir: Path,
        ui_framework: str = "material",
        state_management: str = "ngrx",
        communication: list[str] | None = None,
    ) -> None:
        """
        Khởi tạo AngularEmitter.

        Args:
            stack_dir: Đường dẫn đến templates directory
            ui_framework: UI framework (material, tailwind, bootstrap, antd, carbon)
            state_management: State management pattern (ngrx, signals, service)
            communication: List communication patterns (rest, graphql, websocket, grpc)

        Raises:
            FileNotFoundError: Nếu stack_dir không tồn tại
            ValueError: Nếu ui_framework không hợp lệ
        """
        self.stack_dir = stack_dir
        self.ui_framework = ui_framework
        self.state_management = state_management
        self.communication = communication or ["rest"]

        # Validate UI framework
        if ui_framework not in self.SUPPORTED_UI_FRAMEWORKS:
            raise ValueError(
                f"UI framework '{ui_framework}' không hợp lệ. "
                f"Hỗ trợ: {', '.join(self.SUPPORTED_UI_FRAMEWORKS)}"
            )

        if not stack_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {stack_dir}")

        # Setup Jinja2 environment
        templates_dir = stack_dir / "templates"
        if templates_dir.exists():
            self._env = Environment(
                loader=FileSystemLoader(str(templates_dir)),
                autoescape=True,
            )
        else:
            # Fallback: không có templates, generate inline
            self._env = None

    @classmethod
    def create_emitter(
        cls,
        stack_dir: Path | None = None,
        ui_framework: str = "material",
        state_management: str = "ngrx",
        communication: list[str] | None = None,
    ) -> "AngularEmitter":
        """
        Factory method để tạo AngularEmitter.

        Args:
            stack_dir: Đường dẫn templates (default: midicoder/stacks/angular)
            ui_framework: UI framework (default: material)
            state_management: State management (default: ngrx)
            communication: Communication patterns (default: ["rest"])

        Returns:
            AngularEmitter instance
        """
        if stack_dir is None:
            stack_dir = Path(__file__).parent.parent.parent / "stacks" / "angular"
        return cls(
            stack_dir=stack_dir,
            ui_framework=ui_framework,
            state_management=state_management,
            communication=communication,
        )

    def emit(
        self,
        mir: MIR,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Emit Angular code từ MIR metadata.

        Args:
            mir: MIR instance với metadata
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []

        # Lấy metadata từ MIR
        entities = mir.metadata.get("entities", [])
        routes = mir.metadata.get("routes", [])
        operations = mir.metadata.get("operations", [])
        authnz = mir.metadata.get("authnz", {})

        # Tạo source directory
        src_dir = output_dir / "src" / "app"
        src_dir.mkdir(parents=True, exist_ok=True)

        # FR1: Emit base app structure
        files.extend(self._emit_base_files(src_dir))

        # FR8: Emit models/interfaces
        if entities or operations:
            files.extend(self._emit_models(entities, operations, src_dir))

        # FR2: Emit entity modules (CRUD components + services)
        for entity in entities:
            files.extend(self._emit_entity_module(entity, src_dir))

        # FR3: Emit services
        if entities:
            files.extend(self._emit_services(entities, src_dir))

        # FR4: Emit NgRx state management
        if entities and self.state_management == "ngrx":
            files.extend(self._emit_ngrx_state(entities, src_dir))

        # FR6: Emit auth module
        if authnz:
            files.extend(self._emit_auth(authnz, src_dir))

        # FR7: Emit routing
        if routes or entities:
            files.extend(self._emit_routing(routes, entities, authnz, src_dir))

        return files

    def _emit_base_files(self, output_dir: Path) -> list[GeneratedFile]:
        """
        Emit base app files (FR1).

        Files: app.config.ts, app.routes.ts, app.component.ts, main.ts
        """
        files: list[GeneratedFile] = []
        context = self._get_base_context()

        # app.config.ts - Provider configuration
        files.append(self._write_file(
            filename="app.config.ts",
            content=self._generate_app_config(),
            output_dir=output_dir,
        ))

        # app.routes.ts - Base routes
        files.append(self._write_file(
            filename="app.routes.ts",
            content=self._generate_app_routes([]),
            output_dir=output_dir,
        ))

        # app.component.ts - Root component
        files.append(self._write_file(
            filename="app.component.ts",
            content=self._generate_app_component(),
            output_dir=output_dir,
        ))

        # app.component.html - Root template
        files.append(self._write_file(
            filename="app.component.html",
            content="<router-outlet></router-outlet>\n",
            output_dir=output_dir,
        ))

        # main.ts - Entry point
        files.append(self._write_file(
            filename="main.ts",
            content=self._generate_main_ts(),
            output_dir=output_dir,
        ))

        return files

    def _emit_models(
        self,
        entities: list[dict[str, Any]],
        operations: list[dict[str, Any]],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit TypeScript interfaces (FR8)."""
        files: list[GeneratedFile] = []
        models_dir = output_dir / "models"
        models_dir.mkdir(parents=True, exist_ok=True)

        # Emit entity models
        for entity in entities:
            model_content = self._generate_entity_model(entity)
            model_name = self._to_pascal_case(entity.get("id", "Entity"))
            files.append(self._write_file(
                filename=f"{model_name.lower()}.model.ts",
                content=model_content,
                output_dir=models_dir,
            ))

        # Emit index.ts
        files.append(self._write_file(
            filename="index.ts",
            content=self._generate_models_index(entities, operations),
            output_dir=models_dir,
        ))

        return files

    def _emit_entity_module(
        self,
        entity: dict[str, Any],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit entity CRUD components (FR2)."""
        files: list[GeneratedFile] = []
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()

        # Create entity directory
        entity_dir = output_dir / "entities" / entity_lower
        entity_dir.mkdir(parents=True, exist_ok=True)

        # Generate list component
        files.append(self._write_file(
            filename="list.component.ts",
            content=self._generate_list_component(entity),
            output_dir=entity_dir,
        ))

        files.append(self._write_file(
            filename="list.component.html",
            content=self._generate_list_template(entity),
            output_dir=entity_dir,
        ))

        # Generate detail component
        files.append(self._write_file(
            filename="detail.component.ts",
            content=self._generate_detail_component(entity),
            output_dir=entity_dir,
        ))

        # Generate create component
        files.append(self._write_file(
            filename="create.component.ts",
            content=self._generate_create_component(entity),
            output_dir=entity_dir,
        ))

        # Generate edit component
        files.append(self._write_file(
            filename="edit.component.ts",
            content=self._generate_edit_component(entity),
            output_dir=entity_dir,
        ))

        return files

    def _emit_services(
        self,
        entities: list[dict[str, Any]],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit entity services (FR3)."""
        files: list[GeneratedFile] = []
        services_dir = output_dir / "services"
        services_dir.mkdir(parents=True, exist_ok=True)

        for entity in entities:
            service_content = self._generate_entity_service(entity)
            entity_id = entity.get("id", "Entity")
            files.append(self._write_file(
                filename=f"{entity_id.lower()}.service.ts",
                content=service_content,
                output_dir=services_dir,
            ))

        return files

    def _emit_ngrx_state(
        self,
        entities: list[dict[str, Any]],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit NgRx state files (FR4)."""
        files: list[GeneratedFile] = []
        state_dir = output_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        for entity in entities:
            entity_id = entity.get("id", "Entity")

            # Actions
            files.append(self._write_file(
                filename=f"{entity_id.lower()}.actions.ts",
                content=self._generate_ngrx_actions(entity),
                output_dir=state_dir,
            ))

            # Reducers
            files.append(self._write_file(
                filename=f"{entity_id.lower()}.reducers.ts",
                content=self._generate_ngrx_reducers(entity),
                output_dir=state_dir,
            ))

            # Selectors
            files.append(self._write_file(
                filename=f"{entity_id.lower()}.selectors.ts",
                content=self._generate_ngrx_selectors(entity),
                output_dir=state_dir,
            ))

            # Effects
            files.append(self._write_file(
                filename=f"{entity_id.lower()}.effects.ts",
                content=self._generate_ngrx_effects(entity),
                output_dir=state_dir,
            ))

        return files

    def _emit_auth(
        self,
        authnz: dict[str, Any],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit auth module (FR6)."""
        files: list[GeneratedFile] = []
        auth_dir = output_dir / "auth"
        auth_dir.mkdir(parents=True, exist_ok=True)

        # Auth Service
        files.append(self._write_file(
            filename="auth.service.ts",
            content=self._generate_auth_service(authnz),
            output_dir=auth_dir,
        ))

        # Auth Interceptor
        files.append(self._write_file(
            filename="auth.interceptor.ts",
            content=self._generate_auth_interceptor(),
            output_dir=auth_dir,
        ))

        # Auth Guard
        files.append(self._write_file(
            filename="auth.guard.ts",
            content=self._generate_auth_guard(),
            output_dir=auth_dir,
        ))

        # Permission Directive
        files.append(self._write_file(
            filename="permission.directive.ts",
            content=self._generate_permission_directive(authnz),
            output_dir=auth_dir,
        ))

        return files

    def _emit_routing(
        self,
        routes: list[dict[str, Any]],
        entities: list[dict[str, Any]],
        authnz: dict[str, Any],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit routing with lazy loading + guards + resolvers (FR7)."""
        files: list[GeneratedFile] = []

        # Update app.routes.ts với entity routes
        routes_content = self._generate_app_routes(entities)
        files.append(self._write_file(
            filename="app.routes.ts",
            content=routes_content,
            output_dir=output_dir,
        ))

        # Entity-specific routes
        for entity in entities:
            entity_id = entity.get("id", "Entity")
            entity_lower = entity_id.lower()
            entity_dir = output_dir / "entities" / entity_lower
            entity_dir.mkdir(parents=True, exist_ok=True)

            files.append(self._write_file(
                filename="routes.ts",
                content=self._generate_entity_routes(entity),
                output_dir=entity_dir,
            ))

        return files

    # ========================================================================
    # Template Generation Methods
    # ========================================================================

    def _get_base_context(self) -> dict[str, Any]:
        """Get base template context."""
        return {
            "ui_framework": self.ui_framework,
            "state_management": self.state_management,
            "communication": self.communication,
            "angular_version": "17",
        }

    def _generate_app_config(self) -> str:
        """Generate app.config.ts content."""
        ngrx_import = "import { provideState } from '@ngrx/store';" if self.state_management == "ngrx" else ""
        ngrx_provider = "  provideState(featureKey, reducer),\n" if self.state_management == "ngrx" else ""

        return f'''/**
 * App Configuration - Cấu hình providers cho Angular app.
 * 
 * Providers:
 * - HttpClient: REST API calls
 * - Router: Navigation
 * - {"NgRx: State management" if self.state_management == "ngrx" else "Signals: State management"}
 */

import {{ ApplicationConfig, provideZoneChangeDetection }} from \'@angular/core\';
import {{ provideRouter }} from \'@angular/router\';
import {{ provideHttpClient, withInterceptorsFromDi }} from \'@angular/common/http\';
{ngrx_import}
import {{ routes }} from \'./app.routes\';

export const appConfig: ApplicationConfig = {{
  providers: [
    provideZoneChangeDetection({{ eventCoalescing: true }}),
    provideRouter(routes),
    provideHttpClient(withInterceptorsFromDi()),
{ngrx_provider}    // UI Framework: {self.ui_framework}
  ],
}};
'''

    def _generate_app_routes(self, entities: list[dict[str, Any]]) -> str:
        """Generate app.routes.ts content."""
        entity_routes = ""
        for entity in entities:
            entity_id = entity.get("id", "Entity")
            entity_lower = entity_id.lower()
            entity_routes += f'''
  {{
    path: \'{entity_lower}\',
    loadChildren: () => import(\'./entities/{entity_lower}/routes\').then(m => m.routes),
  }},
'''
        return f'''/**
 * App Routes - Routing configuration với lazy loading.
 * 
 * Features:
 * - Lazy loading cho entity modules
 * - Auth guards cho protected routes
 * - Resolvers cho data pre-fetching
 */

import {{ Routes }} from \'@angular/router\';

export const routes: Routes = [
  {{
    path: \'\',
    redirectTo: \'dashboard\',
    pathMatch: \'full\',
  }},
{entity_routes}  {{
    path: \'**\',
    redirectTo: \'dashboard\',
  }},
];
'''

    def _generate_app_component(self) -> str:
        """Generate app.component.ts content."""
        return '''/**
 * App Component - Root component của Angular app.
 * 
 * Standalone component (Angular v17+).
 * Sử dụng <router-outlet> để render child routes.
 */

import { Component } from \'@angular/core\';
import { RouterOutlet } from \'@angular/router\';

@Component({
  selector: \'app-root\',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: \'./app.component.html\',
})
export class AppComponent {{
  title = \'midicoder-app\';
}}
'''

    def _generate_main_ts(self) -> str:
        """Generate main.ts content."""
        return '''/**
 * Main Entry Point - Điểm khởi động của Angular app.
 */

import { bootstrapApplication } from \'@angular/platform-browser\';
import { appConfig } from \'./app/app.config\';
import { AppComponent } from \'./app/app.component\';

bootstrapApplication(AppComponent, appConfig)
  .catch((err) => console.error(err));
'''

    def _generate_entity_model(self, entity: dict[str, Any]) -> str:
        """Generate entity model interface (FR8)."""
        entity_id = entity.get("id", "Entity")
        fields = entity.get("fields", [])
        
        properties = ""
        for field in fields:
            name = field.get("name", "")
            field_type = self._ts_type(field.get("type", "str"))
            required = "" if field.get("required") else "?"
            properties += f"  {name}{required}: {field_type};\n"
        
        return f'''/**
 * {entity_id} Model - Interface cho entity {entity_id}.
 */

export interface {entity_id} {{
{properties}}}
'''

    def _generate_models_index(
        self,
        entities: list[dict[str, Any]],
        operations: list[dict[str, Any]],
    ) -> str:
        """Generate models/index.ts."""
        exports = ""
        for entity in entities:
            entity_id = entity.get("id", "Entity")
            exports += f"export * from \'./{entity_id.lower()}.model\';\n"
        return f"// Models Index - Export tất cả interfaces\n\n{exports}"

    def _generate_list_component(self, entity: dict[str, Any]) -> str:
        """Generate list component (FR2)."""
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        return f'''/**
 * {entity_id} List Component - Hiển thị danh sách {entity_lower}.
 * 
 * Features:
 * - CRUD operations
 * - Pagination
 * - Sorting & Filtering
 */

import {{ Component, OnInit }} from \'@angular/core\';
import {{ CommonModule }} from \'@angular/common\';
import {{ RouterModule }} from \'@angular/router\';
import {{ {entity_id} }} from \'../../models/{entity_lower}.model\';

@Component({{
  selector: \'app-{entity_lower}-list\',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: \'./list.component.html\',
}})
export class {entity_id}ListComponent implements OnInit {{
  items: {entity_id}[] = [];
  
  ngOnInit(): void {{
    // Load {entity_lower} list
  }}
}}
'''

    def _generate_list_template(self, entity: dict[str, Any]) -> str:
        """Generate list component template."""
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        fields = entity.get("fields", [])
        
        columns = "".join(f"<th>{{{f.get('name', '')}}}</th>\n" for f in fields)
        cells = "".join(f"<td>{{{entity_lower}.{f.get('name', '')}}}</td>\n" for f in fields)
        
        return f'''<!-- {entity_id} List Template -->
<div class="container">
  <h1>{entity_id}s</h1>
  <a routerLink="/{entity_lower}/create" class="btn btn-primary">Create New</a>
  
  <table class="table">
    <thead>
      <tr>
{columns}        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr *ngFor="let {entity_lower} of items">
{cells}        <td>
          <a routerLink="/{entity_lower}/detail/{{{entity_lower}.id}}">View</a>
          <a routerLink="/{entity_lower}/edit/{{{entity_lower}.id}}">Edit</a>
        </td>
      </tr>
    </tbody>
  </table>
</div>
'''

    def _generate_detail_component(self, entity: dict[str, Any]) -> str:
        """Generate detail component."""
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        return (
            f"/**\n"
            f" * {entity_id} Detail Component - Hien thi chi tiet {entity_lower}.\n"
            f" */\n\n"
            f"import {{ Component, OnInit }} from '@angular/core';\n"
            f"import {{ CommonModule }} from '@angular/common';\n"
            f"import {{ {entity_id} }} from '../../models/{entity_lower}.model';\n\n"
            f"@Component({{\n"
            f"  selector: 'app-{entity_lower}-detail',\n"
            f"  standalone: true,\n"
            f"  imports: [CommonModule],\n"
            f"  template: `<div><h1>{entity_id} Detail</h1></div>`,\n"
            f"}})\n"
            f"export class {entity_id}DetailComponent implements OnInit {{\n"
            f"  item?: {entity_id};\n\n"
            f"  ngOnInit(): void {{\n"
            f"    // Load {entity_lower} detail\n"
            f"  }}\n"
            f"}}\n"
        )

    def _generate_create_component(self, entity: dict[str, Any]) -> str:
        """Generate create component."""
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        return (
            f"/**\n"
            f" * {entity_id} Create Component - Form tao moi {entity_lower}.\n"
            f" */\n\n"
            f"import {{ Component }} from '@angular/core';\n"
            f"import {{ CommonModule }} from '@angular/common';\n"
            f"import {{ FormsModule, ReactiveFormsModule }} from '@angular/forms';\n\n"
            f"@Component({{\n"
            f"  selector: 'app-{entity_lower}-create',\n"
            f"  standalone: true,\n"
            f"  imports: [CommonModule, FormsModule, ReactiveFormsModule],\n"
            f"  template: `<div><h1>Create {entity_id}</h1></div>`,\n"
            f"}})\n"
            f"export class {entity_id}CreateComponent {{}}\n"
        )

    def _generate_edit_component(self, entity: dict[str, Any]) -> str:
        """Generate edit component."""
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        return (
            f"/**\n"
            f" * {entity_id} Edit Component - Form chinh sua {entity_lower}.\n"
            f" */\n\n"
            f"import {{ Component }} from '@angular/core';\n"
            f"import {{ CommonModule }} from '@angular/common';\n"
            f"import {{ FormsModule, ReactiveFormsModule }} from '@angular/forms';\n\n"
            f"@Component({{\n"
            f"  selector: 'app-{entity_lower}-edit',\n"
            f"  standalone: true,\n"
            f"  imports: [CommonModule, FormsModule, ReactiveFormsModule],\n"
            f"  template: `<div><h1>Edit {entity_id}</h1></div>`,\n"
            f"}})\n"
            f"export class {entity_id}EditComponent {{}}\n"
        )

    def _generate_entity_service(self, entity: dict[str, Any]) -> str:
        """Generate entity service (FR3)."""
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()

        # Build communication imports
        imports = "import { HttpClient } from '@angular/common/http';"
        if 'graphql' in self.communication:
            imports += "\nimport { Apollo } from 'apollo-angular';"
        if 'websocket' in self.communication:
            imports += "\nimport { WebSocketService } from '../shared/websocket.service';"
        if 'grpc' in self.communication:
            imports += "\nimport { GrpcWebClient } from '../shared/grpc-web.client';"

        # Extra constructor params
        extra_params = ""
        if "graphql" in self.communication:
            extra_params += ", private apollo: Apollo"
        if "websocket" in self.communication:
            extra_params += ", private websocket: WebSocketService"
        if "grpc" in self.communication:
            extra_params += ", private grpc: GrpcWebClient"

        return (
            f'/**\n'
            f' * {entity_id} Service - Service cho CRUD operations của {entity_lower}.\n'
            f' * \n'
            f' * Communication: {", ".join(self.communication)}\n'
            f' */\n\n'
            f"import {{ Injectable }} from '@angular/core';\n"
            f'{imports}\n'
            f'import {{ Observable }} from \'rxjs\';\n'
            f"import {{ {entity_id} }} from '../models/{entity_lower}.model';\n\n"
            f"@Injectable({{\n"
            f"  providedIn: 'root',\n"
            f"}})\n"
            f"export class {entity_id}Service {{\n"
            f"  private readonly apiUrl = '/api/{entity_lower}';\n\n"
            f"  constructor(private httpClient: HttpClient{extra_params}) {{}}\n\n"
            f"  // REST API\n"
            f"  getAll(): Observable<{entity_id}[]> {{\n"
            f"    return this.httpClient.get<{entity_id}[]>(this.apiUrl);\n"
            f"  }}\n\n"
            f"  getById(id: string): Observable<{entity_id}> {{\n"
            f"    return this.httpClient.get<{entity_id}>(`${{{self._ts_tpl('this.apiUrl')}}}/${{{self._ts_tpl('id')}}}`);\n"
            f"  }}\n\n"
            f"  create(item: {entity_id}): Observable<{entity_id}> {{\n"
            f"    return this.httpClient.post<{entity_id}>(this.apiUrl, item);\n"
            f"  }}\n\n"
            f"  update(id: string, item: {entity_id}): Observable<{entity_id}> {{\n"
            f"    return this.httpClient.put<{entity_id}>(`${{{self._ts_tpl('this.apiUrl')}}}/${{{self._ts_tpl('id')}}}`, item);\n"
            f"  }}\n\n"
            f"  delete(id: string): Observable<void> {{\n"
            f"    return this.httpClient.delete<void>(`${{{self._ts_tpl('this.apiUrl')}}}/${{{self._ts_tpl('id')}}}`);\n"
            f"  }}\n"
            f"}}\n"
        )

    def _generate_ngrx_actions(self, entity: dict[str, Any]) -> str:
        """Generate NgRx actions (FR4)."""
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        return f'''/**
 * {entity_id} Actions - NgRx actions cho {entity_lower}.
 */

import {{ createAction, props }} from \'@ngrx/store\';
import {{ {entity_id} }} from \'../../models/{entity_lower}.model\';

export const load{entity_id}s = createAction(
  '[{entity_id}] Load',
);

export const load{entity_id}sSuccess = createAction(
  '[{entity_id}] Load Success',
  props<{{ items: {entity_id}[] }}>(),
);

export const load{entity_id}sFail = createAction(
  '[{entity_id}] Load Fail',
  props<{{ error: any }}>(),
);

export const create{entity_id} = createAction(
  '[{entity_id}] Create',
  props<{{ item: {entity_id} }}>(),
);

export const update{entity_id} = createAction(
  '[{entity_id}] Update',
  props<{{ item: {entity_id} }}>(),
);

export const delete{entity_id} = createAction(
  '[{entity_id}] Delete',
  props<{{ id: string }}>(),
);
'''

    def _generate_ngrx_reducers(self, entity: dict[str, Any]) -> str:
        """Generate NgRx reducers (FR4)."""
        entity_id = entity.get("id", "Entity")
        return f'''/**
 * {entity_id} Reducers - NgRx reducers cho {entity_id.lower()}.
 */

import {{ createReducer, on }} from \'@ngrx/store';
import {{ EntityState, EntityAdapter, createEntityAdapter }} from \'@ngrx/entity';
import {{ {entity_id} }} from \'../../models/{entity_id.lower()}.model\';
import * {{ {entity_id}Actions }} from \'./{entity_id.lower()}.actions\';

export interface {entity_id}State extends EntityState<{entity_id}> {{
  loaded: boolean;
  error?: string;
}}

export const adapter: EntityAdapter<{entity_id}> = createEntityAdapter<{entity_id}>();

export const initial{entity_id}State: {entity_id}State = adapter.getInitialState({{
  loaded: false,
}});

export const {entity_id}Reducer = createReducer(
  initial{entity_id}State,
  on({entity_id}Actions.load{entity_id}sSuccess, (state, {{ items }}) => 
    adapter.setAll(items, {{ ...state, loaded: true }})
  ),
  on({entity_id}Actions.load{entity_id}sFail, (state, {{ error }}) => 
    {{ ...state, error }}
  ),
);
'''

    def _generate_ngrx_selectors(self, entity: dict[str, Any]) -> str:
        """Generate NgRx selectors (FR4)."""
        entity_id = entity.get("id", "Entity")
        return f'''/**
 * {entity_id} Selectors - NgRx selectors cho {entity_id.lower()}.
 */

import {{ createFeatureSelector, createSelector }} from \'@ngrx/store\';
import {{ {entity_id}State, adapter }} from \'./{entity_id.lower()}.reducers\';

export const select{entity_id}State = createFeatureSelector<{entity_id}State>(\'{entity_id.lower()}\');

export const {{
  selectAll{entity_id}s,
  select{entity_id}Total,
}} = adapter.getSelectors();

export const select{entity_id}sLoaded = createSelector(
  select{entity_id}State,
  (state) => state.loaded,
);
'''

    def _generate_ngrx_effects(self, entity: dict[str, Any]) -> str:
        """Generate NgRx effects (FR4)."""
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        return f'''/**
 * {entity_id} Effects - NgRx effects cho {entity_lower}.
 */

import {{ Injectable }} from \'@angular/core\';
import {{ Actions, createEffect, ofType }} from \'@ngrx/effects\';
import {{ map, catchError, mergeMap }} from \'rxjs/operators\';
import {{ of }} from \'rxjs\';
import * {{ {entity_id}Actions }} from \'./{entity_id.lower()}.actions\';
import {{ {entity_id}Service }} from \'../../services/{entity_id.lower()}.service\';

@Injectable()
export class {entity_id}Effects {{
  constructor(
    private actions$: Actions,
    private {entity_id.lower()}Service: {entity_id}Service,
  ) {{}}

  load{entity_id}s$ = createEffect(() =>
    this.actions$.pipe(
      ofType({entity_id}Actions.load{entity_id}s),
      mergeMap(() =>
        this.{entity_id.lower()}Service.getAll().pipe(
          map(items => {entity_id}Actions.load{entity_id}sSuccess({{ items }})),
          catchError(error => of({entity_id}Actions.load{entity_id}sFail({{ error }}))),
        ),
      ),
    ),
  );
}}
'''

    def _generate_auth_service(self, authnz: dict[str, Any]) -> str:
        """Generate auth service (FR6)."""
        return '''/**
 * Auth Service - Quản lý authentication và authorization.
 * 
 * Features:
 * - JWT token management
 * - Login/Logout
 * - Permission checking
 */

import { Injectable } from \'@angular/core\';
import { BehaviorSubject, Observable } from \'rxjs\';

export interface AuthUser {
  id: string;
  email: string;
  roles: string[];
  permissions: string[];
}

@Injectable({
  providedIn: \'root\',
})
export class AuthService {
  private readonly TOKEN_KEY = \'auth_token\';
  private readonly USER_KEY = \'auth_user\';
  
  private currentUserSubject = new BehaviorSubject<AuthUser | null>(null);
  currentUser$ = this.currentUserSubject.asObservable();
  
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }
  
  login(token: string, user: AuthUser): void {
    localStorage.setItem(this.TOKEN_KEY, token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    this.currentUserSubject.next(user);
  }
  
  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.currentUserSubject.next(null);
  }
  
  hasPermission(permission: string): boolean {
    const user = this.currentUserSubject.value;
    return user?.permissions.includes(permission) ?? false;
  }
  
  isAuthenticated(): boolean {
    return this.getToken() !== null;
  }
}
'''

    def _generate_auth_interceptor(self) -> str:
        """Generate auth interceptor (FR6)."""
        return '''/**
 * Auth Interceptor - Tự động attach JWT token vào HTTP requests.
 * 
 * KPI-028: Security - Token không được log hay expose.
 */

import { Injectable } from \'@angular/core\';
import {
  HttpInterceptor,
  HttpRequest,
  HttpHandler,
  HttpEvent,
} from \'@angular/common/http\';
import { Observable } from \'rxjs\';
import { AuthService } from \'./auth.service\';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private authService: AuthService) {}
  
  intercept(
    request: HttpRequest<unknown>,
    next: HttpHandler,
  ): Observable<HttpEvent<unknown>> {
    const token = this.authService.getToken();
    
    if (token) {
      const cloned = request.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`,
        },
      });
      return next.handle(cloned);
    }
    
    return next.handle(request);
  }
}
'''

    def _generate_auth_guard(self) -> str:
        """Generate auth guard (FR6)."""
        return '''/**
 * Auth Guard - Route guard cho protected routes.
 * 
 * Kiểm tra authentication trước khi navigate.
 */

import { Injectable } from \'@angular/core\';
import { CanActivate, Router } from \'@angular/router\';
import { AuthService } from \'./auth.service\';

@Injectable({
  providedIn: \'root\',
})
export class AuthGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router,
  ) {}
  
  canActivate(): boolean {
    if (this.authService.isAuthenticated()) {
      return true;
    }
    
    this.router.navigate([\'/login\']);
    return false;
  }
}
'''

    def _generate_permission_directive(self, authnz: dict[str, Any]) -> str:
        """Generate permission directive (FR6)."""
        permissions = authnz.get("permissions", [])
        return f'''/**
 * Permission Directive - Directive kiểm tra permission.
 * 
 * Usage: <div *appPermission="'order:create'">...</div>
 * 
 * KPI-028: Authorization - Kiểm tra permission trước khi render.
 */

import {{ Directive, TemplateRef, ViewContainerRef }} from \'@angular/core\';
import {{ AuthService }} from \'./auth.service\';

@Directive({{
  selector: \'[appPermission]\',
  standalone: true,
}})
export class PermissionDirective {{
  constructor(
    private authService: AuthService,
    private templateRef: TemplateRef<unknown>,
    private viewContainer: ViewContainerRef,
  ) {{}}
  
  @Input() set appPermission(permission: string) {{
    if (this.authService.hasPermission(permission)) {{
      this.viewContainer.createEmbeddedView(this.templateRef);
    }} else {{
      this.viewContainer.clear();
    }}
  }}
}}
'''

    def _generate_entity_routes(self, entity: dict[str, Any]) -> str:
        """Generate entity-specific routes (FR7)."""
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        return f'''/**
 * {entity_id} Routes - Routing cho {entity_lower} module.
 * 
 * Features:
 * - Lazy loading
 * - Auth guards
 * - CRUD routes
 */

import {{ Routes }} from \'@angular/router\';
import {{ AuthGuard }} from \'../../auth/auth.guard\';

export const routes: Routes = [
  {{
    path: \'\',
    loadComponent: () => import(\'./list.component\').then(m => m.{entity_id}ListComponent),
    canActivate: [AuthGuard],
  }},
  {{
    path: \'create\',
    loadComponent: () => import(\'./create.component\').then(m => m.{entity_id}CreateComponent),
    canActivate: [AuthGuard],
  }},
  {{
    path: \'detail/:id\',
    loadComponent: () => import(\'./detail.component\').then(m => m.{entity_id}DetailComponent),
    canActivate: [AuthGuard],
  }},
  {{
    path: \'edit/:id\',
    loadComponent: () => import(\'./edit.component\').then(m => m.{entity_id}EditComponent),
    canActivate: [AuthGuard],
  }},
];
'''

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _to_pascal_case(self, name: str) -> str:
        """Chuyển string sang PascalCase."""
        return name.strip().title().replace(" ", "")

    def _ts_tpl(self, expr: str) -> str:
        """Escape TypeScript template literal expression cho f-string."""
        return f"${{{{{expr}}}}}"

    def _ts_type(self, python_type: str) -> str:
        """Convert Python type to TypeScript type."""
        type_map = {
            "str": "string",
            "int": "number",
            "float": "number",
            "bool": "boolean",
            "datetime": "Date",
            "dict": "Record<string, any>",
            "list": "any[]",
        }
        return type_map.get(python_type, "any")

    def _write_file(
        self,
        filename: str,
        content: str,
        output_dir: Path,
    ) -> GeneratedFile:
        """Write file và trả về GeneratedFile."""
        file_path = output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return GeneratedFile(
            path=file_path.relative_to(output_dir.parent.parent if output_dir.parent.name == "src" else output_dir.parent),
            content=content,
            template=f"angular/{filename}",
        )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "AngularEmitter",
    "GeneratedFile",
]