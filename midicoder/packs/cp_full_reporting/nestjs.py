# coding: utf-8
"""
Mô-đun NestJS emitter cho Report & Document Generator (CP34).

Emit code NestJS cho:
- ReportService: service chính để generate PDF/Excel/CSV
- ReportController: API controller
- PDFGeneratorService: wrapper Puppeteer/PDFKit
- ExcelGeneratorService: wrapper exceljs
- CSVGeneratorService: wrapper csv-parse/csv-stringify
- BatchWorkerService: background worker cho batch job

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path

from midicoder.packs.cp_full_reporting.models import (
    ReportCollection,
    ReportFormat,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class NestJSReportEmitter:
    """
    Emitter sinh code NestJS cho report & document generation.

    Methods:
        emit(): Generate toàn bộ files từ ReportCollection
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
        Generate toàn bộ files NestJS từ ReportCollection.

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
        result.extend(self.generate_controller(collection))
        result.extend(self.generate_pdf_generator(collection))
        result.extend(self.generate_excel_generator(collection))
        result.extend(self.generate_csv_generator(collection))
        result.extend(self.generate_batch_worker(collection))
        return result

    def generate_service(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh ReportService class."""
        report_ids = [r.id for r in collection.reports]
        has_pdf = any(r.format == ReportFormat.PDF for r in collection.reports)
        has_xlsx = any(r.format == ReportFormat.XLSX for r in collection.reports)
        has_csv = any(r.format == ReportFormat.CSV for r in collection.reports)

        # Xây dựng imports an toàn
        imports = 'import { Injectable } from "@nestjs/common";\n'
        if has_pdf:
            imports += 'import { PdfGeneratorService } from "./pdf-generator.service";\n'
        if has_xlsx:
            imports += 'import { ExcelGeneratorService } from "./excel-generator.service";\n'
        if has_csv:
            imports += 'import { CsvGeneratorService } from "./csv-generator.service";\n'

        # Xây dựng report specs an toàn
        specs_lines: list[str] = []
        for rid in report_ids:
            spec = collection.get_report_by_id(rid)
            specs_lines.append(
                '    "%s": { id: "%s", entity: "%s", format: ReportFormat.%s },'
                % (rid, rid, spec.entity if spec else rid, spec.format.name if spec else "PDF")
            )
        specs_block = ",\n".join(specs_lines)

        # Private fields
        private_fields = ""
        if has_pdf:
            private_fields += "  private readonly pdfGenerator: PdfGeneratorService;\n"
        if has_xlsx:
            private_fields += "  private readonly excelGenerator: ExcelGeneratorService;\n"
        if has_csv:
            private_fields += "  private readonly csvGenerator: CsvGeneratorService;\n"

        # Constructor
        if has_pdf or has_xlsx or has_csv:
            constructor = "  constructor(\n"
            if has_pdf:
                constructor += "    private pdfGenerator: PdfGeneratorService,\n"
            if has_xlsx:
                constructor += "    private excelGenerator: ExcelGeneratorService,\n"
            if has_csv:
                constructor += "    private csvGenerator: CsvGeneratorService,\n"
            constructor += "  ) {}\n"
        else:
            constructor = "  constructor() {}\n"

        # Switch branches
        pdf_branch = '      case ReportFormat.PDF:\n        return this.pdfGenerator.generate(spec, data);' if has_pdf else "      case ReportFormat.PDF:\n        throw new Error('PDF not enabled');"
        xlsx_branch = '      case ReportFormat.XLSX:\n        return this.excelGenerator.generate(spec, data);' if has_xlsx else "      case ReportFormat.XLSX:\n        throw new Error('XLSX not enabled');"
        csv_branch = '      case ReportFormat.CSV:\n        return this.csvGenerator.generate(spec, data);' if has_csv else "      case ReportFormat.CSV:\n        throw new Error('CSV not enabled');"

        code = "// Report Service — Service quản lý generate report và document.\n"
        code += "// CP34: Report & Document Generator (NestJS)\n\n"
        code += imports + "\n"
        code += "export enum ReportFormat {\n"
        code += '  PDF = "pdf",\n'
        code += '  XLSX = "xlsx",\n'
        code += '  CSV = "csv",\n'
        code += "}\n\n"
        code += "export interface ReportSpec {\n"
        code += "  id: string;\n"
        code += "  name: string;\n"
        code += "  entity: string;\n"
        code += "  fields: string[];\n"
        code += "  filter: Record<string, any>;\n"
        code += "  format: ReportFormat;\n"
        code += "  layout: string;\n"
        code += "  groupBy?: string;\n"
        code += "  aggregations?: string[];\n"
        code += "  description?: string;\n"
        code += "}\n\n"
        code += "export interface BatchJob {\n"
        code += "  id: string;\n"
        code += '  status: "pending" | "running" | "completed" | "failed" | "cancelled";\n'
        code += "  reportSpecIds: string[];\n"
        code += "  resultUrls?: string[];\n"
        code += "  error?: string;\n"
        code += "  retries: number;\n"
        code += "  maxRetries: number;\n"
        code += "}\n\n"
        code += '@Injectable()\n'
        code += "export class ReportService {\n"
        code += "  // Report spec registry\n"
        code += "  private readonly REPORT_SPECS: Record<string, ReportSpec> = {\n"
        code += specs_block + "\n"
        code += "  };\n\n"
        code += private_fields + "\n"
        code += constructor + "\n"
        code += "  /**\n"
        code += "   * Generate report và trả về file path hoặc storage URL.\n"
        code += "   */\n"
        code += "  async generateReport(reportId: string, fmt?: ReportFormat, filters?: Record<string, any>): Promise<string> {\n"
        code += "    const spec = this.REPORT_SPECS[reportId];\n"
        code += "    if (!spec) {\n"
        code += "      throw new Error(`Report spec not found: ${reportId}`);\n"
        code += "    }\n"
        code += "    const outputFormat = fmt || spec.format;\n"
        code += "    const data = await this.queryEntityData(spec, filters);\n"
        code += "    switch (outputFormat) {\n"
        code += pdf_branch + "\n"
        code += xlsx_branch + "\n"
        code += csv_branch + "\n"
        code += "      default:\n"
        code += "        throw new Error(`Invalid format: ${outputFormat}`);\n"
        code += "    }\n"
        code += "  }\n\n"
        code += "  private async queryEntityData(spec: ReportSpec, filters?: Record<string, any>): Promise<any[]> {\n"
        code += "    return [];\n"
        code += "  }\n\n"
        code += "  createBatchJob(reportIds: string[]): BatchJob {\n"
        code += "    return { id: crypto.randomUUID(), status: \"pending\", reportSpecIds: reportIds, retries: 0, maxRetries: 3 };\n"
        code += "  }\n\n"
        code += "  listReports(): ReportSpec[] {\n"
        code += "    return Object.values(this.REPORT_SPECS);\n"
        code += "  }\n"
        code += "}\n"

        return [{"path": "src/reports/report.service.ts", "content": code}]

    def generate_controller(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh ReportController."""
        code = '''// Report Controller — API endpoints cho report generation.
// CP34: Report & Document Generator (NestJS)

import {
  Controller,
  Get,
  Post,
  Param,
  Body,
  Query,
} from "@nestjs/common";
import { ReportService, ReportFormat } from "./report.service";

interface GenerateRequest {
  format?: string;
  filters?: Record<string, any>;
}

interface BatchCreateRequest {
  reportIds: string[];
}

@Controller("api/reports")
export class ReportController {
  constructor(private readonly reportService: ReportService) {}

  /**
   * Liệt kê tất cả reports có thể generate.
   */
  @Get()
  async listReports() {
    return this.reportService.listReports();
  }

  /**
   * Generate report và trả về download URL.
   */
  @Post(":reportId/generate")
  async generateReport(
    @Param("reportId") reportId: string,
    @Body() request: GenerateRequest,
  ) {
    const fmt = request.format
      ? (request.format as ReportFormat)
      : undefined;
    const fileUrl = await this.reportService.generateReport(
      reportId,
      fmt,
      request.filters,
    );

    return {
      status: "completed",
      file_url: fileUrl,
      report_id: reportId,
    };
  }

  /**
   * Tạo batch job để generate nhiều reports async.
   */
  @Post("batch")
  async createBatchJob(@Body() request: BatchCreateRequest) {
    const job = this.reportService.createBatchJob(request.reportIds);
    return {
      id: job.id,
      status: job.status,
      report_spec_ids: job.reportSpecIds,
      result_urls: job.resultUrls || [],
      error: job.error || "",
    };
  }

  /**
   * Lấy thông tin batch job (poll status).
   */
  @Get("batch/:jobId")
  async getBatchJob(@Param("jobId") jobId: string) {
    // TODO: Query từ database
    return { error: "Not implemented" };
  }
}
'''
        return [{"path": "src/reports/report.controller.ts", "content": code}]

    def generate_pdf_generator(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh PDF generator service."""
        code = '''// PDF Generator Service — Wrapper cho Puppeteer để generate PDF.
// CP34: Report & Document Generator (NestJS)

import { Injectable } from "@nestjs/common";
import puppeteer from "puppeteer";

export interface ReportSpec {
  id: string;
  name: string;
  fields: string[];
  format: string;
  layout: string;
}

@Injectable()
export class PdfGeneratorService {
  /**
   * Generate PDF từ report spec và data.
   *
   * @param spec ReportSpec
   * @param data Data records
   * @returns Storage URL của PDF
   */
  async generate(spec: ReportSpec, data: any[]): Promise<string> {
    const html = this.buildHtml(spec, data);

    const browser = await puppeteer.launch({ headless: true });
    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: "networkidle0" });
    const pdfBuffer = await page.pdf({
      format: "A4",
      margin: { top: "2cm", right: "2cm", bottom: "2cm", left: "2cm" },
    });
    await page.close();
    await browser.close();

    // TODO: Lưu file qua storage service
    return `/storage/reports/${spec.id}.pdf`;
  }

  private buildHtml(spec: ReportSpec, data: any[]): string {
    const fields = spec.fields || (data.length > 0 ? Object.keys(data[0]) : []);

    let html = `<html><head><title>${spec.name}</title>`;
    html += `<style>`;
    html += `body { font-family: Arial, sans-serif; margin: 20px; }`;
    html += `table { border-collapse: collapse; width: 100%; }`;
    html += `th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }`;
    html += `th { background-color: #4CAF50; color: white; }`;
    html += `</style></head><body>`;
    html += `<h1>${spec.name}</h1>`;

    if (data.length > 0) {
      html += `<table><thead><tr>`;
      for (const f of fields) html += `<th>${f}</th>`;
      html += `</tr></thead><tbody>`;
      for (const row of data) {
        html += `<tr>`;
        for (const f of fields) html += `<td>${row[f] ?? ""}</td>`;
        html += `</tr>`;
      }
      html += `</tbody></table>`;
    } else {
      html += `<p>Không có dữ liệu.</p>`;
    }

    html += `</body></html>`;
    return html;
  }
}
'''
        return [{"path": "src/reports/pdf-generator.service.ts", "content": code}]

    def generate_excel_generator(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh Excel generator service."""
        code = '''// Excel Generator Service — Wrapper cho exceljs để generate Excel.
// CP34: Report & Document Generator (NestJS)

import { Injectable } from "@nestjs/common";
import * as ExcelJS from "exceljs";

export interface ReportSpec {
  id: string;
  name: string;
  fields: string[];
  format: string;
}

@Injectable()
export class ExcelGeneratorService {
  /**
   * Generate Excel file từ report spec và data.
   *
   * @param spec ReportSpec
   * @param data Data records
   * @returns Storage URL của Excel file
   */
  async generate(spec: ReportSpec, data: any[]): Promise<string> {
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet(spec.name.slice(0, 31));

    const fields = spec.fields || (data.length > 0 ? Object.keys(data[0]) : []);

    // Header
    worksheet.columns = fields.map((f) => ({
      header: f,
      key: f,
      width: Math.min(30, 50),
    }));

    // Header style
    worksheet.getRow(1).font = { bold: true, color: { argb: "FFFFFFFF" } };
    worksheet.getRow(1).fill = {
      type: "pattern",
      pattern: "solid",
      fgColor: { argb: "FF4CAF50" },
    };
    worksheet.getRow(1).alignment = { horizontal: "center", vertical: "center" };

    // Freeze header
    worksheet.views = [{ state: "frozen", ySplit: 1 }];

    // Data
    for (const row of data) {
      worksheet.addRow(row);
    }

    // Save
    const buffer = await workbook.xlsx.writeBuffer();
    // TODO: Lưu file qua storage service
    return `/storage/reports/${spec.id}.xlsx`;
  }
}
'''
        return [{"path": "src/reports/excel-generator.service.ts", "content": code}]

    def generate_csv_generator(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh CSV generator service."""
        code = '''// CSV Generator Service — Built-in CSV stringify.
// CP34: Report & Document Generator (NestJS)

import { Injectable } from "@nestjs/common";
import { parse, stringify } from "csv-stringify/sync";

export interface ReportSpec {
  id: string;
  name: string;
  fields: string[];
  format: string;
}

@Injectable()
export class CsvGeneratorService {
  /**
   * Generate CSV file từ report spec và data.
   *
   * @param spec ReportSpec
   * @param data Data records
   * @returns Storage URL của CSV file
   */
  async generate(spec: ReportSpec, data: any[]): Promise<string> {
    const fields = spec.fields || (data.length > 0 ? Object.keys(data[0]) : []);

    const csv = stringify(data, {
      header: true,
      columns: fields,
    });

    // TODO: Lưu file qua storage service
    return `/storage/reports/${spec.id}.csv`;
  }
}
'''
        return [{"path": "src/reports/csv-generator.service.ts", "content": code}]

    def generate_batch_worker(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh batch worker service."""
        code = '''// Batch Worker Service — Background worker cho batch document processing.
// CP34: Report & Document Generator (NestJS)
// Tích hợp với CP13 Workflow Runtime để execute batch jobs.

import { Injectable, Logger } from "@nestjs/common";
import { ReportService, ReportSpec } from "./report.service";

export interface BatchJob {
  id: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  reportSpecIds: string[];
  resultUrls?: string[];
  error?: string;
  retries: number;
  maxRetries: number;
}

@Injectable()
export class BatchWorkerService {
  private readonly logger = new Logger(BatchWorkerService.name);

  constructor(private readonly reportService: ReportService) {}

  /**
   * Execute batch job — generate tất cả reports trong job.
   *
   * @param job BatchJob instance
   */
  async executeJob(job: BatchJob): Promise<void> {
    job.status = "running";
    const resultUrls: string[] = [];

    try {
      for (const reportId of job.reportSpecIds) {
        try {
          const fileUrl = await this.reportService.generateReport(reportId);
          resultUrls.push(fileUrl);
          this.logger.log(`Report ${reportId} generated successfully`);
        } catch (error) {
          this.logger.error(`Failed to generate report ${reportId}: ${error}`);
          resultUrls.push(`error:${reportId}:${error.message}`);
        }
      }

      job.status = "completed";
      job.resultUrls = resultUrls;
      this.logger.log(`Batch job ${job.id} completed with ${resultUrls.length} results`);
    } catch (error) {
      const errorMsg = `Batch job failed: ${error.message}`;
      this.logger.error(errorMsg);

      if (job.retries < job.maxRetries) {
        job.retries += 1;
        this.logger.log(`Retrying job ${job.id} (attempt ${job.retries}/${job.maxRetries})`);
        await this.executeJob(job);
      } else {
        job.status = "failed";
        job.error = errorMsg;
      }
    }
  }

  /**
   * Hủy batch job đang chạy.
   */
  cancelJob(job: BatchJob): void {
    if (job.status !== "completed" && job.status !== "cancelled") {
      job.status = "cancelled";
      this.logger.log(`Batch job ${job.id} cancelled`);
    }
  }
}
'''
        return [{"path": "src/reports/batch-worker.service.ts", "content": code}]
