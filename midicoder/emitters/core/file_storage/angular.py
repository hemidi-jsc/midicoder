# coding: utf-8
"""
CP11: Angular File Storage Emitter.

Module này cung cấp AngularFileStorageEmitter để generate Angular file storage code
từ FileStorageCollection (CP11):
- file-storage.models.ts - FileInfo, UploadResult, StorageConfig, FileUploadProgress interfaces
- file-storage.service.ts - Angular service với HTTP client cho upload/download/delete/presigned-url
- file-upload.component.ts - Angular component với drag-drop, progress bar, preview
- file-storage.module.ts - NgModule để export storage providers
- index.ts - Barrel exports

KPI-029: Tenant-aware file storage qua header x-tenant-id.

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from midicoder.emitters.core.file_storage.models import FileStorageCollection, StorageBackend
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ============================================================================
# Generated File
# ============================================================================


@dataclass
class GeneratedFile:
    """
    File đã generate từ emitter.

    Attributes:
        path: Đường dẫn file
        content: Nội dung file
        template: Tên template
        capability: Core Capability code (CP11)
    """
    path: Path
    content: str
    template: str
    capability: str


# ============================================================================
# Angular File Storage Emitter
# ============================================================================


class AngularFileStorageEmitter:
    """
    Emitter cho Angular file storage code.

    Generate code từ FileStorageCollection cho:
    - src/app/core/storage/file-storage.models.ts
    - src/app/core/storage/file-storage.service.ts
    - src/app/core/storage/file-upload.component.ts
    - src/app/core/storage/file-storage.module.ts
    - src/app/core/storage/index.ts
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo AngularFileStorageEmitter.

        Args:
            stack_dir: Đường dẫn đến templates directory
        """
        self.stack_dir = stack_dir

    def emit(
        self,
        collection: FileStorageCollection,
        output_dir: Path,
    ) -> list[GeneratedFile]:
        """
        Emit Angular file storage code từ FileStorageCollection.

        Args:
            collection: FileStorageCollection instance
            output_dir: Output directory

        Returns:
            List of GeneratedFile instances

        Raises:
            MidicoderError: Nếu collection rỗng
        """
        if not collection.profiles:
            EM.raise_error(
                ErrorCode.CP11_MISSING_POLICY,
                detail="FileStorageCollection không có profiles để emit",
            )

        files: list[GeneratedFile] = []
        storage_dir = output_dir / "src" / "app" / "core" / "storage"
        storage_dir.mkdir(parents=True, exist_ok=True)

        files.append(self._emit_models(storage_dir))
        files.append(self._emit_file_storage_service(collection, storage_dir))
        files.append(self._emit_file_upload_component(storage_dir))
        files.append(self._emit_file_storage_module(collection, storage_dir))
        files.append(self._emit_index(storage_dir))

        return files

    def _emit_models(self, output_dir: Path) -> GeneratedFile:
        """Emit file-storage.models.ts - TypeScript interfaces cho file storage."""
        content = '''/**
 * File Storage Models - CP11.
 *
 * TypeScript interfaces cho file storage layer.
 * KPI-029: Tenant-aware file storage.
 */

/** Thông tin file đã lưu trữ */
export interface FileInfo {
  key: string;
  name: string;
  size: number;
  content_type: string;
  storage_url: string;
  tenant_id?: string;
  created_at: string;
  updated_at: string;
}

/** Kết quả từ file upload */
export interface UploadResult {
  key: string;
  url: string;
  size: number;
  content_type: string;
  filename: string;
  tenant_id?: string;
  success: boolean;
  error?: string;
}

/** Cấu hình storage backend */
export interface StorageConfig {
  backend: "s3" | "local";
  bucket?: string;
  region?: string;
  endpoint_url?: string;
  tenant_isolation: boolean;
  max_file_size: number;
  allowed_content_types: string[];
  allowed_extensions: string[];
}

/** Tiến độ upload file */
export interface FileUploadProgress {
  key: string;
  filename: string;
  loaded: number;
  total: number;
  percentage: number;
  status: "uploading" | "completed" | "error";
  error?: string;
}
'''
        file_path = output_dir / "file-storage.models.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="file_storage/file-storage.models.ts.jinja2", capability="CP11",
        )

    def _emit_file_storage_service(
        self,
        collection: FileStorageCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Emit file-storage.service.ts - Angular service cho file operations."""
        has_s3 = any(p.backend_type == StorageBackend.S3 for p in collection.profiles)
        has_local = any(p.backend_type == StorageBackend.LOCAL for p in collection.profiles)
        default_profile = collection.profiles[0].name if collection.profiles else "default"
        default_max_size = collection.policies[0].max_file_size if collection.policies else 10485760

        # Generate profile config lines
        profile_lines = ""
        for profile in collection.profiles:
            backend = profile.backend_type.value
            profile_lines += f"  {profile.name}: {{ backend: '{backend}', tenant_isolation: {profile.tenant_isolation}"
            if profile.bucket:
                profile_lines += f", bucket: '{profile.bucket}'"
            if profile.region:
                profile_lines += f", region: '{profile.region}'"
            if profile.endpoint_url:
                profile_lines += f", endpoint_url: '{profile.endpoint_url}'"
            profile_lines += " }},\n"

        # Generate policy config lines
        policy_lines = ""
        for policy in collection.policies:
            policy_lines += f"  {policy.name}: {{ max_file_size: {policy.max_file_size}, allowed_content_types: {policy.allowed_content_types!r}, allowed_extensions: {policy.allowed_extensions!r} }},\n"

        backend_desc = "S3 + Local" if has_s3 and has_local else ("S3" if has_s3 else "Local")

        content = (
            '/**\n'
            ' * File Storage Service - CP11.\n'
            ' *\n'
            ' * Service này xử lý file upload, download, delete, và presigned URL.\n'
            ' * KPI-029: Tenant-aware file storage qua header x-tenant-id.\n'
            ' * Sử dụng FormData cho upload file.\n'
            ' *\n'
            f' * Backends: {backend_desc}\n'
            f' * Default profile: {default_profile}\n'
            f' * Default max file size: {default_max_size} bytes\n'
            ' */\n'
            '\n'
            'import { Injectable } from "@angular/core";\n'
            'import { HttpClient, HttpHeaders, HttpEvent } from "@angular/common/http";\n'
            'import { Observable, BehaviorSubject, of } from "rxjs";\n'
            'import { FileInfo, UploadResult, StorageConfig, FileUploadProgress } from "./file-storage.models";\n'
            '\n'
            '@Injectable({\n'
            '  providedIn: "root",\n'
            '})\n'
            'export class FileStorageService {\n'
            '  private tenantId$ = new BehaviorSubject<string | undefined>(undefined);\n'
            f'  private defaultMaxSize = {default_max_size};\n'
            '\n'
            '  /** Storage profiles đã cấu hình */\n'
            '  private profiles: Record<string, StorageConfig> = {\n'
            + profile_lines
            + '  };\n'
            '\n'
            '  /** Upload policies đã cấu hình */\n'
            '  private policies: Record<string, { max_file_size: number; allowed_content_types: string[]; allowed_extensions: string[] }> = {\n'
            + policy_lines
            + '  };\n'
            '\n'
            f'  constructor(private http: HttpClient, private apiBase: string = "/api/v1") {{}}\n'
            '\n'
            '  /**\n'
            '   * Đặt tenant ID cho tenant isolation (KPI-029).\n'
            '   */\n'
            '  setTenantId(tenantId: string | undefined): void {\n'
            '    this.tenantId$.next(tenantId);\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Lấy HTTP headers với tenant ID (KPI-029).\n'
            '   */\n'
            '  private _buildHeaders(): HttpHeaders {\n'
            '    const headers = {\n'
            '      ...(this.tenantId$.value ? { "x-tenant-id": this.tenantId$.value } : {}),\n'
            '    };\n'
            '    return new HttpHeaders(headers);\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Upload file qua FormData.\n'
            '   *\n'
            '   * @param file File cần upload\n'
            '   * @param folder Folder destination (optional)\n'
            '   * @param profile Storage profile name (optional)\n'
            '   * @returns Observable của UploadResult\n'
            '   */\n'
            '  uploadFile(\n'
            '    file: File,\n'
            '    folder?: string,\n'
            '    profile?: string,\n'
            '  ): Observable<HttpEvent<UploadResult>> {\n'
            '    const formData = new FormData();\n'
            '    formData.append("file", file);\n'
            '    if (folder) {\n'
            '      formData.append("folder", folder);\n'
            '    }\n'
            '    if (profile) {\n'
            '      formData.append("profile", profile);\n'
            '    }\n'
            '\n'
            '    return this.http.post<UploadResult>(\n'
            '      `${this.apiBase}/storage/upload`,\n'
            '      formData,\n'
            '      { headers: this._buildHeaders() },\n'
            '    );\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Upload file với progress tracking.\n'
            '   *\n'
            '   * @param file File cần upload\n'
            '   * @param folder Folder destination (optional)\n'
            '   * @returns Observable với progress events\n'
            '   */\n'
            '  uploadFileWithProgress(\n'
            '    file: File,\n'
            '    folder?: string,\n'
            '  ): Observable<HttpEvent<any>> {\n'
            '    const formData = new FormData();\n'
            '    formData.append("file", file);\n'
            '    if (folder) {\n'
            '      formData.append("folder", folder);\n'
            '    }\n'
            '\n'
            '    return this.http.post<UploadResult>(\n'
            '      `${this.apiBase}/storage/upload`,\n'
            '      formData,\n'
            '      {\n'
            '        headers: this._buildHeaders(),\n'
            '        reportProgress: true,\n'
            '        observe: "events",\n'
            '      },\n'
            '    );\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Download file từ storage.\n'
            '   *\n'
            '   * @param key File key\n'
            '   * @returns Observable của Blob\n'
            '   */\n'
            '  downloadFile(key: string): Observable<Blob> {\n'
            '    return this.http.get(`${this.apiBase}/storage/download/${key}`, {\n'
            '      headers: this._buildHeaders(),\n'
            '      responseType: "blob",\n'
            '    });\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Xóa file khỏi storage.\n'
            '   *\n'
            '   * @param key File key\n'
            '   * @returns Observable của void\n'
            '   */\n'
            '  deleteFile(key: string): Observable<void> {\n'
            '    return this.http.delete<void>(\n'
            '      `${this.apiBase}/storage/delete/${key}`,\n'
            '      { headers: this._buildHeaders() },\n'
            '    );\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Lấy presigned URL cho file.\n'
            '   *\n'
            '   * @param key File key\n'
            '   * @param expiresIn Thời gian hết hạn (giây, mặc định 3600)\n'
            '   * @returns Observable của URL string\n'
            '   */\n'
            '  getPresignedUrl(key: string, expiresIn: number = 3600): Observable<string> {\n'
            '    return this.http.get<string>(\n'
            '      `${this.apiBase}/storage/presigned-url/${key}?expiresIn=${expiresIn}`,\n'
            '      { headers: this._buildHeaders(), responseType: "text" as "json" },\n'
            '    );\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Lấy thông tin file.\n'
            '   *\n'
            '   * @param key File key\n'
            '   * @returns Observable của FileInfo\n'
            '   */\n'
            '  getFileInfo(key: string): Observable<FileInfo> {\n'
            '    return this.http.get<FileInfo>(\n'
            '      `${this.apiBase}/storage/info/${key}`,\n'
            '      { headers: this._buildHeaders() },\n'
            '    );\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Lấy danh sách files trong folder.\n'
            '   *\n'
            '   * @param folder Folder path\n'
            '   * @returns Observable của FileInfo array\n'
            '   */\n'
            '  listFiles(folder: string = ""): Observable<FileInfo[]> {\n'
            '    return this.http.get<FileInfo[]>(\n'
            '      `${this.apiBase}/storage/list?folder=${encodeURIComponent(folder)}`,\n'
            '      { headers: this._buildHeaders() },\n'
            '    );\n'
            '  }\n'
            '\n'
            '  /**\n'
            '   * Validate file theo policy.\n'
            '   *\n'
            '   * @param file File cần validate\n'
            '   * @param policyName Policy name (optional)\n'
            '   * @returns True nếu file hợp lệ\n'
            '   */\n'
            '  validateFile(file: File, policyName?: string): boolean {\n'
            '    // Kiểm tra kích thước\n'
            '    if (file.size > this.defaultMaxSize) {\n'
            '      return false;\n'
            '    }\n'
            '\n'
            '    // Nếu có policy cụ thể, validate theo policy\n'
            '    if (policyName && this.policies[policyName]) {\n'
            '      const policy = this.policies[policyName];\n'
            '      if (file.size > policy.max_file_size) {\n'
            '        return false;\n'
            '      }\n'
            '      if (!policy.allowed_content_types.includes(file.type)) {\n'
            '        return false;\n'
            '      }\n'
            '      const ext = file.name.split(".").pop() || "";\n'
            '      if (!policy.allowed_extensions.includes(ext)) {\n'
            '        return false;\n'
            '      }\n'
            '    }\n'
            '\n'
            '    return true;\n'
            '  }\n'
            '}\n'
        )

        file_path = output_dir / "file-storage.service.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="file_storage/file-storage.service.ts.jinja2", capability="CP11",
        )

    def _emit_file_upload_component(self, output_dir: Path) -> GeneratedFile:
        """Emit file-upload.component.ts - Angular component cho file upload."""
        content = '''/**
 * File Upload Component - CP11.
 *
 * Angular component cho file upload với drag-drop, progress bar, preview.
 * KPI-029: Tenant-aware file upload.
 *
 * Sử dụng @Input() để cấu hình accept, maxSize, multiple.
 * Emit UploadResult qua @Output().
 */

import { Component, Input, Output, EventEmitter, ChangeDetectorRef } from "@angular/core";
import { HttpEventType } from "@angular/common/http";
import { FileStorageService } from "./file-storage.service";
import { UploadResult, FileUploadProgress } from "./file-storage.models";

@Component({
  selector: "app-file-upload",
  template: `
    <div
      class="file-upload"
      [class.dragging]="isDragging"
      (dragover)="onDragOver($event)"
      (dragleave)="onDragLeave($event)"
      (drop)="onDrop($event)"
    >
      <label class="file-upload-label">
        <input
          type="file"
          (change)="onFileSelected($event)"
          [multiple]="multiple"
          [accept]="accept"
          style="display: none"
        />
        <span class="file-upload-text">
          {{ isDragging ? "Thả file vào đây" : "Kéo thả file hoặc nhấn để chọn" }}
        </span>
      </label>

      <!-- Progress bar -->
      <div *ngIf="progress > 0" class="progress-bar" role="progressbar" [attr.aria-valuenow]="progress">
        <div class="progress-fill" [style.width.%]="progress"></div>
        <span class="progress-text">{{ progress }}%</span>
      </div>

      <!-- Upload status -->
      <div *ngIf="lastResult" class="upload-result">
        <span *ngIf="lastResult.success" class="success">✓ Upload thành công: {{ lastResult.filename }}</span>
        <span *ngIf="!lastResult.success" class="error">✗ Lỗi: {{ lastResult.error }}</span>
      </div>

      <!-- File preview -->
      <div *ngIf="previewUrl" class="file-preview">
        <img *ngIf="isImageFile" [src]="previewUrl" alt="Preview" />
        <div *ngIf="!isImageFile" class="preview-icon">📄 {{ selectedFile?.name }}</div>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
    }
    .file-upload {
      border: 2px dashed #ccc;
      border-radius: 8px;
      padding: 2rem;
      text-align: center;
      cursor: pointer;
      transition: border-color 0.2s;
    }
    .file-upload.dragging {
      border-color: #0066cc;
      background-color: #f0f7ff;
    }
    .file-upload-label {
      cursor: pointer;
      display: block;
    }
    .file-upload-text {
      font-size: 1rem;
      color: #666;
    }
    .progress-bar {
      margin-top: 1rem;
      background: #e0e0e0;
      border-radius: 4px;
      height: 24px;
      position: relative;
      overflow: hidden;
    }
    .progress-fill {
      height: 100%;
      background: #0066cc;
      transition: width 0.3s ease;
    }
    .progress-text {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 0.85rem;
      font-weight: bold;
      color: #fff;
    }
    .upload-result {
      margin-top: 0.5rem;
      font-size: 0.9rem;
    }
    .success { color: #28a745; }
    .error { color: #dc3545; }
    .file-preview {
      margin-top: 1rem;
      text-align: center;
    }
    .file-preview img {
      max-width: 200px;
      max-height: 200px;
      border-radius: 4px;
    }
  `],
})
export class FileUploadComponent {
  /** MIME types được phép (ví dụ: "image/*" hoặc "application/pdf") */
  @Input() accept: string = "*";

  /** Kích thước tối đa của file (bytes) - mặc định 10MB */
  @Input() maxSize: number = 10485760;

  /** Cho phép chọn nhiều file */
  @Input() multiple: boolean = false;

  /** Folder destination cho file */
  @Input() folder: string = "";

  /** Emit UploadResult khi upload hoàn tất */
  @Output() uploaded = new EventEmitter<UploadResult>();

  /** Emit FileUploadProgress khi có thay đổi tiến độ */
  @Output() progressChanged = new EventEmitter<FileUploadProgress>();

  /** Tiến độ upload hiện tại (phần trăm) */
  progress: number = 0;

  /** Đang có file được kéo vào vùng drop */
  isDragging: boolean = false;

  /** File đang được chọn */
  selectedFile: File | null = null;

  /** URL preview cho file ảnh */
  previewUrl: string = "";

  /** Kết quả upload cuối cùng */
  lastResult: UploadResult | null = null;

  /** Loại file có phải là image không */
  isImageFile: boolean = false;

  constructor(
    private fileStorageService: FileStorageService,
    private cdr: ChangeDetectorRef,
  ) {}

  /**
   * Xử lý khi kéo file vào vùng drop.
   */
  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  /**
   * Xử lý khi kéo file ra khỏi vùng drop.
   */
  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  /**
   * Xử lý khi thả file vào vùng drop.
   */
  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.handleFiles(Array.from(files));
    }
  }

  /**
   * Xử lý khi chọn file qua input.
   */
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const files = input.files;
    if (files && files.length > 0) {
      this.handleFiles(Array.from(files));
    }
  }

  /**
   * Xử lý danh sách files - validate và upload.
   */
  private handleFiles(files: File[]): void {
    for (const file of files) {
      // Validate kích thước
      if (file.size > this.maxSize) {
        const error: UploadResult = {
          key: "",
          url: "",
          size: file.size,
          content_type: file.type,
          filename: file.name,
          success: false,
          error: `File quá lớn: ${(file.size / 1024 / 1024).toFixed(2)}MB > ${(this.maxSize / 1024 / 1024).toFixed(2)}MB`,
        };
        this.uploaded.emit(error);
        continue;
      }

      // Tạo preview nếu là image
      this.createPreview(file);

      // Upload file
      this.uploadSingleFile(file);
    }
  }

  /**
   * Tạo preview URL cho file ảnh.
   */
  private createPreview(file: File): void {
    this.selectedFile = file;
    if (file.type.startsWith("image/")) {
      this.isImageFile = true;
      const reader = new FileReader();
      reader.onload = () => {
        this.previewUrl = reader.result as string;
        this.cdr.detectChanges();
      };
      reader.readAsDataURL(file);
    } else {
      this.isImageFile = false;
      this.previewUrl = "";
    }
  }

  /**
   * Upload một file đơn với progress tracking.
   */
  private uploadSingleFile(file: File): void {
    this.progress = 0;

    this.fileStorageService
      .uploadFileWithProgress(file, this.folder)
      .subscribe({
        next: (event) => {
          if (event.type === HttpEventType.UploadProgress && event.total) {
            this.progress = Math.round((100 * event.loaded) / event.total);
            this.progressChanged.emit({
              key: "",
              filename: file.name,
              loaded: event.loaded,
              total: event.total,
              percentage: this.progress,
              status: "uploading",
            });
          } else if (event.type === HttpEventType.Response) {
            this.progress = 100;
            const body = event.body as UploadResult;
            this.lastResult = { ...body, success: true };
            this.uploaded.emit(this.lastResult);
            this.progressChanged.emit({
              key: body.key,
              filename: file.name,
              loaded: body.size,
              total: body.size,
              percentage: 100,
              status: "completed",
            });
          }
        },
        error: (error) => {
          this.progress = 0;
          const errorResult: UploadResult = {
            key: "",
            url: "",
            size: file.size,
            content_type: file.type,
            filename: file.name,
            success: false,
            error: error.message || "Upload thất bại",
          };
          this.lastResult = errorResult;
          this.uploaded.emit(errorResult);
          this.progressChanged.emit({
            key: "",
            filename: file.name,
            loaded: 0,
            total: file.size,
            percentage: 0,
            status: "error",
            error: errorResult.error,
          });
        },
      });
  }
}
'''
        file_path = output_dir / "file-upload.component.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="file_storage/file-upload.component.ts.jinja2", capability="CP11",
        )

    def _emit_file_storage_module(
        self,
        collection: FileStorageCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Emit file-storage.module.ts - NgModule cho file storage."""
        has_s3 = any(p.backend_type == StorageBackend.S3 for p in collection.profiles)
        has_local = any(p.backend_type == StorageBackend.LOCAL for p in collection.profiles)
        backend_desc = "S3 + Local" if has_s3 and has_local else ("S3" if has_s3 else "Local")

        content_lines = [
            "/**",
            " * File Storage Module - CP11.",
            " *",
            " * Module nay cung cap file storage services va components.",
            " * KPI-029: Tenant-aware file storage.",
            " *",
            f" * Backends: {backend_desc}",
            " */",
            "",
            'import { NgModule } from "@angular/core";',
            'import { CommonModule } from "@angular/common";',
            'import { HttpClientModule } from "@angular/common/http";',
            'import { FileStorageService } from "./file-storage.service";',
            'import { FileUploadComponent } from "./file-upload.component";',
            "",
            "@NgModule({",
            "  imports: [CommonModule, HttpClientModule],",
            "  declarations: [FileUploadComponent],",
            "  exports: [FileUploadComponent],",
            "  providers: [FileStorageService],",
            "})",
            "export class FileStorageModule {}",
        ]
        content = "\n".join(content_lines)
        file_path = output_dir / "file-storage.module.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="file_storage/file-storage.module.ts.jinja2", capability="CP11",
        )

    def _emit_index(self, output_dir: Path) -> GeneratedFile:
        """Emit index.ts - Barrel exports."""
        content = '''/**
 * File Storage Module Exports - CP11.
 */
export * from "./file-storage.models";
export * from "./file-storage.service";
export * from "./file-upload.component";
export * from "./file-storage.module";
'''
        file_path = output_dir / "index.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="file_storage/index.ts.jinja2", capability="CP11",
        )


# ============================================================================
# Convenience Function
# ============================================================================


def emit_angular_file_storage(
    collection: FileStorageCollection,
    stack_dir: Path,
    output_dir: Path,
) -> list[GeneratedFile]:
    """
    Emit Angular file storage code từ FileStorageCollection.

    Args:
        collection: FileStorageCollection instance
        stack_dir: Templates directory
        output_dir: Output directory

    Returns:
        List of GeneratedFile instances
    """
    emitter = AngularFileStorageEmitter(stack_dir)
    return emitter.emit(collection, output_dir)
