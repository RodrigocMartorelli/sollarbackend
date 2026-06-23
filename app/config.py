from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Encryption
    encryption_key: str

    # Email (SMTP atual)
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None

    # Email (Resend futuro)
    resend_api_key: Optional[str] = None

    # Twilio (WhatsApp sandbox)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_from: Optional[str] = None
    
    # Server
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
