from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Auth Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None

# Client Schemas
class ClientCreate(BaseModel):
    nome: str
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    contact_preference: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    is_test: Optional[bool] = False
    cep: Optional[str] = None
    rua: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    codigo_cidade: Optional[str] = None
    installation_codigo_cidade: Optional[str] = None

class ClientUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    contact_preference: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    is_test: Optional[bool] = None
    cep: Optional[str] = None
    rua: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None

class ClientResponse(BaseModel):
    id: int
    user_id: int
    nome: str
    email: Optional[EmailStr] = None
    telefone: Optional[str]
    whatsapp: Optional[str]
    contact_preference: Optional[str]
    cpf_cnpj: Optional[str]
    is_test: bool = False
    cep: Optional[str]
    rua: Optional[str]
    numero: Optional[str]
    complemento: Optional[str]
    bairro: Optional[str]
    cidade: Optional[str]
    estado: Optional[str]
    data_criacao: datetime
    data_atualizacao: datetime

# Proposal Schemas
class ProposalBase(BaseModel):
    client_id: Optional[int] = None
    proposal_name: Optional[str] = None
    client_name: str
    cpf_cnpj: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    contact_preference: Optional[str] = None
    is_test: Optional[bool] = False
    cep: Optional[str] = None
    street: Optional[str] = None
    neighborhood: Optional[str] = None
    house_number: Optional[str] = None
    complement: Optional[str] = None
    logradouro: Optional[str] = None
    income: Optional[float] = None
    average_bill: Optional[float] = None
    status: Optional[str] = None
    obra_value: Optional[float] = None
    consumption: Optional[float] = None
    peak_hours: Optional[str] = None
    energy_unit: Optional[str] = None
    account_type: Optional[str] = None
    installation_address: Optional[str] = None

class ProposalCreate(ProposalBase):
    codigo_cidade: str | None = None
    installation_codigo_cidade: str | None = None

    codigo_distribuidora: str | None = None
    installation_codigo_distribuidora: str | None = None

    installation_city: str | None = None
    installation_state: str | None = None
    installation_cep: str | None = None
    installation_street: str | None = None
    installation_neighborhood: str | None = None
    installation_house_number: str | None = None
    installation_complement: str | None = None

class ProposalUpdate(BaseModel):
    proposal_name: Optional[str] = None
    client_name: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    contact_preference: Optional[str] = None

    street: Optional[str] = None
    neighborhood: Optional[str] = None
    house_number: Optional[str] = None
    complement: Optional[str] = None
    logradouro: Optional[str] = None

    income: Optional[float] = None
    average_bill: Optional[float] = None
    status: Optional[str] = None
    obra_value: Optional[float] = None
    consumption: Optional[float] = None
    peak_hours: Optional[str] = None

    energy_unit: Optional[str] = None
    account_type: Optional[str] = None
    installation_address: Optional[str] = None

    codigo_cidade: Optional[str] = None
    installation_codigo_cidade: Optional[str] = None

    installation_city: Optional[str] = None
    installation_state: Optional[str] = None
    installation_cep: Optional[str] = None
    installation_street: Optional[str] = None
    installation_neighborhood: Optional[str] = None
    installation_house_number: Optional[str] = None
    installation_complement: Optional[str] = None

    codigo_distribuidora: Optional[str] = None
    installation_codigo_distribuidora: Optional[str] = None

class ProposalResponse(ProposalBase):
    id: int
    user_id: int

    codigo_cidade: Optional[str] = None
    installation_codigo_cidade: Optional[str] = None

    codigo_distribuidora: Optional[str] = None
    installation_codigo_distribuidora: Optional[str] = None
    
    installation_city: Optional[str] = None
    installation_state: Optional[str] = None
    installation_cep: Optional[str] = None
    installation_street: Optional[str] = None
    installation_neighborhood: Optional[str] = None
    installation_house_number: Optional[str] = None
    installation_complement: Optional[str] = None

    seller_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
    
class Config:
    from_attributes = True

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

        
from typing import Optional
from pydantic import BaseModel


class ClientEnergyBase(BaseModel):
    client_name: Optional[str] = None
    energy_value: Optional[float] = None
    energy_unit: Optional[str] = None
    account_type: Optional[str] = None
    consumo_mensal: Optional[float] = None

    modalidade_tarifaria: Optional[str] = None
    nome_uc: Optional[str] = None
    tipo_uc: Optional[str] = None
    distribuidora: Optional[str] = None
    iluminacao_publica: Optional[float] = None

    rede: Optional[int] = None

    fator_simult: Optional[float] = None
    classificacao_horo_sazonal: Optional[str] = None

    consumo_ponta: Optional[float] = None
    consumo_fora_ponta: Optional[float] = None

    te_fora_ponta: Optional[float] = None
    te_ponta: Optional[float] = None

    tusd_fora_ponta: Optional[float] = None
    tusd_ponta: Optional[float] = None

    demanda: Optional[float] = None
    tarifa_demanda: Optional[float] = None

    demanda_ponta: Optional[float] = None
    demanda_fora_ponta: Optional[float] = None

    tarifa_demanda_ponta: Optional[float] = None
    tarifa_demanda_fora_ponta: Optional[float] = None

class ClientEnergyCreate(ClientEnergyBase):
    proposal_id: int

class ClientEnergy(ClientEnergyBase):
    id: int
    proposal_id: int

    class Config:
        from_attributes = True

