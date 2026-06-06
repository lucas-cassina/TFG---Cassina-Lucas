#!/usr/bin/env python3
"""
Simulador OBD-II para CIAS (CIAS-002).

Uso:
    python simulator.py --url http://localhost:8000 --email conductor@cias.com \
                        --password Password123! --perfil prudente --sesiones 3

Perfiles disponibles: prudente | medio | riesgoso
"""

import argparse
import time
import httpx
from perfiles import PERFILES


def run(base_url: str, email: str, password: str, perfil: str, n_sesiones: int):
    print(f"[CIAS Simulador] Conectando a {base_url} como {email} (perfil: {perfil})")

    # Login
    resp = httpx.post(f"{base_url}/auth/login", json={"email": email, "password": password})
    resp.raise_for_status()
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"[+] Login OK. Token obtenido.")

    generar_eventos = PERFILES[perfil]

    for i in range(1, n_sesiones + 1):
        print(f"\n--- Sesión {i}/{n_sesiones} ---")

        # Abrir sesión
        resp = httpx.post(f"{base_url}/telemetria/sesion/abrir", json={}, headers=headers)
        resp.raise_for_status()
        sesion_id = resp.json()["sesion_id"]
        print(f"[+] Sesión abierta: ID {sesion_id}")

        # Enviar eventos en lote
        eventos = generar_eventos(n_eventos=30)
        payload = {"sesion_id": sesion_id, "eventos": eventos}
        resp = httpx.post(f"{base_url}/telemetria/eventos", json=payload, headers=headers)
        resp.raise_for_status()
        result = resp.json()
        print(f"[+] {result['eventos_procesados']} eventos enviados, {result['alertas_generadas']} alertas")

        # Cerrar sesión (dispara cálculo del índice)
        resp = httpx.post(f"{base_url}/telemetria/sesion/cerrar",
                          json={"sesion_id": sesion_id}, headers=headers)
        resp.raise_for_status()
        idx = resp.json()
        print(f"[+] Sesión cerrada. Índice: {idx['indice']} ({idx['nivel']}) | {idx['distancia_km']:.1f} km")

        time.sleep(0.5)

    print(f"\n[✓] Simulación completada: {n_sesiones} sesiones procesadas.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulador OBD-II CIAS")
    parser.add_argument("--url", default="http://localhost:8000", help="URL base del backend")
    parser.add_argument("--email", required=True, help="Email del conductor")
    parser.add_argument("--password", required=True, help="Contraseña del conductor")
    parser.add_argument("--perfil", choices=["prudente", "medio", "riesgoso"], default="medio")
    parser.add_argument("--sesiones", type=int, default=3, help="Número de sesiones a simular")
    args = parser.parse_args()

    run(args.url, args.email, args.password, args.perfil, args.sesiones)
