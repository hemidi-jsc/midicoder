# coding: utf-8
"""
CP11: React File Storage Emitter.

Module này cung cấp ReactFileStorageEmitter để generate React file storage code
từ FileStorageCollection (CP11):
- fileStorage.types.ts - FileInfo, UploadResult, FileStorageContextType, CdnConfig interfaces
- FileStorageProvider.tsx - React context provider với upload/download/delete operations
- useFileStorage.ts - Custom hook để truy cập file storage
- FileUpload.tsx - React component với drag-drop, preview, progress
- index.ts - Barrel exports

KPI-029: Tenant-aware file storage qua header x-tenant-id.
CDN: AWS CloudFront integration với CDN URL resolution.

Author: Midicoder Team
Version: 1.1.0
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from midicoder.emitters.core.cp11_file_media.models import FileStorageCollection, StorageBackend
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
# React File Storage Emitter
# ============================================================================


class ReactFileStorageEmitter:
    """
    Emitter cho React file storage code.

    Generate code từ FileStorageCollection cho:
    - src/storage/fileStorage.types.ts
    - src/storage/FileStorageProvider.tsx
    - src/storage/useFileStorage.ts
    - src/storage/FileUpload.tsx
    - src/storage/index.ts
    """

    def __init__(self, stack_dir: Path) -> None:
        """
        Khởi tạo ReactFileStorageEmitter.

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
        Emit React file storage code từ FileStorageCollection.

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
        storage_dir = output_dir / "src" / "storage"
        storage_dir.mkdir(parents=True, exist_ok=True)

        files.append(self._emit_types(collection, storage_dir))
        files.append(self._emit_file_storage_provider(collection, storage_dir))
        files.append(self._emit_use_file_storage(storage_dir))
        files.append(self._emit_file_upload_component(storage_dir))
        files.append(self._emit_index(storage_dir))

        return files

    def _emit_types(
        self,
        collection: FileStorageCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Emit fileStorage.types.ts - TypeScript interfaces cho file storage."""
        default_max_size = collection.policies[0].max_file_size if collection.policies else 10485760

        content = f'''/**
 * File Storage Types - CP11.
 *
 * TypeScript interfaces cho file storage layer.
 * KPI-029: Tenant-aware file storage.
 */

/** Thông tin file đã lưu trữ */
export interface FileInfo {{
  key: string;
  name: string;
  size: number;
  content_type: string;
  storage_url: string;
  tenant_id?: string;
  created_at: string;
  updated_at: string;
}}

/** Kết quả từ file upload */
export interface UploadResult {{
  key: string;
  url: string;
  size: number;
  content_type: string;
  filename: string;
  tenant_id?: string;
  success: boolean;
  error?: string;
}}

/** Cấu hình storage backend */
export interface StorageConfig {{
  backend: "s3" | "local";
  bucket?: string;
  region?: string;
  endpoint_url?: string;
  tenant_isolation: boolean;
  max_file_size: number;
  allowed_content_types: string[];
  allowed_extensions: string[];
}}

/** Tiến độ upload file */
export interface FileUploadProgress {{
  key: string;
  filename: string;
  loaded: number;
  total: number;
  percentage: number;
  status: "uploading" | "completed" | "error";
  error?: string;
}}

/** Cấu hình CDN (AWS CloudFront) */
export interface CdnConfig {{
  distribution_id?: string;
  domain?: string;
  origin_bucket?: string;
  signed_url: boolean;
  default_ttl: number;
  max_ttl: number;
}}

/** Context type cho FileStorageProvider */
export interface FileStorageContextType {{
  uploadFile: (file: File, folder?: string) => Promise<UploadResult>;
  downloadFile: (key: string) => Promise<Blob>;
  deleteFile: (key: string) => Promise<void>;
  getPresignedUrl: (key: string) => Promise<string>;
  getFileInfo: (key: string) => Promise<FileInfo>;
  listFiles: (folder?: string) => Promise<FileInfo[]>;
  tenantId: string | undefined;
  setTenantId: (id: string | undefined) => void;
  apiBase: string;
  defaultMaxSize: number;
}}

/** Props cho FileStorageProvider */
export interface FileStorageProviderProps {{
  children: React.ReactNode;
  apiBase?: string;
  initialTenantId?: string;
  defaultMaxSize?: number;
}}
'''
        file_path = output_dir / "fileStorage.types.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="file_storage/fileStorage.types.ts.jinja2", capability="CP11",
        )

    def _emit_file_storage_provider(
        self,
        collection: FileStorageCollection,
        output_dir: Path,
    ) -> GeneratedFile:
        """Emit FileStorageProvider.tsx - React context provider cho file storage."""
        has_s3 = any(p.backend_type == StorageBackend.S3 for p in collection.profiles)
        has_local = any(p.backend_type == StorageBackend.LOCAL for p in collection.profiles)
        backend_desc = "S3 + Local" if has_s3 and has_local else ("S3" if has_s3 else "Local")
        default_max_size = collection.policies[0].max_file_size if collection.policies else 10485760

        content = f'''/**
 * File Storage Provider - CP11.
 *
 * React context để cung cấp file storage operations cho toàn bộ app.
 * KPI-029: Tenant-aware file storage qua header x-tenant-id.
 * Sử dụng fetch API cho HTTP operations.
 *
 * Backends: {backend_desc}
 * Default max file size: {default_max_size} bytes
 */

import {{
  createContext,
  useContext,
  useState,
  useCallback,
  ReactNode,
}} from "react";
import {{
  FileStorageContextType,
  UploadResult,
  FileInfo,
  FileStorageProviderProps,
}} from "./fileStorage.types";

const FileStorageContext = createContext<FileStorageContextType | undefined>(undefined);

export {{ FileStorageContext }};

/** FileStorageProvider - wrap app để cung cấp file storage context */
export function FileStorageProvider({{
  children,
  apiBase = "/api/v1",
  initialTenantId,
  defaultMaxSize = {default_max_size},
}}: FileStorageProviderProps) {{
  const [tenantId, setTenantIdState] = useState<string | undefined>(initialTenantId);

  /** Xây dựng headers với tenant ID (KPI-029) */
  const _buildHeaders = useCallback((): Record<string, string> => {{
    const headers: Record<string, string> = {{
      "Content-Type": undefined as any, // để fetch tự set hoặc FormData
    }};
    if (tenantId) {{
      headers["x-tenant-id"] = tenantId;
    }}
    return headers;
  }}, [tenantId]);

  /**
   * Upload file qua FormData (KPI-029: tenant-aware).
   *
   * @param file File cần upload
   * @param folder Folder destination (optional)
   * @returns UploadResult
   */
  const uploadFile = useCallback(async (
    file: File,
    folder?: string,
  ): Promise<UploadResult> => {{
    const formData = new FormData();
    formData.append("file", file);
    if (folder) {{
      formData.append("folder", folder);
    }}

    const headers: Record<string, string> = {{}};
    if (tenantId) {{
      headers["x-tenant-id"] = tenantId;
    }}

    const response = await fetch(`${{apiBase}}/storage/upload`, {{
      method: "POST",
      headers,
      body: formData,
    }});

    if (!response.ok) {{
      const errorText = await response.text();
      throw new Error(`Upload thất bại: ${{response.status}} - ${{errorText}}`);
    }}

    const result: UploadResult = await response.json();
    result.success = true;
    return result;
  }}, [apiBase, tenantId]);

  /**
   * Download file từ storage (KPI-029: tenant-aware).
   *
   * @param key File key
   * @returns Blob
   */
  const downloadFile = useCallback(async (key: string): Promise<Blob> => {{
    const headers: Record<string, string> = {{}};
    if (tenantId) {{
      headers["x-tenant-id"] = tenantId;
    }}

    const response = await fetch(`${{apiBase}}/storage/download/${{encodeURIComponent(key)}}`, {{
      method: "GET",
      headers,
    }});

    if (!response.ok) {{
      throw new Error(`Download thất bại: ${{response.status}}`);
    }}

    return response.blob();
  }}, [apiBase, tenantId]);

  /**
   * Xóa file khỏi storage (KPI-029: tenant-aware).
   *
   * @param key File key
   */
  const deleteFile = useCallback(async (key: string): Promise<void> => {{
    const headers: Record<string, string> = {{}};
    if (tenantId) {{
      headers["x-tenant-id"] = tenantId;
    }}

    const response = await fetch(`${{apiBase}}/storage/delete/${{encodeURIComponent(key)}}`, {{
      method: "DELETE",
      headers,
    }});

    if (!response.ok) {{
      throw new Error(`Xóa file thất bại: ${{response.status}}`);
    }}
  }}, [apiBase, tenantId]);

  /**
   * Lấy presigned URL cho file (KPI-029: tenant-aware).
   *
   * @param key File key
   * @param expiresIn Thời gian hết hạn (giây, mặc định 3600)
   * @returns URL string
   */
  const getPresignedUrl = useCallback(async (
    key: string,
    expiresIn: number = 3600,
  ): Promise<string> => {{
    const headers: Record<string, string> = {{}};
    if (tenantId) {{
      headers["x-tenant-id"] = tenantId;
    }}

    const response = await fetch(
      `${{apiBase}}/storage/presigned-url/${{encodeURIComponent(key)}}?expiresIn=${{expiresIn}}`,
      {{ method: "GET", headers }},
    );

    if (!response.ok) {{
      throw new Error(`Lấy presigned URL thất bại: ${{response.status}}`);
    }}

    return response.text();
  }}, [apiBase, tenantId]);

  /**
   * Lấy thông tin file (KPI-029: tenant-aware).
   *
   * @param key File key
   * @returns FileInfo
   */
  const getFileInfo = useCallback(async (key: string): Promise<FileInfo> => {{
    const headers: Record<string, string> = {{}};
    if (tenantId) {{
      headers["x-tenant-id"] = tenantId;
    }}

    const response = await fetch(`${{apiBase}}/storage/info/${{encodeURIComponent(key)}}`, {{
      method: "GET",
      headers,
    }});

    if (!response.ok) {{
      throw new Error(`Lấy thông tin file thất bại: ${{response.status}}`);
    }}

    return response.json();
  }}, [apiBase, tenantId]);

  /**
   * Lấy danh sách files trong folder (KPI-029: tenant-aware).
   *
   * @param folder Folder path (optional)
   * @returns FileInfo array
   */
  const listFiles = useCallback(async (folder: string = ""): Promise<FileInfo[]> => {{
    const headers: Record<string, string> = {{}};
    if (tenantId) {{
      headers["x-tenant-id"] = tenantId;
    }}

    const response = await fetch(
      `${{apiBase}}/storage/list?folder=${{encodeURIComponent(folder)}}`,
      {{ method: "GET", headers }},
    );

    if (!response.ok) {{
      throw new Error(`Lấy danh sách file thất bại: ${{response.status}}`);
    }}

    return response.json();
  }}, [apiBase, tenantId]);

  /** Đặt tenant ID (KPI-029) */
  const setTenantId = useCallback((id: string | undefined) => {{
    setTenantIdState(id);
  }}, []);

  const value: FileStorageContextType = {{
    uploadFile,
    downloadFile,
    deleteFile,
    getPresignedUrl,
    getFileInfo,
    listFiles,
    tenantId,
    setTenantId,
    apiBase,
    defaultMaxSize,
  }};

  return (
    <FileStorageContext.Provider value={{value}}>
      {{children}}
    </FileStorageContext.Provider>
  );
}}
'''
        file_path = output_dir / "FileStorageProvider.tsx"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="file_storage/FileStorageProvider.tsx.jinja2", capability="CP11",
        )

    def _emit_use_file_storage(self, output_dir: Path) -> GeneratedFile:
        """Emit useFileStorage.ts - Custom hook cho file storage."""
        content = '''/**
 * useFileStorage Hook - CP11.
 *
 * Custom hook để sử dụng file storage từ FileStorageProvider context.
 * KPI-029: Tenant-aware file storage.
 */

import { useContext } from "react";
import { FileStorageContext } from "./FileStorageProvider";
import { FileStorageContextType, CdnConfig } from "./fileStorage.types";

/**
 * Hook để truy cập file storage operations.
 *
 * @throws Error nếu dùng bên ngoài FileStorageProvider
 *
 * @example
 *   const { uploadFile, downloadFile, deleteFile } = useFileStorage();
 *   const result = await uploadFile(myFile, "documents");
 */
export function useFileStorage(): FileStorageContextType {
  const context = useContext(FileStorageContext);

  if (context === undefined) {
    throw new Error("useFileStorage phải dùng bên trong FileStorageProvider");
  }

  return context;
}

/**
 * Resolve file URL - CDN first, then fallback to S3 presigned.
 *
 * @param key File key trong storage
 * @param cdnDomain CDN domain (tùy chọn)
 * @returns URL string
 */
export function resolveFileUrl(key: string, cdnDomain?: string): string {
  if (cdnDomain) {
    return `https://${cdnDomain}/${key.replace(/^\\/+/, '')}`;
  }
  return '';
}
'''
        file_path = output_dir / "useFileStorage.ts"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="file_storage/useFileStorage.ts.jinja2", capability="CP11",
        )

    def _emit_file_upload_component(self, output_dir: Path) -> GeneratedFile:
        """Emit FileUpload.tsx - React component cho file upload."""
        content = '''/**
 * File Upload Component - CP11.
 *
 * React component cho file upload với drag-drop, preview, progress.
 * KPI-029: Tenant-aware file upload.
 *
 * Sử dụng useState cho progress và dragged state.
 * Accept, maxSize, onUpload props để cấu hình.
 */

import { useState, useCallback, DragEvent, ChangeEvent } from "react";
import { useFileStorage } from "./useFileStorage";
import { UploadResult } from "./fileStorage.types";

export interface FileUploadProps {
  /** MIME types được phép (ví dụ: "image/*" hoặc "application/pdf") */
  accept?: string;
  /** Kích thước tối đa của file (bytes) - mặc định 10MB */
  maxSize?: number;
  /** Cho phép chọn nhiều file */
  multiple?: boolean;
  /** Callback khi upload hoàn tất */
  onUpload?: (result: UploadResult) => void;
  /** Folder destination cho file */
  folder?: string;
}

export function FileUpload({
  accept = "*",
  maxSize = 10485760,
  multiple = false,
  onUpload,
  folder,
}: FileUploadProps) {
  const [progress, setProgress] = useState(0);
  const [dragged, setDragged] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<UploadResult | null>(null);
  const [uploading, setUploading] = useState(false);
  const { uploadFile } = useFileStorage();

  /** Xử lý khi kéo file vào vùng drop */
  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragged(true);
  }, []);

  /** Xử lý khi kéo file ra khỏi vùng drop */
  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragged(false);
  }, []);

  /** Xử lý khi thả file vào vùng drop */
  const handleDrop = useCallback(
    async (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setDragged(false);

      const files = e.dataTransfer.files;
      if (files && files.length > 0) {
        await processFiles(Array.from(files));
      }
    },
    [uploadFile],
  );

  /** Xử lý khi chọn file qua input */
  const handleFileSelect = useCallback(
    async (e: ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        await processFiles(Array.from(files));
        // Reset input để có thể chọn lại cùng file
        e.target.value = "";
      }
    },
    [uploadFile],
  );

  /** Xử lý danh sách files - validate và upload */
  const processFiles = useCallback(
    async (files: File[]) => {
      for (const file of files) {
        // Validate kích thước
        if (file.size > maxSize) {
          const error: UploadResult = {
            key: "",
            url: "",
            size: file.size,
            content_type: file.type,
            filename: file.name,
            success: false,
            error: `File quá lớn: ${(file.size / 1024 / 1024).toFixed(2)}MB > ${(maxSize / 1024 / 1024).toFixed(2)}MB`,
          };
          setLastResult(error);
          onUpload?.(error);
          continue;
        }

        // Tạo preview nếu là image
        if (file.type.startsWith("image/")) {
          const reader = new FileReader();
          reader.onload = () => setPreviewUrl(reader.result as string);
          reader.readAsDataURL(file);
        } else {
          setPreviewUrl(null);
        }

        // Upload file
        setUploading(true);
        setProgress(0);
        try {
          const result = await uploadFile(file, folder);
          setProgress(100);
          setLastResult(result);
          onUpload?.(result);
        } catch (error) {
          setProgress(0);
          const errorResult: UploadResult = {
            key: "",
            url: "",
            size: file.size,
            content_type: file.type,
            filename: file.name,
            success: false,
            error: error instanceof Error ? error.message : "Upload thất bại",
          };
          setLastResult(errorResult);
          onUpload?.(errorResult);
        } finally {
          setUploading(false);
        }
      }
    },
    [uploadFile, folder, maxSize, onUpload],
  );

  return (
    <div
      className={{
        "file-upload": true,
        "file-upload--dragging": dragged,
        "file-upload--uploading": uploading,
      }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <label className="file-upload__label">
        <input
          type="file"
          className="file-upload__input"
          onChange={handleFileSelect}
          multiple={multiple}
          accept={accept}
          disabled={uploading}
        />
        <span className="file-upload__text">
          {dragged ? "Thả file vào đây" : "Kéo thả file hoặc nhấn để chọn"}
        </span>
      </label>

      {/* Progress bar */}
      {progress > 0 && (
        <div className="file-upload__progress" role="progressbar" aria-valuenow={progress}>
          <div className="file-upload__progress-fill" style={{ width: `${progress}%` }} />
          <span className="file-upload__progress-text">{progress}%</span>
        </div>
      )}

      {/* Upload result */}
      {lastResult && (
        <div className={{
          "file-upload__result": true,
          "file-upload__result--success": lastResult.success,
          "file-upload__result--error": !lastResult.success,
        }}>
          {lastResult.success ? (
            <span>✓ Upload thành công: {lastResult.filename}</span>
          ) : (
            <span>✗ Lỗi: {lastResult.error}</span>
          )}
        </div>
      )}

      {/* File preview */}
      {previewUrl && (
        <div className="file-upload__preview">
          <img src={previewUrl} alt="Preview" />
        </div>
      )}
    </div>
  );
}
'''
        file_path = output_dir / "FileUpload.tsx"
        file_path.write_text(content, encoding="utf-8")
        return GeneratedFile(
            path=file_path, content=content,
            template="file_storage/FileUpload.tsx.jinja2", capability="CP11",
        )

    def _emit_index(self, output_dir: Path) -> GeneratedFile:
        """Emit index.ts - Barrel exports."""
        content = '''/**
 * File Storage Module Exports - CP11.
 */
export * from "./fileStorage.types";
export * from "./FileStorageProvider";
export * from "./useFileStorage";
export * from "./FileUpload";
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


def emit_react_file_storage(
    collection: FileStorageCollection,
    stack_dir: Path,
    output_dir: Path,
) -> list[GeneratedFile]:
    """
    Emit React file storage code từ FileStorageCollection.

    Args:
        collection: FileStorageCollection instance
        stack_dir: Templates directory
        output_dir: Output directory

    Returns:
        List of GeneratedFile instances
    """
    emitter = ReactFileStorageEmitter(stack_dir)
    return emitter.emit(collection, output_dir)
