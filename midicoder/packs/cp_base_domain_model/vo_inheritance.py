"""
Value Object Inheritance Resolver

Resolver cho extends hierarchy trong Value Objects.
Support multi-level inheritance với field merging.

Author: Midicoder Team
Version: 2.0.0
"""

from dataclasses import dataclass, field
from typing import Optional

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM
from midicoder.dsl.projection import (
    FieldDefinition,
    MethodDefinition,
    ValidationRule,
    ExtendedValueObjectParams,
)


@dataclass
class InheritanceChain:
    """
    Inheritance chain cho một Value Object.

    Attributes:
        vo_id: VO ID
        chain: Danh sách VO IDs từ root đến current
        root: Root VO ID
        depth: Chiều sâu của inheritance
    """

    vo_id: str
    chain: list[str] = field(default_factory=list)
    root: Optional[str] = None
    depth: int = 0

    def __post_init__(self) -> None:
        """Initialize computed fields."""
        if self.chain:
            self.root = self.chain[0] if self.chain else None
            self.depth = len(self.chain) - 1


class InheritanceResolver:
    """
    Resolver cho Value Object inheritance.

    Process:
    1. Build inheritance chain từ extends references
    2. Detect circular inheritance
    3. Merge fields từ tất cả parent VOs
    4. Merge methods và validation rules

    Usage:
        resolver = InheritanceResolver(vo_map)
        chain = resolver.resolve_chain("BillingAddress")
        merged = resolver.merge_vo("BillingAddress", chain)
    """

    def __init__(self, vo_map: dict[str, ExtendedValueObjectParams]) -> None:
        """
        Initialize resolver.

        Args:
            vo_map: Map của tất cả VOs (id → params)
        """
        self.vo_map = vo_map
        self._chain_cache: dict[str, InheritanceChain] = {}

    def resolve_chain(self, vo_id: str) -> InheritanceChain:
        """
        Resolve inheritance chain cho một VO.

        Args:
            vo_id: VO ID để resolve

        Returns:
            InheritanceChain từ root đến current VO

        Raises:
            ValueError: Nếu circular inheritance detected
            KeyError: Nếu VO không tìm thấy
        """
        # Check cache
        if vo_id in self._chain_cache:
            return self._chain_cache[vo_id]

        # Build chain
        chain = []
        visited = set()
        current_id = vo_id

        while current_id:
            # Check circular
            if current_id in visited:
                EM.raise_error(
                    ErrorCode.B01_VALUE_OBJECT_NOT_FOUND,
                    cycle=f"{' → '.join(chain)} → {current_id}",
                )

            visited.add(current_id)
            chain.append(current_id)

            # Get parent
            if current_id not in self.vo_map:
                EM.raise_error(
                    ErrorCode.B01_VALUE_OBJECT_NOT_FOUND,
                    vo_id=current_id,
                )

            vo_params = self.vo_map[current_id]
            current_id = vo_params.get("extends")

        # Reverse để root first
        chain.reverse()

        # Create chain object
        inheritance_chain = InheritanceChain(
            vo_id=vo_id,
            chain=chain,
            root=chain[0] if chain else None,
            depth=len(chain) - 1,
        )

        # Cache
        self._chain_cache[vo_id] = inheritance_chain

        return inheritance_chain

    def merge_vo(
        self,
        vo_id: str,
        chain: Optional[InheritanceChain] = None
    ) -> ExtendedValueObjectParams:
        """
        Merge VO từ inheritance chain.

        Process:
        1. Resolve chain (nếu chưa có)
        2. Merge fields (child overrides parent)
        3. Merge methods (child overrides parent)
        4. Merge validation rules (cumulative)

        Args:
            vo_id: VO ID để merge
            chain: Pre-resolved chain (optional)

        Returns:
            Merged VO params
        """
        if chain is None:
            chain = self.resolve_chain(vo_id)

        if not chain.chain:
            return self.vo_map.get(vo_id, {})

        # Start with root
        merged = self._deep_copy(self.vo_map.get(chain.chain[0], {}))

        # Merge each level
        for parent_id in chain.chain[1:]:
            child_params = self.vo_map.get(parent_id, {})
            merged = self._merge_params(merged, child_params)

        return merged

    def _merge_params(
        self,
        parent: ExtendedValueObjectParams,
        child: ExtendedValueObjectParams
    ) -> ExtendedValueObjectParams:
        """
        Merge parent và child VO params.

        Child values override parent values.
        Lists are merged (not replaced).

        Args:
            parent: Parent VO params
            child: Child VO params

        Returns:
            Merged params
        """
        merged = self._deep_copy(parent)

        # Merge scalar fields (child overrides)
        scalar_fields = ["id", "description", "immutable", "comparable", "source"]
        for field_name in scalar_fields:
            if field_name in child:
                merged[field_name] = child[field_name]

        # Merge lists
        if "fields" in child:
            merged["fields"] = self._merge_fields(
                parent.get("fields", []),
                child["fields"]
            )

        if "methods" in child:
            merged["methods"] = self._merge_methods(
                parent.get("methods", []),
                child["methods"]
            )

        if "validation_rules" in child:
            merged["validation_rules"] = self._merge_rules(
                parent.get("validation_rules", []),
                child["validation_rules"]
            )

        if "tags" in child:
            merged["tags"] = list(set(parent.get("tags", []) + child["tags"]))

        if "compliance" in child:
            merged["compliance"] = parent.get("compliance", []) + child["compliance"]

        return merged

    def _merge_fields(
        self,
        parent_fields: list[FieldDefinition],
        child_fields: list[FieldDefinition]
    ) -> list[FieldDefinition]:
        """
        Merge fields từ parent và child.

        Child fields override parent fields với cùng name.
        Order: parent fields first, then child-added fields.

        Args:
            parent_fields: Parent fields
            child_fields: Child fields

        Returns:
            Merged fields
        """
        # Build map từ parent
        field_map = {f["name"]: self._deep_copy(f) for f in parent_fields}

        # Override với child fields
        child_names = set()
        for child_field in child_fields:
            field_name = child_field["name"]
            child_names.add(field_name)

            if field_name in field_map:
                # Override existing field
                field_map[field_name] = self._deep_copy(child_field)
            else:
                # New field from child
                field_map[field_name] = self._deep_copy(child_field)

        # Return in order: parent order preserved, new fields at end
        result = []
        for parent_field in parent_fields:
            if parent_field["name"] in field_map:  # pragma: no branch  # always True by construction
                result.append(field_map[parent_field["name"]])

        for child_field in child_fields:
            if child_field["name"] not in child_names or child_field["name"] not in [f["name"] for f in result]:
                result.append(child_field)

        return result

    def _merge_methods(
        self,
        parent_methods: list[MethodDefinition],
        child_methods: list[MethodDefinition]
    ) -> list[MethodDefinition]:
        """
        Merge methods từ parent và child.

        Child methods override parent methods với cùng name.

        Args:
            parent_methods: Parent methods
            child_methods: Child methods

        Returns:
            Merged methods
        """
        method_map = {m["name"]: self._deep_copy(m) for m in parent_methods}

        for child_method in child_methods:
            method_map[child_method["name"]] = self._deep_copy(child_method)

        return list(method_map.values())

    def _merge_rules(
        self,
        parent_rules: list[ValidationRule],
        child_rules: list[ValidationRule]
    ) -> list[ValidationRule]:
        """
        Merge validation rules từ parent và child.

        Rules are cumulative (child can add new rules).
        Child rules override parent rules với cùng name.

        Args:
            parent_rules: Parent rules
            child_rules: Child rules

        Returns:
            Merged rules
        """
        rule_map = {r["name"]: self._deep_copy(r) for r in parent_rules}

        for child_rule in child_rules:
            rule_map[child_rule["name"]] = self._deep_copy(child_rule)

        return list(rule_map.values())

    def _deep_copy(self, obj: any) -> any:
        """
        Deep copy an object.

        Args:
            obj: Object to copy

        Returns:
            Deep copied object
        """
        if obj is None:
            return None

        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}

        if isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]

        return obj

    def get_inherited_fields(self, vo_id: str) -> dict[str, list[str]]:
        """
        Get field inheritance info cho một VO.

        Returns:
            Map của field_name → list of VO IDs mà field xuất hiện

        Args:
            vo_id: VO ID

        Returns:
            Field inheritance map
        """
        chain = self.resolve_chain(vo_id)
        field_sources: dict[str, list[str]] = {}

        for vo_in_chain in chain.chain:
            vo_params = self.vo_map.get(vo_in_chain, {})
            for field_def in vo_params.get("fields", []):
                field_name = field_def["name"]
                if field_name not in field_sources:
                    field_sources[field_name] = []
                field_sources[field_name].append(vo_in_chain)

        return field_sources

    def detect_all_cycles(self) -> list[list[str]]:
        """
        Detect tất cả circular inheritance trong vo_map.

        Returns:
            List of cycles (mỗi cycle là list of VO IDs)
        """
        cycles = []

        for vo_id in self.vo_map:
            try:
                self.resolve_chain(vo_id)
            except ValueError as e:  # pragma: no cover  # resolve_chain raises MidicoderError, not ValueError
                if "Circular inheritance" in str(e):
                    # Extract cycle from error message
                    cycle_str = str(e).split(": ")[1] if ": " in str(e) else str(e)
                    cycle = cycle_str.replace(" →", "").split("→")
                    cycles.append([c.strip() for c in cycle])

        return cycles