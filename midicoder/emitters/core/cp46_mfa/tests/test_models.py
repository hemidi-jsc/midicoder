# coding: utf-8
"""
Tests for CP46 models — MFA & Advanced Authentication.
"""

import pytest
from datetime import datetime, timezone

from midicoder.emitters.core.cp46_mfa.models import (
    MFAChallenge,
    MFAChallengeSession,
    MFACredential,
    MFAEnrollment,
    MFAMethod,
    MFAMethodStatus,
    MFAPriority,
    MFASession,
    MFAEngine,
)
from midicoder.errors import ErrorCode


class TestMFAMethod:
    def test_method_totp(self):
        assert MFAMethod.TOTP.value == "totp"

    def test_method_sms_otp(self):
        assert MFAMethod.SMS_OTP.value == "sms_otp"

    def test_method_webauthn_fido2(self):
        assert MFAMethod.WEBAUTHN_FIDO2.value == "webauthn_fido2"

    def test_method_biometric(self):
        assert MFAMethod.BIOMETRIC.value == "biometric"


class TestMFAMethodStatus:
    def test_status_enabled(self):
        assert MFAMethodStatus.ENABLED.value == "enabled"

    def test_status_disabled(self):
        assert MFAMethodStatus.DISABLED.value == "disabled"

    def test_status_pending_verification(self):
        assert MFAMethodStatus.PENDING_VERIFICATION.value == "pending_verification"

    def test_status_revoked(self):
        assert MFAMethodStatus.REVOKED.value == "revoked"


class TestMFAPriority:
    def test_priority_required(self):
        assert MFAPriority.REQUIRED.value == "required"

    def test_priority_optional(self):
        assert MFAPriority.OPTIONAL.value == "optional"

    def test_priority_backup(self):
        assert MFAPriority.BACKUP.value == "backup"


class TestMFAChallenge:
    def test_challenge_otp_code(self):
        assert MFAChallenge.OTP_CODE.value == "otp_code"

    def test_challenge_webauthn(self):
        assert MFAChallenge.WEBAUTHN_CHALLENGE.value == "webauthn_challenge"

    def test_challenge_biometric(self):
        assert MFAChallenge.BIOMETRIC_PROMPT.value == "biometric_prompt"


class TestMFACredential:
    def test_create_valid_credential(self):
        cred = MFACredential(
            credential_id="cred_001",
            user_id="user_001",
            method=MFAMethod.TOTP,
            secret="JBSWY3DPEHPK3PXP",
        )
        assert cred.credential_id == "cred_001"
        assert cred.user_id == "user_001"
        assert cred.method == MFAMethod.TOTP
        assert cred.status == MFAMethodStatus.PENDING_VERIFICATION
        assert cred.priority == MFAPriority.REQUIRED
        assert cred.is_active is True

    def test_empty_credential_id_raises_error(self):
        with pytest.raises(Exception):
            MFACredential(credential_id="", user_id="user_001", method=MFAMethod.TOTP)

    def test_empty_user_id_raises_error(self):
        with pytest.raises(Exception):
            MFACredential(credential_id="cred_001", user_id="", method=MFAMethod.TOTP)

    def test_is_active_when_enabled(self):
        cred = MFACredential(
            credential_id="cred_001",
            user_id="user_001",
            method=MFAMethod.TOTP,
            status=MFAMethodStatus.ENABLED,
        )
        assert cred.is_active is True

    def test_to_dict(self):
        cred = MFACredential(
            credential_id="cred_001",
            user_id="user_001",
            method=MFAMethod.TOTP,
            device_name="My Phone",
        )
        d = cred.to_dict()
        assert d["credential_id"] == "cred_001"
        assert d["method"] == "totp"
        assert d["device_name"] == "My Phone"

    def test_from_dict(self):
        data = {
            "credential_id": "cred_001",
            "user_id": "user_001",
            "method": "totp",
            "status": "enabled",
            "priority": "required",
        }
        cred = MFACredential.from_dict(data)
        assert cred.credential_id == "cred_001"
        assert cred.method == MFAMethod.TOTP
        assert cred.status == MFAMethodStatus.ENABLED


