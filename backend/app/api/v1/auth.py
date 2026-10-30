from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserRegisterPatient,
    UserRegisterDoctor,
    UserLogin,
    Token,
    UserResponse,
)
from app.services.authentication.auth_service import AuthService
from app.core.dependencies import get_current_user, log_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register/patient", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_patient(
    payload: UserRegisterPatient,
    request: Request,
    db: Session = Depends(get_db),
):
    """Register a new patient account with associated clinical profile."""
    new_user = AuthService.register_patient(db, payload)
    log_audit_event(
        db=db,
        action="REGISTER_PATIENT",
        resource_type="user",
        resource_id=str(new_user.id),
        user_id=new_user.id,
        request=request,
        details={"email": new_user.email},
    )
    return AuthService.authenticate_user(db, payload.email, payload.password)


@router.post("/register/doctor", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_doctor(
    payload: UserRegisterDoctor,
    request: Request,
    db: Session = Depends(get_db),
):
    """Register a new medical practitioner account with license details."""
    new_user = AuthService.register_doctor(db, payload)
    log_audit_event(
        db=db,
        action="REGISTER_DOCTOR",
        resource_type="user",
        resource_id=str(new_user.id),
        user_id=new_user.id,
        request=request,
        details={"email": new_user.email, "license": payload.license_number},
    )
    return AuthService.authenticate_user(db, payload.email, payload.password)


@router.post("/login", response_model=Token)
def login(
    payload: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    """Authenticate with email and password to receive a signed JWT access token."""
    token = AuthService.authenticate_user(db, payload.email, payload.password)
    log_audit_event(
        db=db,
        action="LOGIN_SUCCESS",
        resource_type="user",
        resource_id=str(token.user_id),
        user_id=token.user_id,
        request=request,
    )
    return token


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Retrieve identity, role, and profile summary for the currently authenticated user."""
    return current_user
