import base64
import io
from PIL import Image

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Employee, User
from pydantic import BaseModel
from datetime import datetime
from app.security import get_password_hash
from app.utils.document_utils import is_valid_cpf_cnpj

router = APIRouter(prefix="/employees", tags=["employees"])


def _save_employee_photo(employee_id: int, upload_file: UploadFile) -> str:
    image_bytes = upload_file.file.read()
    return base64.b64encode(image_bytes).decode("ascii")


def _process_photo_to_webp(file_bytes: bytes, max_size: int = 512, quality: int = 80) -> bytes:
    """
    Converte imagem para WebP e redimensiona para no máximo max_size x max_size.
    Retorna bytes da imagem processada.
    """
    try:
        # Abrir imagem
        img = Image.open(io.BytesIO(file_bytes))
        
        # Converter RGBA para RGB se necessário (WebP com RGB)
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionar se necessário
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Salvar como WebP
        webp_buffer = io.BytesIO()
        img.save(webp_buffer, format='WebP', quality=quality, method=6)
        webp_buffer.seek(0)
        return webp_buffer.getvalue()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar imagem: {str(e)}")


def _role_from_funcao(funcao: str | None) -> str:
    normalized = (funcao or "").strip().lower()
    if normalized == "adm":
        return "adm"
    if normalized == "dev":
        return "dev"
    return "vendedor"

class EmployeeCreate(BaseModel):
    nome: str
    cpf_cnpj: str | None = None
    tipo_contrato: str | None = None
    funcao: str
    email: str | None = None
    telefone: str | None = None

class EmployeeUpdate(BaseModel):
    nome: str | None = None
    cpf_cnpj: str | None = None
    tipo_contrato: str | None = None
    funcao: str | None = None
    email: str | None = None
    telefone: str | None = None

class EmployeeResponse(BaseModel):
    id: int
    nome: str
    cpf_cnpj: str | None
    tipo_contrato: str | None
    funcao: str
    email: str | None
    telefone: str | None
    photo_url: str | None = None
    photo_base64: str | None = None
    photo_type: str | None = None
    has_photo: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True
class EmployeeResponse(BaseModel):
    id: int
    nome: str
    cpf_cnpj: str | None
    tipo_contrato: str | None
    funcao: str
    email: str | None
    telefone: str | None
    photo_url: str | None = None
    photo_base64: str | None = None
    photo_type: str | None = None
    has_photo: bool = False
    created_at: datetime
    deleted_at: datetime | None = None
    
    class Config:
        from_attributes = True


def _serialize_employee(employee: Employee) -> dict:
    return {
        "id": employee.id,
        "nome": employee.nome,
        "cpf_cnpj": employee.cpf_cnpj,
        "tipo_contrato": employee.tipo_contrato,
        "funcao": employee.funcao,
        "email": employee.email,
        "telefone": employee.telefone,
        "photo_url": employee.photo_url,
        "photo_base64": employee.photo_base64,
        "photo_type": employee.photo_type,
        "has_photo": bool(employee.photo),
        "created_at": employee.created_at,
        "updated_at": employee.updated_at,
    }
def _serialize_employee(employee: Employee) -> dict:
    return {
        "id": employee.id,
        "nome": employee.nome,
        "cpf_cnpj": employee.cpf_cnpj,
        "tipo_contrato": employee.tipo_contrato,
        "funcao": employee.funcao,
        "email": employee.email,
        "telefone": employee.telefone,
        "photo_url": employee.photo_url,
        "photo_base64": employee.photo_base64,
        "photo_type": employee.photo_type,
        "has_photo": bool(employee.photo),
        "created_at": employee.created_at,
        "updated_at": employee.updated_at,
        "deleted_at": employee.deleted_at,
    }

@router.get("/", response_model=list[EmployeeResponse])
def list_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    return [_serialize_employee(employee) for employee in employees]
@router.get("/", response_model=list[EmployeeResponse])
def list_employees(deleted_only: bool = Query(False), db: Session = Depends(get_db)):
    """
    Listar funcionários.
    - deleted_only=false: retorna apenas funcionários ativos
    - deleted_only=true: retorna apenas funcionários deletados
    """
    if deleted_only:
        employees = db.query(Employee).filter(Employee.deleted_at.isnot(None)).all()
    else:
        employees = db.query(Employee).filter(Employee.deleted_at.is_(None)).all()
    return [_serialize_employee(employee) for employee in employees]

