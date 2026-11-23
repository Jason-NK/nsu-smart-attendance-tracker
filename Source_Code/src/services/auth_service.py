"""Authentication and input validation service (SPR-01, SPR-05, SPR-09)."""
import re
from typing import Optional, Tuple
import bcrypt
from repositories.user_repo import UserRepository
from services.log_service import LogService

NSU_EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@(spartans\.nsu\.edu|nsu\.edu)$", re.IGNORECASE)
STUDENT_ID_REGEX = re.compile(r"^\d{7}$")
COURSE_CODE_REGEX = re.compile(r"^[A-Za-z]{3,4}-\d{3}$")


def validate_nsu_email(email: str) -> Tuple[bool, str]:
    if not email or not NSU_EMAIL_REGEX.match(email.strip()):
        return False, "Enter a valid NSU email address."
    return True, ""


def validate_password_strength(password: str) -> Tuple[bool, str]:
    if (
        not password
        or len(password) < 8
        or len(password) > 64
        or not any(c.isupper() for c in password)
        or not any(c.islower() for c in password)
        or not any(c.isdigit() for c in password)
    ):
        return False, "Password must be at least 8 characters and include a number and an uppercase letter."
    return True, ""


def validate_student_id(student_id: str) -> Tuple[bool, str]:
    if not student_id or not STUDENT_ID_REGEX.match(student_id.strip()):
        return False, "Student ID is required and must be a 7-digit number."
    return True, ""


def validate_course_code(course_code: str) -> Tuple[bool, str]:
    if not course_code or not COURSE_CODE_REGEX.match(course_code.strip()):
        return False, "Enter a valid course code (for example, CSC-380)."
    return True, ""


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


class AuthService:
    def __init__(
        self,
        user_repo: Optional[UserRepository] = None,
        log_service: Optional[LogService] = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.log_service = log_service or LogService()

    def authenticate(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
    ) -> Tuple[Optional[dict], str]:
        valid_email, email_err = validate_nsu_email(email)
        if not valid_email:
            self.log_service.log_event(
                "FAILED_LOGIN",
                f"Rejected non-NSU or invalid email format: {email}",
                email=email,
                ip_address=ip_address,
            )
            return None, email_err

        if not password:
            self.log_service.log_event(
                "FAILED_LOGIN",
                "Blank password submitted during login.",
                email=email,
                ip_address=ip_address,
            )
            return None, "Invalid NSU email or password."

        user = self.user_repo.find_by_email(email)
        if not user or not verify_password(password, user["password_hash"]):
            self.log_service.log_event(
                "FAILED_LOGIN",
                "Incorrect password or unknown NSU account.",
                email=email,
                ip_address=ip_address,
            )
            return None, "Invalid NSU email or password."

        return user, ""
