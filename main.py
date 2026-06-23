from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text
from pathlib import Path
from app.database import Base, engine
from app.config import settings
from app.routes import auth, proposals, clients, employees, email_test, whatsapp_test, system, inventory, fotus_proxy, errors, api_tools, budget_test, utility_companies, panels
from app.models import InventoryItem, ErrorLog  # Import to create tables (including error_logs)
from app.routes.pricing import router as pricing_router

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
EMPLOYEE_PHOTOS_DIR = UPLOADS_DIR / "employees"
EMPLOYEE_PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

# Criar tabelas
Base.metadata.create_all(bind=engine)

def calcular_codigo_rede(rede: str, consumo: float) -> int:
    if rede == "Monofásico":
        return 0

    if rede == "Bifásico":
        return 0 if consumo < 3000 else 2

    if rede == "Trifásico":
        return 2

def _ensure_employee_columns() -> None:
    with engine.begin() as connection:
        inspector = inspect(connection)
        if "employees" not in inspector.get_table_names():
            return

        columns = {column["name"] for column in inspector.get_columns("employees")}

        if "cpf_cnpj" not in columns:
            connection.execute(text("ALTER TABLE employees ADD COLUMN cpf_cnpj VARCHAR(20)"))

        if "tipo_contrato" not in columns:
            connection.execute(text("ALTER TABLE employees ADD COLUMN tipo_contrato VARCHAR(10)"))

        if "photo_url" not in columns:
            connection.execute(text("ALTER TABLE employees ADD COLUMN photo_url VARCHAR(255)"))

        if "photo_base64" not in columns:
            connection.execute(text("ALTER TABLE employees ADD COLUMN photo_base64 TEXT"))

        if "photo" not in columns:
            connection.execute(text("ALTER TABLE employees ADD COLUMN photo BYTEA"))

        if "photo_type" not in columns:
            connection.execute(
                text("ALTER TABLE employees ADD COLUMN photo_type VARCHAR(50) DEFAULT 'image/webp'")
            )

        if "deleted_at" not in columns:
            connection.execute(text("ALTER TABLE employees ADD COLUMN deleted_at TIMESTAMP NULL"))

def _ensure_proposal_columns() -> None:
    with engine.begin() as connection:
        inspector = inspect(connection)
        if "proposals" not in inspector.get_table_names():
            return

        columns = {column["name"] for column in inspector.get_columns("proposals")}

        if "status" not in columns:
            connection.execute(
                text("ALTER TABLE proposals ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'proposta enviada'")
            )

        if "obra_value" not in columns:
            connection.execute(text("ALTER TABLE proposals ADD COLUMN obra_value FLOAT"))

        if "is_test" not in columns:
            connection.execute(
                text("ALTER TABLE proposals ADD COLUMN is_test BOOLEAN NOT NULL DEFAULT false")
            )

        if "client_id" not in columns:
            connection.execute(text("ALTER TABLE proposals ADD COLUMN client_id INTEGER"))

        if "proposal_name" not in columns:
            connection.execute(text("ALTER TABLE proposals ADD COLUMN proposal_name VARCHAR(255)"))

        if "energy_unit" not in columns:
            connection.execute(text("ALTER TABLE proposals ADD COLUMN energy_unit VARCHAR(20)"))

        if "account_type" not in columns:
            connection.execute(text("ALTER TABLE proposals ADD COLUMN account_type VARCHAR(50)"))

        if "installation_address" not in columns:
            connection.execute(text("ALTER TABLE proposals ADD COLUMN installation_address VARCHAR(255)"))

        if "codigo_cidade" not in columns:
            connection.execute(text("ALTER TABLE proposals ADD COLUMN codigo_cidade VARCHAR(20)"))

        if "installation_codigo_cidade" not in columns:
            connection.execute(text("ALTER TABLE proposals ADD COLUMN installation_codigo_cidade VARCHAR(20)"))

        if "installation_city" not in columns:
            connection.execute(text("ALTER TABLE proposals ADD COLUMN installation_city VARCHAR(100)"))

        if "installation_state" not in columns:
            connection.execute(text("ALTER TABLE proposals ADD COLUMN installation_state VARCHAR(2)"))

        if "installation_cep" not in columns:
            connection.execute(text("ALTER TABLE proposals ADD COLUMN installation_cep VARCHAR(10)"))

        if "installation_street" not in columns:
            connection.execute(text("ALTER TABLE proposals ADD COLUMN installation_street VARCHAR(255)"))

        if "installation_neighborhood" not in columns:
            connection.execute(text("ALTER TABLE proposals ADD COLUMN installation_neighborhood VARCHAR(255)"))

        if "installation_house_number" not in columns:
            connection.execute(text("ALTER TABLE proposals ADD COLUMN installation_house_number VARCHAR(20)"))

        if "installation_complement" not in columns:
            connection.execute(text("ALTER TABLE proposals ADD COLUMN installation_complement VARCHAR(255)"))

        _ensure_employee_columns()
        _ensure_proposal_columns()
        _ensure_client_columns()
        _ensure_error_log_columns()