class TestMFAChallengeSession:
    def test_create_valid_session(self):
        session = MFAChallengeSession(
            session_id="challenge_001",
            user_id="user_001",
            credential_id="cred_001",
            challenge=MFAChallenge.OTP_CODE,
            otp_code="123456",
            max_attempts=5,
        )
        assert session.session_id == "challenge_001"
        assert session.attempts == 0
        assert session.verified is False

    def test_empty_session_id_raises_error(self):
        with pytest.raises(Exception):
            MFAChallengeSession(
                session_id="",
                user_id="user_001",
                credential_id="cred_001",
                challenge=MFAChallenge.OTP_CODE,
            )

    def test_is_expired(self):
        from datetime import timedelta
        session = MFAChallengeSession(
            session_id="challenge_001",
            user_id="user_001",
            credential_id="cred_001",
            challenge=MFAChallenge.OTP_CODE,
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        assert session.is_expired is True

    def test_is_max_attempts_reached(self):
        session = MFAChallengeSession(
            session_id="challenge_001",
            user_id="user_001",
            credential_id="cred_001",
            challenge=MFAChallenge.OTP_CODE,
            attempts=5,
            max_attempts=5,
        )
        assert session.is_max_attempts_reached is True

    def test_to_dict(self):
        session = MFAChallengeSession(
            session_id="challenge_001",
            user_id="user_001",
            credential_id="cred_001",
            challenge=MFAChallenge.OTP_CODE,
            otp_code="123456",
        )
        d = session.to_dict()
        assert d["session_id"] == "challenge_001"
        assert d["challenge"] == "otp_code"
        assert d["otp_code"] == "123456"

    def test_from_dict(self):
        data = {
            "session_id": "challenge_001",
            "user_id": "user_001",
            "credential_id": "cred_001",
            "challenge": "otp_code",
        }
        session = MFAChallengeSession.from_dict(data)
        assert session.session_id == "challenge_001"
        assert session.challenge == MFAChallenge.OTP_CODE


class TestMFAEnrollment:
    def test_create_valid_enrollment(self):
        enrollment = MFAEnrollment(
            enrollment_id="enroll_001",
            user_id="user_001",
            method=MFAMethod.TOTP,
            qr_code_data="otpauth://totp/Test:user?secret=ABC",
            setup_secret="JBSWY3DPEHPK3PXP",
            verification_code="123456",
        )
        assert enrollment.enrollment_id == "enroll_001"
        assert enrollment.method == MFAMethod.TOTP
        assert enrollment.status == MFAMethodStatus.PENDING_VERIFICATION

    def test_empty_enrollment_id_raises_error(self):
        with pytest.raises(Exception):
            MFAEnrollment(enrollment_id="", user_id="user_001", method=MFAMethod.TOTP)

    def test_to_dict(self):
        enrollment = MFAEnrollment(
            enrollment_id="enroll_001",
            user_id="user_001",
            method=MFAMethod.TOTP,
            qr_code_data="otpauth://totp/Test:user?secret=ABC",
        )
        d = enrollment.to_dict()
        assert d["enrollment_id"] == "enroll_001"
        assert d["method"] == "totp"

    def test_from_dict(self):
        data = {
            "enrollment_id": "enroll_001",
            "user_id": "user_001",
            "method": "sms_otp",
            "status": "enabled",
        }
        enrollment = MFAEnrollment.from_dict(data)
        assert enrollment.method == MFAMethod.SMS_OTP
        assert enrollment.status == MFAMethodStatus.ENABLED


class TestMFASession:
    def test_create_valid_session(self):
        session = MFASession(
            session_id="mfa_sess_001",
            user_id="user_001",
            credential_id="cred_001",
            method=MFAMethod.TOTP,
            is_verified=True,
        )
        assert session.session_id == "mfa_sess_001"
        assert session.is_verified is True

    def test_empty_session_id_raises_error(self):
        with pytest.raises(Exception):
            MFASession(
                session_id="",
                user_id="user_001",
                credential_id="cred_001",
                method=MFAMethod.TOTP,
            )

    def test_to_dict(self):
        session = MFASession(
            session_id="mfa_sess_001",
            user_id="user_001",
            credential_id="cred_001",
            method=MFAMethod.TOTP,
            is_verified=True,
        )
        d = session.to_dict()
        assert d["session_id"] == "mfa_sess_001"
        assert d["is_verified"] is True

    def test_from_dict(self):
        data = {
            "session_id": "mfa_sess_001",
            "user_id": "user_001",
            "credential_id": "cred_001",
            "method": "webauthn_fido2",
            "is_verified": True,
        }
        session = MFASession.from_dict(data)
        assert session.method == MFAMethod.WEBAUTHN_FIDO2
        assert session.is_verified is True


class TestMFAEngine:
    def test_create_engine(self):
        engine = MFAEngine()
        assert engine.credentials == {}
        assert engine.sessions == {}
        assert engine.enrollments == {}
        assert engine.mfa_sessions == {}

    def test_enroll_totp(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001", "My Phone", "TestIssuer")
        assert enrollment.user_id == "user_001"
        assert enrollment.method == MFAMethod.TOTP
        assert enrollment.qr_code_data
        assert enrollment.setup_secret
        assert "otpauth://totp" in enrollment.qr_code_data

    def test_verify_enrollment_success(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001")
        credential = engine.verify_enrollment(enrollment.enrollment_id, enrollment.verification_code)
        assert credential.user_id == "user_001"
        assert credential.status == MFAMethodStatus.ENABLED

    def test_verify_enrollment_wrong_code(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001")
        with pytest.raises(Exception):
            engine.verify_enrollment(enrollment.enrollment_id, "000000")

    def test_verify_enrollment_not_found(self):
        engine = MFAEngine()
        with pytest.raises(Exception):
            engine.verify_enrollment("nonexistent", "123456")

    def test_enroll_sms_otp(self):
        engine = MFAEngine()
        enrollment = engine.enroll_sms_otp("user_001", "+1234567890")
        assert enrollment.method == MFAMethod.SMS_OTP
        assert enrollment.verification_code

    def test_create_challenge_totp(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001")
        engine.verify_enrollment(enrollment.enrollment_id, enrollment.verification_code)
        challenge = engine.create_challenge("user_001", MFAMethod.TOTP)
        assert challenge.user_id == "user_001"
        assert challenge.challenge == MFAChallenge.OTP_CODE
        assert challenge.otp_code

    def test_create_challenge_no_credential(self):
        engine = MFAEngine()
        with pytest.raises(Exception):
            engine.create_challenge("user_001", MFAMethod.TOTP)
