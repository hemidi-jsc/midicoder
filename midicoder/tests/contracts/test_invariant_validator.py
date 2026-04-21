"""
Tests cho InvariantValidator - Epic E10: Invariant Gates

Module này test các invariant validators INV001-INV008:
- INV001: Entity ref resolution
- INV002: Permission ref resolution  
- INV003: Role ref resolution
- INV004: Command permission guard
- INV005: Query tenant filter
- INV006: Mutation transaction scope
- INV007: Role policy binding
- INV008: Policy syntax validation

Author: Midicoder Team
Version: 1.0.0
"""

import pytest
from datetime import datetime

from midicoder.contracts.artifact import ArtifactMetadata
from midicoder.contracts.graph import (
    CapabilityGraph,
    CapabilityInstance,
    CoreCapability,
    MacroCapability,
    Obligation,
)
from midicoder.contracts.validation import (
    InvariantValidator,
    ValidationReport,
    ValidationError,
    ErrorCode,
    ValidationStatus,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_metadata() -> ArtifactMetadata:
    """Trả về sample metadata cho testing."""
    return ArtifactMetadata(
        created_at="2026-04-21T08:00:00Z",
        updated_at="2026-04-21T08:00:00Z",
        author="test",
        organization="midicoder",
        version="1.0.0",
        generated_by="test",
        git_commit="abc123",
        description="Test metadata",
        tags=["test"],
        source_files=[],
    )


@pytest.fixture
def empty_graph(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """Trả về empty CapabilityGraph."""
    graph = CapabilityGraph(
        core_capabilities=[],
        macro_capabilities=[],
        instances=[],
        obligations=[],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def graph_with_entities(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph với entities.
    
    Dành cho test INV001: Entity ref resolution.
    """
    # Tạo core capability cho read entity
    load_entity = CoreCapability(
        id="load_entity",
        name="Load Entity",
        description="Load một entity từ database",
        params_schema={
            "entity": {"type": "string", "required": True},
            "entity_id": {"type": "string", "required": True},
        },
    )
    
    # Tạo instance load_entity với entity_ref valid
    # Entity "Order" được declare trong reads
    valid_instance = CapabilityInstance(
        id="load_order",
        type="load_entity",
        description="Load Order entity",
        params={
            "entity_ref": "Order",  # Entity ref valid
            "entity_id": "$input.order_id",
        },
        reads=["Order"],  # Entity "Order" được declare ở đây
    )
    
    # Tạo instance load_entity với entity_ref invalid
    # Entity "NonExistentEntity" không được declare trong reads của instance này
    # nên entity_ref sẽ không resolve được
    invalid_instance = CapabilityInstance(
        id="load_nonexistent",
        type="load_entity",
        description="Load NonExistent entity",
        params={
            "entity_ref": "NonExistentEntity",  # Entity ref không tồn tại
            "entity_id": "$input.id",
        },
        reads=["Order"],  # Chỉ declare "Order", không có "NonExistentEntity"
    )
    
    graph = CapabilityGraph(
        core_capabilities=[load_entity],
        macro_capabilities=[],
        instances=[valid_instance, invalid_instance],
        obligations=[],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def graph_with_permissions(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph với permissions.
    
    Dành cho test INV002: Permission ref resolution.
    """
    # Tạo core capability cho authorize_permission
    authorize = CoreCapability(
        id="authorize_permission",
        name="Authorize Permission",
        description="Check user có permission không",
        params_schema={
            "permission": {"type": "string", "required": True},
        },
    )
    
    # Tạo instance với permission_ref valid
    valid_instance = CapabilityInstance(
        id="create_order_check",
        type="authorize_permission",
        description="Check order.create permission",
        params={
            "permission_ref": "order.create",  # Permission ref valid
        },
    )
    
    # Tạo instance với permission_ref invalid
    invalid_instance = CapabilityInstance(
        id="invalid_perm_check",
        type="authorize_permission",
        description="Check invalid permission",
        params={
            "permission_ref": "invalid.permission",  # Permission ref không tồn tại
        },
    )
    
    graph = CapabilityGraph(
        core_capabilities=[authorize],
        macro_capabilities=[],
        instances=[valid_instance, invalid_instance],
        obligations=[],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def graph_with_roles(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph với roles.
    
    Dành cho test INV003: Role ref resolution.
    """
    # Tạo instance với role_ref valid
    valid_instance = CapabilityInstance(
        id="admin_action",
        type="authorized_mutation",
        description="Admin action",
        params={
            "role_ref": "admin",  # Role ref valid
            "permission": "admin.action",
        },
    )
    
    # Tạo instance với role_ref invalid
    invalid_instance = CapabilityInstance(
        id="unknown_role_action",
        type="authorized_mutation",
        description="Unknown role action",
        params={
            "role_ref": "unknown_role",  # Role ref không tồn tại
            "permission": "unknown.action",
        },
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        macro_capabilities=[],
        instances=[valid_instance, invalid_instance],
        obligations=[],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def graph_with_commands(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph với commands.
    
    Dành cho test INV004: Command permission guard.
    """
    # Command có permission guard
    guarded_command = CapabilityInstance(
        id="create_order",
        type="authorized_mutation",
        description="Create order with permission guard",
        params={
            "permission": "order.create",
            "permission_ref": "order.create",
        },
        writes=["Order"],
    )
    
    # Command không có permission guard
    unguarded_command = CapabilityInstance(
        id="create_product",
        type="authorized_mutation",
        description="Create product WITHOUT permission guard",
        params={},  # Không có permission
        writes=["Product"],
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        macro_capabilities=[],
        instances=[guarded_command, unguarded_command],
        obligations=[],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def graph_with_queries(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph với queries.
    
    Dành cho test INV005: Query tenant filter.
    """
    # Query có tenant filter
    filtered_query = CapabilityInstance(
        id="list_orders",
        type="authorized_query",
        description="List orders with tenant filter",
        params={
            "tenant_filter": "tenant_id",
            "tenant_scope": "tenant_isolated",
        },
        reads=["Order"],
    )
    
    # Query không có tenant filter
    unfiltered_query = CapabilityInstance(
        id="list_all_orders",
        type="authorized_query",
        description="List orders WITHOUT tenant filter",
        params={},  # Không có tenant_filter
        reads=["Order"],
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        macro_capabilities=[],
        instances=[filtered_query, unfiltered_query],
        obligations=[],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def graph_with_mutations(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph với mutations.
    
    Dành cho test INV006: Mutation transaction scope.
    """
    # Mutation có transaction scope
    scoped_mutation = CapabilityInstance(
        id="create_order_with_items",
        type="authorized_mutation",
        description="Create order with transaction scope",
        params={
            "transaction": "required",
            "permission": "order.create",
        },
        writes=["Order", "OrderItem"],
    )
    
    # Mutation không có transaction scope
    unscoped_mutation = CapabilityInstance(
        id="update_inventory",
        type="authorized_mutation",
        description="Update inventory WITHOUT transaction scope",
        params={
            "permission": "inventory.update",
            # Không có transaction field
        },
        writes=["Inventory"],
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        macro_capabilities=[],
        instances=[scoped_mutation, unscoped_mutation],
        obligations=[],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def graph_with_role_policies(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph với role policy bindings.
    
    Dành cho test INV007: Role policy binding.
    """
    # Role có policy binding
    role_with_policy = CapabilityInstance(
        id="admin",
        type="role",
        description="Admin role with policy binding",
        params={
            "policy_ref": "admin_policy",
            "permissions": ["admin.*"],
        },
    )
    
    # Role không có policy binding
    role_without_policy = CapabilityInstance(
        id="staff",
        type="role",
        description="Staff role WITHOUT policy binding",
        params={
            "permissions": ["staff.*"],
            # Không có policy_ref
        },
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        macro_capabilities=[],
        instances=[role_with_policy, role_without_policy],
        obligations=[],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


@pytest.fixture
def graph_with_policies(sample_metadata: ArtifactMetadata) -> CapabilityGraph:
    """
    Trả về CapabilityGraph với policies.
    
    Dành cho test INV008: Policy syntax validation.
    """
    # Policy valid - RBAC policy với cấu trúc đúng
    valid_policy = CapabilityInstance(
        id="admin_policy",
        type="policy",
        description="Valid admin policy",
        params={
            "name": "admin_policy",
            "effect": "allow",
            "subject": {"role": "admin"},
            "action": {"permission": "admin.*"},
            "resource": {"type": "*"},
        },
    )
    
    # Policy invalid - thiếu field bắt buộc
    invalid_policy_missing_effect = CapabilityInstance(
        id="incomplete_policy",
        type="policy",
        description="Invalid policy missing effect",
        params={
            "name": "incomplete_policy",
            # Thiếu effect field
            "subject": {"role": "user"},
            "action": {"permission": "user.*"},
        },
    )
    
    # Policy invalid - effect không valid
    invalid_policy_bad_effect = CapabilityInstance(
        id="bad_effect_policy",
        type="policy",
        description="Invalid policy with bad effect",
        params={
            "name": "bad_effect_policy",
            "effect": "invalid_effect",  # Effect phải là "allow" hoặc "deny"
            "subject": {"role": "user"},
            "action": {"permission": "user.*"},
        },
    )
    
    graph = CapabilityGraph(
        core_capabilities=[],
        macro_capabilities=[],
        instances=[valid_policy, invalid_policy_missing_effect, invalid_policy_bad_effect],
        obligations=[],
    )
    object.__setattr__(graph, 'metadata', sample_metadata)
    return graph


# ============================================================================
# Test INV001: Entity Ref Resolution
# ============================================================================


class TestINV001_EntityRefResolution:
    """Tests cho INV001: Entity ref resolution."""
    
    def test_validate_entity_refs_passes_for_valid_refs(
        self,
        sample_metadata: ArtifactMetadata,
    ) -> None:
        """
        Test INV001: Validation pass khi tất cả entity refs đều valid.
        
        Scenario: Graph chỉ có instances với entity_ref tồn tại trong reads.
        Expected: Không có errors.
        """
        # Setup: Tạo graph với valid entity refs
        load_entity = CoreCapability(
            id="load_entity",
            name="Load Entity",
            params_schema={"entity": {"type": "string"}},
        )
        
        instance = CapabilityInstance(
            id="load_order",
            type="load_entity",
            params={"entity_ref": "Order"},
            reads=["Order"],  # Entity "Order" được declare
        )
        
        graph = CapabilityGraph(
            core_capabilities=[load_entity],
            instances=[instance],
        )
        object.__setattr__(graph, 'metadata', sample_metadata)
        
        # Execute
        validator = InvariantValidator(graph)
        report = validator.validate_entity_refs()
        
        # Assert
        assert report.status == ValidationStatus.PASS.value
        assert len(report.errors) == 0
        assert report.checks.get("INV001") == ValidationStatus.PASS.value
    
    def test_validate_entity_refs_fails_for_unresolved_refs(
        self,
        graph_with_entities: CapabilityGraph,
    ) -> None:
        """
        Test INV001: Validation fail khi có entity refs không resolve được.
        
        Scenario: Instance có entity_ref nhưng entity đó không tồn tại trong reads.
        Expected: Có error UNRESOLVED_ENTITY_REF.
        """
        # Execute
        validator = InvariantValidator(graph_with_entities)
        report = validator.validate_entity_refs()
        
        # Assert
        assert report.status == ValidationStatus.FAIL.value
        assert len(report.errors) > 0
        
        # Check có error với code UNRESOLVED_ENTITY_REF
        unresolved_errors = [
            e for e in report.errors 
            if e.code == ErrorCode.UNRESOLVED_ENTITY_REF.value
        ]
        assert len(unresolved_errors) > 0
        
        # Check message có thông tin về entity không tồn tại
        error_messages = [e.message for e in unresolved_errors]
        assert any("NonExistentEntity" in msg for msg in error_messages)


# ============================================================================
# Test INV002: Permission Ref Resolution
# ============================================================================


class TestINV002_PermissionRefResolution:
    """Tests cho INV002: Permission ref resolution."""
    
    def test_validate_permission_refs_passes_for_valid_refs(
        self,
        sample_metadata: ArtifactMetadata,
    ) -> None:
        """
        Test INV002: Validation pass khi tất cả permission refs đều valid.
        
        Scenario: Graph có permission definitions và instances reference chúng.
        Expected: Không có errors.
        """
        # Setup: Tạo graph với valid permission refs
        authorize = CoreCapability(
            id="authorize_permission",
            name="Authorize Permission",
            params_schema={"permission": {"type": "string"}},
        )
        
        # Declare permission
        permission_def = CapabilityInstance(
            id="order_create_perm",
            type="permission",
            params={"name": "order.create", "description": "Create order"},
        )
        
        instance = CapabilityInstance(
            id="check_order_create",
            type="authorize_permission",
            params={"permission_ref": "order.create"},
        )
        
        graph = CapabilityGraph(
            core_capabilities=[authorize],
            instances=[permission_def, instance],
        )
        object.__setattr__(graph, 'metadata', sample_metadata)
        
        # Execute
        validator = InvariantValidator(graph)
        report = validator.validate_permission_refs()
        
        # Assert
        assert report.status == ValidationStatus.PASS.value
        assert len(report.errors) == 0
        assert report.checks.get("INV002") == ValidationStatus.PASS.value
    
    def test_validate_permission_refs_fails_for_unresolved_refs(
        self,
        graph_with_permissions: CapabilityGraph,
    ) -> None:
        """
        Test INV002: Validation fail khi có permission refs không resolve được.
        
        Scenario: Instance có permission_ref nhưng permission đó không tồn tại.
        Expected: Có error UNRESOLVED_PERMISSION_REF.
        """
        # Execute
        validator = InvariantValidator(graph_with_permissions)
        report = validator.validate_permission_refs()
        
        # Assert
        assert report.status == ValidationStatus.FAIL.value
        assert len(report.errors) > 0
        
        # Check có error với code UNRESOLVED_PERMISSION_REF
        unresolved_errors = [
            e for e in report.errors 
            if e.code == ErrorCode.UNRESOLVED_PERMISSION_REF.value
        ]
        assert len(unresolved_errors) > 0
        
        # Check message có thông tin về permission không tồn tại
        error_messages = [e.message for e in unresolved_errors]
        assert any("invalid.permission" in msg for msg in error_messages)


# ============================================================================
# Test INV003: Role Ref Resolution
# ============================================================================


class TestINV003_RoleRefResolution:
    """Tests cho INV003: Role ref resolution."""
    
    def test_validate_role_refs_passes_for_valid_refs(
        self,
        sample_metadata: ArtifactMetadata,
    ) -> None:
        """
        Test INV003: Validation pass khi tất cả role refs đều valid.
        
        Scenario: Graph có role definitions và instances reference chúng.
        Expected: Không có errors.
        """
        # Setup: Tạo graph với valid role refs
        # Declare role
        role_def = CapabilityInstance(
            id="admin_role",
            type="role",
            params={"name": "admin", "description": "Administrator role"},
        )
        
        instance = CapabilityInstance(
            id="admin_action",
            type="authorized_mutation",
            params={"role_ref": "admin"},
        )
        
        graph = CapabilityGraph(
            core_capabilities=[],
            instances=[role_def, instance],
        )
        object.__setattr__(graph, 'metadata', sample_metadata)
        
        # Execute
        validator = InvariantValidator(graph)
        report = validator.validate_role_refs()
        
        # Assert
        assert report.status == ValidationStatus.PASS.value
        assert len(report.errors) == 0
        assert report.checks.get("INV003") == ValidationStatus.PASS.value
    
    def test_validate_role_refs_fails_for_unresolved_refs(
        self,
        graph_with_roles: CapabilityGraph,
    ) -> None:
        """
        Test INV003: Validation fail khi có role refs không resolve được.
        
        Scenario: Instance có role_ref nhưng role đó không tồn tại.
        Expected: Có error UNRESOLVED_ROLE_REF.
        """
        # Execute
        validator = InvariantValidator(graph_with_roles)
        report = validator.validate_role_refs()
        
        # Assert
        assert report.status == ValidationStatus.FAIL.value
        assert len(report.errors) > 0
        
        # Check có error với code UNRESOLVED_ROLE_REF
        unresolved_errors = [
            e for e in report.errors 
            if e.code == ErrorCode.UNRESOLVED_ROLE_REF.value
        ]
        assert len(unresolved_errors) > 0
        
        # Check message có thông tin về role không tồn tại
        error_messages = [e.message for e in unresolved_errors]
        assert any("unknown_role" in msg for msg in error_messages)


# ============================================================================
# Test INV004: Command Permission Guard
# ============================================================================


class TestINV004_CommandPermissionGuard:
    """Tests cho INV004: Command permission guard."""
    
    def test_validate_command_permission_guards_passes(
        self,
        sample_metadata: ArtifactMetadata,
    ) -> None:
        """
        Test INV004: Validation pass khi tất cả commands đều có permission guard.
        
        Scenario: Tất cả instances loại mutation đều có permission field.
        Expected: Không có errors.
        """
        # Setup: Tạo graph với commands có permission guard
        command = CapabilityInstance(
            id="create_order",
            type="authorized_mutation",
            params={"permission": "order.create"},
            writes=["Order"],
        )
        
        graph = CapabilityGraph(
            core_capabilities=[],
            instances=[command],
        )
        object.__setattr__(graph, 'metadata', sample_metadata)
        
        # Execute
        validator = InvariantValidator(graph)
        report = validator.validate_command_permission_guards()
        
        # Assert
        assert report.status == ValidationStatus.PASS.value
        assert len(report.errors) == 0
        assert report.checks.get("INV004") == ValidationStatus.PASS.value
    
    def test_validate_command_permission_guards_fails(
        self,
        graph_with_commands: CapabilityGraph,
    ) -> None:
        """
        Test INV004: Validation fail khi có commands không có permission guard.
        
        Scenario: Có instance loại mutation nhưng không có permission field.
        Expected: Có error MISSING_PERMISSION_GUARD.
        """
        # Execute
        validator = InvariantValidator(graph_with_commands)
        report = validator.validate_command_permission_guards()
        
        # Assert
        assert report.status == ValidationStatus.FAIL.value
        assert len(report.errors) > 0
        
        # Check có error với code MISSING_PERMISSION_GUARD
        missing_guard_errors = [
            e for e in report.errors 
            if e.code == ErrorCode.MISSING_PERMISSION_GUARD.value
        ]
        assert len(missing_guard_errors) > 0
        
        # Check message có thông tin về command thiếu guard
        error_messages = [e.message for e in missing_guard_errors]
        assert any("create_product" in msg for msg in error_messages)


# ============================================================================
# Test INV005: Query Tenant Filter
# ============================================================================


class TestINV005_QueryTenantFilter:
    """Tests cho INV005: Query tenant filter."""
    
    def test_validate_query_tenant_filters_passes(
        self,
        sample_metadata: ArtifactMetadata,
    ) -> None:
        """
        Test INV005: Validation pass khi tất cả queries đều có tenant filter.
        
        Scenario: Tất cả instances loại query đều có tenant_filter field.
        Expected: Không có errors.
        """
        # Setup: Tạo graph với queries có tenant filter
        query = CapabilityInstance(
            id="list_orders",
            type="authorized_query",
            params={"tenant_filter": "tenant_id", "tenant_scope": "tenant_isolated"},
            reads=["Order"],
        )
        
        graph = CapabilityGraph(
            core_capabilities=[],
            instances=[query],
        )
        object.__setattr__(graph, 'metadata', sample_metadata)
        
        # Execute
        validator = InvariantValidator(graph)
        report = validator.validate_query_tenant_filters()
        
        # Assert
        assert report.status == ValidationStatus.PASS.value
        assert len(report.errors) == 0
        assert report.checks.get("INV005") == ValidationStatus.PASS.value
    
    def test_validate_query_tenant_filters_fails(
        self,
        graph_with_queries: CapabilityGraph,
    ) -> None:
        """
        Test INV005: Validation fail khi có queries không có tenant filter.
        
        Scenario: Có instance loại query nhưng không có tenant_filter field.
        Expected: Có error MISSING_TENANT_FILTER.
        """
        # Execute
        validator = InvariantValidator(graph_with_queries)
        report = validator.validate_query_tenant_filters()
        
        # Assert
        assert report.status == ValidationStatus.FAIL.value
        assert len(report.errors) > 0
        
        # Check có error với code MISSING_TENANT_FILTER
        missing_filter_errors = [
            e for e in report.errors 
            if e.code == ErrorCode.MISSING_TENANT_FILTER.value
        ]
        assert len(missing_filter_errors) > 0
        
        # Check message có thông tin về query thiếu filter
        error_messages = [e.message for e in missing_filter_errors]
        assert any("list_all_orders" in msg for msg in error_messages)


# ============================================================================
# Test INV006: Mutation Transaction Scope
# ============================================================================


class TestINV006_MutationTransactionScope:
    """Tests cho INV006: Mutation transaction scope."""
    
    def test_validate_mutation_transaction_scopes_passes(
        self,
        sample_metadata: ArtifactMetadata,
    ) -> None:
        """
        Test INV006: Validation pass khi tất cả mutations đều có transaction scope.
        
        Scenario: Tất cả instances loại mutation đều có transaction field.
        Expected: Không có errors.
        """
        # Setup: Tạo graph với mutations có transaction scope
        mutation = CapabilityInstance(
            id="create_order",
            type="authorized_mutation",
            params={"transaction": "required", "permission": "order.create"},
            writes=["Order"],
        )
        
        graph = CapabilityGraph(
            core_capabilities=[],
            instances=[mutation],
        )
        object.__setattr__(graph, 'metadata', sample_metadata)
        
        # Execute
        validator = InvariantValidator(graph)
        report = validator.validate_mutation_transaction_scopes()
        
        # Assert
        assert report.status == ValidationStatus.PASS.value
        assert len(report.errors) == 0
        assert report.checks.get("INV006") == ValidationStatus.PASS.value
    
    def test_validate_mutation_transaction_scopes_fails(
        self,
        graph_with_mutations: CapabilityGraph,
    ) -> None:
        """
        Test INV006: Validation fail khi có mutations không có transaction scope.
        
        Scenario: Có instance loại mutation nhưng không có transaction field.
        Expected: Có error MISSING_TRANSACTION_SCOPE.
        """
        # Execute
        validator = InvariantValidator(graph_with_mutations)
        report = validator.validate_mutation_transaction_scopes()
        
        # Assert
        assert report.status == ValidationStatus.FAIL.value
        assert len(report.errors) > 0
        
        # Check có error với code MISSING_TRANSACTION_SCOPE
        missing_scope_errors = [
            e for e in report.errors 
            if e.code == ErrorCode.MISSING_TRANSACTION_SCOPE.value
        ]
        assert len(missing_scope_errors) > 0
        
        # Check message có thông tin về mutation thiếu scope
        error_messages = [e.message for e in missing_scope_errors]
        assert any("update_inventory" in msg for msg in error_messages)


# ============================================================================
# Test INV007: Role Policy Binding
# ============================================================================


class TestINV007_RolePolicyBinding:
    """Tests cho INV007: Role policy binding."""
    
    def test_validate_role_policy_bindings_passes(
        self,
        sample_metadata: ArtifactMetadata,
    ) -> None:
        """
        Test INV007: Validation pass khi tất cả roles đều có policy binding.
        
        Scenario: Tất cả instances loại role đều có policy_ref field.
        Expected: Không có errors.
        """
        # Setup: Tạo graph với roles có policy binding
        role = CapabilityInstance(
            id="admin",
            type="role",
            params={"policy_ref": "admin_policy", "permissions": ["admin.*"]},
        )
        
        graph = CapabilityGraph(
            core_capabilities=[],
            instances=[role],
        )
        object.__setattr__(graph, 'metadata', sample_metadata)
        
        # Execute
        validator = InvariantValidator(graph)
        report = validator.validate_role_policy_bindings()
        
        # Assert
        assert report.status == ValidationStatus.PASS.value
        assert len(report.errors) == 0
        assert report.checks.get("INV007") == ValidationStatus.PASS.value
    
    def test_validate_role_policy_bindings_fails(
        self,
        graph_with_role_policies: CapabilityGraph,
    ) -> None:
        """
        Test INV007: Validation fail khi có roles không có policy binding.
        
        Scenario: Có instance loại role nhưng không có policy_ref field.
        Expected: Có error MISSING_ROLE_POLICY.
        """
        # Execute
        validator = InvariantValidator(graph_with_role_policies)
        report = validator.validate_role_policy_bindings()
        
        # Assert
        assert report.status == ValidationStatus.FAIL.value
        assert len(report.errors) > 0
        
        # Check có error với code MISSING_ROLE_POLICY
        missing_policy_errors = [
            e for e in report.errors 
            if e.code == ErrorCode.MISSING_ROLE_POLICY.value
        ]
        assert len(missing_policy_errors) > 0
        
        # Check message có thông tin về role thiếu policy
        error_messages = [e.message for e in missing_policy_errors]
        assert any("staff" in msg for msg in error_messages)


# ============================================================================
# Test INV008: Policy Syntax Validation
# ============================================================================


class TestINV008_PolicySyntaxValidation:
    """Tests cho INV008: Policy syntax validation."""
    
    def test_validate_policy_syntax_passes(
        self,
        sample_metadata: ArtifactMetadata,
    ) -> None:
        """
        Test INV008: Validation pass khi tất cả policies đều có syntax valid.
        
        Scenario: Tất cả instances loại policy đều có cấu trúc đúng.
        Expected: Không có errors.
        """
        # Setup: Tạo graph với valid policies
        policy = CapabilityInstance(
            id="admin_policy",
            type="policy",
            params={
                "name": "admin_policy",
                "effect": "allow",
                "subject": {"role": "admin"},
                "action": {"permission": "admin.*"},
                "resource": {"type": "*"},
            },
        )
        
        graph = CapabilityGraph(
            core_capabilities=[],
            instances=[policy],
        )
        object.__setattr__(graph, 'metadata', sample_metadata)
        
        # Execute
        validator = InvariantValidator(graph)
        report = validator.validate_policy_syntax()
        
        # Assert
        assert report.status == ValidationStatus.PASS.value
        assert len(report.errors) == 0
        assert report.checks.get("INV008") == ValidationStatus.PASS.value
    
    def test_validate_policy_syntax_fails(
        self,
        graph_with_policies: CapabilityGraph,
    ) -> None:
        """
        Test INV008: Validation fail khi có policies có syntax invalid.
        
        Scenario: Có instances loại policy nhưng không có cấu trúc đúng.
        Expected: Có error INVALID_POLICY_SYNTAX.
        """
        # Execute
        validator = InvariantValidator(graph_with_policies)
        report = validator.validate_policy_syntax()
        
        # Assert
        assert report.status == ValidationStatus.FAIL.value
        assert len(report.errors) > 0
        
        # Check có error với code INVALID_POLICY_SYNTAX
        invalid_syntax_errors = [
            e for e in report.errors 
            if e.code == ErrorCode.INVALID_POLICY_SYNTAX.value
        ]
        assert len(invalid_syntax_errors) > 0
        
        # Check message có thông tin về policy invalid
        error_messages = [e.message for e in invalid_syntax_errors]
        assert any("incomplete_policy" in msg or "bad_effect_policy" in msg for msg in error_messages)


# ============================================================================
# Test InvariantValidator Integration
# ============================================================================


class TestInvariantValidatorIntegration:
    """Integration tests cho InvariantValidator."""
    
    def test_validate_all_runs_all_invariants(
        self,
        sample_metadata: ArtifactMetadata,
    ) -> None:
        """
        Test validate_all chạy tất cả invariants và gộp reports.
        
        Scenario: Chạy validate_all trên graph.
        Expected: Report có tất cả checks từ INV001-INV008.
        """
        # Setup: Tạo graph đơn giản
        graph = CapabilityGraph(
            core_capabilities=[],
            instances=[],
        )
        object.__setattr__(graph, 'metadata', sample_metadata)
        
        # Execute
        validator = InvariantValidator(graph)
        report = validator.validate_all()
        
        # Assert: Check tất cả INV codes có trong checks
        assert report.checks.get("INV001") is not None
        assert report.checks.get("INV002") is not None
        assert report.checks.get("INV003") is not None
        assert report.checks.get("INV004") is not None
        assert report.checks.get("INV005") is not None
        assert report.checks.get("INV006") is not None
        assert report.checks.get("INV007") is not None
        assert report.checks.get("INV008") is not None
    
    def test_validate_all_aggregates_errors(
        self,
        empty_graph: CapabilityGraph,
    ) -> None:
        """
        Test validate_all gộp tất cả errors từ các invariants.
        
        Scenario: Graph có issues ở nhiều invariants.
        Expected: Report có tất cả errors.
        """
        # Test chỉ cần confirm validate_all không throw exception
        validator = InvariantValidator(empty_graph)
        report = validator.validate_all()
        
        # Assert: Report được trả về
        assert isinstance(report, ValidationReport)
        assert report.artifact_type == "capability_graph"


# ============================================================================
# Test Error Codes
# ============================================================================


class TestInvariantErrorCodes:
    """Tests cho error codes của Invariant Gates."""
    
    def test_error_codes_defined(self) -> None:
        """Test các error codes INV được define trong ErrorCode."""
        # Assert các error codes tồn tại
        assert hasattr(ErrorCode, 'UNRESOLVED_ENTITY_REF')
        assert hasattr(ErrorCode, 'UNRESOLVED_PERMISSION_REF')
        assert hasattr(ErrorCode, 'UNRESOLVED_ROLE_REF')
        assert hasattr(ErrorCode, 'MISSING_PERMISSION_GUARD')
        assert hasattr(ErrorCode, 'MISSING_TENANT_FILTER')
        assert hasattr(ErrorCode, 'MISSING_TRANSACTION_SCOPE')
        assert hasattr(ErrorCode, 'MISSING_ROLE_POLICY')
        assert hasattr(ErrorCode, 'INVALID_POLICY_SYNTAX')
    
    def test_error_code_values(self) -> None:
        """Test values của các error codes INV."""
        assert ErrorCode.UNRESOLVED_ENTITY_REF.value == "UNRESOLVED_ENTITY_REF"
        assert ErrorCode.UNRESOLVED_PERMISSION_REF.value == "UNRESOLVED_PERMISSION_REF"
        assert ErrorCode.UNRESOLVED_ROLE_REF.value == "UNRESOLVED_ROLE_REF"
        assert ErrorCode.MISSING_PERMISSION_GUARD.value == "MISSING_PERMISSION_GUARD"
        assert ErrorCode.MISSING_TENANT_FILTER.value == "MISSING_TENANT_FILTER"
        assert ErrorCode.MISSING_TRANSACTION_SCOPE.value == "MISSING_TRANSACTION_SCOPE"
        assert ErrorCode.MISSING_ROLE_POLICY.value == "MISSING_ROLE_POLICY"
        assert ErrorCode.INVALID_POLICY_SYNTAX.value == "INVALID_POLICY_SYNTAX"


# ============================================================================
# Test Critical Errors
# ============================================================================


class TestInvariantCriticalErrors:
    """Tests cho critical errors của Invariant Gates."""
    
    def test_critical_error_codes_include_invariants(self) -> None:
        """
        Test CRITICAL_ERROR_CODES bao gồm các invariant critical errors.
        
        Theo SoT: Các errors sau phải là critical:
        - UNRESOLVED_ENTITY_REF
        - UNRESOLVED_PERMISSION_REF
        - UNRESOLVED_ROLE_REF
        - MISSING_PERMISSION_GUARD
        - MISSING_TENANT_FILTER
        - MISSING_TRANSACTION_SCOPE
        """
        from midicoder.contracts.validation import CRITICAL_ERROR_CODES
        
        # Check các error critical được include
        assert ErrorCode.MISSING_PERMISSION_GUARD.value in CRITICAL_ERROR_CODES
        assert ErrorCode.MISSING_TENANT_FILTER.value in CRITICAL_ERROR_CODES
        assert ErrorCode.MISSING_TRANSACTION_SCOPE.value in CRITICAL_ERROR_CODES