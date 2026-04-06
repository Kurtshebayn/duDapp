def test_login_exitoso(client, admin_user):
    response = client.post("/auth/login", json={
        "email": "admin@dudo.com",
        "password": "admin123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_password_incorrecto(client, admin_user):
    response = client.post("/auth/login", json={
        "email": "admin@dudo.com",
        "password": "equivocado",
    })
    assert response.status_code == 401


def test_login_usuario_inexistente(client):
    response = client.post("/auth/login", json={
        "email": "noexiste@dudo.com",
        "password": "admin123",
    })
    assert response.status_code == 401


def test_endpoint_protegido_sin_token(client, admin_user):
    from app.auth.dependencies import get_current_user
    from app.main import app

    # Add a quick protected route to test the dependency
    from fastapi import Depends
    from app.models.usuario import Usuario

    @app.get("/test-protected")
    def protected(user: Usuario = Depends(get_current_user)):
        return {"id": user.id}

    response = client.get("/test-protected")
    assert response.status_code == 401


def test_endpoint_protegido_con_token_valido(client, admin_user):
    login_response = client.post("/auth/login", json={
        "email": "admin@dudo.com",
        "password": "admin123",
    })
    token = login_response.json()["access_token"]

    from app.auth.dependencies import get_current_user
    from app.main import app
    from fastapi import Depends
    from app.models.usuario import Usuario

    @app.get("/test-protected-2")
    def protected2(user: Usuario = Depends(get_current_user)):
        return {"id": user.id}

    response = client.get("/test-protected-2", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == admin_user.id
