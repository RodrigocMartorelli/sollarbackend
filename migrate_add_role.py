#!/usr/bin/env python
"""
Migração: Adicionar coluna 'role' à tabela 'users'
"""
import psycopg2
from psycopg2 import sql

def migrate():
    conn = psycopg2.connect(
        host="localhost",
        database="sollar",
        user="postgres",
        password="sollarmaxx01"
    )
    
    cursor = conn.cursor()
    
    try:
        # Verificar se a coluna já existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='users' AND column_name='role'
            );
        """)
        
        if cursor.fetchone()[0]:
            print("✓ Coluna 'role' já existe")
        else:
            # Adicionar coluna
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN role VARCHAR DEFAULT 'vendedor';
            """)
            conn.commit()
            print("✓ Coluna 'role' adicionada com sucesso")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Erro: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate()
