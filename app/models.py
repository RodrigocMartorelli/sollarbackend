from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, LargeBinary, Numeric, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="vendedor")  # vendedor, dev, adm
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    cpf = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    proposals = relationship("Proposal", back_populates="user")
    clients = relationship("Client", back_populates="user")

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Dados do cliente
    nome = Column(String(255), index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    telefone = Column(String(20), nullable=True)
    whatsapp = Column(String(20), nullable=True)
    contact_preference = Column(String(50), nullable=True)
    cpf_cnpj = Column(String(20), unique=True, nullable=True)
    is_test = Column(Boolean, nullable=False, default=False)
    
    # Endereço
    cep = Column(String(10), nullable=True)
    rua = Column(String(255), nullable=True)
    numero = Column(String(10), nullable=True)
    complemento = Column(String(255), nullable=True)
    bairro = Column(String(100), nullable=True)
    cidade = Column(String(100), nullable=True)
    estado = Column(String(2), nullable=True)
    
    # Metadados
    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)- user = relationship("User", back_populates="clients")

class Proposal(Base):
    __tablename__ = "proposals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True, index=True)
    is_test = Column(Boolean, nullable=False, default=False)
    proposal_name = Column(String, nullable=True, index=True)
    
    # Client data (encrypted)
    client_name = Column(String, index=True)
    cpf_cnpj = Column(String, nullable=True)  # Encrypted
    phone = Column(String, nullable=True)  # Encrypted
    whatsapp = Column(String, nullable=True)  # Encrypted
    contact_preference = Column(String, nullable=True)
    
    # Address data (optional, encrypted)
    cep = Column(String, nullable=True)  # Encrypted
    street = Column(String, nullable=True)  # Encrypted
    neighborhood = Column(String, nullable=True)  # Encrypted
    house_number = Column(String, nullable=True)  # Encrypted
    complement = Column(String, nullable=True)  # Encrypted
    logradouro = Column(String, nullable=True)  # Encrypted
    status = Column(String, nullable=False, default="proposta enviada")
    obra_value = Column(Float, nullable=True)
    energy_unit = Column(String, nullable=True)
    account_type = Column(String, nullable=True)
    installation_address = Column(String, nullable=True)
    codigo_cidade = Column(String, nullable=True)
    installation_codigo_cidade = Column(String, nullable=True)

    installation_city = Column(String, nullable=True)
    installation_state = Column(String, nullable=True)
    installation_cep = Column(String, nullable=True)
    installation_street = Column(String, nullable=True)
    installation_neighborhood = Column(String, nullable=True)
    installation_house_number = Column(String, nullable=True)
    installation_complement = Column(String, nullable=True)
        
    # Energy data
    income = Column(Float, nullable=True)
    average_bill = Column(Float, nullable=True)
    consumption = Column(Float, nullable=True)
    peak_hours = Column(String, nullable=True)
    codigo_distribuidora = Column(String, nullable=True)
    installation_codigo_distribuidora = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="proposals")

    energy = relationship(
    "ClientEnergy",
    back_populates="proposal",
    uselist=False,
    cascade="all, delete-orphan",)

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    nome = Column(String(255), nullable=False, index=True)
    cpf_cnpj = Column(String(20), unique=True, nullable=True)
    tipo_contrato = Column(String(10), nullable=True)
    funcao = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    telefone = Column(String(20), nullable=True)
    photo_url = Column(String(255), nullable=True)
    photo_base64 = Column(Text, nullable=True)
    photo = Column(LargeBinary, nullable=True)
    photo_type = Column(String(50), default="image/webp", nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True, default=None)
    user = relationship("User", foreign_keys=[user_id])


class InventoryItem(Base):
    """
    Inventory Item model for tracking solar products in stock.
    
    Fields:
    - id: Unique identifier
    - name: Product name (must be unique)
    - brand: Manufacturer/brand name
    - quantity: Amount in stock (decimal for fractional units like meters)
    - unit: Measurement unit (m, un, kg, etc.)
    - type: Product category (Cabo, Placa Solar, etc.)
    - observations: Optional notes about the product
    - created_at: Timestamp when item was added
    - updated_at: Timestamp of last modification
    """
    
    __tablename__ = "inventory"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Core Fields
    name = Column(String(255), unique=True, nullable=False, index=True)
    brand = Column(String(150), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(10), default="un", nullable=False)
    type = Column(String(100), nullable=False, index=True)
    
    # Optional Fields
    observations = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    def __repr__(self):
        return f"<InventoryItem(id={self.id}, name='{self.name}', brand='{self.brand}', quantity={self.quantity}{self.unit})>"


class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True)
    page_name = Column(String(255), nullable=False, index=True)
    error_message = Column(String(1024), nullable=False)
    stack_trace = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ErrorLog(id={self.id}, page='{self.page_name}', message='{self.error_message[:80]}')>"


class FotusCredential(Base):
    __tablename__ = "fotus_credentials"

    id = Column(Integer, primary_key=True, index=True)
    integrator_token = Column(String(255), nullable=False)
    company_token = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<FotusCredential(id={self.id})>"
    

class ClientEnergy(Base):
    __tablename__ = "client_energy"

    id = Column(Integer, primary_key=True)

    proposal_id = Column(
        Integer,
        ForeignKey("proposals.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    client_name = Column(String(255), nullable=True)
    energy_value = Column(Float, nullable=True)
    energy_unit = Column(String(20), nullable=True)
    account_type = Column(String(50), nullable=True)
    consumo_mensal = Column(Float, nullable=True)

    modalidade_tarifaria = Column(String(50), nullable=True)
    nome_uc = Column(String(255), nullable=True)
    tipo_uc = Column(String(50), nullable=True)
    distribuidora = Column(String(255), nullable=True)
    iluminacao_publica = Column(Float, nullable=True)

    rede = Column(Integer, nullable=True)

    fator_simult = Column(Float, nullable=True)
    
    classificacao_horo_sazonal = Column(String(100), nullable=True)

    consumo_ponta = Column(Float, nullable=True)
    consumo_fora_ponta = Column(Float, nullable=True)

    te_fora_ponta = Column(Float, nullable=True)
    te_ponta = Column(Float, nullable=True)

    tusd_fora_ponta = Column(Float, nullable=True)
    tusd_ponta = Column(Float, nullable=True)

    demanda = Column(Float, nullable=True)
    tarifa_demanda = Column(Float, nullable=True)

    demanda_ponta = Column(Float, nullable=True)
    demanda_fora_ponta = Column(Float, nullable=True)

    tarifa_demanda_ponta = Column(Float, nullable=True)
    tarifa_demanda_fora_ponta = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    proposal = relationship("Proposal", back_populates="energy")