# Plan de implementación — entrenanutricion

Desglose de tareas por fase a partir de los requisitos del proyecto («la especificación»).
Cada fase se desarrolla en la rama `phase/N-name` (nombre en inglés), termina con lint + tests en verde, `docs/PROGRESS.md`
actualizado y un *merge* a `main`.

## Fase 0 — Preparación

- [x] Leer la especificación completa y fijar las decisiones iniciales (`docs/DECISIONS.md`).
- [x] `docs/PLAN.md`, `docs/PROGRESS.md`, `docs/TRACEABILITY.md` (esqueleto con las 25 US).
- [x] Esqueleto del monorepo: `backend/` (Django 5.2 + DRF, settings `base/dev/test/prod`, apps vacías),
      `frontend/` (Ionic 8 + React 18 + TS + Vite «hola mundo»).
- [x] Endpoint de salud `GET /api/v1/health` y test.
- [x] Linters y formateadores: `ruff` + `black` (backend), ESLint + Prettier (frontend).
- [x] Vitest configurado con un test mínimo.
- [x] `docker-compose.yml` (db + backend + frontend), `Makefile`, `.env.example`.
- [x] CI de GitHub Actions (`.github/workflows/ci.yml`): lint, tests backend con Postgres, tests frontend, build.

## Fase 1 — Núcleo backend: cuentas

- [ ] App `core`: `TimeStampedModel`, paginación `limit/offset`, *handler* de errores uniforme
      (`{code, message, fields}`), excepciones de dominio, clases de permiso, validadores de ficheros
      (MIME real), renombrado UUID, borrado de ficheros huérfanos (señales), storage conmutables (local/GCS).
- [ ] App `accounts`: `User` (email como identificador, roles, estados, borrado lógico), `UserDetails`,
      `DietPreferences`, `HealthInfo` con validación de listas contra enums.
- [ ] Validador de contraseña (8+, mayúscula, minúscula, número, símbolo), Argon2.
- [ ] Auth: `register`, `login` (remember_me → refresh 7 días / 12 h), `refresh` (rotación), `logout`
      (blacklist), `email-exists`. *Throttling* por *scope*.
- [ ] `/me`, `PATCH /me/profile`, `PUT /me/password`, `PUT /me/photo`, `POST/GET/PUT /me/onboarding`.
- [ ] `progress.WeightRecord` mínimo (lo necesita el onboarding y el perfil).
- [ ] OpenAPI en `/api/docs/` (drf-spectacular).
- [ ] Tests: auth, perfil, onboarding, permisos; cobertura `accounts` ≥ 90 %.

## Fase 2 — Backend de entrenamiento

- [ ] Modelos: `MuscleGroup` (migración de datos), `Exercise`, `ExerciseStep`, `ExerciseMedia`, `Workout`,
      `WorkoutExercise`, `TrainingPlan`, `TrainingPlanWorkout`, `UserTrainingPlan`, `UserPlanWorkout`,
      `ExerciseCompletion`, `WorkoutSession`, `ExerciseLog`.
- [ ] CRUD de staff con anidados (pasos, ejercicios del entrenamiento, entrenamientos del plan) y media.
- [ ] Política de borrado.
- [ ] Servicios: asignación de plan (secuencia con bloqueo), marcar ejercicio, completar entrenamiento
      (transacción atómica, logs, sesión, progreso, cierre de ciclo), duración estimada, calendario por defecto.
- [ ] Endpoints `/me/training-plan*`, `/me/exercises/{id}`, `/users/{id}/assign-training-plan`.
- [ ] Tests de las reglas de negocio: secuencia, progreso, calendario, duración, reasignación y borrado.

## Fase 3 — Backend de nutrición, progreso, asignaciones y estadísticas

- [ ] `MealPlan` (validación macros ±10 %, reparto 100 %), `UserNutritionPlan`, `/me/nutrition-plan` con cálculos.
- [ ] `recompute_user_status`, `/assignments/pending` por rol, `assign-nutrition-plan`, reasignación 409/`replace`.
- [ ] Usuarios: `/users` (lista alfabética, búsqueda, filtro de rol, solo lectura para staff; CRUD admin).
- [ ] Progreso: dashboard (calendario, próximo entrenamiento, %), historial con filtros, pesos, motivación.
- [ ] Estadísticas: popularidad, crecimiento, resumen, años.
- [ ] `seed_demo` idempotente (usuarios, ejercicios con *placeholders* Pillow, entrenamientos, planes).
- [ ] Matriz de permisos parametrizada completa; cobertura global ≥ 90 %; test anti N+1.

## Fase 4 — Base del frontend

- [ ] Tema y paleta (`theme/variables.css`, modo oscuro), layout centrado ≤ 1100 px.
- [ ] i18n (es/en/ca con *lazy loading*), `useLanguage`, selector con banderas, `Accept-Language`, test de paridad.
- [ ] Cliente axios con conversión snake↔camel, interceptor JWT con refresco único y cierre de sesión.
- [ ] `AuthContext`, almacenamiento del refresh según «Recordar sesión», *guards* por rol/estado.
- [ ] Layouts y barras de pestañas por rol (solo una activa), componentes comunes
      (PageLayout, ConfirmDialog, EmptyState, ErrorState, ListSkeleton, MacroDonut, RestTimer, LanguageMenu…).
- [ ] Bienvenida + login + logout funcionales contra el backend.

## Fase 5 — Frontend de cliente

- [ ] Registro (validaciones en vivo, email-exists), onboarding de 6 pasos, estado del plan (*pull-to-refresh*).
- [ ] Plan semanal, entrenamiento del día, detalle de ejercicio (carrusel, modal, cronómetro, marcar hecho).
- [ ] Macronutrientes, Progreso (Control / Workout / Weight), Perfil, Editar perfil, cambio de contraseña.
- [ ] Playwright configurado; E2E 1, 3 y 4.

## Fase 6 — Frontend de gestión

- [ ] Entrenamientos (Workouts / Exercises / Plans): listas, formularios, detalle.
- [ ] Nutrición por categoría: lista, formulario con kcal en vivo, detalle con dónut.
- [ ] Usuarios: lista, detalle, crear/modificar/eliminar (solo admin).
- [ ] Asignaciones: pendientes por rol, ficha, selector de plan, «Crear plan nuevo», reemplazo con confirmación.
- [ ] Estadísticas: KPIs, gráficos y selector de año.
- [ ] E2E 2, 5 y 6 (y 7: idioma en vivo).

## Fase 7 — Calidad y pulido

- [ ] Tests de regresión de los 11 errores conocidos.
- [ ] Accesibilidad, estados vacíos/carga/error, responsive escritorio (tablas en gestión), PWA.
- [ ] Revisión N+1 y de seguridad. Checklist de la *Definition of Done*.

## Fase 8 — Despliegue y documentación

- [ ] Dockerfile multi-stage de producción (gunicorn + whitenoise), Dockerfile del frontend (nginx),
      `docker-compose.prod.yml`, `render.yaml`.
- [ ] README completo (instalación, arranque, credenciales demo, despliegue Render + GCS).
- [ ] `docs/API.md`, `docs/ARCHITECTURE.md` (Mermaid: arquitectura, ER, navegación).

## Fase 9 — (Opcional) Líneas futuras

Solo si todo lo anterior está terminado.
