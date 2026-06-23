from app.database import SessionLocal
from app.models import User
from app.security import get_password_hash

db = SessionLocal()
db.query(User).filter(User.email == 'rodrigomartorelli@gmail.com').delete()
db.commit()

user = User(
    email='rodrigomartorelli@gmail.com',
    hashed_password=get_password_hash('pokemon12'),
    role='dev'
)
db.add(user)
db.commit()
print('✅ DEV recriado com sucesso!')
db.close()
