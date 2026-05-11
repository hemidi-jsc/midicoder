"""
Frontend React Emitter Module (P2-002-B).

Module này cung cấp ReactEmitter class để generate React 18+ frontend code
từ MIR (Midicoder Intermediate Representation).

Theo CURRENT_TASK_REQUIREMENT.md:
- FR1: React App Structure Emission
- FR2: Entity-driven Page Generation
- FR3: Service Layer (REST + GraphQL + WebSocket + gRPC-web)
- FR4: Redux Toolkit State Management
- FR5: UI Framework Support (5 frameworks)
- FR6: Full Auth Integration
- FR7: Full Routing (React Router v6)
- FR8: Type/Interface Generation

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from midicoder.emitters.core.cache import (
    CacheParser,
    ReactEmitter as CacheReactEmitter,
)
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
# React Emitter
# ============================================================================


class ReactEmitter:
    """
    Emitter cho React 18+ frontend code generation.

    Generate code cho:
    - App structure (App.tsx, index.tsx, main.tsx)
    - Entity pages (List, Detail, Create, Edit)
    - Services (REST, GraphQL, WebSocket, gRPC-web)
    - Redux Toolkit state (slices, store)
    - Auth module (context, interceptor, protected routes)
    - Routing (React Router v6)
    - Types/Interfaces

    Usage:
        emitter = ReactEmitter.create_emitter(ui_framework="material")
        files = emitter.emit(mir, output_dir=Path("/tmp/output"))
    """

    # UI Frameworks hỗ trợ (FR5)
    SUPPORTED_UI_FRAMEWORKS = ["material", "tailwind", "bootstrap", "antd", "carbon"]

    def __init__(
        self,
        stack_dir: Path,
        ui_framework: str = "material",
        state_management: str = "redux",
        communication: list[str] | None = None,
    ) -> None:
        """
        Khoi tao ReactEmitter.

        Args:
            stack_dir: Đường dẫn đến templates directory
            ui_framework: UI framework (material, tailwind, bootstrap, antd, carbon)
            state_management: State management pattern (redux, zustand, context)
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

    @classmethod
    def create_emitter(
        cls,
        stack_dir: Path | None = None,
        ui_framework: str = "material",
        state_management: str = "redux",
        communication: list[str] | None = None,
    ) -> "ReactEmitter":
        """
        Factory method để tạo ReactEmitter.

        Args:
            stack_dir: Đường dẫn templates (default: midicoder/stacks/react)
            ui_framework: UI framework (default: material)
            state_management: State management (default: redux)
            communication: Communication patterns (default: ["rest"])

        Returns:
            ReactEmitter instance
        """
        if stack_dir is None:
            stack_dir = Path(__file__).parent.parent.parent / "stacks" / "react"
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
        Emit React code từ MIR metadata.

        Args:
            mir: MIR instance với metadata
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances
        """
        files: list[GeneratedFile] = []

        # Lay metadata từ MIR
        entities = mir.metadata.get("entities", [])
        routes = mir.metadata.get("routes", [])
        operations = mir.metadata.get("operations", [])
        authnz = mir.metadata.get("authnz", {})

        # Tao src directory
        src_dir = output_dir / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        # FR1: Emit base app structure
        files.extend(self._emit_base_files(src_dir))

        # FR8: Emit types/interfaces
        if entities or operations:
            files.extend(self._emit_types(entities, operations, src_dir))

        # FR2: Emit entity pages (CRUD)
        for entity in entities:
            files.extend(self._emit_entity_pages(entity, src_dir))

        # FR3: Emit services
        if entities:
            files.extend(self._emit_services(entities, src_dir))

        # FR4: Emit Redux Toolkit state
        if entities and self.state_management == "redux":
            files.extend(self._emit_redux_state(entities, src_dir))

        # FR6: Emit auth module
        if authnz:
            files.extend(self._emit_auth(authnz, src_dir))

        # Emit cache module (CP09)
        cache_profiles_data = mir.metadata.get("cache_profiles", [])
        if cache_profiles_data:
            files.extend(self._emit_cache(cache_profiles_data, src_dir))

        # FR7: Emit routing
        if routes or entities:
            files.extend(self._emit_routing(routes, entities, authnz, src_dir))

        return files

    def _emit_base_files(self, output_dir: Path) -> list[GeneratedFile]:
        """Emit base app files (FR1)."""
        files: list[GeneratedFile] = []

        # App.tsx - Root component
        files.append(self._write_file(
            filename="App.tsx",
            content=self._generate_app_tsx(),
            output_dir=output_dir,
        ))

        # main.tsx - Entry point
        files.append(self._write_file(
            filename="main.tsx",
            content=self._generate_main_tsx(),
            output_dir=output_dir,
        ))

        # index.css - Base styles
        files.append(self._write_file(
            filename="index.css",
            content="/* Base styles */\n",
            output_dir=output_dir,
        ))

        return files

    def _emit_types(
        self,
        entities: list[dict[str, Any]],
        operations: list[dict[str, Any]],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit TypeScript types (FR8)."""
        files: list[GeneratedFile] = []
        types_dir = output_dir / "types"
        types_dir.mkdir(parents=True, exist_ok=True)

        for entity in entities:
            type_content = self._generate_entity_type(entity)
            entity_id = entity.get("id", "Entity")
            files.append(self._write_file(
                filename=f"{entity_id}.ts",
                content=type_content,
                output_dir=types_dir,
            ))

        # index.ts
        files.append(self._write_file(
            filename="index.ts",
            content=self._generate_types_index(entities),
            output_dir=types_dir,
        ))

        return files

    def _emit_entity_pages(
        self,
        entity: dict[str, Any],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit entity CRUD pages (FR2)."""
        files: list[GeneratedFile] = []
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()

        pages_dir = output_dir / "pages" / entity_lower
        pages_dir.mkdir(parents=True, exist_ok=True)

        # List page
        files.append(self._write_file(
            filename="List.tsx",
            content=self._generate_list_page(entity),
            output_dir=pages_dir,
        ))

        # Detail page
        files.append(self._write_file(
            filename="Detail.tsx",
            content=self._generate_detail_page(entity),
            output_dir=pages_dir,
        ))

        # Create page
        files.append(self._write_file(
            filename="Create.tsx",
            content=self._generate_create_page(entity),
            output_dir=pages_dir,
        ))

        # Edit page
        files.append(self._write_file(
            filename="Edit.tsx",
            content=self._generate_edit_page(entity),
            output_dir=pages_dir,
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
                filename=f"{entity_id}Service.ts",
                content=service_content,
                output_dir=services_dir,
            ))

        return files

    def _emit_redux_state(
        self,
        entities: list[dict[str, Any]],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """Emit Redux Toolkit state (FR4)."""
        files: list[GeneratedFile] = []
        store_dir = output_dir / "store"
        store_dir.mkdir(parents=True, exist_ok=True)

        for entity in entities:
            entity_id = entity.get("id", "Entity")

            # Slice
            files.append(self._write_file(
                filename=f"{entity_id}Slice.ts",
                content=self._generate_redux_slice(entity),
                output_dir=store_dir,
            ))

        # Store
        files.append(self._write_file(
            filename="store.ts",
            content=self._generate_redux_store(entities),
            output_dir=store_dir,
        ))

        return files

    def _emit_cache(
        self,
        cache_profiles_data: list[dict[str, Any]],
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Emit cache module (CP09: Caching & Performance Layer).

        Su dung CacheReactEmitter de generate cache code.

        KPI-029: Tenant-aware caching.

        Args:
            cache_profiles_data: List cua cache profiles tu MIR metadata
            output_dir: Output directory

        Returns:
            List of GeneratedFile
        """
        files: list[GeneratedFile] = []

        try:
            # Parse cache config tu metadata
            parser = CacheParser()
            metadata = {"cache_profiles": cache_profiles_data}
            collection = parser.parse_from_metadata(metadata)

            if not collection.profiles:
                return files

            # Tao emitter va emit files
            cache_emitter = CacheReactEmitter(self.stack_dir)
            emitted_files = cache_emitter.emit(collection, output_dir)

            # Chuyen doi sang GeneratedFile cua ReactEmitter
            for emitted in emitted_files:
                files.append(GeneratedFile(
                    path=emitted.path.relative_to(output_dir) if hasattr(emitted.path, 'relative_to') else emitted.path,
                    content=emitted.content,
                    template=emitted.template,
                ))
        except Exception as e:
            import logging
            logging.warning(f"CacheReactEmitter failed: {e}")

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

        # Auth Context
        files.append(self._write_file(
            filename="AuthContext.tsx",
            content=self._generate_auth_context(),
            output_dir=auth_dir,
        ))

        # Auth Interceptor
        files.append(self._write_file(
            filename="authInterceptor.ts",
            content=self._generate_auth_interceptor(),
            output_dir=auth_dir,
        ))

        # Protected Route
        files.append(self._write_file(
            filename="ProtectedRoute.tsx",
            content=self._generate_protected_route(),
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
        """Emit routing (FR7)."""
        files: list[GeneratedFile] = []

        routes_content = self._generate_app_routes(entities)
        files.append(self._write_file(
            filename="AppRoutes.tsx",
            content=routes_content,
            output_dir=output_dir,
        ))

        return files

    # ========================================================================
    # Template Generation Methods
    # ========================================================================

    def _generate_app_tsx(self) -> str:
        """Generate App.tsx content."""
        return (
            "/**\n"
            " * App Component - Root component cua React app.\n"
            " * \n"
            " * Su dung React Router v6 cho navigation.\n"
            " */\n\n"
            "import { RouterProvider } from 'react-router-dom';\n"
            "import { router } from './AppRoutes';\n\n"
            "function App() {\n"
            "  return <RouterProvider router={router} />;\n"
            "}\n\n"
            "export default App;\n"
        )

    def _generate_main_tsx(self) -> str:
        """Generate main.tsx content."""
        redux_import = ""
        redux_provider = ""
        if self.state_management == "redux":
            redux_import = "import { Provider } from 'react-redux';\nimport { store } from './store/store';\n"
            redux_provider = "<Provider store={store}>"

        return (
            "/**\n"
            " * Main Entry Point - Dieu khoi dong React app.\n"
            " */\n\n"
            "import React from 'react';\n"
            "import ReactDOM from 'react-dom/client';\n"
            f"{redux_import}"
            "import App from './App';\n"
            "import './index.css';\n\n"
            "const root = ReactDOM.createRoot(\n"
            "  document.getElementById('root') as HTMLElement\n"
            ");\n\n"
            "root.render(\n"
            "  <React.StrictMode>\n"
            f"{redux_provider}"
            "    <App />\n"
            f"{'</Provider>' if redux_provider else ''}"
            "  </React.StrictMode>\n"
            ");\n"
        )

    def _generate_entity_type(self, entity: dict[str, Any]) -> str:
        """Generate entity type (FR8)."""
        entity_id = entity.get("id", "Entity")
        fields = entity.get("fields", [])

        properties = ""
        for field in fields:
            name = field.get("name", "")
            field_type = self._ts_type(field.get("type", "str"))
            required = "" if field.get("required") else "?"
            properties += f"  {name}{required}: {field_type};\n"

        return (
            f"/**\n"
            f" * {entity_id} Type - Interface cho entity {entity_id}.\n"
            f" */\n\n"
            f"export interface {entity_id} {{\n"
            f"{properties}}}\n"
        )

    def _generate_types_index(self, entities: list[dict[str, Any]]) -> str:
        """Generate types/index.ts."""
        exports = ""
        for entity in entities:
            entity_id = entity.get("id", "Entity")
            exports += f"export * from './{entity_id}';\n"
        return f"// Types Index - Export tat ca types\n\n{exports}"

    def _generate_list_page(self, entity: dict[str, Any]) -> str:
        """Generate list page (FR2)."""
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        return (
            f"/**\n"
            f" * {entity_id} List Page - Hien thi danh sach {entity_lower}.\n"
            f" */\n\n"
            f"import {{ useState, useEffect }} from 'react';\n"
            f"import {{ Link }} from 'react-router-dom';\n"
            f"import {{ {entity_id} }} from '../../types/{entity_id}';\n"
            f"import {{ useGet{entity_id}sQuery }} from '../../services/{entity_id}Service';\n\n"
            f"export default function {entity_id}List() {{\n"
            f"  const {{ data: items, isLoading }} = useGet{entity_id}sQuery();\n\n"
            f"  if (isLoading) return <div>Loading...</div>;\n\n"
            f"  return (\n"
            f"    <div>\n"
            f"      <h1>{entity_id}s</h1>\n"
            f'      <Link to="/{entity_lower}/create">Create New</Link>\n'
            "      <ul>\n"
            "        {items?.map((item: " + entity_id + ") => (\n"
            '          <li key={item.id}>\n'
            "            <Link to={`" + entity_lower + "/detail/${item.id}`}>{item.id}</Link>\n"
            "          </li>\n"
            "        ))}\n"
            f"      </ul>\n"
            f"    </div>\n"
            f"  );\n"
            f"}}\n"
        )

    def _generate_detail_page(self, entity: dict[str, Any]) -> str:
        """Generate detail page."""
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        return (
            "/**\n"
            f" * {entity_id} Detail Page - Hien thi chi tiet {entity_lower}.\n"
            " */\n\n"
            "import { useParams, Link } from 'react-router-dom';\n"
            f"import {{ useGet{entity_id}ByIdQuery }} from '../../services/{entity_id}Service';\n\n"
            f"export default function {entity_id}Detail() {{\n"
            "  const { id } = useParams();\n"
            f"  const {{ data, isLoading }} = useGet{entity_id}ByIdQuery(id!);\n\n"
            "  if (isLoading) return <div>Loading...</div>;\n\n"
            "  return (\n"
            "    <div>\n"
            f"      <h1>{entity_id} Detail</h1>\n"
            "      <pre>{JSON.stringify(data, null, 2)}</pre>\n"
            f'      <Link to="/{entity_lower}/edit/{{id}}">Edit</Link>\n'
            "    </div>\n"
            "  );\n"
            "}\n"
        )

    def _generate_create_page(self, entity: dict[str, Any]) -> str:
        """Generate create page."""
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        return (
            "/**\n"
            f" * {entity_id} Create Page - Form tao moi {entity_lower}.\n"
            " */\n\n"
            "import { useNavigate } from 'react-router-dom';\n"
            f"import {{ useCreate{entity_id}Mutation }} from '../../services/{entity_id}Service';\n\n"
            f"export default function {entity_id}Create() {{\n"
            "  const navigate = useNavigate();\n"
            f"  const [createItem] = useCreate{entity_id}Mutation();\n\n"
            "  return (\n"
            "    <div>\n"
            f"      <h1>Create {entity_id}</h1>\n"
            "      <form>\n"
            "        {/* Form fields */}\n"
            '        <button type="submit">Create</button>\n'
            "      </form>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )

    def _generate_edit_page(self, entity: dict[str, Any]) -> str:
        """Generate edit page."""
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        return (
            "/**\n"
            f" * {entity_id} Edit Page - Form chinh sua {entity_lower}.\n"
            " */\n\n"
            "import { useParams, useNavigate } from 'react-router-dom';\n"
            f"import {{\n"
            f"  useGet{entity_id}ByIdQuery,\n"
            f"  useUpdate{entity_id}Mutation,\n"
            "}} from '../../services/" + entity_id + "Service';\n\n"
            f"export default function {entity_id}Edit() {{\n"
            "  const { id } = useParams();\n"
            "  const navigate = useNavigate();\n"
            f"  const {{ data }} = useGet{entity_id}ByIdQuery(id!);\n"
            f"  const [updateItem] = useUpdate{entity_id}Mutation();\n\n"
            "  return (\n"
            "    <div>\n"
            f"      <h1>Edit {entity_id}</h1>\n"
            "      <form>\n"
            "        {/* Form fields with initial data */}\n"
            '        <button type="submit">Update</button>\n'
            "      </form>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )

    def _generate_entity_service(self, entity: dict[str, Any]) -> str:
        """Generate entity service (FR3)."""
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()

        return (
            f"/**\n"
            f" * {entity_id} Service - Service cho CRUD operations cua {entity_lower}.\n"
            f" * \n"
            f" * Communication: {', '.join(self.communication)}\n"
            f" */\n\n"
            f"import {{ injectApi }} from '@reduxjs/toolkit/query/react';\n"
            f"import {{ {entity_id} }} from '../types/{entity_id}';\n\n"
            f"export const {entity_id}Api = injectApi({{\n"
            f"  reducerPath: '{entity_id}Api',\n"
            f"  baseQuery: fetchBaseQuery({{ baseUrl: '/api' }}),\n"
            f"  endpoints: (builder) => ({{\n"
            f"    get{entity_id}s: builder.query<{entity_id}[], void>({{\n"
            f"      query: () => '{entity_lower}',\n"
            f"    }}),\n"
            f"    get{entity_id}ById: builder.query<{entity_id}, string>({{\n"
            f"      query: (id) => `{{{entity_lower}}}/{{id}}`,\n"
            f"    }}),\n"
            f"    create{entity_id}: builder.mutation<{entity_id}, Partial<{entity_id}>>({{\n"
            f"      query: (body) => ({{\n"
            f"        url: '{entity_lower}',\n"
            f"        method: 'POST',\n"
            f"        body,\n"
            f"      }}),\n"
            f"    }}),\n"
            f"    update{entity_id}: builder.mutation<{entity_id}, {{ id: string; changes: Partial<{entity_id}> }}>({{\n"
            f"      query: ({{ id, changes }}) => ({{\n"
            f"        url: `{{{entity_lower}}}/{{id}}`,\n"
            f"        method: 'PUT',\n"
            f"        body: changes,\n"
            f"      }}),\n"
            f"    }}),\n"
            f"    delete{entity_id}: builder.mutation<void, string>({{\n"
            f"      query: (id) => ({{\n"
            f"        url: `{{{entity_lower}}}/{{id}}`,\n"
            f"        method: 'DELETE',\n"
            f"      }}),\n"
            f"    }}),\n"
            f"  }}),\n"
            f"}});\n\n"
            f"export const {{\n"
            f"  useGet{entity_id}sQuery,\n"
            f"  useGet{entity_id}ByIdQuery,\n"
            f"  useCreate{entity_id}Mutation,\n"
            f"  useUpdate{entity_id}Mutation,\n"
            f"  useDelete{entity_id}Mutation,\n"
            f"}} = {entity_id}Api;\n"
        )

    def _generate_redux_slice(self, entity: dict[str, Any]) -> str:
        """Generate Redux Toolkit slice (FR4)."""
        entity_id = entity.get("id", "Entity")
        entity_lower = entity_id.lower()
        return (
            f"/**\n"
            f" * {entity_id} Slice - Redux Toolkit slice cho {entity_lower}.\n"
            f" */\n\n"
            f"import {{ createSlice, PayloadAction }} from '@reduxjs/toolkit';\n"
            f"import {{ {entity_id} }} from '../../types/{entity_id}';\n\n"
            f"interface {entity_id}State {{\n"
            f"  items: {entity_id}[];\n"
            f"  selectedId: string | null;\n"
            f"  loading: boolean;\n"
            f"  error: string | null;\n"
            f"}}\n\n"
            f"const initialState: {entity_id}State = {{\n"
            f"  items: [],\n"
            f"  selectedId: null,\n"
            f"  loading: false,\n"
            f"  error: null,\n"
            f"}};\n\n"
            f"export const {entity_id}Slice = createSlice({{\n"
            f"  name: '{entity_lower}',\n"
            f"  initialState,\n"
            f"  reducers: {{\n"
            f"    set{entity_id}s: (state, action: PayloadAction<{entity_id}[]>) => {{\n"
            f"      state.items = action.payload;\n"
            f"    }},\n"
            f"    setSelected{entity_id}: (state, action: PayloadAction<string | null>) => {{\n"
            f"      state.selectedId = action.payload;\n"
            f"    }},\n"
            f"  }},\n"
            f"}});\n\n"
            f"export const {{ set{entity_id}s, setSelected{entity_id} }} = {entity_id}Slice.actions;\n"
            f"export default {entity_id}Slice.reducer;\n"
        )

    def _generate_redux_store(self, entities: list[dict[str, Any]]) -> str:
        """Generate Redux store."""
        reducers = ""
        imports = ""
        for entity in entities:
            entity_id = entity.get("id", "Entity")
            entity_lower = entity_id.lower()
            imports += f"import {entity_lower}Reducer from './{entity_id}Slice';\n"
            reducers += f"  {entity_lower}: {entity_lower}Reducer,\n"

        return (
            "/**\n"
            " * Redux Store - Cau hình Redux store cho toàn bộ app.\n"
            " */\n\n"
            "import { configureStore } from '@reduxjs/toolkit';\n"
            f"{imports}"
            "import { apiSlice } from '../services/apiSlice';\n\n"
            "export const store = configureStore({\n"
            "  reducer: {\n"
            f"{reducers}"
            "    [apiSlice.reducerPath]: apiSlice.reducer,\n"
            "  },\n"
            "  middleware: (getDefaultMiddleware) =>\n"
            "    getDefaultMiddleware().concat(apiSlice.middleware),\n"
            "});\n\n"
            "export type RootState = ReturnType<typeof store.getState>;\n"
            "export type AppDispatch = typeof store.dispatch;\n"
        )

    def _generate_auth_context(self) -> str:
        """Generate Auth Context (FR6)."""
        return (
            '/**\n'
            ' * Auth Context - Quan ly authentication va authorization.\n'
            ' * \n'
            ' * Features:\n'
            ' * - JWT token management\n'
            ' * - Login/Logout\n'
            ' * - Permission checking\n'
            ' */\n\n'
            "import React, { createContext, useContext, useState, ReactNode } from 'react';\n\n"
            'interface AuthUser {\n'
            '  id: string;\n'
            '  email: string;\n'
            '  roles: string[];\n'
            '  permissions: string[];\n'
            '}\n\n'
            'interface AuthContextType {\n'
            '  user: AuthUser | null;\n'
            '  token: string | null;\n'
            '  login: (token: string, user: AuthUser) => void;\n'
            '  logout: () => void;\n'
            '  hasPermission: (permission: string) => boolean;\n'
            '}\n\n'
            'const AuthContext = createContext<AuthContextType | null>(null);\n\n'
            'export function AuthProvider({ children }: { children: ReactNode }) {\n'
            '  const [user, setUser] = useState<AuthUser | null>(null);\n'
            "  const [token, setToken] = useState<string | null>(localStorage.getItem('auth_token'));\n\n"
            '  const login = (newToken: string, newUser: AuthUser) => {\n'
            "    localStorage.setItem('auth_token', newToken);\n"
            '    setToken(newToken);\n'
            '    setUser(newUser);\n'
            '  };\n\n'
            '  const logout = () => {\n'
            "    localStorage.removeItem('auth_token');\n"
            '    setToken(null);\n'
            '    setUser(null);\n'
            '  };\n\n'
            '  const hasPermission = (permission: string): boolean => {\n'
            '    return user?.permissions.includes(permission) ?? false;\n'
            '  };\n\n'
            '  return (\n'
            '    <AuthContext.Provider value={{ user, token, login, logout, hasPermission }}>\n'
            '      {children}\n'
            '    </AuthContext.Provider>\n'
            '  );\n'
            '}\n\n'
            'export function useAuth() {\n'
            '  const context = useContext(AuthContext);\n'
            '  if (!context) {\n'
            "    throw new Error('useAuth must be used within AuthProvider');\n"
            '  }\n'
            '  return context;\n'
            '}\n'
        )

    def _generate_auth_interceptor(self) -> str:
        """Generate Auth Interceptor (FR6)."""
        return (
            '/**\n'
            ' * Auth Interceptor - Tu dong attach JWT token vao HTTP requests.\n'
            ' */\n\n'
            "import { fetchBaseQuery } from '@reduxjs/toolkit/query/react';\n\n"
            'const baseQuery = fetchBaseQuery({\n'
            "  baseUrl: '/api',\n"
            '  prepareHeaders: (headers) => {\n'
            "    const token = localStorage.getItem('auth_token');\n"
            '    if (token) {\n'
            "      headers.set('Authorization', `Bearer ${token}`);\n"
            '    }\n'
            '    return headers;\n'
            '  },\n'
            '});\n\n'
            'export default baseQuery;\n'
        )

    def _generate_protected_route(self) -> str:
        """Generate Protected Route (FR6)."""
        return (
            '/**\n'
            ' * Protected Route - Route guard cho protected routes.\n'
            ' */\n\n'
            "import { Navigate, useLocation } from 'react-router-dom';\n"
            "import { useAuth } from './AuthContext';\n\n"
            'export default function ProtectedRoute({ children }: { children: JSX.Element }) {\n'
            '  const { user } = useAuth();\n'
            '  const location = useLocation();\n\n'
            '  if (!user) {\n'
            "    return <Navigate to='/login' state={{ from: location }} replace />;\n"
            '  }\n\n'
            '  return children;\n'
            '}\n'
        )

    def _generate_app_routes(self, entities: list[dict[str, Any]]) -> str:
        """Generate AppRoutes (FR7)."""
        entity_routes = ""
        for entity in entities:
            entity_id = entity.get("id", "Entity")
            entity_lower = entity_id.lower()
            entity_routes += (
                f"    {{ path: '{entity_lower}', element: <{entity_id}List /> }},\n"
                f"    {{ path: '{entity_lower}/create', element: <{entity_id}Create /> }},\n"
                f"    {{ path: '{entity_lower}/detail/:id', element: <{entity_id}Detail /> }},\n"
                f"    {{ path: '{entity_lower}/edit/:id', element: <{entity_id}Edit /> }},\n"
            )

        imports = ""
        for entity in entities:
            entity_id = entity.get("id", "Entity")
            imports += (
                f"import {entity_id}List from './pages/{entity_id.lower()}/List';\n"
                f"import {entity_id}Create from './pages/{entity_id.lower()}/Create';\n"
                f"import {entity_id}Detail from './pages/{entity_id.lower()}/Detail';\n"
                f"import {entity_id}Edit from './pages/{entity_id.lower()}/Edit';\n"
            )

        return (
            "/**\n"
            " * App Routes - Routing configuration voi React Router v6.\n"
            " */\n\n"
            "import {{ createBrowserRouter }} from 'react-router-dom';\n"
            f"{imports}"
            "import ProtectedRoute from './auth/ProtectedRoute';\n\n"
            "export const router = createBrowserRouter([\n"
            "  {{ path: '/', element: <h1>Home</h1> }},\n"
            "  {{\n"
            "    path: '/app',\n"
            "    element: <ProtectedRoute><AppLayout /></ProtectedRoute>,\n"
            "    children: [\n"
            f"{entity_routes}"
            "    ],\n"
            "  }},\n"
            "]);\n"
        )

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _to_pascal_case(self, name: str) -> str:
        """Chuyen string sang PascalCase."""
        return name.strip().title().replace(" ", "")

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
        """Write file va tra ve GeneratedFile."""
        file_path = output_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return GeneratedFile(
            path=file_path.relative_to(output_dir.parent),
            content=content,
            template=f"react/{filename}",
        )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "ReactEmitter",
    "GeneratedFile",
]