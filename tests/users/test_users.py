import pytest
from datetime import datetime
from app.database.connect_db import Base, engine, SessionLocal
from app.database.models import User, UserRoleEnum
from app.repository import users as repository_users
from app.schemas import UserModel

# -------------------- DB Setup --------------------
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# -------------------- Fixtures --------------------
@pytest.fixture()
def session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def new_user(session):
    email = "artur4ik@example.com"
    user = session.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            username="artur4ik",
            password="password123",
            avatar="url-avatar",
            role="admin",
            is_active=True,
            is_verify=True,
            created_at=datetime.utcnow()
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    return user

@pytest.fixture()
def second_user(session):
    email = "second_user@example.com"
    user = session.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            username="second_user",
            password="qweqwe123123",
            role="user",
            created_at=datetime.utcnow()
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    return user

# -------------------- Repository Tests --------------------
def test_get_me_repo(new_user, session):
    user = repository_users.get_me(new_user, session)
    assert user.username == "artur4ik"
    assert user.email == "artur4ik@example.com"

def test_get_users_repo(new_user, second_user, session):
    users = repository_users.get_users(0, 100, session)
    assert isinstance(users, list)
    assert len(users) >= 2

def test_get_users_with_username_repo(new_user, session):
    users = repository_users.get_users_with_username("artur", session)
    assert isinstance(users, list)
    assert users[0].username == "artur4ik"

def test_get_user_profile_repo(new_user, session):
    user = repository_users.get_user_profile("artur4ik", session)
    assert user.username == "artur4ik"
    assert user.email == "artur4ik@example.com"
