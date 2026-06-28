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

## Usuarios de muestra

Para cargar todos los usuarios de demostración con datos reales de conducción, ejecutá el script de seed **con el stack corriendo**:

```bash
pip install httpx asyncpg
python seed.py
```

El script crea los siguientes usuarios y genera sesiones de conducción distribuidas en el tiempo:

### Conductores

| Nombre | Email | Password | DNI | Perfil | Índice | Nivel incentivo |
|--------|-------|----------|-----|--------|--------|-----------------|
| María García | `maria.garcia@cias.demo` | `Demo1234!` | 30111222 | Prudente | Bajo | **Oro** |
| Carlos López | `carlos.lopez@cias.demo` | `Demo1234!` | 27333444 | Medio | Medio | **Bronce** |
| Pablo Rodríguez | `pablo.rodriguez@cias.demo` | `Demo1234!` | 33555666 | Riesgoso | Alto | **Sin nivel** |

### Auditor

| Nombre | Email | Password | Legajo |
|--------|-------|----------|--------|
| Ana Torres | `ana.torres@cias.demo` | `Demo1234!` | AUD-001 |

> **Para buscar desde el panel auditor:** usar el DNI de cualquier conductor (ej. `30111222`).

---

## Stack tecnológico

**Backend:** Python 3.12 · FastAPI · SQLAlchemy · Alembic · PostgreSQL 16  
**Cálculo de riesgo:** Motor propio puro Python (risk_engine)  
**Auth:** PyJWT · hashlib PBKDF2 · blocklist en servidor  
**Reportes:** ReportLab (PDF)  
**Frontend:** React 18 · JavaScript · CSS plano · React Router · axios · Recharts  
**Infraestructura:** Docker + Docker Compose  
**Tests:** Pytest (backend)

## Requisitos

- Docker Desktop instalado y corriendo
- Git

## Instalación y ejecución

```bash
# 1. Clonar el repositorio
git clone https://github.com/lucas-cassina/TFG---Cassina-Lucas.git
cd TFG---Cassina-Lucas

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

`obd_sim.py` replica el comportamiento exacto de un dongle OBD-II conectado al vehículo. Usa los mismos endpoints REST que usaría el hardware real:

1. `POST /auth/login` — autenticación del conductor
2. `POST /telemetria/sesion/abrir` — se dispara al detectar encendido del motor
3. `POST /telemetria/eventos` — lotes de telemetría cada 5 segundos (frecuencia real: 1 Hz)
4. `POST /telemetria/sesion/cerrar` — se dispara al apagar el motor (o `Ctrl+C`)

### Instalación

```bash
pip install httpx
```

### Uso rápido (usuarios del seed)

```bash
# Perfil medio — Carlos López (índice Medio)
python obd_sim.py

# Perfil prudente — María García (índice Bajo)
python obd_sim.py --perfil prudente

# Perfil riesgoso — Pablo Rodríguez (índice Alto, genera alertas visibles)
python obd_sim.py --perfil riesgoso
```

### Uso con usuario propio

```bash
python obd_sim.py --email tu@email.com --password TuClave1! --perfil medio
```

### Parámetros disponibles

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `--perfil` | `medio` | `prudente` · `medio` · `riesgoso` |
| `--duracion` | `2` | Minutos de conducción a simular |
| `--email` | _(usuario del perfil)_ | Email del conductor |
| `--password` | _(contraseña del perfil)_ | Contraseña del conductor |
| `--api` | `http://localhost:8000` | URL del backend |

### Salida en tiempo real

Mientras corre, el simulador muestra la telemetría en vivo con alertas coloreadas:

```
OBD-II   87.4 km/h  lote #03  138ms  [████████████░░░░░░░░░░░░░░░░░░] 42%
```

Al finalizar imprime el resumen completo con índice de riesgo, distancia estimada y detalle de alertas generadas.

### Perfiles de conducción

| Perfil | Velocidad | Eventos bruscos | Índice esperado |
|--------|-----------|-----------------|-----------------|
| `prudente` | ≤ 95 km/h | Muy raros | Bajo (≤ 70) |
| `medio` | hasta 130 km/h | Ocasionales | Medio (71–85) |
| `riesgoso` | hasta 160 km/h | Frecuentes | Alto (> 85) |

> **Tip para la demo:** abrí en pantalla dividida el terminal con el simulador corriendo y el navegador con la vista del auditor. Cuando el script termine, el auditor busca al conductor por DNI y ve el perfil de riesgo actualizado.

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
└── obd_sim.py               # Simulador de dispositivo OBD-II
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
