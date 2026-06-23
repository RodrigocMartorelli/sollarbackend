from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from sqlalchemy import case, func
from app.models import Proposal, User, Employee
from app.schemas import ProposalCreate, ProposalResponse, ProposalUpdate
from app.security import verify_token, encrypt_data, decrypt_data, get_current_user
from typing import List

router = APIRouter(prefix="/proposals", tags=["proposals"])


def _can_access_all_records(current_user: User) -> bool:
    return current_user.role in {"dev", "adm"}


def _can_access_test_records(current_user: User) -> bool:
    return current_user.role == "dev"


def _decrypt_optional(value):
    if value is None:
        return None
    try:
        return decrypt_data(value)
    except Exception:
        return value


def _serialize_proposal(db: Session, proposal: Proposal, seller_name: str | None) -> dict:
    return {
        'id': proposal.id,
        'user_id': proposal.user_id,
        'client_id': proposal.client_id,
        'proposal_name': proposal.proposal_name,
        'client_name': proposal.client_name,
        'cpf_cnpj': _decrypt_optional(proposal.cpf_cnpj),
        'phone': _decrypt_optional(proposal.phone),
        'whatsapp': _decrypt_optional(proposal.whatsapp),
        'contact_preference': proposal.contact_preference,
        'street': _decrypt_optional(proposal.street),
        'neighborhood': _decrypt_optional(proposal.neighborhood),
        'house_number': _decrypt_optional(proposal.house_number),
        'complement': _decrypt_optional(proposal.complement),
        'logradouro': _decrypt_optional(proposal.logradouro),
        'income': proposal.income,
        'average_bill': proposal.average_bill,
        'status': proposal.status,
        'obra_value': proposal.obra_value,
        'consumption': proposal.consumption,
        'peak_hours': proposal.peak_hours,
        'is_test': proposal.is_test,
        'seller_name': seller_name,
        'created_at': proposal.created_at,
        'updated_at': proposal.updated_at,
        'energy_unit': proposal.energy_unit,
        'account_type': proposal.account_type,
        'installation_address': proposal.installation_address,
        'codigo_cidade': proposal.codigo_cidade,
        'installation_codigo_cidade': proposal.installation_codigo_cidade,
        'installation_city': proposal.installation_city,
        'installation_state': proposal.installation_state,
        'installation_cep': proposal.installation_cep,
        'installation_street': proposal.installation_street,
        'installation_neighborhood': proposal.installation_neighborhood,
        'installation_house_number': proposal.installation_house_number,
        'installation_complement': proposal.installation_complement,
    }

