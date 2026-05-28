# coding: utf-8
"""
Mô-đun FastAPI emitter cho Report & Document Generator (CP34).

Emit code FastAPI cho:
- ReportService: service chính để generate PDF/Excel/CSV
- ReportRoutes: API endpoints
- ReportWorker: background worker cho batch job
- PDFGenerator: wrapper WeasyPrint
- ExcelGenerator: wrapper openpyxl
- CSVGenerator: wrapper csv module

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from midicoder.packs.cp_full_reporting.models import (
    ReportCollection,
    ReportFormat,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class FastAPIReportEmitter:
    """
    Emitter sinh code FastAPI cho report & document generation.

    Methods:
        emit(): Generate toàn bộ files từ ReportCollection
        generate_service(): Sinh ReportService
        generate_routes(): Sinh API routes
        generate_worker(): Sinh batch worker
        generate_pdf_generator(): Sinh PDF generator (WeasyPrint)
        generate_excel_generator(): Sinh Excel generator (openpyxl)
        generate_csv_generator(): Sinh CSV generator
    """

    def __init__(self, stack_dir: str | None = None) -> None:
        """
        Init emitter.

        Args:
            stack_dir: Đường dẫn đến stack template directory
        """
        self.stack_dir = Path(stack_dir) if stack_dir else None

    def emit(
        self, collection: ReportCollection, output_dir: Path | None = None
    ) -> list[dict[str, str]]:
        """
        Generate toàn bộ files FastAPI từ ReportCollection.

        Args:
            collection: ReportCollection chứa report specs
            output_dir: Output directory (optional)

        Returns:
            List của {path, content} cho mỗi file
        """
        if not collection.reports:
            EM.raise_error(ErrorCode.MDC-F22_REPORT_SPEC_INVALID, reason="Collection trống")

        result: list[dict[str, str]] = []
        result.extend(self.generate_service(collection))
        result.extend(self.generate_routes(collection))
        result.extend(self.generate_worker(collection))
        result.extend(self.generate_pdf_generator(collection))
        result.extend(self.generate_excel_generator(collection))
        result.extend(self.generate_csv_generator(collection))
        return result

    def generate_service(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh ReportService class."""
        report_ids = [r.id for r in collection.reports]
        has_pdf = any(r.format == ReportFormat.PDF for r in collection.reports)
        has_xlsx = any(r.format == ReportFormat.XLSX for r in collection.reports)
        has_csv = any(r.format == ReportFormat.CSV for r in collection.reports)

        imports_section = ""
        if has_pdf:
            imports_section += "from app.generators.pdf_generator import PDFGenerator\n"
        if has_xlsx:
            imports_section += "from app.generators.excel_generator import ExcelGenerator\n"
        if has_csv:
            imports_section += "from app.generators.csv_generator import CSVGenerator\n"

        # Xây dựng report specs dict string an toàn (tránh nested f-string)
        specs_lines: list[str] = []
        for rid in report_ids:
            spec = collection.get_report_by_id(rid)
            specs_lines.append(
                '        "%s": {"id": "%s", "entity": "%s", "format": "%s"},'
                % (rid, rid, spec.entity if spec else rid, spec.format.value if spec else "pdf")
            )
        specs_block = ",\n".join(specs_lines)

        # Builder string an toàn cho init
        pdf_init = "        self.pdf_generator = PDFGenerator()" if has_pdf else ""
        xlsx_init = "        self.excel_generator = ExcelGenerator()" if has_xlsx else ""
        csv_init = "        self.csv_generator = CSVGenerator()" if has_csv else ""

        pdf_branch = '            return self.pdf_generator.generate(spec, data)' if has_pdf else '            raise NotImplementedError("PDF not enabled")'
        xlsx_branch = '            return self.excel_generator.generate(spec, data)' if has_xlsx else '            raise NotImplementedError("XLSX not enabled")'
        csv_branch = '            return self.csv_generator.generate(spec, data)' if has_csv else '            raise NotImplementedError("CSV not enabled")'

        code = '"""Report Service — Service quản lý generate report và document.\n\n'
        code += "CP34: Report & Document Generator\n"
        code += '"""\n\n'
        code += "from typing import Any, Dict, List, Optional\n"
        code += "from pathlib import Path\n\n"
        code += "from sqlalchemy.orm import Session\n\n"
        code += imports_section + "\n"
        code += "# Inline model definitions (Rule V1: no midicoder imports in generated code)\n"
        code += "from enum import Enum\n\n"
        code += "class ReportFormat(str, Enum):\n"
        code += '    PDF = "pdf"\n'
        code += '    XLSX = "xlsx"\n'
        code += '    CSV = "csv"\n\n'
        code += "class BatchJobStatus(str, Enum):\n"
        code += '    PENDING = "pending"\n'
        code += '    RUNNING = "running"\n'
        code += '    COMPLETED = "completed"\n'
        code += '    FAILED = "failed"\n'
        code += '    CANCELLED = "cancelled"\n\n'
        code += "from dataclasses import dataclass, field\nfrom datetime import datetime\nfrom typing import Optional\nimport uuid\n\n\n"
        code += "@dataclass\n"
        code += "class BatchJob:\n"
        code += "    id: str = field(default_factory=lambda: str(uuid.uuid4()))\n"
        code += '    status: BatchJobStatus = BatchJobStatus.PENDING\n'
        code += "    report_spec_ids: list[str] = field(default_factory=list)\n"
        code += "    result_urls: list[str] = field(default_factory=list)\n"
        code += '    error: str = ""\n'
        code += "    retries: int = 0\n"
        code += "    max_retries: int = 3\n"
        code += "    created_at: datetime = field(default_factory=datetime.utcnow)\n"
        code += "    updated_at: datetime = field(default_factory=datetime.utcnow)\n"
        code += "\n"
        code += "class ReportService:\n"
        code += '    """Service quản lý generate report và document."""\n\n'
        code += "    # Report spec registry\n"
        code += "    REPORT_SPECS: Dict[str, Dict[str, Any]] = {\n"
        code += specs_block + "\n"
        code += "    }\n\n"
        code += "    def __init__(self, db: Session):\n"
        code += '        """Init report service."""\n'
        code += "        self._db = db\n"
        if pdf_init:
            code += pdf_init + "\n"
        if xlsx_init:
            code += xlsx_init + "\n"
        if csv_init:
            code += csv_init + "\n"
        code += "\n"
        code += "    def generate_report(\n"
        code += "        self,\n"
        code += '        report_id: str,\n'
        code += "        fmt: ReportFormat | None = None,\n"
        code += '        filters: Optional[Dict[str, Any]] = None,\n'
        code += "    ) -> str:\n"
        code += '        """Generate report và trả về file path hoặc storage URL."""\n'
        code += "        spec = self.REPORT_SPECS.get(report_id)\n"
        code += "        if not spec:\n"
        code += "            raise ValueError(f'Report spec not found: {report_id}')\n"
        code += "\n"
        code += "        output_format = fmt or ReportFormat(spec.get('format', 'pdf'))\n"
        code += "        data = self._query_entity_data(spec, filters)\n"
        code += "\n"
        code += "        if output_format == ReportFormat.PDF:\n"
        code += pdf_branch + "\n"
        code += "        elif output_format == ReportFormat.XLSX:\n"
        code += xlsx_branch + "\n"
        code += "        elif output_format == ReportFormat.CSV:\n"
        code += csv_branch + "\n"
        code += "        else:\n"
        code += "            raise ValueError(f'Invalid format: {output_format}')\n"
        code += "\n"
        code += "    def _query_entity_data(self, spec, filters=None):\n"
        code += '        """Query data từ entity source."""\n'
        code += "        return []\n"
        code += "\n"
        code += "    def create_batch_job(self, report_ids):\n"
        code += '        """Tạo batch job để generate nhiều reports async."""\n'
        code += "        return BatchJob(report_spec_ids=report_ids)\n"
        code += "\n"
        code += "    def get_batch_job(self, job_id):\n"
        code += '        """Lấy thông tin batch job."""\n'
        code += "        return None\n"
        code += "\n"
        code += "    def list_reports(self):\n"
        code += '        """Liệt kê tất cả reports có thể generate."""\n'
        code += "        return [\n"
        code += "            {\n"
        code += '                "id": spec.get("id"),\n'
        code += '                "name": spec.get("name", ""),\n'
        code += '                "entity": spec.get("entity"),\n'
        code += '                "format": spec.get("format", "pdf"),\n'
        code += '                "layout": spec.get("layout", "table"),\n'
        code += '                "description": spec.get("description", ""),\n'
        code += "            }\n"
        code += "            for spec in self.REPORT_SPECS.values()\n"
        code += "        ]\n"

        return [{"path": "app/services/report_service.py", "content": code}]

    def generate_routes(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh API routes."""
        code = '''"""Report API Routes — Endpoints cho report generation.

CP34: Report & Document Generator
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.report_service import ReportService

router = APIRouter(prefix="/api/reports", tags=["reports"])


def get_report_service(db: Session = Depends(lambda: None)) -> ReportService:
    """Dependency injector cho ReportService."""
    return ReportService(db)


class ReportGenerateRequest(BaseModel):
    """Request schema cho generate report."""
    report_id: str = Field(..., description="ID của report spec")
    format: Optional[str] = Field(None, description="Định dạng output (pdf/xlsx/csv)")
    filters: Optional[dict] = Field(None, description="Query filters")


class BatchCreateRequest(BaseModel):
    """Request schema cho tạo batch job."""
    report_ids: list[str] = Field(..., description="Danh sách report IDs")


class ReportResponse(BaseModel):
    """Response schema cho report."""
    id: str
    name: str
    entity: str
    format: str
    layout: str
    description: str = ""


class GenerateResponse(BaseModel):
    """Response schema cho generate report."""
    status: str
    file_url: str
    report_id: str


class BatchJobResponse(BaseModel):
    """Response schema cho batch job."""
    id: str
    status: str
    report_spec_ids: list[str]
    result_urls: list[str] = []
    error: str = ""


@router.get("", response_model=list[ReportResponse])
def list_reports(service: ReportService = Depends(get_report_service)):
    """
    Liệt kê tất cả reports có thể generate.

    Returns:
        List của report metadata
    """
    return service.list_reports()


@router.post("/{report_id}/generate", response_model=GenerateResponse)
def generate_report(
    report_id: str,
    request: ReportGenerateRequest = ReportGenerateRequest(report_id=report_id),
    service: ReportService = Depends(get_report_service),
):
    """
    Generate report và trả về download URL.

    Args:
        report_id: ID của report spec
        request: Request body (format, filters)

    Returns:
        Download URL của file report
    """
    # Import ReportFormat từ service module (inline trong generated code)
    from app.services.report_service import ReportFormat

    fmt = ReportFormat(request.format) if request.format else None
    file_url = service.generate_report(report_id, fmt, request.filters)

    return GenerateResponse(
        status="completed",
        file_url=file_url,
        report_id=report_id,
    )


@router.post("/batch", response_model=BatchJobResponse)
def create_batch_job(
    request: BatchCreateRequest,
    service: ReportService = Depends(get_report_service),
):
    """
    Tạo batch job để generate nhiều reports async.

    Args:
        request: Danh sách report IDs

    Returns:
        BatchJob metadata
    """
    job = service.create_batch_job(request.report_ids)

    return BatchJobResponse(
        id=job.id,
        status=job.status.value,
        report_spec_ids=job.report_spec_ids,
        result_urls=job.result_urls,
        error=job.error,
    )


@router.get("/batch/{job_id}", response_model=BatchJobResponse)
def get_batch_job(
    job_id: str,
    service: ReportService = Depends(get_report_service),
):
    """
    Lấy thông tin batch job (poll status).

    Args:
        job_id: ID của batch job

    Returns:
        BatchJob status và results
    """
    job = service.get_batch_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")

    return BatchJobResponse(
        id=job.id,
        status=job.status.value,
        report_spec_ids=job.report_spec_ids,
        result_urls=job.result_urls,
        error=job.error,
    )
'''
        return [{"path": "app/routes/reports.py", "content": code}]

    def generate_worker(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh batch worker handler."""
        code = '''"""Report Worker — Background worker cho batch document processing.

CP34: Report & Document Generator

Tích hợp với CP13 Workflow Runtime để execute batch jobs.
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

# Import từ module service (inline definitions) — Rule V1: không import midicoder
from app.services.report_service import BatchJob, BatchJobStatus, ReportFormat

logger = logging.getLogger(__name__)


class ReportWorker:
    """Background worker xử lý batch report generation."""

    def __init__(self, db: Session):
        """
        Init report worker.

        Args:
            db: SQLAlchemy session
        """
        self._db = db

    def execute_job(self, job: BatchJob) -> None:
        """
        Execute batch job — generate tất cả reports trong job.

        Args:
            job: BatchJob instance

        Raises:
            RuntimeError: Nếu execute thất bại và không thể retry
        """
        job.mark_running()
        result_urls: List[str] = []

        try:
            # Import service để generate từng report
            from app.services.report_service import ReportService
            service = ReportService(self._db)

            for report_id in job.report_spec_ids:
                try:
                    file_url = service.generate_report(report_id)
                    result_urls.append(file_url)
                    logger.info("Report %s generated successfully", report_id)
                except Exception as e:
                    logger.error("Failed to generate report %s: %s", report_id, str(e))
                    # Tiếp tục với report tiếp theo — ghi lỗi nhưng không abort
                    result_urls.append(f"error:{report_id}:{str(e)}")

            # Tất cả reports đã xử lý
            job.mark_completed(result_urls)
            logger.info("Batch job %s completed with %d results", job.id, len(result_urls))

        except Exception as e:
            error_msg = f"Batch job failed: {str(e)}"
            logger.error("%s", error_msg)

            # Retry nếu còn cơ hội
            if job.can_retry():
                job.retries += 1
                logger.info("Retrying job %s (attempt %d/%d)", job.id, job.retries, job.max_retries)
                # Re-execute — thực tế sẽ submit lại qua CP13 queue
                self.execute_job(job)
            else:
                job.mark_failed(error_msg)
                raise RuntimeError(
                    f"Batch job {job.id} failed after {job.retries} retries: {error_msg}"
                ) from e

    def cancel_job(self, job: BatchJob) -> None:
        """
        Hủy batch job đang chạy.

        Args:
            job: BatchJob instance
        """
        if job.status in (BatchJobStatus.COMPLETED, BatchJobStatus.CANCELLED):
            return
        job.mark_cancelled()
        logger.info("Batch job %s cancelled", job.id)


# Entry point cho CP13 worker
def report_batch_handler(job_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Handler cho CP13 worker — entry point cho batch report job.

    Args:
        job_data: Job data từ CP13 queue
        db: Database session

    Returns:
        Result dict
    """
    job = BatchJob.from_dict(job_data)
    worker = ReportWorker(db)
    worker.execute_job(job)
    return job.to_dict()
'''
        return [{"path": "app/workers/report_worker.py", "content": code}]

    def generate_pdf_generator(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh PDF generator (WeasyPrint)."""
        entity_names = list(set(r.entity for r in collection.reports))

        code = '"""PDF Generator — Wrapper cho WeasyPrint để generate PDF report.\n\n'
        code += "CP34: Report & Document Generator\n"
        code += "\n"
        code += "Dùng WeasyPrint để render HTML template thành PDF.\n"
        code += "Hỗ trợ: header/footer, pagination, table layout.\n"
        code += '"""\n\n'
        code += "import io\n"
        code += "import logging\n"
        code += "from typing import Any, Dict, List\n"
        code += "from pathlib import Path\n\n"
        code += "from weasyprint import HTML, CSS\n\n"
        code += "logger = logging.getLogger(__name__)\n\n"
        code += f"# Entity names cần query\n"
        code += f"ENTITIES = {entity_names!r}\n\n\n"
        code += "class PDFGenerator:\n"
        code += '    """Generator PDF bằng WeasyPrint."""\n\n'
        code += '    def __init__(self, template_dir: str = "app/templates/reports"):\n'
        code += '        """Init PDF generator."""\n'
        code += "        self.template_dir = Path(template_dir)\n\n"
        code += "    def generate(self, spec: 'ReportSpec', data: List[Dict[str, Any]]) -> str:\n"
        code += '        """Generate PDF từ report spec và data."""\n'
        code += "        try:\n"
        code += "            html_content = self._build_html(spec, data)\n"
        code += "            pdf_bytes = HTML(string=html_content).write_pdf()\n"
        code += '            storage_path = f"reports/{spec.id}.pdf"\n'
        code += "            url = self._save_to_storage(storage_path, pdf_bytes)\n"
        code += '            logger.info("PDF generated: %s (%d bytes)", spec.id, len(pdf_bytes))\n'
        code += "            return url\n"
        code += "        except Exception as e:\n"
        code += "            raise RuntimeError(f'PDF generation failed for report: {spec.id}: {e}') from e\n\n"
        code += "    def _build_html(self, spec: 'ReportSpec', data: List[Dict[str, Any]]) -> str:\n"
        code += '        """Build HTML content từ report spec và data."""\n'
        code += "        html = f'<html><head><title>{spec.name}</title>'\n"
        code += "        html += '<style>'\n"
        code += "        html += 'body { font-family: Arial, sans-serif; margin: 20px; }'\n"
        code += "        html += 'table { border-collapse: collapse; width: 100%; }'\n"
        code += "        html += 'th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }'\n"
        code += "        html += 'th { background-color: #4CAF50; color: white; }'\n"
        code += "        html += '@page { size: A4; margin: 2cm; }'\n"
        code += "        html += '</style></head><body>'\n"
        code += "        html += f'<h1>{spec.name}</h1>'\n"
        code += "        if data:\n"
        code += "            fields = spec.fields or list(data[0].keys())\n"
        code += "            html += '<table><thead><tr>'\n"
        code += "            for f in fields:\n"
        code += "                html += f'<th>{f}</th>'\n"
        code += "            html += '</tr></thead><tbody>'\n"
        code += "            for row in data:\n"
        code += "                html += '<tr>'\n"
        code += "                for f in fields:\n"
        code += "                    html += f'<td>{row.get(f, \"\")}</td>'\n"
        code += "                html += '</tr>'\n"
        code += "            html += '</tbody></table>'\n"
        code += "        else:\n"
        code += "            html += '<p>Không có dữ liệu.</p>'\n"
        code += "        html += '</body></html>'\n"
        code += "        return html\n\n"
        code += "    def _save_to_storage(self, path: str, data: bytes) -> str:\n"
        code += '        """Lưu PDF file đến storage (CP11 integration)."""\n'
        code += '        return f"/storage/{path}"\n'

        return [{"path": "app/generators/pdf_generator.py", "content": code}]

    def generate_excel_generator(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh Excel generator (openpyxl)."""
        code = '''"""Excel Generator — Wrapper cho openpyxl để generate Excel report.

CP34: Report & Document Generator

Hỗ trợ: multi-sheet, frozen header, cell styling, auto-column-width.
"""

import logging
from typing import Any, Dict, List
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

logger = logging.getLogger(__name__)


class ExcelGenerator:
    """Generator Excel bằng openpyxl."""

    def __init__(self) -> None:
        """Init Excel generator."""
        # Styles
        self.header_font = Font(bold=True, color="FFFFFF", size=11)
        self.header_fill = PatternFill(start_color="4CAF50", end_color="4CAF50", fill_type="solid")
        self.header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        self.thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

    def generate(
        self,
        spec: "ReportSpec",
        data: List[Dict[str, Any]],
    ) -> str:
        """
        Generate Excel file từ report spec và data.

        Args:
            spec: ReportSpec chứa config
            data: Danh sách records từ entity query

        Returns:
            Storage URL của Excel file

        Raises:
            MidicoderError: Nếu generate thất bại
        """
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = spec.name[:31]  # Excel sheet name max 31 chars

            # Fields
            fields = spec.fields or (list(data[0].keys()) if data else [])

            # Header row
            for col_idx, f in enumerate(fields, 1):
                cell = ws.cell(row=1, column=col_idx, value=f)
                cell.font = self.header_font
                cell.fill = self.header_fill
                cell.alignment = self.header_alignment
                cell.border = self.thin_border

            # Freeze header
            ws.freeze_panes = "A2"

            # Data rows
            for row_idx, row in enumerate(data, 2):
                for col_idx, f in enumerate(fields, 1):
                    cell = ws.cell(row=row_idx, column=col_idx, value=row.get(f, ""))
                    cell.border = self.thin_border

            # Auto-adjust column width
            for col_idx in range(1, len(fields) + 1):
                max_length = 0
                for row in ws.iter_rows(min_row=1, max_col=col_idx, min_col=col_idx, values_only=False):
                    for cell in row:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = adjusted_width

            # Save to bytes and store
            import io
            buf = io.BytesIO()
            wb.save(buf)
            buf.seek(0)
            excel_bytes = buf.read()

            # Lưu file qua CP11 storage
            storage_path = f"reports/{spec.id}.xlsx"
            url = self._save_to_storage(storage_path, excel_bytes)

            logger.info("Excel generated: %s (%d rows)", spec.id, len(data))
            return url

        except Exception as e:
            raise RuntimeError(f'Excel generation failed for report: {spec.id}: {e}') from e

    def _save_to_storage(self, path: str, data: bytes) -> str:
        """
        Lưu Excel file đến storage (CP11 integration).

        Args:
            path: Storage path
            data: Excel bytes

        Returns:
            Download URL
        """
        # TODO: Integrate với CP11 file storage
        return f"/storage/{path}"
'''
        return [{"path": "app/generators/excel_generator.py", "content": code}]

    def generate_csv_generator(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh CSV generator."""
        code = '''"""CSV Generator — Wrapper cho csv module để generate CSV report.

CP34: Report & Document Generator
"""

import csv
import io
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class CSVGenerator:
    """Generator CSV bằng built-in csv module."""

    def generate(
        self,
        spec: "ReportSpec",
        data: List[Dict[str, Any]],
    ) -> str:
        """
        Generate CSV file từ report spec và data.

        Args:
            spec: ReportSpec chứa config
            data: Danh sách records từ entity query

        Returns:
            Storage URL của CSV file

        Raises:
            MidicoderError: Nếu generate thất bại
        """
        try:
            fields = spec.fields or (list(data[0].keys()) if data else [])

            # Write CSV to string buffer
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(data)

            csv_bytes = output.getvalue().encode("utf-8-sig")  # BOM cho Excel compatibility
            output.close()

            # Lưu file qua CP11 storage
            storage_path = f"reports/{spec.id}.csv"
            url = self._save_to_storage(storage_path, csv_bytes)

            logger.info("CSV generated: %s (%d rows)", spec.id, len(data))
            return url

        except Exception as e:
            raise RuntimeError(f'CSV generation failed for report: {spec.id}: {e}') from e

    def _save_to_storage(self, path: str, data: bytes) -> str:
        """
        Lưu CSV file đến storage (CP11 integration).

        Args:
            path: Storage path
            data: CSV bytes

        Returns:
            Download URL
        """
        # TODO: Integrate với CP11 file storage
        return f"/storage/{path}"
'''
        return [{"path": "app/generators/csv_generator.py", "content": code}]
