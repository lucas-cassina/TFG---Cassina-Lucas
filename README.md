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
| HU-002 | Login con JWT/PBKDF2-SHA256 | ✅ |
| HU-003 | Apertura/cierre de sesión telemétrica + ingesta OBD-II | ✅ |
| HU-004 | Cálculo y visualización del índice de riesgo | ✅ |
| HU-005 | Historial de evolución con filtros y estadísticas del mes | ✅ |
| HU-006 | Desglose de las cinco variables del índice | ✅ |
| HU-007 | Alertas de conducción automáticas | ✅ |
| HU-008 | Módulo de incentivos Bronce/Plata/Oro | ✅ |
| HU-009 | Vistas del auditor (buscador + perfil de riesgo) | ✅ |
| HU-010 | Generación de reporte PDF | ✅ |
| HU-011/012 | Cierre de sesión con invalidación de token en servidor | ✅ |

## Usuarios de muestra

Para cargar todos los usuarios de demostración con datos sintéticos de prueba, ejecutá el script de seed **con el stack corriendo**:

```bash
docker compose exec -T backend python seed.py
```

El script crea los siguientes usuarios y genera sesiones de conducción distribuidas en el tiempo:

### Conductores

| Nombre | Email | Password | DNI | Perfil | Índice | Nivel incentivo |
|--------|-------|----------|-----|--------|--------|-----------------|
| María García | `maria.garcia@cias.demo` | `Demo1234!` | 30111222 | Prudente | Bajo (15) | **Oro** |
| Carlos López | `carlos.lopez@cias.demo` | `Demo1234!` | 27333444 | Medio | Medio (84) | **Sin nivel** |
| Pablo Rodríguez | `pablo.rodriguez@cias.demo` | `Demo1234!` | 33555666 | Riesgoso | Alto (100) | **Sin nivel** |

### Auditor

| Nombre | Email | Password | Legajo |
|--------|-------|----------|--------|
| Ana Torres | `ana.torres@cias.demo` | `Demo1234!` | AUD-001 |

> **Para buscar desde el panel auditor:** usar el DNI de cualquier conductor (ej. `30111222`).

---

## Stack tecnológico

**Backend:** Python 3.12 · FastAPI · SQLAlchemy · PostgreSQL 16  
**Cálculo de riesgo:** Motor propio con pandas/NumPy (risk_engine)  
**Auth:** PyJWT · hashlib PBKDF2 · blocklist en servidor  
**Reportes:** ReportLab (PDF)  
**Frontend:** React 18 · JavaScript · CSS plano · React Router · axios · Recharts  
**Infraestructura:** Docker + Docker Compose  
**Tests:** Pytest (backend) · Jest/Testing Library (frontend)

## Requisitos

- Docker Desktop instalado y corriendo
- Git

## Instalación y ejecución

```bash
# 1. Descomprimí el paquete CIAS Demo v22 y abrí una terminal en su carpeta.
# El repositorio público es una referencia; el paquete adjunto contiene esta revisión.

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env si deseás cambiar la contraseña de la DB o el SECRET_KEY

# 3. Levantar el stack completo
docker compose up -d --build

# La aplicación quedará disponible en:
#   Frontend:  http://localhost:3000
#   Backend:   http://localhost:8000
#   API Docs:  http://localhost:8000/docs
```

## Simulador OBD-II

`obd_sim.py` genera telemetría sintética por los endpoints REST del prototipo. La conexión y validación con hardware OBD-II real son trabajo futuro.

1. `POST /auth/login` — autenticación del conductor
2. `POST /telemetria/sesion/abrir` — se dispara al detectar encendido del motor
3. `POST /telemetria/eventos` — lotes de telemetría cada 5 segundos (frecuencia real: 1 Hz)
4. `POST /telemetria/sesion/cerrar` — se dispara al apagar el motor (o `Ctrl+C`)

### Instalación

```bash
docker compose exec -T backend python seed.py
```

### Uso rápido (usuarios del seed)

```bash
# Perfil medio — Carlos López (patrón de eventos medio)
docker compose exec -T backend python obd_sim.py

# Perfil prudente — María García (patrón prudente)
docker compose exec -T backend python obd_sim.py --perfil prudente

# Perfil riesgoso — Pablo Rodríguez (patrón riesgoso, genera alertas visibles)
docker compose exec -T backend python obd_sim.py --perfil riesgoso
```

### Uso con usuario propio

```bash
docker compose exec -T backend python obd_sim.py --email tu@email.com --password TuClave1! --perfil medio
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

| Perfil | Velocidad | Eventos bruscos | Clasificación |
|--------|-----------|-----------------|-----------------|
| `prudente` | ≤ 95 km/h | Muy raros | Depende de las proporciones y duración |
| `medio` | hasta 130 km/h | Ocasionales | Depende de las proporciones y duración |
| `riesgoso` | hasta 160 km/h | Frecuentes | Depende de las proporciones y duración |

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
├── seed.py                  # Escenarios sintéticos deterministas
├── backend/
│   ├── app/
│   │   ├── core/            # Config, JWT, base de datos
│   │   ├── models/          # 9 entidades SQLAlchemy
│   │   ├── schemas/         # Validación Pydantic
│   │   ├── api/routers/     # Endpoints REST
│   │   ├── services/        # risk_engine, incentivos, reportes
│   │   └── tests/           # Suite Pytest
│   └── alembic/             # Configuración parcial; el esquema inicial se crea al arrancar
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

**Niveles:** Bajo ≤ 70 (verde) · Medio 70 < I ≤ 85 (amarillo) · Alto > 85 (rojo)

---

*TFG Lucas V. Cassina · Universidad Siglo 21 · 2026*

La API usa UTC para almacenar tiempos; las estadísticas mensuales toman el calendario de Argentina. El motor evalúa la hora del timestamp recibido sin convertirla a hora local. Los incentivos son ilustrativos: no modifican primas ni otorgan beneficios comerciales reales. El seed está destinado exclusivamente a una base de demostración y reconstruye sus propios escenarios.
