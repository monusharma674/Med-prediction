from typing import Optional
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import DuplicateResourceException, CredentialsException, BadRequestException
from app.models.user import User, UserRole, PatientProfile, DoctorProfile
from app.schemas.user import UserRegisterPatient, UserRegisterDoctor, Token


class AuthService:
    @staticmethod
    def register_patient(db: Session, data: UserRegisterPatient) -> User:
        """Registers a new patient with user record and patient profile."""
        existing_user = db.query(User).filter(User.email == data.email.lower()).first()
        if existing_user:
            raise DuplicateResourceException("An account with this email address already exists")

        new_user = User(
            email=data.email.lower(),
            hashed_password=get_password_hash(data.password),
            role=UserRole.PATIENT,
            is_active=True,
        )
        db.add(new_user)
        db.flush()

        profile = PatientProfile(
            user_id=new_user.id,
            full_name=data.full_name,
            date_of_birth=data.date_of_birth,
            gender=data.gender,
            phone=data.phone,
            blood_group=data.blood_group,
        )
        db.add(profile)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def register_doctor(db: Session, data: UserRegisterDoctor) -> User:
        """Registers a new doctor with user record and doctor profile."""
        existing_user = db.query(User).filter(User.email == data.email.lower()).first()
        if existing_user:
            raise DuplicateResourceException("An account with this email address already exists")

        if data.license_number:
            existing_doc = (
                db.query(DoctorProfile)
                .filter(DoctorProfile.license_number == data.license_number)
                .first()
            )
            if existing_doc:
                raise DuplicateResourceException("Doctor license number already registered")

        new_user = User(
            email=data.email.lower(),
            hashed_password=get_password_hash(data.password),
            role=UserRole.DOCTOR,
            is_active=True,
        )
        db.add(new_user)
        db.flush()

        profile = DoctorProfile(
            user_id=new_user.id,
            full_name=data.full_name,
            specialization=data.specialization,
            license_number=data.license_number,
            hospital=data.hospital,
            phone=data.phone,
        )
        db.add(profile)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Token:
        """Validates credentials and issues a signed JWT token."""
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user or not verify_password(password, user.hashed_password):
            raise CredentialsException("Incorrect email or password")

        if not user.is_active:
            raise BadRequestException("User account is disabled")

        # Determine user display name
        full_name = user.email
        if user.role == UserRole.PATIENT and user.patient_profile:
            full_name = user.patient_profile.full_name
        elif user.role == UserRole.DOCTOR and user.doctor_profile:
            full_name = f"Dr. {user.doctor_profile.full_name}"
        elif user.role == UserRole.ADMIN:
            full_name = "System Administrator"

        access_token = create_access_token(
            subject=user.email,
            role=user.role.value,
            user_id=user.id,
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            role=user.role,
            user_id=user.id,
            full_name=full_name,
            email=user.email,
        )

    @staticmethod
    def seed_admin(
        db: Session, email: str, password: str, name: str = "System Administrator"
    ) -> User:
        """Creates the default administrator if none exists."""
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin:
            return admin

        new_admin = User(
            email=email.lower(),
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        return new_admin