def _ensure_client_columns() -> None:
    with engine.begin() as connection:
        inspector = inspect(connection)
        if "clients" not in inspector.get_table_names():
            return

        columns = {column["name"] for column in inspector.get_columns("clients")}

        if "email" in columns:
            connection.execute(text("ALTER TABLE clients ALTER COLUMN email DROP NOT NULL"))

        if "contact_preference" not in columns:
            connection.execute(
                text("ALTER TABLE clients ADD COLUMN contact_preference VARCHAR(50)")
            )

        if "is_test" not in columns:
            connection.execute(
                text("ALTER TABLE clients ADD COLUMN is_test BOOLEAN NOT NULL DEFAULT false")
            )


def _ensure_error_log_columns() -> None:
    with engine.begin() as connection:
        inspector = inspect(connection)
        if "error_logs" not in inspector.get_table_names():
            return

        columns = {column["name"] for column in inspector.get_columns("error_logs")}

        if "page_name" not in columns:
            connection.execute(text("ALTER TABLE error_logs ADD COLUMN page_name VARCHAR(255)"))
        if "error_message" not in columns:
            connection.execute(text("ALTER TABLE error_logs ADD COLUMN error_message VARCHAR(1024)"))
        if "stack_trace" not in columns:
            connection.execute(text("ALTER TABLE error_logs ADD COLUMN stack_trace TEXT"))
        if "resolved" not in columns:
            connection.execute(text("ALTER TABLE error_logs ADD COLUMN resolved BOOLEAN NOT NULL DEFAULT false"))
        if "created_at" not in columns:
            connection.execute(text("ALTER TABLE error_logs ADD COLUMN created_at TIMESTAMP"))

# Criar aplicação
app = FastAPI(
    title="Sollar Backend",
    description="Backend para aplicação de propostas de energia solar e gerenciamento de clientes",
    version="1.0.0",
)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mude isso em produção!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/v1")
app.include_router(proposals.router, prefix="/api/v1")
app.include_router(clients.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(email_test.router, prefix="/api/v1")
app.include_router(whatsapp_test.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(inventory.router, prefix="/api/v1")
app.include_router(fotus_proxy.router, prefix="/api/v1")
app.include_router(errors.router, prefix="/api/v1")
app.include_router(api_tools.router, prefix="/api/v1")
app.include_router(budget_test.router, prefix="/api/v1")
app.include_router(utility_companies.router, prefix="/api/v1")
app.include_router(panels.router, prefix="/api/v1")
app.include_router(
    pricing_router,
    prefix="/api/tools",
    tags=["pricing"]
)


@app.get("/")
def read_root():
    return {
        "message": "Sollar Backend API",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "auth": "/api/v1/auth",
            "proposals": "/api/v1/proposals",
            "clients": "/api/v1/clients",
            "email-test": "/api/v1/email-test",
            "whatsapp-test": "/api/v1/whatsapp-test",
            "api-tools": "/api/v1/api-tools",
            "budget-test": "/api/v1/api-tools/orcamentos",
        },
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "database": "connected"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )
