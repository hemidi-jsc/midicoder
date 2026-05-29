"""
Test E2E cho CLIE2ERunner — chạy full CLI chain từ brief → code apply.

Test business behavior:
- CLIE2ERunner invoke CLI commands theo chuỗi
- Init workspace → tạo .midicoder directory
- Contract gen → placeholder fallback (không LLM)
- IR build → từ contract → MIR
- Code plan → từ MIR → plan
- Code gen → từ plan → generated files
- Code apply → từ generated → target dir
- Report: số file generated, compile pass/fail
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from click.testing import CliRunner


# ============================================================================
# Minimal brief fixture content
# ============================================================================

MINIMAL_BRIEF = """# Test Project - Brief

## 1. Product Context
### Product Name
Test App

### Product Type
Web Application

### Target Market
Internal

### Problem Statement
Test problem

### Solution Overview
Test solution

### Business Model
Internal tool

### Go-to-Market Strategy
Internal release

## 2. Business Goals and KPIs
### Strategic Goals
Test goal

### Tactical KPIs
| ID | Name | Definition | Baseline | Target |
|----|------|-----------|----------|--------|
| K01 | Uptime | System availability | 90% | 99% |

### Time Horizons
Q1 2026

## 3. User Personas and Roles
### P01: Admin - Quản trị viên
Quản lý hệ thống

### P02: User - Người dùng cuối
Sử dụng tính năng

### P03: Auditor - Kiểm toán
Xem báo cáo

### Role-Permission Matrix
| Role | Permissions |
|------|-------------|
| Admin | `user:read`, `user:write`, `user:delete` |
| User | `user:read` |
| Auditor | `user:read`, `report:read` |

## 4. Core User Journeys
### J01: Đăng nhập
Người dùng đăng nhập vào hệ thống
- **Primary Persona:** P02
- **Trigger:** User mở app
- **Success Criteria:** User thấy dashboard

### J02: Xem danh sách
Người dùng xem danh sách
- **Primary Persona:** P02
- **Trigger:** User vào list view
- **Success Criteria:** Hiển thị danh sách

### J03: Tạo bản ghi
Người dùng tạo bản ghi mới
- **Primary Persona:** P01
- **Trigger:** User bấm tạo mới
- **Success Criteria:** Bản ghi được lưu

### J04: Cập nhật bản ghi
Người dùng cập nhật bản ghi
- **Primary Persona:** P01
- **Trigger:** User bấm sửa
- **Success Criteria:** Bản ghi được cập nhật

### J05: Xóa bản ghi
Người dùng xóa bản ghi
- **Primary Persona:** P01
- **Trigger:** User bấm xóa
- **Success Criteria:** Bản ghi bị xóa

### J06: Tìm kiếm
Tìm kiếm bản ghi
- **Primary Persona:** P02
- **Trigger:** User nhập từ khóa
- **Success Criteria:** Kết quả tìm kiếm

### J07: Xuất báo cáo
Xuất báo cáo PDF
- **Primary Persona:** P03
- **Trigger:** User chọn export
- **Success Criteria:** PDF được tạo

### J08: Đổi mật khẩu
Người dùng đổi mật khẩu
- **Primary Persona:** P02
- **Trigger:** User vào cài đặt
- **Success Criteria:** Mật khẩu mới

### J09: Xem audit log
Xem lịch sử hoạt động
- **Primary Persona:** P03
- **Trigger:** User vào audit
- **Success Criteria:** Log hiển thị

### J10: Quản lý phân quyền
Admin phân quyền user
- **Primary Persona:** P01
- **Trigger:** Admin vào RBAC
- **Success Criteria:** Phân quyền được lưu

## 5. Functional Requirements
### FR01: Quản lý người dùng
Hệ thống hỗ trợ CRUD người dùng
- **Priority:** P0
- **Acceptance Criteria:** CRUD hoạt động

### FR02: Xác thực người dùng
Hệ thống xác thực qua JWT
- **Priority:** P0
- **Acceptance Criteria:** JWT auth

### FR03: Phân quyền RBAC
Hỗ trợ role-based access
- **Priority:** P0
- **Acceptance Criteria:** RBAC

### FR04: Tìm kiếm
Tìm kiếm full-text
- **Priority:** P1
- **Acceptance Criteria:** Search

### FR05: Pagination
Phân trang danh sách
- **Priority:** P1
- **Acceptance Criteria:** Pagination

