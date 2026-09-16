import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.db.mysql import Base, get_db
from app.main import app
from app.core.auth import hash_password
from app.models.user import User, UserRole, UserStatus

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test.db")

# Use file-based SQLite with check_same_thread=False
engine = create_engine(
    f"sqlite:///{TEST_DB_PATH}",
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Enable WAL mode and foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=OFF")
    cursor.close()


@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            pass
    # also clean WAL and SHM files
    for ext in ["-wal", "-shm"]:
        p = TEST_DB_PATH + ext
        if os.path.exists(p):
            try:
                os.remove(p)
            except PermissionError:
                pass


@pytest.fixture
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin(db):
    user = User(
        username="admin",
        password_hash=hash_password("admin123"),
        display_name="Admin",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def normal_user(db):
    user = User(
        username="testuser",
        password_hash=hash_password("test123"),
        display_name="Test User",
        role=UserRole.USER,
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(client, admin):
    resp = client.post("/api/v1/auth/login", json={
        "username": "admin", "password": "admin123"
    })
    assert resp.status_code == 200
    return resp.json()["token"]


@pytest.fixture
def user_token(client, normal_user):
    resp = client.post("/api/v1/auth/login", json={
        "username": "testuser", "password": "test123"
    })
    assert resp.status_code == 200
    return resp.json()["token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def uploads_dir():
    os.makedirs("uploads", exist_ok=True)
    yield "uploads"
