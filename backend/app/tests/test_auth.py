import pytest

CONDUCTOR_DATA = {
    "nombre": "Lucas",
    "apellido": "Cassina",
    "dni": "30123456",
    "email": "lucas.test@cias.com",
    "password": "Password123!",
    "telefono": "351-123456",
}


async def _registrar(client, overrides=None):
    """Helper: registra un conductor y devuelve la respuesta."""
    data = {**CONDUCTOR_DATA, **(overrides or {})}
    return await client.post("/auth/registro/conductor", json=data)


@pytest.mark.asyncio
async def test_registro_conductor(client):
    """HU-001: Registro exitoso de conductor."""
    resp = await _registrar(client)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "conductor"
    assert data["nombre"] == "Lucas"


@pytest.mark.asyncio
async def test_registro_duplicado(client):
    """HU-001: Registro con email duplicado devuelve 409."""
    await _registrar(client)
    resp = await _registrar(client)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_exitoso(client):
    """HU-002: Login con credenciales válidas."""
    await _registrar(client)
    resp = await client.post("/auth/login", json={
        "email": CONDUCTOR_DATA["email"],
        "password": CONDUCTOR_DATA["password"],
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_credenciales_invalidas(client):
    """HU-002: Login con contraseña incorrecta devuelve 401."""
    await _registrar(client)
    resp = await client.post("/auth/login", json={
        "email": CONDUCTOR_DATA["email"], "password": "wrong",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_bloqueo_cuenta_5_intentos(client):
    """HU-002 (tesis pág. 43): 5 intentos fallidos bloquean la cuenta por 30 min (HTTP 423)."""
    await _registrar(client, {"email": "lockout.test@cias.com", "dni": "30111222"})
    login_url = "/auth/login"
    bad_creds = {"email": "lockout.test@cias.com", "password": "WrongPassword99!"}

    for _ in range(5):
        resp = await client.post(login_url, json=bad_creds)
        assert resp.status_code == 401

    resp = await client.post(login_url, json=bad_creds)
    assert resp.status_code == 423


@pytest.mark.asyncio
async def test_logout_invalida_token(client):
    """HU-011/012: Logout revoca el token; acceso posterior devuelve 401."""
    reg = await _registrar(client, {"email": "logout.test@cias.com", "dni": "30999888"})
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/auth/logout", headers=headers)
    assert resp.status_code == 204

    resp2 = await client.get("/indice/actual", headers=headers)
    assert resp2.status_code == 401


@pytest.mark.asyncio
async def test_password_debil_rechazada(client):
    """A1: contraseña sin mayúscula, número o muy corta es rechazada con 422."""
    for pwd in ["short", "sinmayuscula1!", "SINMINUSCULA1!", "SinNumeroAqui!"]:
        resp = await _registrar(client, {
            "email": f"weak{pwd[:4]}@cias.com", "dni": f"3099{len(pwd)}999", "password": pwd
        })
        assert resp.status_code == 422, f"Se esperaba 422 para contraseña '{pwd}'"


@pytest.mark.asyncio
async def test_cambio_contrasena_no_reutilizacion(client):
    """HU-002 (pág. 43): las últimas 3 contraseñas no pueden reutilizarse."""
    reg = await _registrar(client, {"email": "reuse.test@cias.com", "dni": "31000001"})
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    pwd_original = CONDUCTOR_DATA["password"]
    pwd_2 = "Segunda456!"
    pwd_3 = "Tercera789!"

    # Cambiar a segunda contraseña
    resp = await client.put("/conductor/cambiar-contrasena", headers=headers, json={
        "contrasena_actual": pwd_original,
        "contrasena_nueva": pwd_2,
    })
    assert resp.status_code == 204

    # Intentar reutilizar la original → debe fallar (está en historial)
    resp = await client.put("/conductor/cambiar-contrasena", headers=headers, json={
        "contrasena_actual": pwd_2,
        "contrasena_nueva": pwd_original,
    })
    assert resp.status_code == 400

    # Cambiar a tercera contraseña
    resp = await client.put("/conductor/cambiar-contrasena", headers=headers, json={
        "contrasena_actual": pwd_2,
        "contrasena_nueva": pwd_3,
    })
    assert resp.status_code == 204

    # Intentar reutilizar la segunda → debe fallar (está en historial)
    resp = await client.put("/conductor/cambiar-contrasena", headers=headers, json={
        "contrasena_actual": pwd_3,
        "contrasena_nueva": pwd_2,
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_cambio_contrasena_contrasena_actual_incorrecta(client):
    """Cambio de contraseña falla si la contraseña actual es incorrecta."""
    reg = await _registrar(client, {"email": "wrong.pwd@cias.com", "dni": "31000002"})
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.put("/conductor/cambiar-contrasena", headers=headers, json={
        "contrasena_actual": "ContraseñaErronea1!",
        "contrasena_nueva": "NuevaValida456!",
    })
    assert resp.status_code == 400
