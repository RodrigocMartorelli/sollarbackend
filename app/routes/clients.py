"""
Rotas para gerenciar clientes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Client, User, Proposal, Employee
from app.schemas import ClientCreate, ClientUpdate, ClientResponse
from app.security import get_current_user
from app.utils.document_utils import is_valid_cpf_cnpj
from typing import List, Optional
import json

router = APIRouter(prefix="/clients", tags=["clients"])


def _can_access_all_records(current_user: User) -> bool:
    return current_user.role in {"dev", "adm"}


def _can_access_test_clients(current_user: User) -> bool:
    return current_user.role == "dev"


def _normalize_empty_strings(data: dict) -> dict:
    normalized = {}
    for key, value in data.items():
        if isinstance(value, str) and not value.strip():
            normalized[key] = None
        else:
            normalized[key] = value
    return normalized


def _get_client_creator_name(db: Session, client: Client) -> Optional[str]:
    if not client.user_id:
        return None

    creator = db.query(User).filter(User.id == client.user_id).first()
    if creator and creator.name:
        return creator.name

    employee = db.query(Employee).filter(Employee.user_id == client.user_id).first()
    if employee and employee.nome:
        return employee.nome

    if creator and creator.email:
        return creator.email

    return None

@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def criar_cliente(
    cliente: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Criar um novo cliente"""
    
    cliente_data = _normalize_empty_strings(cliente.model_dump())
    is_test = bool(cliente_data.get("is_test", False))

    if is_test and not _can_access_test_clients(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas dev pode criar cliente de teste"
        )

    cliente_data["is_test"] = is_test and _can_access_test_clients(current_user)

    # Verificar se email já existe
    if cliente_data.get("email"):
        db_cliente = db.query(Client).filter(Client.email == cliente_data["email"]).first()
    else:
        db_cliente = None

    if db_cliente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )

    if cliente_data.get("cpf_cnpj"):
        if not is_valid_cpf_cnpj(cliente_data["cpf_cnpj"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF/CNPJ inválido",
            )
        db_cpf = db.query(Client).filter(Client.cpf_cnpj == cliente_data["cpf_cnpj"]).first()
        if db_cpf:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF/CNPJ já cadastrado"
            )
    
    # Criar novo cliente
    novo_cliente = Client(
        user_id=current_user.id,
        **cliente_data
    )
    
    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)
    
    return novo_cliente

@router.get("/")
def listar_clientes(
    response: Response,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=10000),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Listar clientes com paginação e busca por nome ou número da proposta.

    - `page` (1-based)
    - `per_page` (padrão 10)
    - `q` busca por nome do cliente ou número da proposta (se estiver apenas dígitos)
    Retorna header `X-Total-Count` com total de resultados.
    """

    query_db = db.query(Client)
    # aplicar filtros de visibilidade por role
    if current_user.role == "dev":
        pass
    elif current_user.role == "adm":
        query_db = query_db.filter(Client.is_test.is_(False))
    else:
        query_db = query_db.filter(
            Client.user_id == current_user.id,
            Client.is_test.is_(False),
        )

    # busca por q: nome do cliente ou número da proposta
    if q:
        q_str = q.strip()
        if q_str.isdigit():
            # tentar localizar proposta pelo id
            try:
                prop_id = int(q_str)
                prop = db.query(Proposal).filter(Proposal.id == prop_id).first()
            except Exception:
                prop = None

            if prop and prop.client_name:
                # buscar clientes cujo nome contenha o client_name da proposta
                query_db = query_db.filter(Client.nome.ilike(f"%{prop.client_name}%"))
            else:
                # fallback: buscar por nome contendo o dígito string
                query_db = query_db.filter(Client.nome.ilike(f"%{q_str}%"))
        else:
            query_db = query_db.filter(Client.nome.ilike(f"%{q_str}%"))

    total = query_db.count()

    # paginação
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 10

    clientes = (
        query_db.order_by(
            Client.data_atualizacao.desc(),
            Client.data_criacao.desc(),
            Client.id.desc(),
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # Serializar manualmente os clientes
    clientes_list = [
        {
            "id": c.id,
            "user_id": c.user_id,
            "seller_name": _get_client_creator_name(db, c),
            "nome": c.nome,
            "email": c.email,
            "telefone": c.telefone,
            "whatsapp": c.whatsapp,
            "contact_preference": c.contact_preference,
            "cpf_cnpj": c.cpf_cnpj,
            "is_test": c.is_test,
            "cep": c.cep,
            "rua": c.rua,
            "numero": c.numero,
            "complemento": c.complemento,
            "bairro": c.bairro,
            "cidade": c.cidade,
            "estado": c.estado,
            "created_at": c.data_criacao.isoformat() if c.data_criacao else None,
            "data_criacao": c.data_criacao.isoformat() if c.data_criacao else None,
            "updated_at": c.data_atualizacao.isoformat() if c.data_atualizacao else None,
            "data_atualizacao": c.data_atualizacao.isoformat() if c.data_atualizacao else None,
        }
        for c in clientes
    ]

    # Retornar com header X-Total-Count
    response.headers["X-Total-Count"] = str(total)
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count"
    
    return clientes_list

@router.get("/{cliente_id}", response_model=ClientResponse)
def obter_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obter detalhes de um cliente específico"""
    
    query = db.query(Client).filter(Client.id == cliente_id)
    if current_user.role == "adm":
        query = query.filter(Client.is_test.is_(False))
    elif current_user.role != "dev":
        query = query.filter(
            Client.user_id == current_user.id,
            Client.is_test.is_(False),
        )

    cliente = query.first()
    
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    
    return cliente

@router.put("/{cliente_id}", response_model=ClientResponse)
def atualizar_cliente(
    cliente_id: int,
    cliente_update: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualizar dados de um cliente"""

    query = db.query(Client).filter(Client.id == cliente_id)
    if current_user.role == "adm":
        query = query.filter(Client.is_test.is_(False))
    elif current_user.role != "dev":
        query = query.filter(
            Client.user_id == current_user.id,
            Client.is_test.is_(False),
        )

    cliente = query.first()

    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )

    # Atualizar apenas campos fornecidos
    dados_atualizacao = cliente_update.model_dump(exclude_unset=True)

    # Permitir que o frontend envie explicitamente is_test:false sem bloquear.
    # Só bloquear se o usuário tentar ativar is_test (true) e não for dev.
    if "is_test" in dados_atualizacao:
        novo_is_test = bool(dados_atualizacao["is_test"]) 
        if novo_is_test and not _can_access_test_clients(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas dev pode alterar cliente de teste"
            )
        dados_atualizacao["is_test"] = novo_is_test

    if "cpf_cnpj" in dados_atualizacao and dados_atualizacao["cpf_cnpj"]:
        if not is_valid_cpf_cnpj(dados_atualizacao["cpf_cnpj"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF/CNPJ inválido",
            )

    for campo, valor in dados_atualizacao.items():
        setattr(cliente, campo, valor)

    db.commit()
    db.refresh(cliente)

    return cliente

@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletar um cliente"""
    
    query = db.query(Client).filter(Client.id == cliente_id)
    if current_user.role == "adm":
        query = query.filter(Client.is_test.is_(False))
    elif current_user.role != "dev":
        query = query.filter(
            Client.user_id == current_user.id,
            Client.is_test.is_(False),
        )

    cliente = query.first()
    
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    
    db.delete(cliente)
    db.commit()
    
    return None