### FR06: Lọc
Lọc theo criteria
- **Priority:** P1
- **Acceptance Criteria:** Filter

### FR07: Sắp xếp
Sắp xếp theo field
- **Priority:** P2
- **Acceptance Criteria:** Sort

### FR08: Import/Export
Xuất dữ liệu CSV
- **Priority:** P2
- **Acceptance Criteria:** Export CSV

### FR09: Audit trail
Ghi log hoạt động
- **Priority:** P0
- **Acceptance Criteria:** Audit

### FR10: Notification
Thông báo email
- **Priority:** P2
- **Acceptance Criteria:** Email

### FR11: File upload
Upload file đính kèm
- **Priority:** P2
- **Acceptance Criteria:** Upload

### FR12: Multi-language
Hỗ trợ tiếng Việt
- **Priority:** P2
- **Acceptance Criteria:** i18n

### FR13: Dashboard
Dashboard tổng quan
- **Priority:** P1
- **Acceptance Criteria:** Dashboard

### FR14: Report
Báo cáo thống kê
- **Priority:** P2
- **Acceptance Criteria:** Report

### FR15: Data validation
Validate input
- **Priority:** P0
- **Acceptance Criteria:** Validation

### FR16: Error handling
Xử lý lỗi thống nhất
- **Priority:** P0
- **Acceptance Criteria:** Error format

### FR17: API versioning
API có version
- **Priority:** P1
- **Acceptance Criteria:** /api/v1/

### FR18: Rate limiting
Giới hạn request
- **Priority:** P1
- **Acceptance Criteria:** Rate limit

### FR19: Caching
Cache response
- **Priority:** P2
- **Acceptance Criteria:** Cache

### FR20: Health check
Health check endpoint
- **Priority:** P0
- **Acceptance Criteria:** /health

### FR21: Swagger docs
Tài liệu API
- **Priority:** P1
- **Acceptance Criteria:** /docs

### FR22: Logging
Structured logging
- **Priority:** P0
- **Acceptance Criteria:** JSON log

### FR23: Config management
Quản lý config
- **Priority:** P1
- **Acceptance Criteria:** Config

### FR24: Database migration
Migration tự động
- **Priority:** P0
- **Acceptance Criteria:** Alembic

### FR25: Backup/restore
Sao lưu dữ liệu
- **Priority:** P1
- **Acceptance Criteria:** Backup

### FR26: Tenant isolation
Multi-tenancy
- **Priority:** P0
- **Acceptance Criteria:** Isolation

### FR27: Soft delete
Xóa mềm dữ liệu
- **Priority:** P1
- **Acceptance Criteria:** DeletedAt

### FR28: Bulk operation
Xử lý hàng loạt
- **Priority:** P2
- **Acceptance Criteria:** Bulk

### FR29: Webhook
Webhook callback
- **Priority:** P2
- **Acceptance Criteria:** Webhook

### FR30: API key auth
Auth bằng API key
- **Priority:** P1
- **Acceptance Criteria:** API key

## 6. Non-Functional Requirements
### NFR01: Performance
Response time < 200ms
- **Metric:** p95 latency

### NFR02: Scalability
Hỗ trợ 10K concurrent users

### NFR03: Availability
Uptime 99.9%

### NFR04: Security
OWASP Top 10 protection

### NFR05: Reliability
Auto-recovery sau failure

### NFR06: Observability
Logging, metrics, tracing

### NFR07: Maintainability
90%+ test coverage

### NFR08: Deployability
Zero-downtime deploy

### NFR09: Data integrity
ACID transactions

### NFR10: Backup
Daily backup, 30-day retention

### NFR11: Disaster recovery
RPO < 1h, RTO < 4h

### NFR12: Compliance
GDPR compliant

### NFR13: Accessibility
WCAG 2.1 AA

### NFR14: Mobile responsive
Mobile-first design

### NFR15: Documentation
API docs + user guide

## 7. Domain Rules and Invariants
### INV01: User email unique
Mỗi email chỉ 1 user

### INV02: Order total positive
Tổng đơn hàng > 0

### INV03: Active user can login
Chỉ user active mới login

### INV04: Deleted user cannot login
User đã xóa không login

### INV05: Password complexity
Độ phức tạp mật khẩu

### INV06: Session expiry
Session hết hạn sau 24h

### INV07: Tenant data isolation
Data tenant A không thấy tenant B

### INV08: Audit log immutable
Audit log không sửa được