@router.post("/", response_model=ProposalResponse)
def create_proposal(
    proposal: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Criar nova proposta (dados encriptados)"""
    proposal_is_test = bool(proposal.is_test)
    if proposal_is_test and not _can_access_test_records(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas dev pode criar proposta de teste"
        )
    
    # Encriptar dados sensíveis
    cpf_cnpj = encrypt_data(proposal.cpf_cnpj) if proposal.cpf_cnpj else None
    phone = encrypt_data(proposal.phone) if proposal.phone else None
    whatsapp = encrypt_data(proposal.whatsapp) if proposal.whatsapp else None
    cep = encrypt_data(proposal.cep) if proposal.cep else None
    street = encrypt_data(proposal.street) if proposal.street else None
    neighborhood = encrypt_data(proposal.neighborhood) if proposal.neighborhood else None
    house_number = encrypt_data(proposal.house_number) if proposal.house_number else None
    complement = encrypt_data(proposal.complement) if proposal.complement else None
    logradouro = encrypt_data(proposal.logradouro) if proposal.logradouro else None
    
    # Criar proposta
    db_proposal = Proposal(
        user_id=current_user.id,
        client_id=proposal.client_id,
        is_test=proposal_is_test,
        proposal_name=proposal.proposal_name,
        client_name=proposal.client_name,
        cpf_cnpj=cpf_cnpj,
        phone=phone,
        whatsapp=whatsapp,
        contact_preference=proposal.contact_preference,
        cep=cep,
        street=street,
        neighborhood=neighborhood,
        house_number=house_number,
        complement=complement,
        logradouro=logradouro,
        status=proposal.status or "proposta enviada",
        obra_value=proposal.obra_value if proposal.obra_value is not None else proposal.average_bill,
        income=proposal.income,
        average_bill=proposal.average_bill,
        consumption=proposal.consumption,
        peak_hours=proposal.peak_hours,
        energy_unit=proposal.energy_unit,
        account_type=proposal.account_type,
        installation_address=proposal.installation_address,
        codigo_cidade=proposal.codigo_cidade,
        installation_codigo_cidade=proposal.installation_codigo_cidade,
        installation_city=proposal.installation_city,
        installation_state=proposal.installation_state,
        installation_cep=proposal.installation_cep,
        installation_street=proposal.installation_street,
        installation_neighborhood=proposal.installation_neighborhood,
        installation_house_number=proposal.installation_house_number,
        installation_complement=proposal.installation_complement,
)
    
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    if not db_proposal.proposal_name:
        db_proposal.proposal_name = f"Proposta {db_proposal.client_name} #{db_proposal.id}"
        db.commit()
        db.refresh(db_proposal)
    return db_proposal

@router.get("/", response_model=List[ProposalResponse])
def list_proposals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    sort_field: str | None = Query(None, alias='sort_field'),
    sort_dir: str | None = Query(None, alias='sort_dir'),
):
    """Listar propostas do usuário"""

    query = db.query(Proposal)
    if current_user.role == "dev":
        pass
    elif current_user.role == "adm":
        query = query.filter(Proposal.is_test.is_(False))
    else:
        query = query.filter(
            Proposal.user_id == current_user.id,
            Proposal.is_test.is_(False),
        )

    # server-side ordering must happen before pagination
    sf = (sort_field or '').strip().lower()
    sd = (sort_dir or 'desc').strip().lower()
    asc = sd == 'asc'

    if sf == 'created':
        order_by = [
            Proposal.updated_at.asc() if asc else Proposal.updated_at.desc(),
            Proposal.created_at.asc() if asc else Proposal.created_at.desc(),
        ]
    elif sf == 'status':
        # Priority tuned for proposal workflow. Desc (default) puts "em obras" first.
        status_rank = case(
            {
                'sem proposta': 0,
                'proposta enviada': 1,
                'proposta aceita': 2,
                'em obras': 3,
                'pos venda': 4,
                'pós venda': 4,
            },
            value=func.lower(func.coalesce(Proposal.status, 'proposta enviada')),
            else_=0,
        )
        order_by = [
            status_rank.asc() if asc else status_rank.desc(),
            Proposal.updated_at.desc(),
            Proposal.created_at.desc(),
        ]
    else:
        order_by = [
            Proposal.updated_at.desc(),
            Proposal.created_at.desc(),
        ]

    proposals = query.order_by(*order_by).offset(skip).limit(limit).all()

    result = []
    for proposal in proposals:
        seller_name = None
        if proposal.user_id:
            seller_user = db.query(User).filter(User.id == proposal.user_id).first()
            if seller_user and seller_user.name:
                seller_name = seller_user.name

            if not seller_name:
                seller_employee = db.query(Employee).filter(Employee.user_id == proposal.user_id).first()
                if seller_employee and seller_employee.nome:
                    seller_name = seller_employee.nome
        
        # Criar dict com dados da proposta + seller_name
        result.append(ProposalResponse.model_validate(_serialize_proposal(db, proposal, seller_name)))

    return result

@router.get("/{proposal_id}", response_model=ProposalResponse)
def get_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obter detalhes de uma proposta (dados desencriptados)"""

    query = db.query(Proposal).filter(Proposal.id == proposal_id)
    if current_user.role == "adm":
        query = query.filter(Proposal.is_test.is_(False))
    elif current_user.role != "dev":
        query = query.filter(
            Proposal.user_id == current_user.id,
            Proposal.is_test.is_(False),
        )

    proposal = query.first()
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )
    
    # Calcular seller_name
    seller_name = None
    if proposal.user_id:
        seller_user = db.query(User).filter(User.id == proposal.user_id).first()
        if seller_user and seller_user.name:
            seller_name = seller_user.name

        if not seller_name:
            seller_employee = db.query(Employee).filter(Employee.user_id == proposal.user_id).first()
            if seller_employee and seller_employee.nome:
                seller_name = seller_employee.nome
    
    # Criar dict com dados da proposta + seller_name
    return ProposalResponse.model_validate(_serialize_proposal(db, proposal, seller_name))