@router.post("/", response_model=EmployeeResponse, status_code=201)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    employee_data = employee.dict()
    email = employee_data.get("email")
    role = _role_from_funcao(employee_data.get("funcao"))

    cpf_cnpj = employee_data.get("cpf_cnpj")
    if cpf_cnpj and not is_valid_cpf_cnpj(cpf_cnpj):
        raise HTTPException(status_code=400, detail="CPF/CNPJ inválido")

    db_user = None
    if email:
        db_user = db.query(User).filter(User.email == email).first()
        generated_password = f"{email.split('@')[0].replace('.', '').replace('_', '').replace('-', '').lower()}123"
        if db_user:
            db_user.role = role
            db_user.hashed_password = get_password_hash(generated_password)
            # populate user fields from employee when available
            if employee_data.get('nome'):
                db_user.name = employee_data.get('nome')
            if employee_data.get('telefone'):
                db_user.phone = employee_data.get('telefone')
            if employee_data.get('cpf_cnpj'):
                db_user.cpf = employee_data.get('cpf_cnpj')
        else:
            db_user = User(
                email=email,
                hashed_password=get_password_hash(generated_password),
                role=role,
                name=employee_data.get('nome'),
                phone=employee_data.get('telefone'),
                cpf=employee_data.get('cpf_cnpj'),
            )
            db.add(db_user)
            db.flush()

    db_employee = Employee(
        **employee_data,
        user_id=db_user.id if db_user else None,
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return _serialize_employee(db_employee)

@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, employee: EmployeeUpdate, db: Session = Depends(get_db)):
    db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    
    update_data = employee.dict(exclude_unset=True)
    role = _role_from_funcao(update_data.get("funcao", db_employee.funcao))

    if "cpf_cnpj" in update_data and update_data["cpf_cnpj"] and not is_valid_cpf_cnpj(update_data["cpf_cnpj"]):
        raise HTTPException(status_code=400, detail="CPF/CNPJ inválido")

    if db_employee.user_id:
        db_user = db.query(User).filter(User.id == db_employee.user_id).first()
        if db_user:
            if "email" in update_data and update_data["email"]:
                db_user.email = update_data["email"]
            db_user.role = role
            # update related user fields when employee data changes
            if "nome" in update_data and update_data["nome"]:
                db_user.name = update_data["nome"]
            if "telefone" in update_data and update_data["telefone"]:
                db_user.phone = update_data["telefone"]
            if "cpf_cnpj" in update_data and update_data["cpf_cnpj"]:
                db_user.cpf = update_data["cpf_cnpj"]

    for field, value in update_data.items():
        setattr(db_employee, field, value)

    if not db_employee.user_id and update_data.get("email"):
        db_user = db.query(User).filter(User.email == update_data["email"]).first()
        if not db_user:
            generated_password = f"{update_data['email'].split('@')[0].replace('.', '').replace('_', '').replace('-', '').lower()}123"
            db_user = User(
                email=update_data["email"],
                hashed_password=get_password_hash(generated_password),
                role=role,
                name=update_data.get('nome'),
                phone=update_data.get('telefone'),
                cpf=update_data.get('cpf_cnpj'),
            )
            db.add(db_user)
            db.flush()
        db_employee.user_id = db_user.id

    db_employee.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_employee)
    return _serialize_employee(db_employee)

@router.delete("/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    
    db.delete(db_employee)
    db.commit()
    return {"message": "Funcionário deletado com sucesso"}
@router.delete("/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    """Soft delete do funcionário - marca como deletado sem remover dados"""
    db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    
    db_employee.deleted_at = datetime.utcnow()
    db_employee.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Funcionário deletado com sucesso", "deleted_at": db_employee.deleted_at}


@router.post("/{employee_id}/photo", response_model=EmployeeResponse)
@router.post("/{employee_id}/restore")
def restore_employee(employee_id: int, db: Session = Depends(get_db)):
    """Restaura um funcionário deletado"""
    db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    
    if db_employee.deleted_at is None:
        raise HTTPException(status_code=400, detail="Funcionário não foi deletado")
    
    db_employee.deleted_at = None
    db_employee.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Funcionário restaurado com sucesso"}

@router.post("/{employee_id}/photo", response_model=EmployeeResponse)
def upload_employee_photo(
    employee_id: int,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload de foto para funcionário.
    Converte para WebP, redimensiona para max 512x512 com quality 80.
    Salva bytes em campo BYTEA.
    """
    db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")

    # Validar tipo de arquivo
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.gif'}
    allowed_content_types = {
        'image/jpeg', 'image/png', 'image/webp', 'image/heic', 
        'image/gif', 'application/octet-stream'
    }
    
    if photo.content_type and not (
        photo.content_type in allowed_content_types 
        or photo.content_type.startswith("image/")
    ):
        raise HTTPException(status_code=400, detail="Tipo de arquivo não permitido")

    # Validar tamanho (máximo 5MB antes do processamento)
    max_upload_size = 5 * 1024 * 1024  # 5MB
    file_bytes = photo.file.read()
    
    if len(file_bytes) > max_upload_size:
        raise HTTPException(
            status_code=413, 
            detail=f"Arquivo muito grande. Máximo: 5MB"
        )
    
    # Processar para WebP
    webp_bytes = _process_photo_to_webp(file_bytes, max_size=512, quality=80)
    
    # Salvar no banco
    db_employee.photo = webp_bytes
    db_employee.photo_type = "image/webp"
    # Codificar WebP para base64
    db_employee.photo_base64 = base64.b64encode(webp_bytes).decode("ascii")
    # Gerar URL de foto
    version = int(db_employee.updated_at.timestamp()) if db_employee.updated_at else int(datetime.utcnow().timestamp())
    db_employee.photo_url = f"/api/v1/employees/photo/{db_employee.id}?v={version}"
    db_employee.updated_at = datetime.utcnow()
    
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return _serialize_employee(db_employee)


@router.get("/photo/{employee_id}")
def get_employee_photo(employee_id: int, db: Session = Depends(get_db)):
    """
    Retorna foto em formato WebP.
    Se não existir foto, retorna 404.
    """
    db_employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    
    if not db_employee.photo:
        raise HTTPException(status_code=404, detail="Foto não encontrada")
    
    return Response(
        content=db_employee.photo,
        media_type=db_employee.photo_type or "image/webp"
    )
