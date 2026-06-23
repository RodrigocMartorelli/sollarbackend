from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from cryptography.fernet import Fernet
import base64
import hashlib

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

# Encrypt/Decrypt sensitive data
def get_cipher():
    """Retorna cipher Fernet para encriptação"""
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.encryption_key.encode()).digest())
    return Fernet(key)

def encrypt_data(data: str) -> str:
    """Encripta dados sensíveis (CPF, telefone, etc)"""
    cipher = get_cipher()
    encrypted = cipher.encrypt(data.encode())
    return encrypted.decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decripta dados sensíveis"""
    cipher = get_cipher()
    decrypted = cipher.decrypt(encrypted_data.encode())
    return decrypted.decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica senha"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Faz hash da senha"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def verify_token(credentials = Depends(security)) -> str:
    """Verifica e extrai user_id do token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    token: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Obtém usuário atual a partir do token"""
    from app.models import User
    
    try:
        user_id = int(token)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user
