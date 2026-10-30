import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import Base, engine, SessionLocal
from app.services.authentication.auth_service import AuthService
from app.core.config import settings
from app.models import *


def main():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print(f"Checking/seeding default admin: {settings.ADMIN_EMAIL}...")
        admin = AuthService.seed_admin(
            db=db,
            email=settings.ADMIN_EMAIL,
            password=settings.ADMIN_PASSWORD,
            name=settings.ADMIN_NAME,
        )
        print(f"Admin account verified with ID: {admin.id}, Email: {admin.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
