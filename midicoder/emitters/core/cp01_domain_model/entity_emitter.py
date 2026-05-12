"""
Mô-đun base class cho Entity Emitter.

Cung cấp:
- EntityEmitter: Abstract base class định nghĩa interface
- Helper methods cho template rendering và code generation

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from .models import Entity


class EntityEmitter(ABC):
    """
    Abstract base class cho Entity Emitter.
    
    Tất cả concrete emitters (FastAPI, NestJS) phải implement:
    - emit(): Generate code từ Entity object
    - _build_template_context(): Build context cho Jinja2 template
    
    Usage:
        class MyEmitter(EntityEmitter):
            def emit(self, entity: Entity) -> str:
                context = self._build_template_context(entity)
                return self.render_template("entity.jinja2", context)
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo EntityEmitter.
        
        Args:
            stack_dir: Đường dẫn đến templates directory
        """
        self.stack_dir = stack_dir
        self._init_template_env()

    def _init_template_env(self) -> None:
        """Initialize Jinja2 environment."""
        self.template_env = Environment(
            loader=FileSystemLoader(str(self.stack_dir)),
            autoescape=True,
        )

    @abstractmethod
    def emit(self, entity: Entity, all_entities: list[Entity]) -> str:
        """
        Generate code từ Entity object.
        
        Args:
            entity: Entity để emit
            all_entities: Danh sách tất cả entities (để resolve relationships)
            
        Returns:
            Generated code string
        """
        pass

    @abstractmethod
    def _build_template_context(
        self,
        entity: Entity,
        all_entities: list[Entity],
    ) -> dict[str, Any]:
        """
        Build template context cho Jinja2 rendering.
        
        Args:
            entity: Entity để build context
            all_entities: Danh sách tất cả entities
            
        Returns:
            Template context dictionary
        """
        pass

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render Jinja2 template với context.
        
        Args:
            template_name: Tên template file
            context: Template context
            
        Returns:
            Rendered template string
        """
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            # Fallback: Generate code manually
            return self._generate_code_fallback(context, e)

    @abstractmethod
    def _generate_code_fallback(
        self,
        context: dict[str, Any],
        error: Exception,
    ) -> str:
        """
        Fallback code generation nếu template rendering failed.
        
        Args:
            context: Template context
            error: Error xảy ra khi render template
            
        Returns:
            Generated code string
        """
        pass

    def get_table_name(self, entity_id: str) -> str:
        """
        Convert entity ID sang table name (snake_case, plural).
        
        Args:
            entity_id: Entity ID (PascalCase)
            
        Returns:
            Table name (snake_case, plural)
            
        Ví dụ:
            >>> emitter = ...
            >>> emitter.get_table_name("User")
            "users"
            >>> emitter.get_table_name("OrderItem")
            "order_items"
        """
        # Convert PascalCase to snake_case
        snake_case = ""
        for i, char in enumerate(entity_id):
            if i > 0 and char.isupper() and entity_id[i - 1].islower():
                snake_case += "_"
            snake_case += char.lower()
        
        # Pluralize
        if not snake_case.endswith("s"):
            snake_case += "s"
        
        return snake_case

    def to_snake_case(self, name: str) -> str:
        """
        Convert string sang snake_case.
        
        Args:
            name: Tên cần convert
            
        Returns:
            Snake case string
        """
        import re
        
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def find_entity_by_id(
        self,
        entity_id: str,
        all_entities: list[Entity],
    ) -> Entity | None:
        """
        Tìm entity theo ID (case-insensitive).
        
        Args:
            entity_id: Entity ID để tìm
            all_entities: Danh sách tất cả entities
            
        Returns:
            Entity nếu tìm thấy, None nếu không
        """
        for entity in all_entities:
            if entity.id.lower() == entity_id.lower():
                return entity
        return None