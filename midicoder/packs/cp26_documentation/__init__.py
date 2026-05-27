# coding: utf-8
"""
CP26: Documentation Generator.

Author: Midicoder Team
Version: 1.0.0
"""

from midicoder.packs.cp26_documentation.models import (
    ApiDocConfig,
    DocCollection,
    DocPortal,
    DocPortalType,
    DocSection,
)
from midicoder.packs.cp26_documentation.parser import DocParser
from midicoder.packs.cp26_documentation.fastapi import FastAPIDocEmitter
from midicoder.packs.cp26_documentation.nestjs import NestJSDocEmitter
from midicoder.packs.cp26_documentation.angular import AngularDocEmitter
from midicoder.packs.cp26_documentation.react import ReactDocEmitter
from midicoder.packs.cp26_documentation.recipes import (
    auto_generate_docs_from_mir,
    generate_api_docs,
    generate_component_docs,
    generate_project_docs,
)

__all__ = [
    "AngularDocEmitter",
    "ApiDocConfig",
    "auto_generate_docs_from_mir",
    "DocCollection",
    "DocParser",
    "DocPortal",
    "DocPortalType",
    "DocSection",
    "FastAPIDocEmitter",
    "generate_api_docs",
    "generate_component_docs",
    "generate_project_docs",
    "NestJSDocEmitter",
    "ReactDocEmitter",
]
