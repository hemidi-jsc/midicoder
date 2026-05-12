# coding: utf-8
"""
UI Component Generator (CP19).

Module này cung cấp các models và emitters để sinh reusable UI components
từ entity definitions: form fields, data tables, card lists, dialogs.

Models:
    - ComponentSpec: Spec cho UI component
    - FormFieldSpec: Spec cho form field
    - TableSpec: Spec cho data table
    - ComponentType: Enum (FORM_FIELD, DATA_TABLE, CARD_LIST, DIALOG)
    - FieldType: Enum (TEXT, NUMBER, EMAIL, DATE, BOOLEAN, SELECT, TEXTAREA, RADIO, SWITCH)

Emitters:
    - AngularUIEmitter: Angular components
    - ReactUIEmitter: React components
    - FastAPIUIEmitter: FastAPI Pydantic schemas
    - NestJSUIEmitter: NestJS DTOs + ValidationPipe
"""

from midicoder.emitters.core.cp19_ui_components.models import (
    ComponentType,
    FieldType,
    TableColumn,
    FormFieldSpec,
    TableSpec,
    ComponentSpec,
)

__all__ = [
    "ComponentType",
    "FieldType",
    "TableColumn",
    "FormFieldSpec",
    "TableSpec",
    "ComponentSpec",
]
