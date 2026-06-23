import random
import string
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.utils import parseaddr
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from app.database import get_db
from app.models import User, Employee
from app.config import settings
from typing import List

router = APIRouter(prefix="/email-test", tags=["email-test"])

_VERIFICATION_CODES: dict[str, dict[str, object]] = {}
_ALLOWED_RECOVERY_ROLES = {"vendedor", "adm", "dev"}


class TestEmailRequest(BaseModel):
    emails: List[EmailStr] = Field(min_length=1, description="Lista de emails para enviar")


class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


def generate_verification_code(length: int = 6) -> str:
    """Gera código de verificação com letras (A-Z) e números (0-9)"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def _normalize_code(value: str) -> str:
    return ''.join(ch for ch in value.upper() if ch.isalnum())


def _store_verification_code(email: str, code: str) -> None:
    normalized_email = email.strip().lower()
    _VERIFICATION_CODES[normalized_email] = {
        "code": _normalize_code(code),
        "expires_at": datetime.utcnow() + timedelta(minutes=5),
    }


def _is_code_valid(email: str, code: str) -> bool:
    normalized_email = email.strip().lower()
    record = _VERIFICATION_CODES.get(normalized_email)
    if not record:
        return False

    expires_at = record.get("expires_at")
    stored_code = record.get("code")
    if not isinstance(expires_at, datetime) or not isinstance(stored_code, str):
        return False

    if datetime.utcnow() > expires_at:
        _VERIFICATION_CODES.pop(normalized_email, None)
        return False

    return _normalize_code(code) == stored_code


def _is_allowed_recovery_email(db: Session, email: str) -> bool:
        normalized_email = email.strip().lower()
        db_user = db.query(User).filter(User.email.ilike(normalized_email)).first()
        if not db_user:
            return False

        if db_user.role not in _ALLOWED_RECOVERY_ROLES:
                return False

        db_employee = db.query(Employee).filter(Employee.user_id == db_user.id).first()
        return db_employee is not None


def create_password_reset_email(verification_code: str) -> tuple[str, str]:
    """Cria assunto e HTML para email de troca de senha"""
    subject = "Código de Verificação - Troca de Senha"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
        <h2 style="color: #333;">Troca de Senha</h2>
        <p>Você solicitou uma troca de senha. Use o código abaixo para verificar sua identidade:</p>
        
        <div style="background-color: #f8fafc; padding: 22px; text-align: center; border-radius: 12px; margin: 20px 0; border: 1px solid #e2e8f0;">
            <div style="font-size: 32px; font-weight: 700; letter-spacing: 8px; color: #0f172a; font-family: 'Courier New', monospace;">
                {verification_code}
            </div>
        </div>
        
        <p style="color: #666;">Este código é válido por 10 minutos.</p>
        <p style="color: #666;">Se você não solicitou uma troca de senha, ignore este email.</p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
        <p style="font-size: 12px; color: #999;">© 2026 Sollar. Todos os direitos reservados.</p>
    </div>
    """
    return subject, html


def _build_email_message(subject: str, html: str, recipients: List[str]) -> EmailMessage:
    _, sender_email = parseaddr(settings.email_from or settings.smtp_user or "")
    if not sender_email:
        raise HTTPException(
            status_code=503,
            detail="SMTP sender não configurado no backend",
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_from or sender_email
    message["To"] = ", ".join(recipients)
    message.set_content("Seu cliente de email não suporta HTML.")
    message.add_alternative(html, subtype="html")
    return message


def _send_via_smtp(subject: str, html: str, recipients: List[str]) -> None:
    smtp_host = settings.smtp_host
    smtp_user = settings.smtp_user
    smtp_password = settings.smtp_password

    if not smtp_host or not smtp_user or not smtp_password:
        raise HTTPException(
            status_code=503,
            detail="SMTP não configurado no backend",
        )

    message = _build_email_message(subject, html, recipients)

    with smtplib.SMTP(smtp_host, settings.smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user, smtp_password)
        server.send_message(message)


@router.post("/send")
def send_test_email(payload: TestEmailRequest, db: Session = Depends(get_db)):
    try:
        for recipient in payload.emails:
            if not _is_allowed_recovery_email(db, str(recipient)):
                raise HTTPException(
                    status_code=403,
                    detail="A recuperação de senha é permitida apenas para vendedores, admins e devs cadastrados",
                )

        verification_code = generate_verification_code()
        subject, html = create_password_reset_email(verification_code)

        _send_via_smtp(subject, html, payload.emails)
        for recipient in payload.emails:
            _store_verification_code(str(recipient), verification_code)
        return {
            "message": f"Email de verificação enviado com sucesso para {len(payload.emails)} destinatário(s)",
            "recipients": payload.emails,
            "verification_code": verification_code,
            "provider": "smtp",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Falha ao enviar email: {str(exc)}",
        )


@router.post("/verify-code")
def verify_code(payload: VerifyCodeRequest, db: Session = Depends(get_db)):
    if not _is_allowed_recovery_email(db, str(payload.email)):
        raise HTTPException(
            status_code=403,
            detail="A recuperação de senha é permitida apenas para vendedores, admins e devs cadastrados",
        )

    if not _is_code_valid(str(payload.email), payload.code):
        raise HTTPException(
            status_code=400,
            detail="Código inválido ou expirado",
        )

    return {"message": "Código validado com sucesso"}
