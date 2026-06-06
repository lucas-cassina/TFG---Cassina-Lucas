# CIAS — Sistema Telemático de Gestión del Riesgo Asegurador Vehicular Personalizado

**Trabajo Final de Grado · Lucas V. Cassina · Legajo SOF02472**  
Universidad Siglo 21 — Ingeniería en Software

---

## Descripción

CIAS (*Ciudadano Asegurado*) es una plataforma web telemática que recibe datos de conducción de un dispositivo OBD-II, calcula un índice de riesgo asegurador personalizado y lo expone a los asegurados mediante un dashboard interactivo con módulo de incentivos. Los auditores de suscripción pueden consultar el índice y generar reportes en PDF.

## Historias de usuario implementadas

| ID | Historia | Estado |
|----|----------|--------|
| HU-001 | Registro de asegurado | ✅ |
| HU-002 | Login con JWT/bcrypt | ✅ |
| HU-003 | Apertura/cierre de sesión telemétrica + ingesta OBD-II | ✅ |
| HU-004 | Cálculo y visualización del índice de riesgo | ✅ |
| HU-005 | Estadísticas del mes en curso | ✅ |
| HU-006 | Historial de sesiones con filtros | ✅ |
| HU-007 | Alertas de conducción automáticas | ✅ |
| HU-008 | Módulo de incentivos Bronce/Plata/Oro | ✅ |
| HU-009 | Vistas del auditor (buscador + perfil de riesgo) | ✅ |
| HU-010 | Generación de reporte PDF | ✅ |
| HU-011/012 | Cierre de sesión con invalidación de token en servidor | ✅ |

## Stack tecnológico

**Backend:** Python 3.12 · FastAPI · SQLAlchemy · Alembic · PostgreSQL 16  
**Cálculo de riesgo:** pandas · NumPy  
**Auth:** PyJWT · passlib[bcrypt] · blocklist en servidor  
**Reportes:** ReportLab (PDF)  
**Frontend:** React 18 · JavaScript · CSS plano · React Router · axios · Recharts  
**Infraestructura:** Docker + Docker Compose  
**Tests:** Pytest (backend) · Jest + RTL (frontend)

## Requisitos

- Docker Desktop instalado y corriendo
- Git

## Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone https://github.com/<TU_USUARIO>/cias-sistema.git
cd cias-sistema

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env si deseás cambiar la contraseña de la DB o el SECRET_KEY

# 3. Levantar el stack completo
docker-compose up --build

# La aplicación quedará disponible en:
#   Frontend:  http://localhost:3000
#   Backend:   http://localhost:8000
#   API Docs:  http://localhost:8000/docs
```

## Simulador OBD-II

```bash
# Instalar dependencias del simulador
pip install httpx

# Primero registrá un conductor desde http://localhost:3000/registro
# Luego ejecutar el simulador:
cd obd-simulator
python simulator.py \
  --url http://localhost:8000 \
  --email tu@email.com \
  --password TuPassword123! \
  --perfil prudente \
  --sesiones 5
```

Perfiles disponibles: `prudente` | `medio` | `riesgoso`

## Tests del backend

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

## Estructura del proyecto

```
cias-sistema/
├── docker-compose.yml
├── .env.example
├── .artifacts/              # Artifacts del pipeline CIAS-001…005
├── backend/
│   ├── app/
│   │   ├── core/            # Config, JWT, base de datos
│   │   ├── models/          # 9 entidades SQLAlchemy
│   │   ├── schemas/         # Validación Pydantic
│   │   ├── api/routers/     # Endpoints REST
│   │   ├── services/        # risk_engine, incentivos, reportes
│   │   └── tests/           # Suite Pytest
│   └── alembic/             # Migraciones DB
├── frontend/
│   └── src/
│       ├── design-system/   # Tokens CSS
│       ├── api/             # Cliente axios
│       ├── context/         # AuthContext (JWT)
│       ├── components/      # Gauge, Badge, ProgressBar…
│       └── pages/           # Dashboard, Historial, Incentivos, Perfil, Auditor
└── obd-simulator/           # Simulador de dispositivo OBD-II
```

## Motor de cálculo del índice

5 variables ponderadas (escala 0–100):

| Variable | Peso |
|----------|------|
| Velocidad | 25 % |
| Frenadas bruscas | 25 % |
| Aceleraciones bruscas | 20 % |
| Horario de conducción | 15 % |
| Distancia recorrida | 15 % |

**Niveles:** Bajo ≤ 70 (verde) · Medio 71–85 (amarillo) · Alto > 85 (rojo)

---

*TFG Lucas V. Cassina · Universidad Siglo 21 · 2025*