### INV09: Soft delete retention
Giữ soft delete 30 ngày

### INV10: Role hierarchy
Admin > Manager > User

## 8. Compliance and Regulatory Constraints
### CC01: GDPR
Bảo vệ dữ liệu cá nhân EU

### CC02: OWASP
Bảo mật ứng dụng web

### CC03: SOC2
Kiểm soát bảo mật

### CC04: ISO27001
Quản lý an toàn thông tin

### CC05: PCI-DSS
Bảo mật thanh toán

### CC06: HIPAA
Bảo vệ thông tin y tế

### CC07: Data residency
Dữ liệu lưu trong nước

### CC08: Right to be forgotten
Xóa dữ liệu theo yêu cầu

## 9. Integration Requirements
### INT01: Email service
Gửi email qua SMTP

### INT02: Payment gateway
Thanh toán Stripe

### INT03: Cloud storage
AWS S3

### INT04: CDN
CloudFront

### INT05: Monitoring
Datadog

### INT06: Log aggregation
ELK stack

### INT07: CI/CD
GitHub Actions

### INT08: DNS
Route53

### INT09: SSL/TLS
LetsEncrypt

### INT10: Backup service
AWS Backup

## 10. Data Model Expectations
#### User
- **id:** UUID
- **email:** str, unique
- **password_hash:** str
- **name:** str
- **status:** str
- **tenant_id:** UUID

#### Product
- **id:** UUID
- **name:** str
- **price:** decimal
- **stock:** int

#### Order
- **id:** UUID
- **user_id:** UUID
- **total:** decimal
- **status:** str

#### OrderItem
- **id:** UUID
- **order_id:** UUID
- **product_id:** UUID
- **quantity:** int
- **price:** decimal

#### AuditLog
- **id:** UUID
- **user_id:** UUID
- **action:** str
- **entity:** str
- **timestamp:** datetime

#### Role
- **id:** UUID
- **name:** str
- **permissions:** list

#### Permission
- **id:** UUID
- **resource:** str
- **action:** str

#### Tenant
- **id:** UUID
- **name:** str
- **status:** str

#### Category
- **id:** UUID
- **name:** str
- **parent_id:** UUID

#### Address
- **id:** UUID
- **user_id:** UUID
- **city:** str
- **country:** str

#### Payment
- **id:** UUID
- **order_id:** UUID
- **amount:** decimal
- **method:** str

#### Notification
- **id:** UUID
- **user_id:** UUID
- **message:** str
- **read:** bool

#### FileAttachment
- **id:** UUID
- **entity_id:** UUID
- **entity_type:** str
- **file_url:** str

#### Session
- **id:** UUID
- **user_id:** UUID
- **token:** str
- **expires_at:** datetime

#### Config
- **id:** UUID
- **key:** str
- **value:** str

## 11. Security and Access Control
### Authentication
JWT-based, 24h expiry

### Authorization
RBAC model

### Role Definitions
1. Admin - Full access
2. Manager - Department access
3. User - Own data only
4. Auditor - Read-only reports
5. Guest - Public pages

### Permission Definitions
- `user:read`, `user:write`, `user:delete`, `user:list`
- `product:read`, `product:write`, `product:delete`
- `order:read`, `order:write`, `order:delete`
- `report:read`, `report:export`
- `config:read`, `config:write`

## 12. Observability and Operations
### Logging
JSON structured logging

### Metrics
Prometheus + Grafana

### Tracing
OpenTelemetry

### Alerting
PagerDuty integration

### Dashboard
Grafana dashboards

### Incident Response
Runbook + escalation

## 13. Acceptance Criteria
### Definition of Done
- Code reviewed
- Tests pass
- CI green
- Docs updated

### MVP Scope
- User CRUD
- Product list
- Order flow
- Auth

### Launch Readiness Checklist
1. Security review done
2. Load test passed
3. Backup verified
4. Runbook ready
5. Monitoring active
6. DNS configured
7. SSL deployed
8. CDN configured
9. Error tracking setup
10. Performance baseline set

## 14. Out-of-Scope
1. Mobile native app
2. Desktop client
3. Voice assistant
4. VR/AR integration
5. Blockchain features

## 15. Open Questions
### Q01: Payment method
Phương thức thanh toán nào?

### Q02: Hosting region
Khu vực nào?

### Q03: Data retention period
Giữ data bao lâu?