@router.put("/{proposal_id}", response_model=ProposalResponse)
def update_proposal(
    proposal_id: int,
    proposal_update: ProposalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualizar proposta (dados sensíveis encriptados)"""

    query = db.query(Proposal).filter(Proposal.id == proposal_id)
    if current_user.role == "adm":
        query = query.filter(Proposal.is_test.is_(False))
    elif current_user.role != "dev":
        query = query.filter(
            Proposal.user_id == current_user.id,
            Proposal.is_test.is_(False),
        )

    proposal = query.first()
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )
    
    # Atualizar campos (encriptando sensíveis se fornecidos)
    if proposal_update.client_name is not None:
        proposal.client_name = proposal_update.client_name
    if proposal_update.proposal_name is not None:
        proposal.proposal_name = proposal_update.proposal_name
    if proposal_update.phone is not None:
        proposal.phone = encrypt_data(proposal_update.phone)
    if proposal_update.whatsapp is not None:
        proposal.whatsapp = encrypt_data(proposal_update.whatsapp)
    if proposal_update.contact_preference is not None:
        proposal.contact_preference = proposal_update.contact_preference
    if proposal_update.street is not None:
        proposal.street = encrypt_data(proposal_update.street)
    if proposal_update.neighborhood is not None:
        proposal.neighborhood = encrypt_data(proposal_update.neighborhood)
    if proposal_update.house_number is not None:
        proposal.house_number = encrypt_data(proposal_update.house_number)
    if proposal_update.complement is not None:
        proposal.complement = encrypt_data(proposal_update.complement)
    if proposal_update.logradouro is not None:
        proposal.logradouro = encrypt_data(proposal_update.logradouro)
    if proposal_update.income is not None:
        proposal.income = proposal_update.income
    if proposal_update.average_bill is not None:
        proposal.average_bill = proposal_update.average_bill
        if proposal_update.obra_value is None:
            proposal.obra_value = proposal_update.average_bill
    if proposal_update.status is not None:
        proposal.status = proposal_update.status
    if proposal_update.obra_value is not None:
        proposal.obra_value = proposal_update.obra_value
    if proposal_update.consumption is not None:
        proposal.consumption = proposal_update.consumption
    if proposal_update.peak_hours is not None:
        proposal.peak_hours = proposal_update.peak_hours
    if proposal_update.energy_unit is not None:
        proposal.energy_unit = proposal_update.energy_unit
    if proposal_update.account_type is not None:
        proposal.account_type = proposal_update.account_type
    if proposal_update.installation_address is not None:
        proposal.installation_address = proposal_update.installation_address
    if proposal_update.codigo_cidade is not None:
        proposal.codigo_cidade = proposal_update.codigo_cidade
    if proposal_update.installation_codigo_cidade is not None:
        proposal.installation_codigo_cidade = proposal_update.installation_codigo_cidade
    if proposal_update.installation_city is not None:
        proposal.installation_city = proposal_update.installation_city

    if proposal_update.installation_state is not None:
        proposal.installation_state = proposal_update.installation_state

    if proposal_update.installation_cep is not None:
        proposal.installation_cep = proposal_update.installation_cep

    if proposal_update.installation_street is not None:
        proposal.installation_street = proposal_update.installation_street

    if proposal_update.installation_neighborhood is not None:
        proposal.installation_neighborhood = proposal_update.installation_neighborhood

    if proposal_update.installation_house_number is not None:
        proposal.installation_house_number = proposal_update.installation_house_number

    if proposal_update.installation_complement is not None:
        proposal.installation_complement = proposal_update.installation_complement
    
    db.commit()
    db.refresh(proposal)

    seller_name = None
    if proposal.user_id:
        seller_user = db.query(User).filter(User.id == proposal.user_id).first()
        if seller_user and seller_user.name:
            seller_name = seller_user.name

        if not seller_name:
            seller_employee = db.query(Employee).filter(Employee.user_id == proposal.user_id).first()
            if seller_employee and seller_employee.nome:
                seller_name = seller_employee.nome

    return ProposalResponse.model_validate(_serialize_proposal(db, proposal, seller_name))

@router.delete("/{proposal_id}")
def delete_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletar proposta"""

    query = db.query(Proposal).filter(Proposal.id == proposal_id)
    if current_user.role == "adm":
        query = query.filter(Proposal.is_test.is_(False))
    elif current_user.role != "dev":
        query = query.filter(
            Proposal.user_id == current_user.id,
            Proposal.is_test.is_(False),
        )

    proposal = query.first()
    
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposal not found"
        )
    
    db.delete(proposal)
    db.commit()
    return {"message": "Proposal deleted"}
