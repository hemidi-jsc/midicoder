"""
Pydantic models cho data validation trong storage module.

Cung cấp type validation cho:
- Brief data
- Artifact data
- Decision data
- Lineage data

Q24=A: Thêm Pydantic cho type safety và auto validation.
"""

from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Brief Models
# ============================================================================

class BriefData(BaseModel):
    """
    Model cho brief data validation.

    Fields:
        brief_id: ID duy nhất cho brief
        version: Version number (format: v1.0.0)
        content: Nội dung brief (markdown)
        title: Tiêu đề brief (optional)
        brief_type: Loại brief (working, master, patch, library)
        status: Status của brief
    """

    brief_id: str = Field(..., min_length=1, description="ID duy nhất cho brief")
    version: str = Field(..., min_length=1, description="Version number")
    content: str = Field(..., min_length=1, description="Nội dung brief (markdown)")
    title: Optional[str] = Field(None, description="Tiêu đề brief")
    brief_type: Literal["working", "master", "patch", "library"] = Field(
        default="working", description="Loại brief"
    )
    status: Literal["draft", "clarified", "frozen", "archived"] = Field(
        default="draft", description="Status của brief"
    )

    @field_validator("version")
    @classmethod
    def validate_version_format(cls, v: str) -> str:
        """Validate version format (v1.0.0)."""
        if not v.startswith("v"):
            raise ValueError("Version phải bắt đầu bằng 'v' (ví dụ: v1.0.0)")
        return v


class ClarificationData(BaseModel):
    """
    Model cho clarification Q&A.

    Fields:
        brief_id: Brief ID reference
        round_num: Round number
        question: Câu hỏi
        answer: Câu trả lời
        is_memo: Có phải memo (highlighted memory) không
    """

    brief_id: str = Field(..., min_length=1, description="Brief ID reference")
    round_num: int = Field(..., ge=1, description="Round number")
    question: str = Field(..., min_length=1, description="Câu hỏi")
    answer: str = Field(..., min_length=1, description="Câu trả lời")
    is_memo: bool = Field(default=False, description="Có phải memo không")


class BriefLineageData(BaseModel):
    """
    Model cho brief lineage tracking.

    Fields:
        brief_id: Current brief ID
        parent_brief_id: Parent brief ID
        version: Version number
        change_type: Type of change
        change_description: Description of changes
    """

    brief_id: str = Field(..., min_length=1, description="Current brief ID")
    parent_brief_id: str = Field(..., min_length=1, description="Parent brief ID")
    version: str = Field(..., min_length=1, description="Version number")
    change_type: str = Field(..., min_length=1, description="Type of change")
    change_description: str = Field(..., min_length=1, description="Description of changes")


# ============================================================================
# Artifact Models
# ============================================================================

class ArtifactData(BaseModel):
    """
    Model cho artifact data validation.

    Fields:
        artifact_id: ID duy nhất
        artifact_type: Loại artifact
        name: Tên artifact
        version: Version number
        brief_id: Brief ID reference (optional)
        content: Full content (optional)
        status: Status của artifact
    """

    artifact_id: str = Field(..., min_length=1, description="ID duy nhất")
    artifact_type: Literal["analysis", "contract", "mir", "plan", "code"] = Field(
        ..., description="Loại artifact"
    )
    name: str = Field(..., min_length=1, description="Tên artifact")
    version: str = Field(..., min_length=1, description="Version number")
    brief_id: Optional[str] = Field(None, description="Brief ID reference")
    content: Optional[str] = Field(None, description="Full content")
    status: Literal["pending", "generated", "validated", "applied"] = Field(
        default="pending", description="Status của artifact"
    )
    metadata: Optional[dict] = Field(None, description="Metadata (JSON)")

    @field_validator("version")
    @classmethod
    def validate_version_format(cls, v: str) -> str:
        """Validate version format (v1.0.0)."""
        if not v.startswith("v"):
            raise ValueError("Version phải bắt đầu bằng 'v' (ví dụ: v1.0.0)")
        return v


class ActivityLogData(BaseModel):
    """
    Model cho activity log data.

    Fields:
        action: Hành động
        resource_type: Loại resource (optional)
        resource_id: ID resource (optional)
        details: Chi tiết (optional)
        status: Status (success, failed)
        duration_ms: Thời gian thực hiện ms (optional)
    """

    action: str = Field(..., min_length=1, description="Hành động")
    resource_type: Optional[str] = Field(None, description="Loại resource")
    resource_id: Optional[str] = Field(None, description="ID resource")
    details: Optional[dict] = Field(None, description="Chi tiết")
    status: Literal["success", "failed", "partial"] = Field(
        default="success", description="Status"
    )
    duration_ms: Optional[int] = Field(None, ge=0, description="Thời gian thực hiện (ms)")