### Q04: Multi-language support
Những ngôn ngữ nào?

### Q05: SLA target
Mục tiêu SLA bao nhiêu?

## 16. Glossary
1. **Tenant** - Single tenant trong hệ thống multi-tenant
2. **RBAC** - Role-Based Access Control
3. **JWT** - JSON Web Token
4. **MVP** - Minimum Viable Product
5. **API** - Application Programming Interface
6. **CRUD** - Create, Read, Update, Delete
7. **DTO** - Data Transfer Object
8. **ORM** - Object-Relational Mapping
9. **DSL** - Domain Specific Language
10. **MIR** - Midicoder IR
11. **NFR** - Non-Functional Requirement
12. **SLA** - Service Level Agreement
13. **RPO** - Recovery Point Objective
14. **RTO** - Recovery Time Objective
15. **CI/CD** - Continuous Integration/Deployment
16. **OWASP** - Open Web Application Security Project
17. **GDPR** - General Data Protection Regulation
18. **PCI-DSS** - Payment Card Industry Data Security
19. **SOC2** - Service Organization Control 2
20. **WCAG** - Web Content Accessibility Guidelines
"""


# ============================================================================
# CLIE2ERunner class
# ============================================================================

class CLIE2ERunner:
    """
    Runner cho E2E CLI test — chạy full chain qua Click CliRunner.

    Bypass shell để test trong environment không có TTY (CI/CD).
    Mỗi instance chạy trong temp workdir riêng.

    Usage:
        runner = CLIE2ERunner()
        runner.run()
        report = runner.report()
    """

    def __init__(self, brief_content: str | None = None):
        """
        Khởi tạo CLIE2ERunner.

        Args:
            brief_content: Nội dung brief (nếu None, dùng MINIMAL_BRIEF)
        """
        self.brief_content = brief_content or MINIMAL_BRIEF
        self.workdir = None
        self.output_dir = None
        self.steps = []
        self._runner = CliRunner()

    def _run_command(self, args: list[str], expect_success: bool = True) -> str:
        """
        Chạy 1 CLI command trong workdir hiện tại.

        Args:
            args: Danh sách arguments (vd: ["init", "--force"])
            expect_success: Nếu True, assert exit_code == 0

        Returns:
            stdout output
        """
        from midicoder.pipeline.cli import cli

        # Chuyển về workdir để CLI đọc đúng config
        original_cwd = os.getcwd()
        os.chdir(self.workdir)

        try:
            result = self._runner.invoke(
                cli, args,
                catch_exceptions=False,
            )
        finally:
            os.chdir(original_cwd)

        step_info = {
            "command": " ".join(args),
            "exit_code": result.exit_code,
            "stdout": result.output if result.output else "",
            "stderr": str(result.exception) if result.exception else "",
        }
        self.steps.append(step_info)

        if expect_success and result.exit_code != 0:
            raise AssertionError(
                f"Command failed: {' '.join(args)}\n"
                f"Exit code: {result.exit_code}\n"
                f"Output: {result.output}"
            )

        return result.output

    def _seed_brief_and_analysis(self) -> str:
        """
        Seed brief + analysis artifact vào SQLite trong workdir.

        Returns:
            brief_id được insert
        """
        import uuid
        from midicoder.storage.sqlite import BriefsManager, ArtifactsManager
        from midicoder.storage.sqlite import get_connection

        brief_id = f"test-{uuid.uuid4().hex[:8]}"

        # Dùng db_path tuyệt đối trong workdir (tránh conflict với DB repo root)
        briefs_db = self.workdir / ".midicoder" / "data" / "briefs.db"
        artifacts_db = self.workdir / ".midicoder" / "data" / "artifacts.db"

        # Insert brief vào SQLite
        bm = BriefsManager(db_path=briefs_db)
        bm.init()
        bm.create(
            brief_id=brief_id,
            version="v1.0.0",
            content=self.brief_content,
            title="Test App",
            brief_type="working",
        )

        # Update status thành 'analyzed' (create() chỉ set 'draft')
        with get_connection(bm.db_path) as conn:
            conn.execute(
                "UPDATE briefs SET status = ? WHERE brief_id = ?",
                ("analyzed", brief_id),
            )

        # Insert analysis artifact (placeholder)
        am = ArtifactsManager(db_path=artifacts_db)
        am.init()
        am.create(
            artifact_id=f"analysis-{brief_id}",
            artifact_type="analysis",
            name="Analysis",
            version="v1.0.0",
            content=json.dumps({
                "entities": [
                    {"id": "User", "fields": [{"name": "id", "type": "UUID"}, {"name": "email", "type": "str"}]},
                    {"id": "Product", "fields": [{"name": "id", "type": "UUID"}, {"name": "name", "type": "str"}]},
                    {"id": "Order", "fields": [{"name": "id", "type": "UUID"}, {"name": "user_id", "type": "UUID"}]},
                ],
                "commands": [
                    {"id": "CreateUser", "input": [{"name": "email", "type": "str"}], "entity": "User"},
                    {"id": "CreateOrder", "input": [{"name": "product_id", "type": "UUID"}], "entity": "Order"},
                ],
                "queries": [
                    {"id": "GetUserById", "input": [{"name": "user_id", "type": "UUID"}], "returns": "User"},
                    {"id": "ListProducts", "returns": "list[Product]"},
                    {"id": "GetOrdersByUser", "input": [{"name": "user_id", "type": "UUID"}], "returns": "list[Order]"},
                ],
            }),
            metadata={"source_brief": brief_id},
        )

        return brief_id

    def run(self):
        """
        Chạy full CLI chain: init → contract gen → ir build → code plan → code gen → code apply

        Tạo temp workdir, init project, seed brief/analysis, generate contracts placeholder,
        build IR, tạo plan, generate code, và apply vào output dir.
        """
        # Tạo temp workdir
        tmpdir = tempfile.mkdtemp()
        self.workdir = Path(tmpdir)
        self.output_dir = self.workdir / "output"

        # Step 0: Tạo brief file
        brief_path = self.workdir / "brief.md"
        brief_path.write_text(self.brief_content, encoding="utf-8")

        # Step 1: Init workspace (tạo .midicoder + SQLite DB)
        self._run_command(["init", "--force", "-v", "v1.0.0"], expect_success=True)

        # Step 2: Seed brief + analysis artifact vào SQLite
        brief_id = self._seed_brief_and_analysis()

        # Step 3: Copy brief vào .midicoder/versions/
        versions_brief_dir = self.workdir / ".midicoder" / "versions" / "v1.0.0"
        versions_brief_dir.mkdir(parents=True, exist_ok=True)
        versions_brief = versions_brief_dir / "brief.md"
        versions_brief.write_text(self.brief_content, encoding="utf-8")

        # Step 4: Contract gen (placeholder fallback — không LLM)
        with patch("midicoder.pipeline.commands.contract.load_llm_config",
                   side_effect=Exception("No LLM config — use placeholder")):
            self._run_command(["contract", "gen", "--force"], expect_success=True)

        # Step 5: IR build
        self._run_command(["ir", "build"], expect_success=True)

        # Step 6: Code plan
        self._run_command(["code", "plan"], expect_success=True)

        # Step 7: Code gen
        self._run_command(["code", "gen", "--target", "backend"], expect_success=True)

        # Step 8: Code apply
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._run_command(
            ["code", "apply", "--target-dir", str(self.output_dir), "--force"],
            expect_success=True,
        )

    def verify(self) -> dict:
        """
        Verify generated code.

        Returns:
            Dict với stats: total_files, python_files, typescript_files, pass_count, fail_count
        """
        from midicoder.pipeline.code_verifier import CodeVerifier

        if not self.output_dir or not self.output_dir.exists():
            return {"error": "Output directory không tồn tại"}

        verifier = CodeVerifier()
        all_files = list(self.output_dir.rglob("*"))
        code_files = [f for f in all_files if f.is_file()]

        report = verifier.verify_batch(code_files, check_imports=False)

        return {
            "total_files": len(code_files),
            "python_files": sum(1 for f in code_files if f.suffix == ".py"),
            "typescript_files": sum(1 for f in code_files if f.suffix in (".ts", ".tsx")),
            "passed": report.passed,
            "failed": report.failed,
            "report": report.summary(),
        }

    def report(self) -> dict:
        """
        Generate test report.

        Returns:
            Dict với steps, verify result, và conclusion.
        """
        verify_result = self.verify()

        failed_steps = [s for s in self.steps if s["exit_code"] != 0]

        return {
            "total_steps": len(self.steps),
            "failed_steps": len(failed_steps),
            "steps": self.steps,
            "verify": verify_result,
            "success": len(failed_steps) == 0,
        }

    def cleanup(self):
        """Xóa temp workdir."""
        import shutil
        if self.workdir and self.workdir.exists():
            shutil.rmtree(self.workdir, ignore_errors=True)


# ============================================================================
# Tests
# ============================================================================

class TestCLIE2ERunnerBasics:
    """Test cơ bản của CLIE2ERunner class."""

    def test_runner_creation(self):
        """Tạo CLIE2ERunner thành công."""
        runner = CLIE2ERunner()
        assert runner.brief_content is not None
        assert runner.steps == []

    def test_runner_with_custom_brief(self):
        """Tạo runner với brief tùy chỉnh."""
        custom = "# Custom Brief\n## Content"
        runner = CLIE2ERunner(brief_content=custom)
        assert runner.brief_content == custom

    def test_verify_without_run(self):
        """Verify trước khi run → trả về error."""
        runner = CLIE2ERunner()
        result = runner.verify()
        assert "error" in result

    def test_report_without_run(self):
        """Report trước khi run → steps rỗng."""
        runner = CLIE2ERunner()
        report = runner.report()
        assert report["total_steps"] == 0
        assert report["failed_steps"] == 0


class TestCLIE2ERunnerFullChain:
    """Test full CLI chain E2E."""

    def test_full_pipeline_runs(self):
        """Chạy full pipeline từ init → apply."""
        runner = CLIE2ERunner()

        try:
            runner.run()

            report = runner.report()

            # Kiểm tra tất cả steps thành công
            assert report["success"] is True, (
                f"Pipeline failed at step: {report['steps']}"
            )
            assert report["total_steps"] >= 5  # Ít nhất 5 steps

            # Kiểm tra output directory có files
            assert runner.output_dir.exists()
            output_files = list(runner.output_dir.rglob("*"))
            assert len([f for f in output_files if f.is_file()]) > 0

            # Kiểm tra verify result
            verify = report["verify"]
            assert "total_files" in verify
            assert verify["passed"] >= 0
            assert verify["failed"] >= 0

        finally:
            runner.cleanup()

    def test_generated_files_structure(self):
        """Generated files có đúng directory structure."""
        runner = CLIE2ERunner()

        try:
            runner.run()

            # Kiểm tra các directories chính tồn tại
            assert (runner.output_dir / "app").exists() or (
                runner.output_dir / "docker-compose.yml"
            ).exists()

            # Kiểm tra có file Python
            py_files = list(runner.output_dir.rglob("*.py"))
            assert len(py_files) > 0, "Không có file Python nào được generate"

        finally:
            runner.cleanup()

    def test_steps_log_correctly(self):
        """Mỗi step được log đúng command + exit_code."""
        runner = CLIE2ERunner()

        try:
            runner.run()

            # Mỗi step có đủ thông tin
            for step in runner.steps:
                assert "command" in step
                assert "exit_code" in step
                assert step["exit_code"] == 0

            # Các commands được chạy theo thứ tự
            commands = [s["command"] for s in runner.steps]
            assert any("init" in c for c in commands)
            assert any("contract" in c for c in commands)
            assert any("ir" in c for c in commands)
            assert any("code plan" in c for c in commands)
            assert any("code gen" in c for c in commands)

        finally:
            runner.cleanup()

    def test_verify_report_has_stats(self):
        """Verify report có đầy đủ stats."""
        runner = CLIE2ERunner()

        try:
            runner.run()

            verify = runner.verify()

            # Report có đúng keys
            assert "total_files" in verify
            assert "python_files" in verify
            assert "passed" in verify
            assert "failed" in verify
            assert "report" in verify

            # Stats hợp lệ
            assert verify["total_files"] > 0
            assert verify["python_files"] > 0
            assert verify["passed"] + verify["failed"] == verify["total_files"]

        finally:
            runner.cleanup()


class TestCLIE2ERunnerCIReady:
    """Test CI/CD readiness."""

    def test_no_tty_required(self):
        """Test chạy được không cần TTY (mô phỏng CI)."""
        # CliRunner không cần TTY — đây là test xác nhận
        runner = CLIE2ERunner()

        try:
            runner.run()
            assert runner.steps
        finally:
            runner.cleanup()

    def test_cleanup_removes_workdir(self):
        """Cleanup xóa sạch workdir."""
        runner = CLIE2ERunner()

        try:
            runner.run()
            assert runner.workdir.exists()
        finally:
            runner.cleanup()

        assert not runner.workdir.exists()
