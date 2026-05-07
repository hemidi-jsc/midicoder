"""
Emitter Module — Jinja2 Template Rendering Engine.

Mô-đun này cung cấp Emitter class, thành phần chịu trách nhiệm render templates
Jinja2 để generate source code từ MIR metadata.

Theo SoT E07, Emitter là bridge giữa Plan (typed IR) và source code output.
Emitter load Jinja2 Environment từ template directory, render templates với
MIR context, và write generated files ra output directory.

Sử dụng:
    from midicoder.pipeline.emitter import Emitter

    # Khởi tạo Emitter cho stack FastAPI
    emitter = Emitter(stack="fastapi")
    
    # Render template với context
    content = emitter.render("main.py.jinja2", {"entities": [...]})
    
    # Emit files từ FileSpecs
    files = emitter.emit(file_specs, output_dir)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import jinja2

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ============================================================================
# Generated File
# ============================================================================


@dataclass
class GeneratedFile:
    """
    File đã được generate từ template.
    
    Attributes:
        path: Đường dẫn file tương đối so với output directory
        content: Nội dung file đã render
        file_type: Loại file (model, schema, route, service, etc.)
        template: Template name đã dùng để render
    """
    path: str
    content: str
    file_type: str
    template: str


# ============================================================================
# Emitter Class
# ============================================================================


class Emitter:
    """
    Emitter class với full lifecycle cho Jinja2 template rendering.
    
    Emitter là bridge giữa Implementation Plan và source code output.
    Class này chịu trách nhiệm:
    - Load Jinja2 Environment từ template directory của stack target
    - Render templates với MIR context (entities, commands, queries, events)
    - Write generated files ra output directory
    
    Theo CORE_PACK_SPECIFICATION.md Section 1.5.4:
    - Template directory: midicoder/stacks/{stack}/core/
    - Context = MIR metadata (entities, commands, queries, events)
    - Emitter đọc template path từ FileSpec.template
    
    Attributes:
        stack: Target stack (fastapi, nestjs, angular, react)
        environment: Jinja2 Environment instance
        _template_dir: Đường dẫn absolute đến template directory
    
    Ví dụ:
        emitter = Emitter(stack="fastapi")
        content = emitter.render("main.py.jinja2", {"entities": [...]})
        files = emitter.emit(file_specs, output_dir)
    """
    
    def __init__(self, stack: str = "fastapi", template_dir: Optional[Path] = None) -> None:
        """
        Khởi tạo Emitter với Jinja2 Environment.
        
        Load templates từ directory: midicoder/stacks/{stack}/core/
        Nếu directory không tồn tại, tạo empty environment.
        
        Args:
            stack: Target stack (fastapi, nestjs, angular, react).
                   Mặc định: "fastapi"
            template_dir: Optional custom template directory (chủ yếu dùng cho test).
                          Nếu cung cấp, sẽ override tự động detection.
        """
        self.stack = stack
        self.environment: Optional[jinja2.Environment] = None
        self._template_dir_value: Optional[Path] = None
        
        # Nếu template_dir được cung cấp (test mode), dùng trực tiếp
        if template_dir is not None:
            self._template_dir = template_dir
        else:
            self._init_environment()
    
    def _init_environment(self) -> None:
        """
        Load Jinja2 Environment từ template directory.
        
        Template directory structure theo CORE_PACK_SPECIFICATION.md:
        stacks/{stack}/core/<cp-name>/
            service.py.jinja2
            <support>.py.jinja2
        
        Nếu template directory không tồn tại (ví dụ: stack chưa có templates),
        tạo empty environment để avoid crashes.
        """
        # Xác định đường dẫn template directory
        # Ưu tiên: stacks/{stack}/core/ (new structure)
        stacks_dir = self._get_stacks_directory()
        core_dir = stacks_dir / self.stack / "core"
        
        # Fallback: stacks/{stack}/templates/ (old structure)
        templates_dir = stacks_dir / self.stack / "templates"
        
        if core_dir.exists():
            self._template_dir = core_dir
        elif templates_dir.exists():
            self._template_dir = templates_dir
        else:
            # Template directory không tồn tại — tạo empty environment
            self._template_dir = core_dir
            self._template_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def _template_dir(self) -> Optional[Path]:
        """Getter cho _template_dir."""
        return self._template_dir_value
    
    @_template_dir.setter
    def _template_dir(self, value: Optional[Path]) -> None:
        """
        Setter cho _template_dir — reinitialize environment khi directory thay đổi.
        
        Dùng cho test: khi test set emitter._template_dir = tmp_path, environment
        sẽ được reload với directory mới.
        
        Args:
            value: New template directory path
        """
        self._template_dir_value = value
        # Reinitialize environment với directory mới
        if value and value.exists():
            self.environment = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(value)),
                autoescape=True,
                undefined=jinja2.Undefined,
            )
        else:
            self.environment = jinja2.Environment(
                loader=jinja2.BaseLoader(),
                autoescape=True,
                undefined=jinja2.Undefined,
            )
    
    def _get_stacks_directory(self) -> Path:
        """
        Lấy đường dẫn đến stacks directory.
        
        Stacks directory nằm cùng cấp với module midicoder.
        
        Returns:
            Path đến stacks/ directory
        """
        # midicoder/ là package directory
        package_dir = Path(__file__).resolve().parent.parent
        return package_dir / "stacks"
    
    def render(self, template_path: str, context: dict[str, Any]) -> str:
        """
        Render template với context.
        
        Load template từ template directory và render với context provided.
        Context thường chứa MIR metadata (entities, commands, queries, events)
        và/hoặc entity/command/query cụ thể.
        
        Args:
            template_path: Path template tương đối so với template directory
                          (ví dụ: "main.py.jinja2", "db/model.py.jinja2")
            context: Template context — MIR metadata và/hoặc specific entity data
        
        Returns:
            Rendered content string
        
        Raises:
            MidicoderError: Khi template không tìm thấy (CODE_TEMPLATE_NOT_FOUND)
                           hoặc render fail (TEMPLATE_RENDER_FAILED)
        """
        if self.environment is None:
            EM.raise_error(
                ErrorCode.TEMPLATE_RENDER_FAILED,
                error_type="EnvironmentNotInitialized",
                template=template_path
            )
        
        try:
            template = self.environment.get_template(template_path)
        except jinja2.TemplateNotFound:
            EM.raise_error(
                ErrorCode.CODE_TEMPLATE_NOT_FOUND,
                template=template_path,
                stack=self.stack
            )
        except Exception as e:
            EM.raise_error(
                ErrorCode.TEMPLATE_RENDER_FAILED,
                template=template_path,
                error_type=type(e).__name__
            )
        
        try:
            return template.render(**context)
        except Exception as e:
            EM.raise_error(
                ErrorCode.TEMPLATE_RENDER_FAILED,
                template=template_path,
                error_type=type(e).__name__,
                original_error=str(e)
            )
    
    def emit(
        self, 
        file_specs: list[Any], 
        output_dir: Path
    ) -> list[GeneratedFile]:
        """
        Emit generated files từ FileSpecs ra output directory.
        
        Iterate qua danh sách FileSpecs, render template cho mỗi spec,
        và write content ra file trong output directory.
        
        Args:
            file_specs: List của FileSpec instances (từ ImplementationPlan)
            output_dir: Output directory path
        
        Returns:
            List của GeneratedFile instances (files đã generate)
        """
        generated_files: list[GeneratedFile] = []
        
        for spec in file_specs:
            # Lấy attributes từ FileSpec
            file_path = spec.path
            template = spec.template
            file_type = spec.file_type
            context = spec.context
            
            # Render template với context
            content = self.render(template, context)
            
            # Tạo output file path
            full_path = output_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content ra file
            full_path.write_text(content, encoding="utf-8")
            
            generated_files.append(GeneratedFile(
                path=file_path,
                content=content,
                file_type=file_type,
                template=template,
            ))
        
        return generated_files