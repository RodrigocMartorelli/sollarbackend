#!/usr/bin/env python
"""
Script para verificar conexão com PostgreSQL e testar API
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório ao path
sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "="*60)
print("  🔍 TESTANDO CONEXÃO COM POSTGRESQL")
print("="*60 + "\n")

# Passo 1: Carregar variáveis de ambiente
print("📝 Passo 1: Carregando configurações...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    db_url = os.getenv("DATABASE_URL")
    print(f"✅ DATABASE_URL carregada: {db_url[:50]}...")
except Exception as e:
    print(f"❌ Erro ao carregar .env: {e}")
    sys.exit(1)

# Passo 2: Testar importações
print("\n📦 Passo 2: Testando importações...")
try:
    from app.database import engine, SessionLocal, Base
    print("✅ database.py carregado")
except Exception as e:
    print(f"❌ Erro ao importar database: {e}")
    sys.exit(1)

try:
    from app.models import User, Client, Proposal
    print("✅ models.py carregado")
except Exception as e:
    print(f"❌ Erro ao importar models: {e}")
    sys.exit(1)

# Passo 3: Testar conexão com banco
print("\n🔗 Passo 3: Testando conexão com PostgreSQL...")
try:
    with engine.connect() as connection:
        result = connection.execute("SELECT 1")
        print(f"✅ Conexão com PostgreSQL OK!")
        print(f"   Versão: {connection.execute('SELECT version()').scalar()[:50]}...")
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    sys.exit(1)

# Passo 4: Criar tabelas
print("\n📊 Passo 4: Criando/verificando tabelas...")
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Tabelas criadas/verificadas com sucesso!")
    
    # Listar tabelas
    inspector_result = engine.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = [row[0] for row in inspector_result]
    print(f"   Tabelas no banco: {', '.join(tables) if tables else 'nenhuma'}")
except Exception as e:
    print(f"❌ Erro ao criar tabelas: {e}")
    sys.exit(1)

# Passo 5: Testar app FastAPI
print("\n⚡ Passo 5: Carregando aplicação FastAPI...")
try:
    from main import app
    print("✅ main.py carregado com sucesso!")
except Exception as e:
    print(f"❌ Erro ao carregar main.py: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Sucesso!
print("\n" + "="*60)
print("  ✅ TUDO PRONTO!")
print("="*60)
print("\n📍 Próxima etapa:")
print("   python main.py")
print("\n🌐 Acesse:")
print("   http://localhost:8000/docs")
print("\n")
