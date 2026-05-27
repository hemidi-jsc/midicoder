# coding: utf-8
"""
Mô-đun models cho CP46 — MFA & Advanced Authentication.

Định nghĩa các dataclass biểu diễn:
- MFAMethod: Loại phương thức MFA (totp, sms_otp, webauthn_fido2, biometric)
- MFAMethodStatus: Trạng thái phương thức (enabled, disabled, pending_verification, revoked)
- MFAPriority: Mức ưu tiên xác thực (required, optional, backup)
- MFAChallenge: Thử thách xác thực (otp_code, webauthn_challenge, biometric_prompt)
- MFACredential: Chứng chỉ MFA của user
- MFAChallengeSession: Phiên thử thách xác thực MFA
- MFAEnrollment: Đăng ký MFA của user
- MFASession: Phiên xác thực MFA
- MFAEngine: Engine quản lý MFA (in-memory simulation)

KPI-005: CP Obligations Coverage (>= 2 obligations cho CP46).

Tác giả: Midicoder Team
Version: 1.0.0
"""

from __future__ import annotations

import base64
import secrets
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from midicoder.errors import ErrorCode, MidicoderErrorManager as EM


# ===========================================================================
# Enums
# ===========================================================================


class MFAMethod(str, Enum):
    """Loại phương thức xác thực đa yếu tố.

    - TOTP: Time-based One-Time Password (RFC 6238)
    - SMS_OTP: OTP gửi qua SMS
    - WEBAUTHN_FIDO2: WebAuthn/FIDO2 (key biometrics, hardware keys)
    - BIOMETRIC: Xác thực sinh trắc học
    """
    TOTP = "totp"
    SMS_OTP = "sms_otp"
    WEBAUTHN_FIDO2 = "webauthn_fido2"
    BIOMETRIC = "biometric"


class MFAMethodStatus(str, Enum):
    """Trạng thái phương thức MFA.

    - ENABLED: Đã kích hoạt
    - DISABLED: Đã vô hiệu hóa
    - PENDING_VERIFICATION: Đang chờ xác minh
    - REVOKED: Đã thu hồi
    """
    ENABLED = "enabled"
    DISABLED = "disabled"
    PENDING_VERIFICATION = "pending_verification"
    REVOKED = "revoked"


class MFAPriority(str, Enum):
    """Mức ưu tiên xác thực MFA.

    - REQUIRED: Bắt buộc phải xác thực MFA
    - OPTIONAL: Xác thực MFA tùy chọn
    - BACKUP: Phương thức dự phòng
    """
    REQUIRED = "required"
    OPTIONAL = "optional"
    BACKUP = "backup"


class MFAChallenge(str, Enum):
    """Loại thử thách xác thực MFA.

    - OTP_CODE: Mã OTP 6 chữ số
    - WEBAUTHN_CHALLENGE: Challenge cho WebAuthn
    - BIOMETRIC_PROMPT: Prompt xác thực sinh trắc học
    """
    OTP_CODE = "otp_code"
    WEBAUTHN_CHALLENGE = "webauthn_challenge"
    BIOMETRIC_PROMPT = "biometric_prompt"


# ===========================================================================
# MFACredential
# ===========================================================================


@dataclass
class MFACredential:
    """Chứng chỉ MFA của user.

    Đại diện cho một phương thức xác thực MFA đã được user đăng ký,
    bao gồm loại phương thức, trạng thái, và dữ liệu cần thiết để xác thực.

    Attributes:
        credential_id: ID duy nhất của chứng chỉ
        user_id: ID của user sở hữu
        method: Loại phương thức MFA
        status: Trạng thái hiện tại
        priority: Mức ưu tiên xác thực
        secret: Bí mật mã hóa (cho TOTP)
        public_key: Khóa công khai (cho WebAuthn)
        phone_number: Số điện thoại (cho SMS OTP)
        device_name: Tên thiết bị đã đăng ký
        metadata: Dữ liệu bổ sung
        created_at: Thời điểm tạo
        updated_at: Thời điểm cập nhật cuối
        last_used_at: Thời điểm sử dụng cuối
    """
    credential_id: str
    user_id: str
    method: MFAMethod
    status: MFAMethodStatus = MFAMethodStatus.PENDING_VERIFICATION
    priority: MFAPriority = MFAPriority.REQUIRED
    secret: str = ""
    public_key: str = ""
    phone_number: str = ""
    device_name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_used_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate credential sau khi khởi tạo."""
        if not self.credential_id or not self.credential_id.strip():
            raise EM.raise_error(
                ErrorCode.CP46_MFA_FACTOR_NOT_FOUND,
                reason="credential_id bắt buộc và không được để trống",
            )

        if not self.user_id or not self.user_id.strip():
            raise EM.raise_error(
                ErrorCode.CP46_MFA_FACTOR_NOT_FOUND,
                reason="user_id bắt buộc và không được để trống",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    @property
    def is_active(self) -> bool:
        """Kiểm tra xem credential có đang hoạt động không."""
        return self.status in (
            MFAMethodStatus.ENABLED,
            MFAMethodStatus.PENDING_VERIFICATION,
        )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển MFACredential sang dict."""
        return {
            "credential_id": self.credential_id,
            "user_id": self.user_id,
            "method": self.method.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "secret": self.secret,
            "public_key": self.public_key,
            "phone_number": self.phone_number,
            "device_name": self.device_name,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MFACredential":
        """Tạo MFACredential từ dict."""
        return cls(
            credential_id=data["credential_id"],
            user_id=data["user_id"],
            method=MFAMethod(data["method"]),
            status=MFAMethodStatus(data.get("status", "pending_verification")),
            priority=MFAPriority(data.get("priority", "required")),
            secret=data.get("secret", ""),
            public_key=data.get("public_key", ""),
            phone_number=data.get("phone_number", ""),
            device_name=data.get("device_name", ""),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# MFAChallengeSession
# ===========================================================================


@dataclass
class MFAChallengeSession:
    """Phiên thử thách xác thực MFA.

    Đại diện cho một phiên xác thực MFA đang diễn ra, bao gồm loại
    thử thách, mã OTP (nếu có), và thông tin về phiên.

    Attributes:
        session_id: ID duy nhất của phiên
        user_id: ID của user
        credential_id: ID của credential được sử dụng
        challenge: Loại thử thách
        otp_code: Mã OTP (cho TOTP/SMS)
        otp_expires_at: Thời gian hết hạn của OTP
        challenge_data: Dữ liệu thử thách (cho WebAuthn)
        attempts: Số lần đã thử
        max_attempts: Số lần thử tối đa
        verified: Đã xác minh thành công chưa
        created_at: Thời điểm tạo phiên
        expires_at: Thời gian hết hạn phiên
    """
    session_id: str
    user_id: str
    credential_id: str
    challenge: MFAChallenge
    otp_code: str = ""
    otp_expires_at: datetime | None = None
    challenge_data: dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    max_attempts: int = 5
    verified: bool = False
    created_at: datetime | None = None
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate challenge session sau khi khởi tạo."""
        if not self.session_id or not self.session_id.strip():
            raise EM.raise_error(
                ErrorCode.CP46_MFA_FACTOR_NOT_FOUND,
                reason="session_id bắt buộc và không được để trống",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now
        if self.expires_at is None:
            # Default 5 phút
            from datetime import timedelta
            self.expires_at = now + timedelta(minutes=5)

    @property
    def is_expired(self) -> bool:
        """Kiểm tra xem phiên có hết hạn không."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_max_attempts_reached(self) -> bool:
        """Kiểm tra xem đã vượt quá số lần thử tối đa chưa."""
        return self.attempts >= self.max_attempts

    def to_dict(self) -> dict[str, Any]:
        """Chuyển MFAChallengeSession sang dict."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "credential_id": self.credential_id,
            "challenge": self.challenge.value,
            "otp_code": self.otp_code,
            "otp_expires_at": self.otp_expires_at.isoformat() if self.otp_expires_at else None,
            "challenge_data": self.challenge_data,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "verified": self.verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MFAChallengeSession":
        """Tạo MFAChallengeSession từ dict."""
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            credential_id=data["credential_id"],
            challenge=MFAChallenge(data["challenge"]),
            otp_code=data.get("otp_code", ""),
            attempts=data.get("attempts", 0),
            max_attempts=data.get("max_attempts", 5),
            verified=data.get("verified", False),
        )


# ===========================================================================
# MFAEnrollment
# ===========================================================================


@dataclass
class MFAEnrollment:
    """Đăng ký MFA của user.

    Đại diện cho quá trình đăng ký một phương thức MFA mới, bao gồm
    dữ liệu cần thiết để hoàn tất đăng ký (QR code cho TOTP, v.v.).

    Attributes:
        enrollment_id: ID duy nhất của đăng ký
        user_id: ID của user
        method: Loại phương thức MFA
        status: Trạng thái đăng ký
        qr_code_data: Dữ liệu QR code (cho TOTP)
        setup_secret: Bí mật thiết lập tạm thời
        verification_code: Mã xác minh để hoàn tất đăng ký
        metadata: Dữ liệu bổ sung
        created_at: Thời điểm tạo đăng ký
        completed_at: Thời điểm hoàn tất đăng ký
    """
    enrollment_id: str
    user_id: str
    method: MFAMethod
    status: MFAMethodStatus = MFAMethodStatus.PENDING_VERIFICATION
    qr_code_data: str = ""
    setup_secret: str = ""
    verification_code: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate enrollment sau khi khởi tạo."""
        if not self.enrollment_id or not self.enrollment_id.strip():
            raise EM.raise_error(
                ErrorCode.CP46_MFA_FACTOR_NOT_FOUND,
                reason="enrollment_id bắt buộc và không được để trống",
            )

        now = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = now

    def to_dict(self) -> dict[str, Any]:
        """Chuyển MFAEnrollment sang dict."""
        return {
            "enrollment_id": self.enrollment_id,
            "user_id": self.user_id,
            "method": self.method.value,
            "status": self.status.value,
            "qr_code_data": self.qr_code_data,
            "setup_secret": self.setup_secret,
            "verification_code": self.verification_code,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MFAEnrollment":
        """Tạo MFAEnrollment từ dict."""
        return cls(
            enrollment_id=data["enrollment_id"],
            user_id=data["user_id"],
            method=MFAMethod(data["method"]),
            status=MFAMethodStatus(data.get("status", "pending_verification")),
            qr_code_data=data.get("qr_code_data", ""),
            setup_secret=data.get("setup_secret", ""),
            verification_code=data.get("verification_code", ""),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# MFASession
# ===========================================================================


@dataclass
class MFASession:
    """Phiên xác thực MFA.

    Đại diện cho một phiên xác thực MFA thành công, bao gồm thông tin
    về phương thức đã sử dụng và thời gian hợp lệ.

    Attributes:
        session_id: ID duy nhất của phiên
        user_id: ID của user
        credential_id: ID của credential được sử dụng
        method: Loại phương thức MFA
        is_verified: Đã xác thực thành công chưa
        verified_at: Thời điểm xác thực
        expires_at: Thời gian hết hạn phiên
        metadata: Dữ liệu bổ sung
    """
    session_id: str
    user_id: str
    credential_id: str
    method: MFAMethod
    is_verified: bool = False
    verified_at: datetime | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate session sau khi khởi tạo."""
        if not self.session_id or not self.session_id.strip():
            raise EM.raise_error(
                ErrorCode.CP46_MFA_FACTOR_NOT_FOUND,
                reason="session_id bắt buộc và không được để trống",
            )

        now = datetime.now(timezone.utc)
        if self.expires_at is None:
            from datetime import timedelta
            self.expires_at = now + timedelta(hours=24)

    @property
    def is_expired(self) -> bool:
        """Kiểm tra xem phiên có hết hạn không."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Chuyển MFASession sang dict."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "credential_id": self.credential_id,
            "method": self.method.value,
            "is_verified": self.is_verified,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MFASession":
        """Tạo MFASession từ dict."""
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            credential_id=data["credential_id"],
            method=MFAMethod(data["method"]),
            is_verified=data.get("is_verified", False),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# MFARule
# ===========================================================================


@dataclass
class MFARule:
    """Quy tắc MFA cho user/role.

    Đại diện cho một quy tắc xác thực MFA được áp dụng cho user cụ thể
    hoặc role, bao gồm loại phương thức, mức ưu tiên, và trạng thái.

    Attributes:
        rule_id: ID duy nhất của quy tắc
        user_id: ID của user (nếu áp dụng cho user cụ thể)
        role_id: ID của role (nếu áp dụng cho role)
        method: Loại phương thức MFA
        priority: Mức ưu tiên xác thực
        enabled: Có bật quy tắc không
        metadata: Dữ liệu bổ sung
    """
    rule_id: str
    user_id: str = ""
    role_id: str = ""
    method: MFAMethod = MFAMethod.TOTP
    priority: MFAPriority = MFAPriority.REQUIRED
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate rule sau khi khởi tạo."""
        if not self.rule_id or not self.rule_id.strip():
            raise EM.raise_error(
                ErrorCode.CP46_MFA_FACTOR_NOT_FOUND,
                reason="rule_id bắt buộc và không được để trống",
            )

    def to_dict(self) -> dict[str, Any]:
        """Chuyển MFARule sang dict."""
        return {
            "rule_id": self.rule_id,
            "user_id": self.user_id,
            "role_id": self.role_id,
            "method": self.method.value,
            "priority": self.priority.value,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MFARule":
        """Tạo MFARule từ dict."""
        return cls(
            rule_id=data["rule_id"],
            user_id=data.get("user_id", ""),
            role_id=data.get("role_id", ""),
            method=MFAMethod(data.get("method", "totp")),
            priority=MFAPriority(data.get("priority", "required")),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {}),
        )


# ===========================================================================
# MFAEngine
# ===========================================================================


class MFAEngine:
    """Engine quản lý MFA (in-memory simulation).

    Quản lý vòng đời của MFA: enrollment, challenge creation,
    verification, và session management.

    Đây là in-memory simulation để testing và demonstration.
    Trong thực tế, engine sẽ tích hợp với database và các dịch vụ
    bên ngoài (SMS provider, WebAuthn server, v.v.).

    Attributes:
        credentials: Từ điển chứa tất cả credentials (credential_id -> MFACredential)
        sessions: Từ điển chứa tất cả challenge sessions (session_id -> MFAChallengeSession)
        enrollments: Từ điển chứa tất cả enrollments (enrollment_id -> MFAEnrollment)
        mfa_sessions: Từ điển chứa tất cả MFA sessions (session_id -> MFASession)
    """

    def __init__(self) -> None:
        """Khởi tạo MFAEngine."""
        self.credentials: dict[str, MFACredential] = {}
        self.sessions: dict[str, MFAChallengeSession] = {}
        self.enrollments: dict[str, MFAEnrollment] = {}
        self.mfa_sessions: dict[str, MFASession] = {}

    def enroll_totp(
        self,
        user_id: str,
        device_name: str = "",
        issuer: str = "Midicoder",
    ) -> MFAEnrollment:
        """Đăng ký TOTP cho user.

        Args:
            user_id: ID của user
            device_name: Tên thiết bị
            issuer: Tên issuer cho TOTP

        Returns:
            MFAEnrollment đã tạo
        """
        secret = base64.b32encode(secrets.token_bytes(20)).decode("ascii")
        enrollment_id = f"enroll_{uuid.uuid4().hex[:8]}"

        # Tạo QR code data URI (simplified)
        qr_data = f"otpauth://totp/{issuer}:{user_id}?secret={secret}&issuer={issuer}"

        enrollment = MFAEnrollment(
            enrollment_id=enrollment_id,
            user_id=user_id,
            method=MFAMethod.TOTP,
            status=MFAMethodStatus.PENDING_VERIFICATION,
            qr_code_data=qr_data,
            setup_secret=secret,
            verification_code=self._generate_otp(secret),
            metadata={"device_name": device_name, "issuer": issuer},
        )

        self.enrollments[enrollment_id] = enrollment
        return enrollment

    def verify_enrollment(
        self,
        enrollment_id: str,
        verification_code: str,
    ) -> MFACredential:
        """Xác minh đăng ký MFA và tạo credential.

        Args:
            enrollment_id: ID của enrollment
            verification_code: Mã xác minh

        Returns:
            MFACredential đã tạo

        Raises:
            MidicoderError: Nếu enrollment không tồn tại hoặc mã xác minh sai
        """
        if enrollment_id not in self.enrollments:
            raise EM.raise_error(
                ErrorCode.CP46_MFA_FACTOR_NOT_FOUND,
                reason=f"Enrollment '{enrollment_id}' không tồn tại",
            )

        enrollment = self.enrollments[enrollment_id]

        if enrollment.verification_code != verification_code:
            raise EM.raise_error(
                ErrorCode.CP46_INVALID_OTP_CODE,
                reason="Mã xác minh không đúng",
            )

        # Tạo credential từ enrollment đã xác minh
        credential = MFACredential(
            credential_id=f"cred_{uuid.uuid4().hex[:8]}",
            user_id=enrollment.user_id,
            method=enrollment.method,
            status=MFAMethodStatus.ENABLED,
            secret=enrollment.setup_secret,
            device_name=enrollment.metadata.get("device_name", ""),
            metadata=enrollment.metadata,
        )

        self.credentials[credential.credential_id] = credential

        # Cập nhật enrollment
        enrollment.status = MFAMethodStatus.ENABLED
        enrollment.completed_at = datetime.now(timezone.utc)

        return credential

    def enroll_sms_otp(
        self,
        user_id: str,
        phone_number: str,
    ) -> MFAEnrollment:
        """Đăng ký SMS OTP cho user.

        Args:
            user_id: ID của user
            phone_number: Số điện thoại

        Returns:
            MFAEnrollment đã tạo
        """
        enrollment_id = f"enroll_{uuid.uuid4().hex[:8]}"
        verification_code = f"{secrets.randbelow(900000) + 100000:06d}"

        enrollment = MFAEnrollment(
            enrollment_id=enrollment_id,
            user_id=user_id,
            method=MFAMethod.SMS_OTP,
            status=MFAMethodStatus.PENDING_VERIFICATION,
            verification_code=verification_code,
            metadata={"phone_number": phone_number},
        )

        self.enrollments[enrollment_id] = enrollment
        return enrollment

    def create_challenge(
        self,
        user_id: str,
        method: MFAMethod,
    ) -> MFAChallengeSession:
        """Tạo thử thách xác thực MFA.

        Args:
            user_id: ID của user
            method: Loại phương thức MFA

        Returns:
            MFAChallengeSession đã tạo

        Raises:
            MidicoderError: Nếu không tìm thấy credential phù hợp
        """
        # Tìm credential phù hợp
        credential = None
        for cred in self.credentials.values():
            if cred.user_id == user_id and cred.method == method and cred.is_active:
                credential = cred
                break

        if not credential:
            raise EM.raise_error(
                ErrorCode.CP46_MFA_FACTOR_NOT_FOUND,
                reason=f"Không tìm thấy credential {method.value} cho user '{user_id}'",
            )

        session_id = f"challenge_{uuid.uuid4().hex[:8]}"

        # Tạo thử thách dựa trên loại phương thức
        if method == MFAMethod.TOTP:
            otp_code = self._generate_otp(credential.secret)
            challenge = MFAChallengeSession(
                session_id=session_id,
                user_id=user_id,
                credential_id=credential.credential_id,
                challenge=MFAChallenge.OTP_CODE,
                otp_code=otp_code,
            )
        elif method == MFAMethod.SMS_OTP:
            otp_code = f"{secrets.randbelow(900000) + 100000:06d}"
            challenge = MFAChallengeSession(
                session_id=session_id,
                user_id=user_id,
                credential_id=credential.credential_id,
                challenge=MFAChallenge.OTP_CODE,
                otp_code=otp_code,
            )
        elif method == MFAMethod.WEBAUTHN_FIDO2:
            challenge_data = {
                "challenge": secrets.token_urlsafe(32),
                "rp_id": "example.com",
                "timeout": 60000,
            }
            challenge = MFAChallengeSession(
                session_id=session_id,
                user_id=user_id,
                credential_id=credential.credential_id,
                challenge=MFAChallenge.WEBAUTHN_CHALLENGE,
                challenge_data=challenge_data,
            )
        elif method == MFAMethod.BIOMETRIC:
            challenge = MFAChallengeSession(
                session_id=session_id,
                user_id=user_id,
                credential_id=credential.credential_id,
                challenge=MFAChallenge.BIOMETRIC_PROMPT,
            )
        else:
            raise EM.raise_error(
                ErrorCode.CP46_MFA_FACTOR_NOT_FOUND,
                reason=f"Phương thức MFA không được hỗ trợ: {method.value}",
            )

        self.sessions[session_id] = challenge
        return challenge

    def verify_challenge(
        self,
        session_id: str,
        otp_code: str = "",
        signature: str = "",
    ) -> MFASession:
        """Xác minh thử thách MFA.

        Args:
            session_id: ID của challenge session
            otp_code: Mã OTP (cho TOTP/SMS)
            signature: Chữ ký (cho WebAuthn)

        Returns:
            MFASession đã xác thực

        Raises:
            MidicoderError: Nếu session không tồn tại hoặc xác minh thất bại
        """
        if session_id not in self.sessions:
            raise EM.raise_error(
                ErrorCode.CP46_MFA_FACTOR_NOT_FOUND,
                reason=f"Challenge session '{session_id}' không tồn tại",
            )

        session = self.sessions[session_id]

        if session.is_expired:
            raise EM.raise_error(
                ErrorCode.CP46_OTP_EXPIRED,
                reason="Challenge session đã hết hạn",
            )

        if session.is_max_attempts_reached:
            raise EM.raise_error(
                ErrorCode.CP46_MFA_RATE_LIMIT_EXCEEDED,
                reason=f"Đã vượt quá số lần thử tối đa ({session.max_attempts})",
            )

        session.attempts += 1

        # Xác minh dựa trên loại thử thách
        verified = False
        if session.challenge == MFAChallenge.OTP_CODE:
            verified = session.otp_code == otp_code
        elif session.challenge == MFAChallenge.WEBAUTHN_CHALLENGE:
            # Simulation: WebAuthn luôn thành công nếu có signature
            verified = bool(signature)
        elif session.challenge == MFAChallenge.BIOMETRIC_PROMPT:
            # Simulation: Biometric luôn thành công
            verified = True

        if not verified:
            raise EM.raise_error(
                ErrorCode.CP46_INVALID_OTP_CODE,
                reason="Xác minh thất bại",
            )

        # Tạo MFA session thành công
        session.verified = True
        now = datetime.now(timezone.utc)

        mfa_session = MFASession(
            session_id=f"mfa_{uuid.uuid4().hex[:8]}",
            user_id=session.user_id,
            credential_id=session.credential_id,
            method=self.credentials[session.credential_id].method,
            is_verified=True,
            verified_at=now,
        )

        self.mfa_sessions[mfa_session.session_id] = mfa_session

        # Cập nhật last_used_at của credential
        if session.credential_id in self.credentials:
            self.credentials[session.credential_id].last_used_at = now

        return mfa_session

    def disable_mfa(
        self,
        credential_id: str,
    ) -> MFACredential:
        """Vô hiệu hóa phương thức MFA.

        Args:
            credential_id: ID của credential

        Returns:
            MFACredential đã vô hiệu hóa

        Raises:
            MidicoderError: Nếu credential không tồn tại
        """
        if credential_id not in self.credentials:
            raise EM.raise_error(
                ErrorCode.CP46_MFA_FACTOR_NOT_FOUND,
                reason=f"Credential '{credential_id}' không tồn tại",
            )

        credential = self.credentials[credential_id]
        credential.status = MFAMethodStatus.DISABLED
        credential.updated_at = datetime.now(timezone.utc)

        return credential

    def revoke_credential(
        self,
        credential_id: str,
    ) -> MFACredential:
        """Thu hồi credential MFA.

        Args:
            credential_id: ID của credential

        Returns:
            MFACredential đã thu hồi

        Raises:
            MidicoderError: Nếu credential không tồn tại
        """
        if credential_id not in self.credentials:
            raise EM.raise_error(
                ErrorCode.CP46_MFA_FACTOR_NOT_FOUND,
                reason=f"Credential '{credential_id}' không tồn tại",
            )

        credential = self.credentials[credential_id]
        credential.status = MFAMethodStatus.REVOKED
        credential.updated_at = datetime.now(timezone.utc)

        return credential

    def get_user_credentials(
        self,
        user_id: str,
    ) -> list[MFACredential]:
        """Lấy danh sách credentials của user.

        Args:
            user_id: ID của user

        Returns:
            Danh sách MFACredential
        """
        return [
            cred for cred in self.credentials.values()
            if cred.user_id == user_id
        ]

    def is_mfa_enabled(
        self,
        user_id: str,
    ) -> bool:
        """Kiểm tra xem user có bật MFA không.

        Args:
            user_id: ID của user

        Returns:
            True nếu user có ít nhất một credential đang hoạt động
        """
        credentials = self.get_user_credentials(user_id)
        return any(cred.status == MFAMethodStatus.ENABLED for cred in credentials)

    def _generate_otp(self, secret: str) -> str:
        """Generate OTP code từ secret (simplified TOTP simulation).

        Args:
            secret: Base32-encoded secret

        Returns:
            6-digit OTP code
        """
        # Simplified TOTP - trong thực tế sẽ dùng pyotp hoặc hmac
        import hmac
        import hashlib

        secret_bytes = base64.b32decode(secret)
        time_step = int(time.time()) // 30

        msg = hmac.new(
            secret_bytes,
            time_step.to_bytes(8, "big"),
            hashlib.sha1,
        ).digest()

        offset = msg[-1] & 0x0F
        code = (
            ((msg[offset] & 0x7F) << 24)
            | ((msg[offset + 1] & 0xFF) << 16)
            | ((msg[offset + 2] & 0xFF) << 8)
            | (msg[offset + 3] & 0xFF)
        ) % 1000000

        return f"{code:06d}"


__all__ = [
    # Enums
    "MFAMethod",
    "MFAMethodStatus",
    "MFAPriority",
    "MFAChallenge",
    # Dataclasses
    "MFARule",
    "MFACredential",
    "MFAChallengeSession",
    "MFAEnrollment",
    "MFASession",
    # Engine
    "MFAEngine",
]
