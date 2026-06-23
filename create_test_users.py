#!/usr/bin/env python
"""
Script para criar usuários de teste no banco de dados
"""
from app.database import SessionLocal
from app.models import User
from app.security import get_password_hash

def create_test_users():
    db = SessionLocal()
    
    try:
        # Usuário 1: Dev - Rodrigo
        user1_email = "rodrigomartorelli@gmail.com"
        user1 = db.query(User).filter(User.email == user1_email).first()
        
        if not user1:
            user1 = User(
                email=user1_email,
                hashed_password=get_password_hash("pokemon12"),
                role="dev"
            )
            db.add(user1)
            print(f"✓ Usuário DEV criado: {user1_email}")
        else:
            user1.hashed_password = get_password_hash("pokemon12")
            user1.role = user1.role or "dev"
            db.add(user1)
            print(f"✓ Usuário DEV atualizado: {user1_email}")
        
        # Usuário 2: Admin - Sollar SE
        user2_email = "sollarSE@gmail.com"
        user2 = db.query(User).filter(User.email == user2_email).first()
        
        if not user2:
            user2 = User(
                email=user2_email,
                hashed_password=get_password_hash("teste123"),
                role="adm"
            )
            db.add(user2)
            print(f"✓ Usuário ADM criado: {user2_email}")
        else:
            user2.hashed_password = get_password_hash("teste123")
            user2.role = user2.role or "adm"
            db.add(user2)
            print(f"✓ Usuário ADM atualizado: {user2_email}")
        
        db.commit()
        print("\n✓ Usuários de teste criados com sucesso!")
        print("\nCredenciais:")
        print("  DEV: rodrigomartorelli@gmail.com / pokemon12")
        print("  ADM: sollarSE@gmail.com / teste123")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Erro ao criar usuários: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()