# ============================================================================
# Provenance Models
# ============================================================================

class LineageData(BaseModel):
    """
    Model cho lineage data (polymorphic - Q6=B).

    Fields:
        entity_id: Entity ID
        entity_type: Entity type (brief, artifact, code, etc.)
        source_id: Source entity ID
        source_type: Source entity type
        relationship: Relationship type
        metadata: Additional metadata (optional)
    """

    entity_id: str = Field(..., min_length=1, description="Entity ID")
    entity_type: str = Field(..., min_length=1, description="Entity type")
    source_id: str = Field(..., min_length=1, description="Source entity ID")
    source_type: str = Field(..., min_length=1, description="Source entity type")
    relationship: str = Field(..., min_length=1, description="Relationship type")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class DecisionData(BaseModel):
    """
    Model cho architectural decision (DDD-AIF style - Q5=B).

    Fields:
        decision_id: Unique decision ID
        title: Decision title
        status: Status (proposed, accepted, rejected, deprecated)
        description: Decision description
        rationale: Rationale for decision
        consequences: Consequences of decision
        decided_by: Who made the decision
        related_brief_id: Related brief ID (optional)
        related_version: Related version (optional)
    """

    decision_id: str = Field(..., min_length=1, description="Unique decision ID")
    title: str = Field(..., min_length=1, description="Decision title")
    status: Literal["proposed", "accepted", "rejected", "deprecated"] = Field(
        ..., description="Decision status"
    )
    description: Optional[str] = Field(None, description="Decision description")
    rationale: Optional[str] = Field(None, description="Rationale for decision")
    consequences: Optional[str] = Field(None, description="Consequences of decision")
    decided_by: Optional[str] = Field(None, description="Who made the decision")
    related_brief_id: Optional[str] = Field(None, description="Related brief ID")
    related_version: Optional[str] = Field(None, description="Related version")


# ============================================================================
# Context Models
# ============================================================================

class SymbolData(BaseModel):
    """
    Model cho codebase symbol.

    Fields:
        name: Symbol name
        type: Symbol type (function, class, interface, entity)
        file_path: File path
        line_number: Line number (optional)
        signature: Function signature (optional)
        description: Description (optional)
    """

    name: str = Field(..., min_length=1, description="Symbol name")
    type: Literal["function", "class", "interface", "entity", "module", "constant"] = Field(
        ..., description="Symbol type"
    )
    file_path: str = Field(..., min_length=1, description="File path")
    line_number: Optional[int] = Field(None, ge=1, description="Line number")
    signature: Optional[str] = Field(None, description="Function signature")
    description: Optional[str] = Field(None, description="Description")


class FileData(BaseModel):
    """
    Model cho indexed file.

    Fields:
        path: File path
        content_hash: Content hash (optional)
        language: Language (optional)
        size_bytes: File size in bytes (optional)
    """

    path: str = Field(..., min_length=1, description="File path")
    content_hash: Optional[str] = Field(None, description="Content hash (SHA-256)")
    language: Optional[str] = Field(None, description="Programming language")
    size_bytes: Optional[int] = Field(None, ge=0, description="File size in bytes")


class ReferenceData(BaseModel):
    """
    Model cho symbol reference.

    Fields:
        from_symbol: Source symbol name
        from_type: Source symbol type
        from_file: Source file path
        to_symbol: Target symbol name
        to_type: Target symbol type (optional)
        to_file: Target file path (optional)
        ref_type: Reference type (calls, extends, implements, uses)
    """

    from_symbol: str = Field(..., min_length=1, description="Source symbol name")
    from_type: str = Field(..., min_length=1, description="Source symbol type")
    from_file: str = Field(..., min_length=1, description="Source file path")
    to_symbol: str = Field(..., min_length=1, description="Target symbol name")
    to_type: Optional[str] = Field(None, description="Target symbol type")
    to_file: Optional[str] = Field(None, description="Target file path")
    ref_type: Literal["calls", "extends", "implements", "uses", "imports", "depends_on"] = Field(
        ..., description="Reference type"
    )


# ============================================================================
# Export all
# ============================================================================

__all__ = [
    # Brief models
    "BriefData",
    "ClarificationData",
    "BriefLineageData",
    # Artifact models
    "ArtifactData",
    "ActivityLogData",
    # Provenance models
    "LineageData",
    "DecisionData",
    # Context models
    "SymbolData",
    "FileData",
    "ReferenceData",
]