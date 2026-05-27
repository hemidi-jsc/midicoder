# coding: utf-8
"""
Mô-đun React emitter cho Report & Document Generator (CP34).

Emit code React cho:
- ReportList.tsx: Danh sách reports có thể generate
- ReportViewer.tsx: Xem report (PDF embed, Excel table)
- BatchStatus.tsx: Progress indicator cho batch job

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path

from midicoder.packs.cp34_reporting.models import (
    ReportCollection,
)
from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


class ReactReportEmitter:
    """Emitter sinh code React cho report viewer components."""

    def emit(
        self, collection: ReportCollection, output_dir: Path | None = None
    ) -> list[dict[str, str]]:
        """
        Generate toàn bộ React components từ ReportCollection.

        Args:
            collection: ReportCollection chứa report specs
            output_dir: Output directory (optional)

        Returns:
            List của {path, content} cho mỗi file
        """
        if not collection.reports:
            EM.raise_error(ErrorCode.CP34_REPORT_SPEC_INVALID, reason="Collection trống")

        result: list[dict[str, str]] = []
        result.extend(self.generate_report_list(collection))
        result.extend(self.generate_report_viewer(collection))
        result.extend(self.generate_batch_status(collection))
        return result

    def generate_report_list(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh ReportList.tsx."""
        code = '''// Report List — Hiển thị danh sách reports có thể generate.
// CP34: Report & Document Generator (React)

import React, { useState, useEffect } from "react";

export interface ReportMeta {
  id: string;
  name: string;
  entity: string;
  format: string;
  layout: string;
  description: string;
}

const ReportList: React.FC = () => {
  const [reports, setReports] = useState<ReportMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/reports")
      .then((res) => res.json())
      .then((data) => {
        setReports(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const handleGenerate = async (reportId: string) => {
    try {
      const res = await fetch(`/api/reports/${reportId}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      window.open(data.file_url, "_blank");
    } catch (err) {
      console.error("Failed to generate report:", err);
    }
  };

  if (loading) return <div>Đang tải danh sách báo cáo...</div>;
  if (error) return <div className="error">Lỗi: {error}</div>;

  return (
    <div className="report-list">
      <h2>Danh sách Báo cáo</h2>
      <div className="report-grid">
        {reports.map((report) => (
          <div key={report.id} className="report-card">
            <h3>{report.name}</h3>
            <p className="entity">{report.entity}</p>
            <span className="format-badge">{report.format}</span>
            <p className="description">{report.description}</p>
            <button onClick={() => handleGenerate(report.id)}>Generate</button>
          </div>
        ))}
      </div>
      <style jsx>{`
        .report-list { padding: 20px; }
        .report-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 16px;
        }
        .report-card {
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 16px;
          cursor: pointer;
          transition: box-shadow 0.2s;
        }
        .report-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
        .format-badge {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 4px;
          background: #4CAF50;
          color: white;
          font-size: 12px;
        }
        .entity { color: #666; margin: 4px 0; }
        .description { color: #888; font-size: 14px; }
        button {
          margin-top: 8px;
          padding: 8px 16px;
          background: #4CAF50;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }
      `}</style>
    </div>
  );
};

export default ReportList;
'''
        return [{"path": "src/components/reports/ReportList.tsx", "content": code}]

    def generate_report_viewer(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh ReportViewer.tsx."""
        code = '''// Report Viewer — Hiển thị report trong browser.
// CP34: Report & Document Generator (React)
// Hỗ trợ: PDF embed (iframe), Excel table.

import React, { useState, useEffect } from "react";

export interface ViewerConfig {
  reportId: string;
  format: "pdf" | "xlsx" | "csv";
  autoGenerate?: boolean;
}

interface ReportViewerProps {
  config: ViewerConfig;
  title?: string;
}

const ReportViewer: React.FC<ReportViewerProps> = ({
  config,
  title = "Xem Báo cáo",
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileUrl, setFileUrl] = useState<string>("");

  const generate = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`/api/reports/${config.reportId}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      const data = await res.json();
      setFileUrl(data.file_url);
    } catch (err) {
      setError(`Tạo báo cáo thất bại: ${(err as Error).message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (config.autoGenerate !== false) {
      generate();
    }
  }, [config.reportId]);

  return (
    <div className="report-viewer">
      <div className="viewer-header">
        <h2>{title}</h2>
        <div className="actions">
          <button onClick={generate}>Tạo lại</button>
          {fileUrl && (
            <button onClick={() => window.open(fileUrl, "_blank")}>
              Tải xuống
            </button>
          )}
        </div>
      </div>

      {config.format === "pdf" && fileUrl && (
        <iframe src={fileUrl} className="pdf-frame" title="PDF Viewer" />
      )}

      {config.format !== "pdf" && fileUrl && (
        <div className="download-prompt">
          <p>Báo cáo sẽ được tải xuống dưới định dạng {config.format}.</p>
          <button onClick={() => window.open(fileUrl, "_blank")}>
            Tải xuống
          </button>
        </div>
      )}

      {loading && <div className="loading">Đang tạo báo cáo...</div>}
      {error && <div className="error">{error}</div>}

      <style jsx>{`
        .report-viewer { padding: 20px; }
        .viewer-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        .pdf-frame {
          width: 100%;
          height: 80vh;
          border: 1px solid #ddd;
          border-radius: 4px;
        }
        .loading { text-align: center; padding: 40px; color: #666; }
        .error { text-align: center; padding: 40px; color: red; }
        button {
          padding: 8px 16px;
          background: #4CAF50;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          margin-left: 8px;
        }
      `}</style>
    </div>
  );
};

export default ReportViewer;
'''
        return [{"path": "src/components/reports/ReportViewer.tsx", "content": code}]

    def generate_batch_status(self, collection: ReportCollection) -> list[dict[str, str]]:
        """Sinh BatchStatus.tsx."""
        code = '''// Batch Status — Progress indicator cho batch job.
// CP34: Report & Document Generator (React)

import React, { useState, useEffect } from "react";

export interface BatchJobStatus {
  id: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  reportSpecIds: string[];
  resultUrls: string[];
  error: string;
}

interface BatchStatusProps {
  jobId: string;
}

const statusLabels: Record<string, string> = {
  pending: "Đang chờ",
  running: "Đang chạy",
  completed: "Hoàn thành",
  failed: "Thất bại",
  cancelled: "Đã hủy",
};

const BatchStatus: React.FC<BatchStatusProps> = ({ jobId }) => {
  const [job, setJob] = useState<BatchJobStatus | null>(null);

  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch(`/api/reports/batch/${jobId}`);
        const data = await res.json();
        setJob(data);
        if (
          data.status === "completed" ||
          data.status === "failed" ||
          data.status === "cancelled"
        ) {
          clearInterval(timer);
        }
      } catch (err) {
        console.error("Failed to poll batch status:", err);
      }
    };

    poll();
    const timer = setInterval(poll, 3000);
    return () => clearInterval(timer);
  }, [jobId]);

  if (!job) return <div>Đang tải trạng thái...</div>;

  const completedCount = job.resultUrls?.length || 0;
  const totalCount = job.reportSpecIds?.length || 0;
  const progressPercent =
    totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <div className="batch-status">
      <h3>Trạng thái Batch Job</h3>
      <span className={`status-badge ${job.status}`}>
        {statusLabels[job.status] || "Không rõ"}
      </span>

      {job.status === "running" && (
        <div className="progress">
          <div
            className="progress-bar"
            style={{ width: `${progressPercent}%` }}
          />
          <p>
            {completedCount} / {totalCount} báo cáo
          </p>
        </div>
      )}

      {job.status === "completed" && (
        <div className="results">
          <h4>Kết quả ({job.resultUrls.length}):</h4>
          <ul>
            {job.resultUrls.map((url, i) => (
              <li key={i}>
                <a href={url} target="_blank" rel="noopener noreferrer">
                  Báo cáo {i + 1}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}

      {job.status === "failed" && <div className="error">{job.error}</div>}

      <style jsx>{`
        .batch-status { padding: 20px; }
        .status-badge {
          display: inline-block;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 14px;
          font-weight: bold;
        }
        .status-badge.pending { background: #ff9800; color: white; }
        .status-badge.running { background: #2196f3; color: white; }
        .status-badge.completed { background: #4caf50; color: white; }
        .status-badge.failed { background: #f44336; color: white; }
        .status-badge.cancelled { background: #9e9e9e; color: white; }
        .progress { margin: 16px 0; }
        .progress-bar {
          height: 8px;
          background: #4caf50;
          border-radius: 4px;
          transition: width 0.3s;
        }
        .results ul { list-style: none; padding: 0; }
        .results li { padding: 4px 0; }
        .error { color: red; margin-top: 16px; }
      `}</style>
    </div>
  );
};

export default BatchStatus;
'''
        return [{"path": "src/components/reports/BatchStatus.tsx", "content": code}]
