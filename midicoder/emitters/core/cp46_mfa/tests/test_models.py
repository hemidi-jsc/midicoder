# coding: utf-8
"""
Tests for CP46 models — MFA & Advanced Authentication.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone

from midicoder.emitters.core.cp46_mfa.models import (
    MFAChallenge,
    MFAChallengeSession,
    MFACredential,
    MFAEnrollment,
    MFAMethod,
    MFAMethodStatus,
    MFAPriority,
    MFARule,
    MFASession,
    MFAEngine,
)
from midicoder.errors import ErrorCode, MidicoderError


# ===========================================================================
# Error Codes
# ===========================================================================


class TestCP46ErrorCodes:
    def test_mfa_factor_not_found_code(self):
        assert ErrorCode.CP46_MFA_FACTOR_NOT_FOUND.value == "MDC-CP46-001"

    def test_mfa_already_enabled_code(self):
        assert ErrorCode.CP46_MFA_ALREADY_ENABLED.value == "MDC-CP46-002"

    def test_mfa_not_enabled_code(self):
        assert ErrorCode.CP46_MFA_NOT_ENABLED.value == "MDC-CP46-003"

    def test_invalid_otp_code(self):
        assert ErrorCode.CP46_INVALID_OTP_CODE.value == "MDC-CP46-004"

    def test_otp_expired_code(self):
        assert ErrorCode.CP46_OTP_EXPIRED.value == "MDC-CP46-005"

    def test_totp_secret_invalid_code(self):
        assert ErrorCode.CP46_TOTP_SECRET_INVALID.value == "MDC-CP46-006"

    def test_webauthn_registration_failed_code(self):
        assert ErrorCode.CP46_WEBAUTHN_REGISTRATION_FAILED.value == "MDC-CP46-007"

    def test_webauthn_verification_failed_code(self):
        assert ErrorCode.CP46_WEBAUTHN_VERIFICATION_FAILED.value == "MDC-CP46-008"

    def test_biometric_not_supported_code(self):
        assert ErrorCode.CP46_BIOMETRIC_NOT_SUPPORTED.value == "MDC-CP46-009"

    def test_mfa_rate_limit_exceeded_code(self):
        assert ErrorCode.CP46_MFA_RATE_LIMIT_EXCEEDED.value == "MDC-CP46-010"


# ===========================================================================
# Enums
# ===========================================================================


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


# ===========================================================================
# MFARule
# ===========================================================================


class TestMFARule:
    def test_create_valid_rule(self):
        rule = MFARule(rule_id="rule_001", role_id="admin", method=MFAMethod.TOTP)
        assert rule.rule_id == "rule_001"
        assert rule.method == MFAMethod.TOTP
        assert rule.enabled is True

    def test_empty_rule_id_raises_error(self):
        with pytest.raises(MidicoderError):
            MFARule(rule_id="", role_id="admin")

    def test_to_dict(self):
        rule = MFARule(rule_id="r1", role_id="staff", method=MFAMethod.SMS_OTP, priority=MFAPriority.BACKUP)
        d = rule.to_dict()
        assert d["rule_id"] == "r1"
        assert d["method"] == "sms_otp"
        assert d["priority"] == "backup"

    def test_from_dict(self):
        data = {"rule_id": "r1", "method": "webauthn_fido2", "priority": "required", "enabled": True}
        rule = MFARule.from_dict(data)
        assert rule.method == MFAMethod.WEBAUTHN_FIDO2
        assert rule.priority == MFAPriority.REQUIRED

    def test_roundtrip(self):
        rule = MFARule(rule_id="r1", role_id="admin", method=MFAMethod.BIOMETRIC, priority=MFAPriority.OPTIONAL)
        restored = MFARule.from_dict(rule.to_dict())
        assert restored.rule_id == rule.rule_id
        assert restored.method == rule.method


# ===========================================================================
# MFACredential
# ===========================================================================


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
        with pytest.raises(MidicoderError):
            MFACredential(credential_id="", user_id="user_001", method=MFAMethod.TOTP)

    def test_empty_user_id_raises_error(self):
        with pytest.raises(MidicoderError):
            MFACredential(credential_id="cred_001", user_id="", method=MFAMethod.TOTP)

    def test_is_active_when_enabled(self):
        cred = MFACredential(
            credential_id="cred_001",
            user_id="user_001",
            method=MFAMethod.TOTP,
            status=MFAMethodStatus.ENABLED,
        )
        assert cred.is_active is True

    def test_is_active_when_pending(self):
        cred = MFACredential(
            credential_id="cred_001",
            user_id="user_001",
            method=MFAMethod.TOTP,
            status=MFAMethodStatus.PENDING_VERIFICATION,
        )
        assert cred.is_active is True

    def test_is_active_when_disabled(self):
        cred = MFACredential(
            credential_id="cred_001",
            user_id="user_001",
            method=MFAMethod.TOTP,
            status=MFAMethodStatus.DISABLED,
        )
        assert cred.is_active is False

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


# ===========================================================================
# MFAChallengeSession
# ===========================================================================


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
        with pytest.raises(MidicoderError):
            MFAChallengeSession(
                session_id="",
                user_id="user_001",
                credential_id="cred_001",
                challenge=MFAChallenge.OTP_CODE,
            )

    def test_is_expired(self):
        session = MFAChallengeSession(
            session_id="challenge_001",
            user_id="user_001",
            credential_id="cred_001",
            challenge=MFAChallenge.OTP_CODE,
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        assert session.is_expired is True

    def test_is_not_expired(self):
        session = MFAChallengeSession(
            session_id="challenge_001",
            user_id="user_001",
            credential_id="cred_001",
            challenge=MFAChallenge.OTP_CODE,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        assert session.is_expired is False

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


# ===========================================================================
# MFAEnrollment
# ===========================================================================


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
        with pytest.raises(MidicoderError):
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


# ===========================================================================
# MFASession
# ===========================================================================


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
        with pytest.raises(MidicoderError):
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


# ===========================================================================
# MFAEngine
# ===========================================================================


class TestMFAEngine:
    def test_create_engine(self):
        engine = MFAEngine()
        assert engine.credentials == {}
        assert engine.sessions == {}
        assert engine.enrollments == {}
        assert engine.mfa_sessions == {}

    # -- Enrollment --
    def test_enroll_totp(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001", "My Phone", "TestIssuer")
        assert enrollment.user_id == "user_001"
        assert enrollment.method == MFAMethod.TOTP
        assert enrollment.qr_code_data
        assert enrollment.setup_secret
        assert "otpauth://totp" in enrollment.qr_code_data

    def test_enroll_totp_default_params(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001")
        assert enrollment.user_id == "user_001"
        assert enrollment.metadata["issuer"] == "Midicoder"

    def test_enroll_sms_otp(self):
        engine = MFAEngine()
        enrollment = engine.enroll_sms_otp("user_001", "+1234567890")
        assert enrollment.method == MFAMethod.SMS_OTP
        assert len(enrollment.verification_code) == 6

    # -- Verify Enrollment --
    def test_verify_enrollment_success(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001")
        credential = engine.verify_enrollment(enrollment.enrollment_id, enrollment.verification_code)
        assert credential.user_id == "user_001"
        assert credential.status == MFAMethodStatus.ENABLED

    def test_verify_enrollment_wrong_code(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001")
        with pytest.raises(MidicoderError):
            engine.verify_enrollment(enrollment.enrollment_id, "000000")

    def test_verify_enrollment_not_found(self):
        engine = MFAEngine()
        with pytest.raises(MidicoderError):
            engine.verify_enrollment("nonexistent", "123456")

    # -- Create Challenge --
    def test_create_challenge_totp(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001")
        engine.verify_enrollment(enrollment.enrollment_id, enrollment.verification_code)
        challenge = engine.create_challenge("user_001", MFAMethod.TOTP)
        assert challenge.user_id == "user_001"
        assert challenge.challenge == MFAChallenge.OTP_CODE
        assert challenge.otp_code

    def test_create_challenge_sms_otp(self):
        engine = MFAEngine()
        enrollment = engine.enroll_sms_otp("user_001", "+1234567890")
        engine.verify_enrollment(enrollment.enrollment_id, enrollment.verification_code)
        challenge = engine.create_challenge("user_001", MFAMethod.SMS_OTP)
        assert challenge.challenge == MFAChallenge.OTP_CODE

    def test_create_challenge_webauthn(self):
        engine = MFAEngine()
        cred = MFACredential(
            credential_id="cred_wa",
            user_id="user_001",
            method=MFAMethod.WEBAUTHN_FIDO2,
            status=MFAMethodStatus.ENABLED,
        )
        engine.credentials["cred_wa"] = cred
        challenge = engine.create_challenge("user_001", MFAMethod.WEBAUTHN_FIDO2)
        assert challenge.challenge == MFAChallenge.WEBAUTHN_CHALLENGE

    def test_create_challenge_biometric(self):
        engine = MFAEngine()
        cred = MFACredential(
            credential_id="cred_bio",
            user_id="user_001",
            method=MFAMethod.BIOMETRIC,
            status=MFAMethodStatus.ENABLED,
        )
        engine.credentials["cred_bio"] = cred
        challenge = engine.create_challenge("user_001", MFAMethod.BIOMETRIC)
        assert challenge.challenge == MFAChallenge.BIOMETRIC_PROMPT

    def test_create_challenge_no_credential(self):
        engine = MFAEngine()
        with pytest.raises(MidicoderError):
            engine.create_challenge("user_001", MFAMethod.TOTP)

    # -- Verify Challenge --
    def test_verify_challenge_totp_success(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001")
        engine.verify_enrollment(enrollment.enrollment_id, enrollment.verification_code)
        challenge = engine.create_challenge("user_001", MFAMethod.TOTP)
        session = engine.verify_challenge(challenge.session_id, otp_code=challenge.otp_code)
        assert session.is_verified is True

    def test_verify_challenge_wrong_code(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001")
        engine.verify_enrollment(enrollment.enrollment_id, enrollment.verification_code)
        challenge = engine.create_challenge("user_001", MFAMethod.TOTP)
        with pytest.raises(MidicoderError):
            engine.verify_challenge(challenge.session_id, otp_code="000000")

    def test_verify_challenge_session_not_found(self):
        engine = MFAEngine()
        with pytest.raises(MidicoderError):
            engine.verify_challenge("nonexistent", otp_code="123456")

    def test_verify_challenge_expired(self):
        engine = MFAEngine()
        session = MFAChallengeSession(
            session_id="expired",
            user_id="user_001",
            credential_id="cred_001",
            challenge=MFAChallenge.OTP_CODE,
            otp_code="123456",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        engine.sessions["expired"] = session
        cred = MFACredential(
            credential_id="cred_001",
            user_id="user_001",
            method=MFAMethod.TOTP,
            status=MFAMethodStatus.ENABLED,
        )
        engine.credentials["cred_001"] = cred
        with pytest.raises(MidicoderError):
            engine.verify_challenge("expired", otp_code="123456")

    def test_verify_challenge_max_attempts(self):
        engine = MFAEngine()
        session = MFAChallengeSession(
            session_id="maxed",
            user_id="user_001",
            credential_id="cred_001",
            challenge=MFAChallenge.OTP_CODE,
            otp_code="123456",
            attempts=5,
            max_attempts=5,
        )
        engine.sessions["maxed"] = session
        cred = MFACredential(
            credential_id="cred_001",
            user_id="user_001",
            method=MFAMethod.TOTP,
            status=MFAMethodStatus.ENABLED,
        )
        engine.credentials["cred_001"] = cred
        with pytest.raises(MidicoderError):
            engine.verify_challenge("maxed", otp_code="123456")

    # -- Disable / Revoke --
    def test_disable_mfa(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001")
        cred = engine.verify_enrollment(enrollment.enrollment_id, enrollment.verification_code)
        disabled = engine.disable_mfa(cred.credential_id)
        assert disabled.status == MFAMethodStatus.DISABLED

    def test_disable_mfa_not_found(self):
        engine = MFAEngine()
        with pytest.raises(MidicoderError):
            engine.disable_mfa("nonexistent")

    def test_revoke_credential(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001")
        cred = engine.verify_enrollment(enrollment.enrollment_id, enrollment.verification_code)
        revoked = engine.revoke_credential(cred.credential_id)
        assert revoked.status == MFAMethodStatus.REVOKED

    def test_revoke_credential_not_found(self):
        engine = MFAEngine()
        with pytest.raises(MidicoderError):
            engine.revoke_credential("nonexistent")

    # -- User credentials / MFA status --
    def test_get_user_credentials(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001")
        engine.verify_enrollment(enrollment.enrollment_id, enrollment.verification_code)
        creds = engine.get_user_credentials("user_001")
        assert len(creds) == 1

    def test_get_user_credentials_empty(self):
        engine = MFAEngine()
        creds = engine.get_user_credentials("unknown_user")
        assert creds == []

    def test_is_mfa_enabled_true(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001")
        engine.verify_enrollment(enrollment.enrollment_id, enrollment.verification_code)
        assert engine.is_mfa_enabled("user_001") is True

    def test_is_mfa_enabled_false(self):
        engine = MFAEngine()
        assert engine.is_mfa_enabled("unknown_user") is False

    def test_is_mfa_enabled_false_after_disable(self):
        engine = MFAEngine()
        enrollment = engine.enroll_totp("user_001")
        cred = engine.verify_enrollment(enrollment.enrollment_id, enrollment.verification_code)
        engine.disable_mfa(cred.credential_id)
        assert engine.is_mfa_enabled("user_001") is False
