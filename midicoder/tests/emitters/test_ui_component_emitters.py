# coding: utf-8
"""
Tests cho emitters của UI Component Generator (CP19).

Modules:
  - midicoder/emitters/core/ui_component/angular.py
  - midicoder/emitters/core/ui_component/react.py
  - midicoder/emitters/core/ui_component/fastapi.py
  - midicoder/emitters/core/ui_component/nestjs.py

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from pathlib import Path
from midicoder.emitters.core.ui_component.models import (
    ComponentSpec, ComponentType, FormFieldSpec, FieldType,
    TableSpec, TableColumn,
)


class TestAngularUIEmitter:
    """Tests cho AngularUIEmitter."""

    def test_angular_emitter_init_with_material(self):
        """Test khởi tạo AngularUIEmitter với material."""
        from midicoder.emitters.core.ui_component.angular import AngularUIEmitter
        emitter = AngularUIEmitter(ui_framework="material")
        assert emitter.ui_framework == "material"

    def test_angular_emitter_init_with_tailwind(self):
        """Test khởi tạo AngularUIEmitter với tailwind."""
        from midicoder.emitters.core.ui_component.angular import AngularUIEmitter
        emitter = AngularUIEmitter(ui_framework="tailwind")
        assert emitter.ui_framework == "tailwind"

    def test_angular_emitter_invalid_framework_raises(self):
        """Test framework không hợp lệ thì raise."""
        from midicoder.emitters.core.ui_component.angular import AngularUIEmitter
        with pytest.raises(ValueError):
            AngularUIEmitter(ui_framework="invalid")

    def test_angular_emitter_generate_form_field(self, tmp_path: Path):
        """Test generate form field component cho Angular."""
        from midicoder.emitters.core.ui_component.angular import AngularUIEmitter
        emitter = AngularUIEmitter(ui_framework="material")
        components = [
            ComponentSpec(
                component_type=ComponentType.FORM_FIELD,
                entity_id="User",
                fields=[
                    FormFieldSpec(
                        field_name="email",
                        field_type=FieldType.EMAIL,
                        label="Email",
                        binding_path="user.email",
                    ),
                ],
            ),
        ]
        files = emitter.generate(components, tmp_path)
        assert len(files) == 1
        assert "form-field.component.ts" in str(files[0].path)
        assert Path(tmp_path / "form-field.component.ts").exists()

    def test_angular_emitter_generate_all_components(self, tmp_path: Path):
        """Test generate tất cả 4 components cho Angular."""
        from midicoder.emitters.core.ui_component.angular import AngularUIEmitter
        emitter = AngularUIEmitter(ui_framework="material")
        components = [
            ComponentSpec(component_type=ComponentType.FORM_FIELD, entity_id="User"),
            ComponentSpec(component_type=ComponentType.DATA_TABLE, entity_id="Order",
                        table_spec=TableSpec(entity_id="Order",
                                           columns=[TableColumn(field_name="id", label="ID")])),
            ComponentSpec(component_type=ComponentType.CARD_LIST, entity_id="Product"),
            ComponentSpec(component_type=ComponentType.DIALOG, entity_id="User"),
        ]
        files = emitter.generate(components, tmp_path)
        assert len(files) == 4
        generated_names = {f.path.name for f in files}
        assert "form-field.component.ts" in generated_names
        assert "data-table.component.ts" in generated_names
        assert "card-list.component.ts" in generated_names
        assert "dialog.component.ts" in generated_names


class TestReactUIEmitter:
    """Tests cho ReactUIEmitter."""

    def test_react_emitter_init_with_tailwind(self):
        """Test khởi tạo ReactUIEmitter với tailwind."""
        from midicoder.emitters.core.ui_component.react import ReactUIEmitter
        emitter = ReactUIEmitter(ui_framework="tailwind")
        assert emitter.ui_framework == "tailwind"

    def test_react_emitter_init_with_material(self):
        """Test khởi tạo ReactUIEmitter với material."""
        from midicoder.emitters.core.ui_component.react import ReactUIEmitter
        emitter = ReactUIEmitter(ui_framework="material")
        assert emitter.ui_framework == "material"

    def test_react_emitter_invalid_framework_raises(self):
        """Test framework không hợp lệ thì raise."""
        from midicoder.emitters.core.ui_component.react import ReactUIEmitter
        with pytest.raises(ValueError):
            ReactUIEmitter(ui_framework="invalid")

    def test_react_emitter_generate_form_field(self, tmp_path: Path):
        """Test generate form field component cho React."""
        from midicoder.emitters.core.ui_component.react import ReactUIEmitter
        emitter = ReactUIEmitter(ui_framework="tailwind")
        components = [
            ComponentSpec(
                component_type=ComponentType.FORM_FIELD,
                entity_id="User",
                fields=[
                    FormFieldSpec(
                        field_name="name",
                        field_type=FieldType.TEXT,
                        label="Tên",
                        binding_path="user.name",
                    ),
                ],
            ),
        ]
        files = emitter.generate(components, tmp_path)
        assert len(files) == 1
        assert "FormField.tsx" in str(files[0].path)
        assert Path(tmp_path / "FormField.tsx").exists()

    def test_react_emitter_generate_all_components(self, tmp_path: Path):
        """Test generate tất cả 4 components cho React."""
        from midicoder.emitters.core.ui_component.react import ReactUIEmitter
        emitter = ReactUIEmitter(ui_framework="tailwind")
        components = [
            ComponentSpec(component_type=ComponentType.FORM_FIELD, entity_id="User"),
            ComponentSpec(component_type=ComponentType.DATA_TABLE, entity_id="Order",
                        table_spec=TableSpec(entity_id="Order",
                                           columns=[TableColumn(field_name="id", label="ID")])),
            ComponentSpec(component_type=ComponentType.CARD_LIST, entity_id="Product"),
            ComponentSpec(component_type=ComponentType.DIALOG, entity_id="User"),
        ]
        files = emitter.generate(components, tmp_path)
        assert len(files) == 4
        generated_names = {f.path.name for f in files}
        assert "FormField.tsx" in generated_names
        assert "DataTable.tsx" in generated_names
        assert "CardList.tsx" in generated_names
        assert "Dialog.tsx" in generated_names


class TestFastAPIUIEmitter:
    """Tests cho FastAPIUIEmitter."""

    def test_fastapi_emitter_init(self):
        """Test khởi tạo FastAPIUIEmitter."""
        from midicoder.emitters.core.ui_component.fastapi import FastAPIUIEmitter
        emitter = FastAPIUIEmitter()
        assert emitter.name == "fastapi-ui"
        assert emitter.language == "python"

    def test_fastapi_emitter_generate_form_validation(self, tmp_path: Path):
        """Test generate form validation service."""
        from midicoder.emitters.core.ui_component.fastapi import FastAPIUIEmitter
        emitter = FastAPIUIEmitter()
        components = [
            ComponentSpec(
                component_type=ComponentType.FORM_FIELD,
                entity_id="User",
                fields=[
                    FormFieldSpec(
                        field_name="email",
                        field_type=FieldType.EMAIL,
                        label="Email",
                        binding_path="user.email",
                        required=True,
                    ),
                ],
            ),
        ]
        files = emitter.generate(components, tmp_path)
        assert len(files) == 1
        assert "form_validation_service.py" in str(files[0].path)
        assert Path(tmp_path / "form_validation_service.py").exists()

    def test_fastapi_emitter_no_form_components(self, tmp_path: Path):
        """Test sinh service mặc định khi không có form component."""
        from midicoder.emitters.core.ui_component.fastapi import FastAPIUIEmitter
        emitter = FastAPIUIEmitter()
        files = emitter.generate([], tmp_path)
        assert len(files) == 1


class TestNestJSUIEmitter:
    """Tests cho NestJSUIEmitter."""

    def test_nestjs_emitter_init(self):
        """Test khởi tạo NestJSUIEmitter."""
        from midicoder.emitters.core.ui_component.nestjs import NestJSUIEmitter
        emitter = NestJSUIEmitter()
        assert emitter.name == "nestjs-ui"
        assert emitter.language == "typescript"

    def test_nestjs_emitter_generate_dto_and_pipe(self, tmp_path: Path):
        """Test generate DTO + Pipe."""
        from midicoder.emitters.core.ui_component.nestjs import NestJSUIEmitter
        emitter = NestJSUIEmitter()
        components = [
            ComponentSpec(
                component_type=ComponentType.FORM_FIELD,
                entity_id="Order",
                fields=[
                    FormFieldSpec(
                        field_name="status",
                        field_type=FieldType.SELECT,
                        label="Trạng thái",
                        binding_path="order.status",
                        options=["pending", "confirmed"],
                    ),
                ],
            ),
        ]
        files = emitter.generate(components, tmp_path)
        assert len(files) == 2
        generated_names = {f.path.name for f in files}
        assert "order-form-validation.dto.ts" in generated_names
        assert "form-validation.pipe.ts" in generated_names

    def test_nestjs_emitter_only_pipe_when_no_forms(self, tmp_path: Path):
        """Test chỉ sinh Pipe khi không có form component."""
        from midicoder.emitters.core.ui_component.nestjs import NestJSUIEmitter
        emitter = NestJSUIEmitter()
        files = emitter.generate([], tmp_path)
        assert len(files) == 1
        assert "form-validation.pipe.ts" in str(files[0].path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
