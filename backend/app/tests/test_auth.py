import pytest


CONDUCTOR_DATA = {
    "nombre": "Lucas",
    "apellido": "Cassina",
    "dni": "30123456",
    "email": "lucas.test@cias.com",
    "password": "Password123!",
    "telefono": "351-123456",
}


@pytest.mark.asyncio
async def test_registro_conductor(client):
    """HU-001: Registro exitoso de conductor."""
    resp = await client.post("/auth/registro/conductor", json=CONDUCTOR_DATA)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "conductor"
    assert data["nombre"] == "Lucas"


@pytest.mark.asyncio
async def test_registro_duplicado(client):
    """HU-001: Registro con email duplicado devuelve 409."""
    await client.post("/auth/registro/conductor", json=CONDUCTOR_DATA)
    resp = await client.post("/auth/registro/conductor", json=CONDUCTOR_DATA)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_exitoso(client):
    """HU-002: Login con credenciales válidas."""
    resp = await client.post("/auth/login", json={
        "email": CONDUCTOR_DATA["email"],
        "password": CONDUCTOR_DATA["password"]
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_credenciales_invalidas(client):
    """HU-002: Login con contraseña incorrecta devuelve 401."""
    resp = await client.post("/auth/login", json={
        "email": CONDUCTOR_DATA["email"], "password": "wrong"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_invalida_token(client):
    """HU-011/012: Logout revoca el token; acceso posterior devuelve 401."""
    # Registrar y obtener token
    reg = await client.post("/auth/registro/conductor", json={
        **CONDUCTOR_DATA, "email": "logout.test@cias.com", "dni": "30999888"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Logout
    resp = await client.post("/auth/logout", headers=headers)
    assert resp.status_code == 204

    # Verificar que el token fue revocado
    resp2 = await client.get("/indice/actual", headers=headers)
    assert resp2.status_code == 401
