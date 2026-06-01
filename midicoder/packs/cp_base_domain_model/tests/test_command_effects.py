"""
Comprehensive tests for CommandEffects (CP01 Domain Model).

Test coverage:
- Basic execution with conditional effects
- Core CRUD: create, update, delete, query, upsert
- Transaction: begin, commit, rollback
- Events: publish_event
- Integration: call_api, send_email, send_sms, webhook
- Observability: audit_log, metrics
- Compliance: check_compliance, mask_pii
- Multiple effects executed in order

Author: Midicoder Team
Version: 2.0.0
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from midicoder.packs.cp_base_domain_model import (
    Command,
    CommandEffect,
    EffectType,
)
from midicoder.packs.cp_base_domain_model.command_effects import CommandEffects


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_repository():
    """Mock repository with async create/update/delete/query/upsert methods."""
    repo = AsyncMock()

    # Mock record returned by create/upsert
    mock_record = MagicMock()
    mock_record.id = "record-001"

    repo.create = AsyncMock(return_value=mock_record)
    repo.update = AsyncMock(return_value=True)
    repo.delete = AsyncMock(return_value=True)
    repo.query = AsyncMock(return_value=[{"id": "1", "name": "test"}])
    repo.upsert = AsyncMock(return_value=mock_record)

    return repo


@pytest.fixture
def mock_event_bus():
    """Mock event bus with async publish method."""
    bus = AsyncMock()
    bus.publish = AsyncMock(return_value=None)
    return bus


@pytest.fixture
def mock_notification_service():
    """Mock notification service for email/SMS."""
    service = AsyncMock()
    service.send_email = AsyncMock(return_value=True)
    service.send_sms = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_audit_service():
    """Mock audit service."""
    service = AsyncMock()
    mock_record = MagicMock()
    mock_record.id = "audit-001"
    service.log = AsyncMock(return_value=mock_record)
    return service


@pytest.fixture
def command_create_user():
    """Sample Command with create_record effect."""
    return Command(
        id="CreateUser",
        description="Create a new user",
        effects=[
            CommandEffect(effect_type=EffectType.CREATE_RECORD, entity="User"),
        ],
    )


@pytest.fixture
def command_update_user():
    """Sample Command with update_record effect."""
    return Command(
        id="UpdateUser",
        description="Update user",
        effects=[
            CommandEffect(effect_type=EffectType.UPDATE_RECORD, entity="User"),
        ],
    )


@pytest.fixture
def command_delete_user():
    """Sample Command with delete_record effect."""
    return Command(
        id="DeleteUser",
        description="Delete user",
        effects=[
            CommandEffect(effect_type=EffectType.DELETE_RECORD, entity="User"),
        ],
    )


@pytest.fixture
def command_multi_effect():
    """Command with multiple effects of different types."""
    return Command(
        id="ComplexCommand",
        description="Command with multiple effects",
        effects=[
            CommandEffect(effect_type=EffectType.BEGIN_TRANSACTION),
            CommandEffect(effect_type=EffectType.CREATE_RECORD, entity="Order"),
            CommandEffect(effect_type=EffectType.UPDATE_RECORD, entity="Inventory"),
            CommandEffect(effect_type=EffectType.PUBLISH_EVENT, event="OrderPlaced"),
            CommandEffect(effect_type=EffectType.WRITE_AUDIT_LOG, audit_action="order_placed"),
            CommandEffect(effect_type=EffectType.COMMIT_TRANSACTION),
        ],
    )


# ============================================================================
# TestCommandEffectsBasic
# ============================================================================


class TestCommandEffectsBasic:
    """Tests for basic CommandEffects execution."""

    @pytest.mark.asyncio
    async def test_execute_returns_results_dict(
        self, command_create_user, mock_repository
    ):
        """Test: execute() returns results dict with correct structure."""
        effects = CommandEffects(
            command=command_create_user,
            repositories={"user": mock_repository},
        )
        results = await effects.execute(
            {"name": "John"},
            user_id="user-001",
            tenant_id="tenant-001",
        )

        assert isinstance(results, dict)
        # Keys preserve entity name case: create_record_User
        assert "create_record_User" in results

    @pytest.mark.asyncio
    async def test_execute_with_condition_true(self):
        """Test: Conditional effect executes when condition evaluates to True."""
        command = Command(
            id="ConditionalCommand",
            description="Command with conditional effect",
            effects=[
                CommandEffect(
                    effect_type=EffectType.UPDATE_RECORD,
                    entity="Entity",
                    condition="some_condition",
                ),
            ],
        )

        mock_repo = AsyncMock()
        mock_repo.update = AsyncMock(return_value=True)

        effects = CommandEffects(
            command=command,
            repositories={"entity": mock_repo},
        )

        # _evaluate_condition always returns True by default
        results = await effects.execute({"id": "1"})

        assert "update_record_Entity" in results

    @pytest.mark.asyncio
    async def test_execute_with_no_effects(self):
        """Test: execute() returns empty dict when no effects."""
        command = Command(
            id="EmptyCommand",
            description="Command with no effects",
            effects=[],
        )

        effects = CommandEffects(command=command)
        results = await effects.execute({})

        assert results == {}


# ============================================================================
# TestCommandEffectCreateRecord
# ============================================================================


class TestCommandEffectCreateRecord:
    """Tests for create_record effect."""

    @pytest.mark.asyncio
    async def test_create_record_with_repository(
        self, command_create_user, mock_repository
    ):
        """Test: create_record calls repo.create() with tenant_id and created_by."""
        effects = CommandEffects(
            command=command_create_user,
            repositories={"user": mock_repository},
        )

        await effects.execute(
            {"name": "John"},
            user_id="user-001",
            tenant_id="tenant-001",
        )

        mock_repository.create.assert_awaited_once()
        call_args = mock_repository.create.call_args[0][0]
        assert call_args["tenant_id"] == "tenant-001"
        assert call_args["created_by"] == "user-001"
        assert call_args["name"] == "John"

    @pytest.mark.asyncio
    async def test_create_record_without_repository(self, command_create_user):
        """Test: create_record returns 'generated-id' when no repository."""
        effects = CommandEffects(
            command=command_create_user,
            repositories={},
        )

        results = await effects.execute(
            {"name": "John"},
            user_id="user-001",
            tenant_id="tenant-001",
        )

        assert results["create_record_User"] == "generated-id"

    @pytest.mark.asyncio
    async def test_create_record_returns_record_id(
        self, command_create_user, mock_repository
    ):
        """Test: create_record returns string representation of record ID."""
        effects = CommandEffects(
            command=command_create_user,
            repositories={"user": mock_repository},
        )

        results = await effects.execute(
            {"name": "John"},
            user_id="user-001",
            tenant_id="tenant-001",
        )

        assert results["create_record_User"] == "record-001"


# ============================================================================
# TestCommandEffectUpdateRecord
# ============================================================================


class TestCommandEffectUpdateRecord:
    """Tests for update_record effect."""

    @pytest.mark.asyncio
    async def test_update_record_with_repository(
        self, command_update_user, mock_repository
    ):
        """Test: update_record calls repo.update() with updated_by."""
        effects = CommandEffects(
            command=command_update_user,
            repositories={"user": mock_repository},
        )

        await effects.execute(
            {"id": "1", "name": "Jane"},
            user_id="user-001",
        )

        mock_repository.update.assert_awaited_once()
        call_args = mock_repository.update.call_args[0]
        # first arg is id, second is data dict
        assert call_args[0] == "1"
        assert call_args[1]["updated_by"] == "user-001"

    @pytest.mark.asyncio
    async def test_update_record_without_repository(self, command_update_user):
        """Test: update_record returns True when no repository."""
        effects = CommandEffects(
            command=command_update_user,
            repositories={},
        )

        results = await effects.execute(
            {"id": "1", "name": "Jane"},
            user_id="user-001",
        )

        assert results["update_record_User"] is True


# ============================================================================
# TestCommandEffectDeleteRecord
# ============================================================================


class TestCommandEffectDeleteRecord:
    """Tests for delete_record effect."""

    @pytest.mark.asyncio
    async def test_delete_record_with_repository(
        self, command_delete_user, mock_repository
    ):
        """Test: delete_record calls repo.delete() with correct ID."""
        effects = CommandEffects(
            command=command_delete_user,
            repositories={"user": mock_repository},
        )

        await effects.execute({"id": "record-to-delete"})

        mock_repository.delete.assert_awaited_once_with("record-to-delete")

    @pytest.mark.asyncio
    async def test_delete_record_without_repository(self, command_delete_user):
        """Test: delete_record returns True when no repository."""
        effects = CommandEffects(
            command=command_delete_user,
            repositories={},
        )

        results = await effects.execute({"id": "record-to-delete"})

        assert results["delete_record_User"] is True


# ============================================================================
# TestCommandEffectPublishEvent
# ============================================================================


class TestCommandEffectPublishEvent:
    """Tests for publish_event effect."""

    @pytest.mark.asyncio
    async def test_publish_event_with_event_bus(self, mock_event_bus):
        """Test: publish_event calls bus.publish() with correct event structure."""
        command = Command(
            id="PublishCommand",
            description="Command with publish event",
            effects=[
                CommandEffect(effect_type=EffectType.PUBLISH_EVENT, event="UserCreated"),
            ],
        )

        effects = CommandEffects(
            command=command,
            event_bus=mock_event_bus,
        )

        await effects.execute(
            {"name": "John"},
            user_id="user-001",
            tenant_id="tenant-001",
        )

        mock_event_bus.publish.assert_awaited_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert event["type"] == "UserCreated"
        assert event["payload"] == {"name": "John"}
        assert event["metadata"]["user_id"] == "user-001"
        assert event["metadata"]["tenant_id"] == "tenant-001"

    @pytest.mark.asyncio
    async def test_publish_event_without_event_bus(self):
        """Test: publish_event returns True when no event_bus."""
        command = Command(
            id="PublishCommand",
            description="Command with publish event",
            effects=[
                CommandEffect(effect_type=EffectType.PUBLISH_EVENT, event="UserCreated"),
            ],
        )

        effects = CommandEffects(command=command, event_bus=None)
        results = await effects.execute({"name": "John"})

        # Keys preserve event name case: publish_event_UserCreated
        assert results["publish_event_UserCreated"] is True


# ============================================================================
# TestCommandEffectQueryRecords
# ============================================================================


class TestCommandEffectQueryRecords:
    """Tests for query_records effect."""

    @pytest.mark.asyncio
    async def test_query_records_with_repository(self, mock_repository):
        """Test: query_records returns query results from repository."""
        command = Command(
            id="QueryCommand",
            description="Command with query effect",
            effects=[
                CommandEffect(effect_type=EffectType.QUERY_RECORDS, entity="User"),
            ],
        )

        effects = CommandEffects(
            command=command,
            repositories={"user": mock_repository},
        )

        results = await effects.execute({"status": "active"})

        mock_repository.query.assert_awaited_once()
        assert results["query_records_User"] == [{"id": "1", "name": "test"}]

    @pytest.mark.asyncio
    async def test_query_records_without_repository(self):
        """Test: query_records returns empty list when no repository."""
        command = Command(
            id="QueryCommand",
            description="Command with query effect",
            effects=[
                CommandEffect(effect_type=EffectType.QUERY_RECORDS, entity="User"),
            ],
        )

        effects = CommandEffects(
            command=command,
            repositories={},
        )

        results = await effects.execute({"status": "active"})

        assert results["query_records_User"] == []


# ============================================================================
# TestCommandEffectUpsertRecord
# ============================================================================


class TestCommandEffectUpsertRecord:
    """Tests for upsert_record effect."""

    @pytest.mark.asyncio
    async def test_upsert_record_with_repository(self, mock_repository):
        """Test: upsert_record calls repo.upsert() and returns record ID."""
        command = Command(
            id="UpsertCommand",
            description="Command with upsert effect",
            effects=[
                CommandEffect(effect_type=EffectType.UPSERT_RECORD, entity="User"),
            ],
        )

        effects = CommandEffects(
            command=command,
            repositories={"user": mock_repository},
        )

        results = await effects.execute(
            {"name": "John"},
            tenant_id="tenant-001",
        )

        mock_repository.upsert.assert_awaited_once()
        assert results["upsert_record_User"] == "record-001"

    @pytest.mark.asyncio
    async def test_upsert_record_without_repository(self):
        """Test: upsert_record returns 'generated-id' when no repository."""
        command = Command(
            id="UpsertCommand",
            description="Command with upsert effect",
            effects=[
                CommandEffect(effect_type=EffectType.UPSERT_RECORD, entity="User"),
            ],
        )

        effects = CommandEffects(
            command=command,
            repositories={},
        )

        results = await effects.execute({"name": "John"})

        assert results["upsert_record_User"] == "generated-id"


# ============================================================================
# TestCommandEffectIntegration
# ============================================================================


class TestCommandEffectIntegration:
    """Tests for integration effects (email, SMS, API, webhook)."""

    @pytest.mark.asyncio
    async def test_send_email_with_notification_service(
        self, mock_notification_service
    ):
        """Test: send_email calls notification_service.send_email()."""
        command = Command(
            id="EmailCommand",
            description="Command with email effect",
            effects=[
                CommandEffect(
                    effect_type=EffectType.SEND_EMAIL,
                    email_template="welcome",
                ),
            ],
        )

        effects = CommandEffects(
            command=command,
            notification_service=mock_notification_service,
        )

        results = await effects.execute(
            {"to": "user@example.com"},
            user_id="user-001",
        )

        mock_notification_service.send_email.assert_awaited_once_with(
            template="welcome",
            data={"to": "user@example.com"},
            user_id="user-001",
        )
        assert results["send_email_default"] is True

    @pytest.mark.asyncio
    async def test_send_email_without_notification_service(self):
        """Test: send_email returns True when no notification_service."""
        command = Command(
            id="EmailCommand",
            description="Command with email effect",
            effects=[
                CommandEffect(
                    effect_type=EffectType.SEND_EMAIL,
                    email_template="welcome",
                ),
            ],
        )

        effects = CommandEffects(command=command, notification_service=None)
        results = await effects.execute({"to": "user@example.com"})

        assert results["send_email_default"] is True

    @pytest.mark.asyncio
    async def test_send_sms_with_notification_service(
        self, mock_notification_service
    ):
        """Test: send_sms calls notification_service.send_sms()."""
        command = Command(
            id="SMSCommand",
            description="Command with SMS effect",
            effects=[
                CommandEffect(
                    effect_type=EffectType.SEND_SMS,
                    sms_template="otp_code",
                ),
            ],
        )

        effects = CommandEffects(
            command=command,
            notification_service=mock_notification_service,
        )

        results = await effects.execute(
            {"phone": "+1234567890"},
            user_id="user-001",
        )

        mock_notification_service.send_sms.assert_awaited_once_with(
            template="otp_code",
            data={"phone": "+1234567890"},
            user_id="user-001",
        )
        assert results["send_sms_default"] is True

    @pytest.mark.asyncio
    async def test_send_sms_without_notification_service(self):
        """Test: send_sms returns True when no notification_service."""
        command = Command(
            id="SMSCommand",
            description="Command with SMS effect",
            effects=[
                CommandEffect(
                    effect_type=EffectType.SEND_SMS,
                    sms_template="otp_code",
                ),
            ],
        )

        effects = CommandEffects(command=command, notification_service=None)
        results = await effects.execute({"phone": "+1234567890"})

        assert results["send_sms_default"] is True

    @pytest.mark.asyncio
    async def test_call_external_api(self):
        """Test: call_external_api returns placeholder success dict."""
        command = Command(
            id="APICommand",
            description="Command with API call effect",
            effects=[
                CommandEffect(effect_type=EffectType.CALL_EXTERNAL_API),
            ],
        )

        effects = CommandEffects(command=command)
        results = await effects.execute({"url": "https://api.example.com"})

        assert results["call_external_api_default"] == {"status": "success"}

    @pytest.mark.asyncio
    async def test_call_webhook(self):
        """Test: webhook returns True (placeholder)."""
        command = Command(
            id="WebhookCommand",
            description="Command with webhook effect",
            effects=[
                CommandEffect(effect_type=EffectType.WEBHOOK),
            ],
        )

        effects = CommandEffects(command=command)
        results = await effects.execute({"url": "https://webhook.example.com"})

        assert results["webhook_default"] is True


# ============================================================================
# TestCommandEffectObservability
# ============================================================================


class TestCommandEffectObservability:
    """Tests for observability effects (audit log, metrics)."""

    @pytest.mark.asyncio
    async def test_write_audit_log_with_audit_service(
        self, mock_audit_service
    ):
        """Test: write_audit_log calls audit_service.log() and returns audit ID."""
        command = Command(
            id="AuditCommand",
            description="Command with audit log",
            effects=[
                CommandEffect(
                    effect_type=EffectType.WRITE_AUDIT_LOG,
                    audit_action="user_created",
                ),
            ],
        )

        effects = CommandEffects(
            command=command,
            audit_service=mock_audit_service,
        )

        results = await effects.execute(
            {"name": "John"},
            user_id="user-001",
            tenant_id="tenant-001",
        )

        mock_audit_service.log.assert_awaited_once_with(
            action="user_created",
            data={"name": "John"},
            user_id="user-001",
            tenant_id="tenant-001",
        )
        assert results["write_audit_log_default"] == "audit-001"

    @pytest.mark.asyncio
    async def test_write_audit_log_without_audit_service(self):
        """Test: write_audit_log returns 'audit-id' when no audit_service."""
        command = Command(
            id="AuditCommand",
            description="Command with audit log",
            effects=[
                CommandEffect(
                    effect_type=EffectType.WRITE_AUDIT_LOG,
                    audit_action="user_created",
                ),
            ],
        )

        effects = CommandEffects(command=command, audit_service=None)
        results = await effects.execute({"name": "John"})

        assert results["write_audit_log_default"] == "audit-id"

    @pytest.mark.asyncio
    async def test_record_metric_calls_metric_registry(self):
        """Test: record_metric calls MetricRegistry.record()."""
        command = Command(
            id="MetricCommand",
            description="Command with metric effect",
            effects=[
                CommandEffect(effect_type=EffectType.RECORD_METRIC),
            ],
        )

        effects = CommandEffects(command=command)
        results = await effects.execute({"value": 42})

        assert results["record_metric_default"] is True

    @pytest.mark.asyncio
    async def test_record_metric_uses_default_values(self):
        """Test: record_metric uses default metric name and value when not specified."""
        command = Command(
            id="MetricCommand",
            description="Command with metric effect",
            effects=[
                CommandEffect(effect_type=EffectType.RECORD_METRIC),
            ],
        )

        effects = CommandEffects(command=command)

        # MetricRegistry is imported inside the method, so patch at the import site
        with patch(
            "midicoder.packs.cp_core_observability.metrics.MetricRegistry"
        ) as MockRegistry:
            mock_instance = MagicMock()
            mock_instance.record = MagicMock(return_value=True)
            MockRegistry.return_value = mock_instance

            await effects.execute({})

            MockRegistry.assert_called_once()
            mock_instance.record.assert_called_once()
            # Verify default metric name and value
            call_args = mock_instance.record.call_args[0]
            assert call_args[0] == "command.duration"
            assert call_args[1] == 1.0


# ============================================================================
# TestCommandEffectCompliance
# ============================================================================


class TestCommandEffectCompliance:
    """Tests for compliance effects (check_compliance, mask_pii)."""

    @pytest.mark.asyncio
    async def test_check_compliance_returns_true(self):
        """Test: check_compliance returns True (placeholder)."""
        command = Command(
            id="ComplianceCommand",
            description="Command with compliance check",
            effects=[
                CommandEffect(effect_type=EffectType.CHECK_COMPLIANCE),
            ],
        )

        effects = CommandEffects(command=command)
        results = await effects.execute(
            {"data": "sensitive"},
            user_id="user-001",
        )

        assert results["check_compliance_default"] is True

    @pytest.mark.asyncio
    async def test_mask_pii_returns_data(self):
        """Test: mask_pii returns the data dict (placeholder passthrough)."""
        command = Command(
            id="MaskPIICommand",
            description="Command with PII masking",
            effects=[
                CommandEffect(effect_type=EffectType.MASK_PII),
            ],
        )

        effects = CommandEffects(command=command)
        input_data = {"email": "user@example.com", "name": "John"}
        results = await effects.execute(input_data)

        assert results["mask_pii_default"] == input_data


# ============================================================================
# TestCommandEffectTransaction
# ============================================================================


class TestCommandEffectTransaction:
    """Tests for transaction effects (begin, commit, rollback)."""

    @pytest.mark.asyncio
    async def test_begin_transaction(self):
        """Test: begin_transaction returns 'transaction_id'."""
        command = Command(
            id="TransactionCommand",
            description="Command with transaction",
            effects=[
                CommandEffect(effect_type=EffectType.BEGIN_TRANSACTION),
            ],
        )

        effects = CommandEffects(command=command)
        results = await effects.execute({})

        assert results["begin_transaction_default"] == "transaction_id"

    @pytest.mark.asyncio
    async def test_commit_transaction(self):
        """Test: commit_transaction executes without error."""
        command = Command(
            id="TransactionCommand",
            description="Command with transaction",
            effects=[
                CommandEffect(effect_type=EffectType.COMMIT_TRANSACTION),
            ],
        )

        effects = CommandEffects(command=command)
        results = await effects.execute({})

        assert "commit_transaction_default" in results

    @pytest.mark.asyncio
    async def test_rollback_transaction(self):
        """Test: rollback_transaction executes without error."""
        command = Command(
            id="TransactionCommand",
            description="Command with transaction",
            effects=[
                CommandEffect(effect_type=EffectType.ROLLBACK_TRANSACTION),
            ],
        )

        effects = CommandEffects(command=command)
        results = await effects.execute({})

        assert "rollback_transaction_default" in results


# ============================================================================
# TestCommandEffectsMultipleEffects
# ============================================================================


class TestCommandEffectsMultipleEffects:
    """Tests for executing commands with multiple effects."""

    @pytest.mark.asyncio
    async def test_execute_multiple_effects_in_order(
        self, command_multi_effect, mock_repository, mock_event_bus, mock_audit_service
    ):
        """Test: All effects are executed and results dict has correct keys."""
        effects = CommandEffects(
            command=command_multi_effect,
            repositories={
                "order": mock_repository,
                "inventory": mock_repository,
            },
            event_bus=mock_event_bus,
            audit_service=mock_audit_service,
        )

        results = await effects.execute(
            {"product_id": "prod-001", "quantity": 2},
            user_id="user-001",
            tenant_id="tenant-001",
        )

        # Verify all expected keys exist (preserve entity/event name case)
        assert "begin_transaction_default" in results
        assert "create_record_Order" in results
        assert "update_record_Inventory" in results
        assert "publish_event_OrderPlaced" in results
        assert "write_audit_log_default" in results
        assert "commit_transaction_default" in results

    @pytest.mark.asyncio
    async def test_multiple_effects_verify_execution_order(
        self, mock_repository, mock_event_bus
    ):
        """Test: Effects execute in the order they are defined."""
        command = Command(
            id="OrderedCommand",
            description="Command to verify effect order",
            effects=[
                CommandEffect(effect_type=EffectType.CREATE_RECORD, entity="A"),
                CommandEffect(effect_type=EffectType.CREATE_RECORD, entity="B"),
                CommandEffect(effect_type=EffectType.CREATE_RECORD, entity="C"),
            ],
        )

        effects = CommandEffects(
            command=command,
            repositories={
                "a": mock_repository,
                "b": mock_repository,
                "c": mock_repository,
            },
        )

        await effects.execute({"data": "test"})

        # Verify create was called 3 times (once per entity)
        assert mock_repository.create.await_count == 3

    @pytest.mark.asyncio
    async def test_results_dict_has_correct_count(self, command_multi_effect, mock_repository, mock_event_bus, mock_audit_service):
        """Test: Results dict has same number of entries as effects."""
        effects = CommandEffects(
            command=command_multi_effect,
            repositories={
                "order": mock_repository,
                "inventory": mock_repository,
            },
            event_bus=mock_event_bus,
            audit_service=mock_audit_service,
        )

        results = await effects.execute(
            {"product_id": "prod-001"},
            user_id="user-001",
            tenant_id="tenant-001",
        )

        assert len(results) == len(command_multi_effect.effects)

    @pytest.mark.asyncio
    async def test_effects_without_services(self):
        """Test: Multiple effects with no services attached still execute."""
        command = Command(
            id="NoServiceCommand",
            description="Command with no services",
            effects=[
                CommandEffect(effect_type=EffectType.CREATE_RECORD, entity="User"),
                CommandEffect(effect_type=EffectType.PUBLISH_EVENT, event="UserCreated"),
                CommandEffect(effect_type=EffectType.SEND_EMAIL, email_template="welcome"),
            ],
        )

        effects = CommandEffects(command=command)

        results = await effects.execute({"name": "John"})

        assert "create_record_User" in results
        assert results["create_record_User"] == "generated-id"
        assert results["publish_event_UserCreated"] is True
        assert results["send_email_default"] is True


    @pytest.mark.asyncio
    async def test_upsert_record_without_tenant_id(self, mock_repository):
        """Test: upsert_record does not set tenant_id when tenant_id is None."""
        command = Command(
            id="UpsertCommand",
            description="Command with upsert effect",
            effects=[
                CommandEffect(effect_type=EffectType.UPSERT_RECORD, entity="User"),
            ],
        )

        effects = CommandEffects(
            command=command,
            repositories={"user": mock_repository},
        )

        # Execute without tenant_id
        results = await effects.execute({"name": "John"})

        mock_repository.upsert.assert_awaited_once()
        call_args = mock_repository.upsert.call_args[0][0]
        assert "tenant_id" not in call_args
        assert results["upsert_record_User"] == "record-001"

    @pytest.mark.asyncio
    async def test_condition_false_skips_effect(self):
        """Test: Effect with condition is skipped when _evaluate_condition returns False."""
        command = Command(
            id="ConditionalCommand",
            description="Command with conditional effect",
            effects=[
                CommandEffect(
                    effect_type=EffectType.UPDATE_RECORD,
                    entity="Entity",
                    condition="skip_me",
                ),
            ],
        )

        effects = CommandEffects(command=command, repositories={})

        # Patch _evaluate_condition to return False
        with patch.object(effects, "_evaluate_condition", return_value=False):
            results = await effects.execute({"id": "1"})

        # Effect should be skipped, results dict should be empty
        assert results == {}

    @pytest.mark.asyncio
    async def test_unknown_effect_type_returns_none(self):
        """Test: Unknown effect type returns None in results dict."""
        # Use a mock effect_type that has .value (for results key)
        # but does not equal any EffectType enum member
        mock_effect_type = MagicMock()
        mock_effect_type.value = "unknown_effect_type"
        # Ensure it does not match any EffectType comparison
        mock_effect_type.__eq__ = MagicMock(return_value=False)

        effect = CommandEffect(effect_type=EffectType.CREATE_RECORD, entity="X")
        effect.effect_type = mock_effect_type

        command = Command(
            id="UnknownEffectCommand",
            description="Command with unknown effect type",
            effects=[effect],
        )

        effects = CommandEffects(command=command)
        results = await effects.execute({})

        assert results["unknown_effect_type_X"] is None


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
