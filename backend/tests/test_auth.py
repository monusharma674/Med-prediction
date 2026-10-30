import os
os.environ["APP_ENV"] = "testing"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.session import Base, get_db
from app.models.user import User, UserRole
from contextlib import asynccontextmanager

@asynccontextmanager
async def noop_lifespan(app_instance):
    yield

app.router.lifespan_context = noop_lifespan

# Isolated in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app, raise_server_exceptions=True)
    yield test_client
    app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_patient_registration(client):
    payload = {
        "email": "testpatient@example.com",
        "password": "Password123!",
        "full_name": "John Doe",
        "date_of_birth": "1990-05-15",
        "gender": "Male",
        "phone": "+1234567890",
        "blood_group": "O+",
    }
    response = client.post("/api/v1/auth/register/patient", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "patient"
    assert data["email"] == "testpatient@example.com"


def test_duplicate_email_registration_fails(client):
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "full_name": "First User",
    }
    res1 = client.post("/api/v1/auth/register/patient", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register/patient", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


def test_doctor_registration(client):
    payload = {
        "email": "doctor@hospital.org",
        "password": "DocSecurePassword123!",
        "full_name": "Dr. Sarah Smith",
        "specialization": "Cardiologist",
        "license_number": "MED-123456",
        "hospital": "City Memorial Hospital",
    }
    response = client.post("/api/v1/auth/register/doctor", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "doctor"


def test_login_success_and_failure(client):
    # Register patient
    client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "loginuser@example.com",
            "password": "MySecretPassword123!",
            "full_name": "Login User",
        },
    )

    # Valid login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "loginuser@example.com", "password": "MySecretPassword123!"},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Invalid password
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": "loginuser@example.com", "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401


def test_auth_me_endpoint(client):
    reg = client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "me_user@example.com",
            "password": "Password123!",
            "full_name": "Alice Wonderland",
            "blood_group": "A+",
        },
    )
    token = reg.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["email"] == "me_user@example.com"
    assert data["role"] == "patient"
    assert data["patient_profile"]["full_name"] == "Alice Wonderland"


def test_role_based_access_control(client):
    # Register a patient
    reg = client.post(
        "/api/v1/auth/register/patient",
        json={
            "email": "patient_only@example.com",
            "password": "Password123!",
            "full_name": "Patient Role Test",
        },
    )
    patient_token = reg.json()["access_token"]

    headers = {"Authorization": f"Bearer {patient_token}"}
    # Patient should successfully access patient profile
    patient_res = client.get("/api/v1/users/profile/patient", headers=headers)
    assert patient_res.status_code == 200

    # Patient attempting to access doctor profile route should be forbidden (403)
    doctor_res = client.get("/api/v1/users/profile/doctor", headers=headers)
    assert doctor_res.status_code == 403
