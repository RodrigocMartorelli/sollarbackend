import base64

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models import User, Employee
from app.schemas import UserCreate, UserLogin, Token, UserResponse
from app.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from app.config import settings
from app.utils.document_utils import is_valid_cpf_cnpj

router = APIRouter(prefix="/auth", tags=["auth"])

_ALLOWED_RECOVERY_ROLES = {"vendedor", "adm", "dev"}


class ProfileUpdateRequest(BaseModel):
    user_id: int
    email: EmailStr
    name: str | None = None
    phone: str | None = None
    cpf: str | None = None


def _resolve_user_profile(db: Session, db_user: User) -> dict:
    """Return user profile data, falling back to employee record when user fields are empty."""
    name = db_user.name
    phone = db_user.phone
    cpf = db_user.cpf
    photo_base64 = None
    photo_url = None

    db_employee = db.query(Employee).filter(Employee.user_id == db_user.id).first()
    if db_employee:
        if not name:
            name = db_employee.nome
        if not phone:
            phone = db_employee.telefone
        if not cpf:
            cpf = db_employee.cpf_cnpj
        photo_base64 = db_employee.photo_base64
        if db_employee.photo:
            version = int(db_employee.updated_at.timestamp()) if db_employee.updated_at else int(db_user.created_at.timestamp())
            # Return full URL with host (or relative if backend deployed at root)
            photo_url = f"http://localhost:8000/api/v1/employees/photo/{db_employee.id}?v={version}"

    return {
        "id": db_user.id,
        "email": db_user.email,
        "name": name,
        "phone": phone,
        "cpf": cpf,
        "photo_base64": photo_base64,
        "photo_url": photo_url,
        "role": db_user.role,
    }


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Registrar novo usuário"""
    # Verificar se usuário já existe
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Criar novo usuário
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login e retorna JWT token com role"""
    normalized_email = user.email.strip().lower()

    # Buscar usuário
    db_user = (
        db.query(User)
        .filter(func.lower(User.email) == normalized_email)
        .first()
    )
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Criar token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": db_user.role,
        "user": _resolve_user_profile(db, db_user),
    }


@router.post("/verify-email")
def verify_email(data: dict, db: Session = Depends(get_db)):
    """Verificar se email existe"""
    email = data.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email é obrigatório",
        )

    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email não encontrado",
        )

    return {"message": "Email verificado"}


@router.post("/reset-password")
def reset_password(data: dict, db: Session = Depends(get_db)):
    """Alterar senha do usuário"""
    email = data.get("email")
    new_password = data.get("new_password")

    if not email or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email e nova senha são obrigatórios",
        )

    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email não encontrado",
        )

    if db_user.role not in _ALLOWED_RECOVERY_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A troca de senha está disponível apenas para vendedores, admins e devs cadastrados",
        )

    db_employee = db.query(Employee).filter(Employee.user_id == db_user.id).first()
    if not db_employee:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A troca de senha está disponível apenas para funcionários cadastrados",
        )

    # Atualizar senha
    db_user.hashed_password = get_password_hash(new_password)
    db.add(db_user)
    db.commit()

    return {"message": "Senha alterada com sucesso"}


@router.get("/profile/{user_id}")
def get_profile(user_id: int, db: Session = Depends(get_db)):
    """Buscar perfil do usuário"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    return {
        "user": _resolve_user_profile(db, db_user)
    }


@router.put("/profile")
def update_profile(payload: ProfileUpdateRequest, db: Session = Depends(get_db)):
    """Atualizar perfil do usuário"""
    db_user = db.query(User).filter(User.id == payload.user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    existing_email = (
        db.query(User)
        .filter(User.email == payload.email, User.id != payload.user_id)
        .first()
    )
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este email já está em uso",
        )

    if payload.cpf and not is_valid_cpf_cnpj(payload.cpf):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF inválido",
        )

    db_user.email = payload.email
    db_user.name = payload.name
    db_user.phone = payload.phone
    db_user.cpf = payload.cpf

    db_employee = db.query(Employee).filter(Employee.user_id == db_user.id).first()
    if db_employee:
        if payload.name is not None:
            db_employee.nome = payload.name
        if payload.phone is not None:
            db_employee.telefone = payload.phone
        if payload.cpf is not None:
            db_employee.cpf_cnpj = payload.cpf

    db.add(db_user)
    if db_employee:
        db.add(db_employee)
    db.commit()
    db.refresh(db_user)

    if db_employee:
        db.refresh(db_employee)

    return {
        "message": "Perfil atualizado com sucesso",
        "user": _resolve_user_profile(db, db_user),
    }


@router.post("/profile/{user_id}/photo")
def upload_profile_photo(
    user_id: int,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    db_employee = db.query(Employee).filter(Employee.user_id == db_user.id).first()
    if not db_employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Funcionário não encontrado para este usuário",
        )

    if photo.content_type and not photo.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo inválido",
        )

    image_bytes = photo.file.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Imagem vazia",
        )

    # Encode original image as base64 and also store as WebP bytes
    db_employee.photo_base64 = base64.b64encode(image_bytes).decode("ascii")
    # Also store as WebP for photo serving endpoint
    db_employee.photo = image_bytes
    db_employee.photo_type = photo.content_type or "image/jpeg"
    db_employee.updated_at = datetime.utcnow()
    
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)

    return {
        "message": "Foto atualizada com sucesso",
        "user": _resolve_user_profile(db, db_user),
    }
