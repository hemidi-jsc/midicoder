# coding: utf-8
"""
Mô-đun FastAPI emitter cho Code Quality & Security Scanner Generator (CP24).

Emit các file cấu hình chất lượng code và bảo mật cho FastAPI:
- pyproject.toml (ruff config section)
- bandit.yaml (bandit security scan config)
- .safety-policy.json (safety dependency audit policy)
- scripts/quality_gate.py (quality gate runner script)
- .flake8 (flake8 config)
- .isort.cfg (isort config)

Author: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from midicoder.pipeline.emitter import Emitter

from midicoder.packs.cp24_quality_security.models import (
    QualityCollection,
    QualityProfile,
    SecurityScanConfig,
    StackType,
)


class FastAPIQualityEmitter:
    """
    Emitter sinh các file cấu hình chất lượng code và bảo mật cho FastAPI.

    Sinh ra:
    - pyproject.toml — section cấu hình ruff
    - bandit.yaml — cấu hình bandit security scan
    - .safety-policy.json — policy cho safety dependency audit
    - scripts/quality_gate.py — script chạy quality gate
    - .flake8 — cấu hình flake8
    - .isort.cfg — cấu hình isort
    """

    def __init__(self, stack_dir: str | Path) -> None:
        """
        Khởi tạo emitter.

        Args:
            stack_dir: Đường dẫn đến template directory
        """
        self.emitter = Emitter(stack="fastapi")
        self.stack_dir = Path(stack_dir)

    def generate(self, collection: QualityCollection) -> list[dict[str, str]]:
        """
        Generate toàn bộ files chất lượng code và bảo mật cho FastAPI.

        Lấy các profile và security config phù hợp với stack FastAPI từ
        QualityCollection, rồi render từng template.

        Args:
            collection: QualityCollection từ parser

        Returns:
            Danh sách {path, content} cho mỗi file sinh ra
        """
        results: list[dict[str, str]] = []

        # Lấy các profile và security config cho stack FastAPI
        profiles = collection.get_profiles_for_stack(StackType.FASTAPI)
        security_configs = collection.get_security_for_stack(StackType.FASTAPI)

        # Nếu không có profile, dùng mặc định
        profile: Optional[QualityProfile] = profiles[0] if profiles else None
        # Nếu không có security config, dùng mặc định
        security_config: Optional[SecurityScanConfig] = security_configs[0] if security_configs else None

        # Generate infrastructure files — mỗi file chỉ cần profile hoặc security_config
        results.extend(self._generate_pyproject_quality(profile))
        results.extend(self._generate_bandit_config(security_config))
        results.extend(self._generate_safety_policy(security_config))
        results.extend(self._generate_quality_gate(profile, security_config))
        results.extend(self._generate_flake8_config(profile))
        results.extend(self._generate_isort_config(profile))

        return results

    def _generate_pyproject_quality(
        self, profile: Optional[QualityProfile]
    ) -> list[dict[str, str]]:
        """Sinh pyproject.toml section cho ruff config.

        Args:
            profile: QualityProfile để lấy cấu hình exclude

        Returns:
            Danh sách {path, content} cho file pyproject.toml
        """
        if profile is None:
            return []
        try:
            content = self.emitter.render(
                "cp24_quality_security/pyproject_quality.toml.jinja2",
                {"profile": profile},
            )
            return [{"path": "pyproject.toml", "content": content}]
        except Exception:
            return []

    def _generate_bandit_config(
        self, security_config: Optional[SecurityScanConfig]
    ) -> list[dict[str, str]]:
        """Sinh bandit.yaml config cho security scan.

        Args:
            security_config: SecurityScanConfig để lấy cấu hình scan

        Returns:
            Danh sách {path, content} cho file bandit.yaml
        """
        if security_config is None:
            return []
        try:
            content = self.emitter.render(
                "cp24_quality_security/bandit.yaml.jinja2",
                {"security_config": security_config},
            )
            return [{"path": "bandit.yaml", "content": content}]
        except Exception:
            return []

    def _generate_safety_policy(
        self, security_config: Optional[SecurityScanConfig]
    ) -> list[dict[str, str]]:
        """Sinh .safety-policy.json cho dependency audit.

        Args:
            security_config: SecurityScanConfig để lấy cấu hình

        Returns:
            Danh sách {path, content} cho file .safety-policy.json
        """
        if security_config is None:
            return []
        try:
            content = self.emitter.render(
                "cp24_quality_security/safety_policy.json.jinja2",
                {"security_config": security_config},
            )
            return [{"path": ".safety-policy.json", "content": content}]
        except Exception:
            return []

    def _generate_quality_gate(
        self,
        profile: Optional[QualityProfile],
        security_config: Optional[SecurityScanConfig],
    ) -> list[dict[str, str]]:
        """Sinh scripts/quality_gate.py runner script.

        Script này sẽ:
        - Chạy ruff check và thu thập kết quả
        - Chạy bandit scan và thu thập kết quả
        - Chạy safety check và thu thập kết quả
        - Ghi báo cáo JSON
        - Trả về exit code 0 (pass) hoặc 1 (fail)

        Args:
            profile: QualityProfile để lấy cấu hình
            security_config: SecurityScanConfig để lấy cấu hình scan

        Returns:
            Danh sách {path, content} cho file scripts/quality_gate.py
        """
        try:
            content = self.emitter.render(
                "cp24_quality_security/quality_gate.py.jinja2",
                {
                    "profile": profile,
                    "security_config": security_config,
                },
            )
            return [{"path": "scripts/quality_gate.py", "content": content}]
        except Exception:
            return []

    def _generate_flake8_config(
        self, profile: Optional[QualityProfile]
    ) -> list[dict[str, str]]:
        """Sinh .flake8 config file.

        Args:
            profile: QualityProfile để lấy cấu hình exclude

        Returns:
            Danh sách {path, content} cho file .flake8
        """
        if profile is None:
            return []
        try:
            content = self.emitter.render(
                "cp24_quality_security/flake8.ini.jinja2",
                {"profile": profile},
            )
            return [{"path": ".flake8", "content": content}]
        except Exception:
            return []

    def _generate_isort_config(
        self, profile: Optional[QualityProfile]
    ) -> list[dict[str, str]]:
        """Sinh .isort.cfg config file.

        Args:
            profile: QualityProfile để lấy cấu hình

        Returns:
            Danh sách {path, content} cho file .isort.cfg
        """
        if profile is None:
            return []
        try:
            content = self.emitter.render(
                "cp24_quality_security/isort.cfg.jinja2",
                {"profile": profile},
            )
            return [{"path": ".isort.cfg", "content": content}]
        except Exception:
            return []
