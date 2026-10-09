import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.enums import UserRole, Priority
from app.models.user import User
from app.models.category import Category
from app.models.sla import SLAConfig

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Provides a clean in-memory database for each test function."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Seed baseline users
    u_it = User(username="it.tech", email="it.tech@company.com", full_name="IT Tech", role=UserRole.IT_SUPPORT, department="IT", is_active=True)
    u_mgr = User(username="it.mgr", email="it.mgr@company.com", full_name="IT Manager", role=UserRole.IT_MANAGER, department="IT", is_active=True)
    u_emp = User(username="jane.emp", email="jane@company.com", full_name="Jane Employee", role=UserRole.EMPLOYEE, department="Sales", is_active=True)
    u_inactive = User(username="old.staff", email="old@company.com", full_name="Old Staff", role=UserRole.IT_SUPPORT, department="IT", is_active=False)

    db.add_all([u_it, u_mgr, u_emp, u_inactive])

    # Seed baseline categories
    cat1 = Category(name="Hardware", description="Hardware issues", is_active=True)
    cat2 = Category(name="Software", description="Software issues", is_active=True)
    cat_inactive = Category(name="Deprecated", description="Inactive category", is_active=False)
    db.add_all([cat1, cat2, cat_inactive])

    # Seed baseline SLA configs
    sla_configs = [
        SLAConfig(priority=Priority.CRITICAL, resolution_sla_hours=4.0, response_sla_hours=0.5, is_active=True),
        SLAConfig(priority=Priority.HIGH, resolution_sla_hours=8.0, response_sla_hours=1.0, is_active=True),
        SLAConfig(priority=Priority.MEDIUM, resolution_sla_hours=24.0, response_sla_hours=2.0, is_active=True),
        SLAConfig(priority=Priority.LOW, resolution_sla_hours=48.0, response_sla_hours=4.0, is_active=True),
    ]
    db.add_all(sla_configs)
    db.commit()

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Provides a FastAPI test client using the isolated test database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
