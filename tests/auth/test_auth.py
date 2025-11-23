from app.database.models import User
from app.conf.messages import ALREADY_EXISTS, EMAIL_NOT_CONFIRMED, INVALID_PASSWORD, INVALID_EMAIL, USER_NOT_ACTIVE

def test_signup_user(client, create_user):
    user_data = {"username": "newuser", "email": "newuser@example.com", "password": "password123"}
    response = client.post("/api/auth/signup", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "newuser@example.com"
    assert "id" in data["user"]

def test_signup_user_already_exists(client, create_user):
    user_data = {"username": create_user.username, "email": create_user.email, "password": "password123"}
    response = client.post("/api/auth/signup", json=user_data)
    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == ALREADY_EXISTS

def test_login_not_confirmed(client, create_user, session):
    create_user.is_verify = False
    session.commit()
    response = client.post("/api/auth/login", data={"username": create_user.email, "password": "testpassword"})
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == EMAIL_NOT_CONFIRMED

def test_login_user(client, create_user, session):
    create_user.is_verify = True
    create_user.is_active = True
    session.commit()
    response = client.post("/api/auth/login", data={"username": create_user.email, "password": "testpassword"})
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, create_user, session):
    create_user.is_verify = True
    create_user.is_active = True
    session.commit()
    response = client.post("/api/auth/login", data={"username": create_user.email, "password": "wrongpass"})
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == INVALID_PASSWORD

def test_login_user_not_active(client, create_user, session):
    create_user.is_verify = True
    create_user.is_active = False
    session.commit()
    response = client.post("/api/auth/login", data={"username": create_user.email, "password": "testpassword"})
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == USER_NOT_ACTIVE
