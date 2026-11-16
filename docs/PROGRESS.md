# Progreso

## Estado por fase

| Fase | Estado | Rama |
|---|---|---|
| 0. Preparación | ✅ Completada | `phase/0-setup` |
| 1. Núcleo backend: cuentas | ✅ Completada | `phase/1-accounts` |
| 2. Backend de entrenamiento | ✅ Completada | `phase/2-training` |
| 3. Backend de nutrición, progreso, asignaciones y estadísticas | ✅ Completada | `phase/3-nutrition-progress-statistics` |
| 4. Base del frontend | ✅ Completada | `phase/4-frontend-base` |
| 5. Frontend de cliente | ✅ Completada | `phase/5-client-frontend` |
| 6. Frontend de gestión | ✅ Completada | `phase/6-management-frontend` |
| 7. Calidad y pulido | ✅ Completada | `phase/7-quality` |
| 8. Despliegue y documentación | ✅ Completada | `phase/8-deployment` |
| 9. (Opcional) Líneas futuras | ✅ Completada | `phase/9-future-lines` |
| 10. Puesta en producción | ✅ Completada (salvo lo que requiere cuentas externas) | `phase/10-production-readiness` |
| 11. Rendimiento y robustez | ✅ Completada | `phase/11-performance` |
| 12. Producto | ✅ Completada | `phase/12-product` |
| 13. Nutrición avanzada | ✅ Completada | `phase/13-advanced-nutrition` |
| 14. Contenido en tres idiomas | ✅ Completada | `phase/14-content-translations` |

## Fase 0 — Preparación

**Hecho**
- Documentación base: `docs/PLAN.md`, `docs/DECISIONS.md`, `docs/TRACEABILITY.md`, este fichero.
- Backend: proyecto Django 5.2 con settings `base/dev/test/prod`, 7 apps (`core`, `accounts`, `training`,
  `nutrition`, `progress`, `assignments`, `statistics`), `GET /api/v1/health`, OpenAPI en `/api/docs/`,
  *handler* de errores uniforme, modelo `User` propio, logging JSON, `ruff` + `black`, pytest.
- Frontend: Ionic 8 + React 18 + TS 6 + Vite 8 «hola mundo», ESLint + Prettier, Vitest + RTL.
- `docker-compose.yml` (db + backend + frontend), Dockerfiles de desarrollo, `Makefile`, `.env.example`.
- CI (`.github/workflows/ci.yml`): lint, migraciones al día, pytest con Postgres 16, Vitest, typecheck y build.

**Verificación**
- Backend: `ruff` y `black` OK; `pytest` 2/2 en verde contra PostgreSQL 16.15 local.
- Frontend: `eslint`, `prettier`, `tsc` OK; Vitest 1/1 en verde; `vite build` OK.

**Problemas conocidos / pendientes**
- La máquina de desarrollo no tiene Docker (D-02): `docker compose up` no se ha podido ejecutar en local.
  La configuración se valida en CI y en la Fase 8 (`docker-compose.prod.yml`).
- ~~La CI todavía no exige `--cov-fail-under=90`~~ → activado en la Fase 3.
- ~~El *bundle* del frontend supera 500 kB~~ → *chunks* de *vendor* separados en la Fase 4 (D-34).

## Fase 1 — Núcleo backend: cuentas

**Hecho**
- `core`: permisos por rol (`IsClient`, `IsAdmin`, `IsTrainerOrAdmin`, `IsNutritionistOrAdmin`, `IsStaff`,
  lectura staff / escritura restringida, `IsOwner`), formato de error uniforme con `field_codes`, excepciones de
  dominio, validación del tipo real de ficheros, nombres UUID, borrado de ficheros huérfanos, logging JSON.
- `accounts`: `UserDetails`, `DietPreferences`, `HealthInfo` (listas validadas contra enums), validador de
  complejidad de contraseña, Argon2.
- Endpoints: `auth/register|login|refresh|logout|email-exists`, `me`, `me/profile`, `me/password`,
  `me/photo` (PUT/DELETE), `me/onboarding` (GET/POST/PUT). *Throttling* por *scope*.
- `progress.WeightRecord` (un registro por día) y servicio `record_weight`.
- `assignments.recompute_user_status`: único punto que calcula el estado del cliente.
- OpenAPI sin avisos (validado también en CI).

**Verificación**
- `pytest`: 132 tests en verde; cobertura de `apps` 97 % (`accounts` ≥ 93 % por fichero).
- `ruff`, `black`, `makemigrations --check` y `spectacular --validate --fail-on-warn` OK.

**Pendiente / conocido**
- `accounts.selectors.plan_flags` devuelve `(False, False)` hasta que existan las asignaciones de entrenamiento
  (Fase 2) y de nutrición (Fase 3); entonces `recompute_user_status` activará al cliente.

## Fase 2 — Backend de entrenamiento

**Hecho**
- Modelos: `MuscleGroup` (13 grupos cargados por migración de datos), `Exercise` + `ExerciseStep` +
  `ExerciseMedia`, `Workout` + `WorkoutExercise`, `TrainingPlan` + `TrainingPlanWorkout`, `UserTrainingPlan`
  (restricción única parcial: un plan actual por usuario), `UserPlanWorkout`, `ExerciseCompletion`,
  `WorkoutSession`, `ExerciseLog`.
- CRUD de staff (`/muscle-groups`, `/exercises`, `/workouts`, `/training-plans`) con hijos ordenados, búsqueda,
  filtros, paginación, media (`/exercises/{id}/media`, `/workouts/{id}/media`, `/training-plans/{id}/media`) y
  política de borrado (D-22). Lectura para todo el staff; escritura para entrenador y admin.
- Cliente: `/me/training-plan`, `/me/training-plan/workouts/{id}` (+ `exercises/{we}` y `complete`),
  `/me/exercises/{id}`. Secuencia con bloqueo, % del día, duración estimada, cierre de ciclo, calendario por
  defecto y mensajes de motivación al completar.
- `POST /users/{id}/assign-training-plan` con `replace` y 409 específico.
- `plan_flags` ya refleja la asignación de entrenamiento.

**Verificación**
- `pytest`: 256 tests en verde; cobertura de `apps` 98 % (`training/services|views|serializers` 100 %).
- Tests anti N+1 en listados y detalle de plan; `ruff`, `black`, `makemigrations --check` y
  `spectacular --validate --fail-on-warn` OK.

**Problema resuelto durante la fase**
- La sincronización de clientes al editar un plan asignado leía la lista de entrenamientos precargada por la
  vista (caché obsoleta). Ahora consulta siempre la tabla (`sync_user_plan`).

**Pendiente / conocido**
- ~~`plan_flags` aún no tiene en cuenta la nutrición~~ → resuelto en la Fase 3.

## Fase 3 — Backend de nutrición, progreso, asignaciones y estadísticas

**Hecho**
- `nutrition`: `MealPlan` (catálogo, borrado lógico, validación de macros ±10 % y reparto al 100 %),
  `UserNutritionPlan`, `/meal-plans` (filtro `?category=`), `/me/nutrition-plan` con macros (g, kcal, %) y reparto
  por comida.
- `assignments`: `/assignments/pending` filtrado por rol (`missing` para el admin), asignación nutricional con
  `replace`/409, `recompute_user_status` completo (el cliente pasa a `active` con ambos planes).
- `accounts`: `/users` (lista alfabética con búsqueda, filtro de rol y planes actuales; detalle completo con
  onboarding, pesos y planes; crear/editar/borrado lógico solo admin).
- `progress`: dashboard (calendario del mes, próximo entrenamiento con fecha y hora objetivo, % del plan, ciclo,
  sesiones totales y motivación), historial paginado con filtros `from`/`to`/`workout`, registros de peso con
  líneas inicial y objetivo.
- `statistics`: popularidad de ejercicios por año, crecimiento mensual de clientes, KPIs y años con datos.
- `seed_demo` idempotente: 3 staff, 3 clientes demo (uno en cada estado; el activo con unos 3 meses de sesiones y
  pesos), 18 clientes repartidos en el año anterior y el actual, 25 ejercicios con *placeholders*,
  6 entrenamientos, 3 planes de entrenamiento y 6 planes nutricionales.
- Matriz de permisos completa (`test_permissions.py`). CI con `--cov-fail-under=90`.

**Verificación**
- `pytest`: 562 tests en verde; cobertura total 98,6 % (umbral del 90 % activado).
- `seed_demo` ejecutado dos veces sobre la base de desarrollo con los mismos recuentos; prueba de humo de
  login, dashboard, nutrición, pesos, estadísticas y pendientes con los usuarios demo.
- `ruff`, `black`, `makemigrations --check` y `spectacular --validate --fail-on-warn` OK.

**Pendiente / conocido**
- La contraseña demo no cumple la política de contraseñas (D-27).

## Fase 4 — Base del frontend

**Hecho**
- Tema (`theme/variables.css`): verde primario con contraste AA, rojo para eliminar/cancelar, morado para
  asignar, gris para acciones secundarias, colores fijos por macro y modo oscuro del sistema.
- i18n: es/en/ca con carga diferida, `useLanguage` (cambio instantáneo, persistido y enviado como
  `Accept-Language`), selector con banderas SVG, formateo con `Intl`. Traducciones de todos los códigos de error
  del backend y de todos los enums.
- API: axios con conversión snake↔camel, `ApiError` uniforme, tokens (D-32) y refresco único con cierre de sesión.
- `AuthContext` (restaura la sesión al recargar), reglas de navegación por rol/estado, `TabsLayout` con icono y
  texto, `PageLayout` (barra superior fija, idioma, avatar del admin, *pull-to-refresh*), estados vacío, error y
  carga, `useResource`, `useConfirm`, `TextField` para React Hook Form + Zod.
- Esquemas Zod compartidos con las mismas reglas que el backend (nombre, email, contraseña, fecha dd/mm/aaaa y
  edad 18–120).
- Páginas: Bienvenida, Login (mostrar/ocultar contraseña, «Recordar sesión», error específico) y un Perfil
  mínimo con «Cerrar sesión».
- Playwright configurado (arranca o reutiliza backend y Vite) y *job* de E2E en la CI con `seed_demo`.

**Verificación**
- Vitest: 58 tests en verde (paridad i18n, conversión de claves, tokens, interceptores con refresco único,
  reglas de navegación, esquemas, selector de idioma, arranque de la app).
- Playwright contra el backend real con datos demo: 5 tests en verde (credenciales erróneas; login de admin con
  5 pestañas y una sola activa, logout y protección de rutas; sesión recordada tras recargar; redirección por
  rol; cambio de idioma en vivo y persistido).
- ESLint, Prettier, `tsc` y `vite build` OK.

**Pendiente / conocido**
- Las secciones que no son de esta fase muestran una página temporal «disponible muy pronto»
  (`pages/shared/ComingSoonPage.tsx`); sustituidas en las Fases 5 y 6 y la página eliminada.

## Fase 5 — Frontend de cliente

**Hecho**
- Registro (validaciones en vivo, email comprobado contra la API, indicador de requisitos de contraseña, fecha
  dd/mm/aaaa con máscara, términos en modal, botón deshabilitado hasta que todo es válido).
- Onboarding de 6 pasos con barra de progreso, validación por paso, multiselecciones con opciones exclusivas,
  textos condicionales y selector kg/lbs.
- Estado del plan con *spinner*, ✔/✖ por asignación, recarga al entrar y *pull-to-refresh*.
- Plan semanal (barra de progreso arriba, tarjetas ordenadas con día programado y candado; la tarjeta
  bloqueada avisa y no navega), entrenamiento del día (barra arriba, casillas persistidas, resumen, completar
  al 100 % con mensaje motivacional) y detalle de ejercicio (carrusel con flechas y deslizamiento, modal de
  información, chips de grupos musculares, tres círculos, cronómetro de descanso con vibración/sonido, marcar
  como hecho, *scroll* arriba al entrar).
- Macronutrientes (dieta traducida, kcal, tarjetas por macro, dónut, tabla de comidas, notas).
- Progreso con sub-pestañas fijas: calendario mensual y próximo entrenamiento con cuenta atrás en vivo;
  historial con filtros; peso con gráfica (líneas inicial y objetivo) que se actualiza al instante. Mensaje
  motivacional en las tres.
- Perfil completo y edición (foto con vista previa, datos personales y deportivos, cambio de contraseña).
- Gráficos de Chart.js en un *chunk* aparte, cargados solo donde se usan.

**Verificación**
- Vitest: 79 tests en verde (nuevos: esquemas de registro y onboarding, máscara de fecha, cronómetro,
  cuenta atrás, % del día, requisitos de contraseña, multiselección exclusiva, calendario, gráficos).
- Playwright: 12 tests en verde contra el backend real (nuevos: E2E 1, E2E 3, E2E 4, email duplicado, cliente
  activo con 4 pestañas, macros y detalle de ejercicio, edición de perfil, cambio de contraseña).
- ESLint, Prettier, `tsc` y `vite build` OK.

**Pendiente / conocido**
- La regresión #8 (*scroll* arriba al entrar en el detalle) está implementada (`useIonViewDidEnter` →
  `scrollToTop`); su test específico se añade en la Fase 7.

## Fase 6 — Frontend de gestión

**Hecho**
- Catálogo de entrenamiento (entrenador y admin) con sub-pestañas fijas Entrenamientos | Ejercicios | Planes:
  listados con búsqueda, Ver / Modificar (verde) / Eliminar (rojo, con confirmación y motivo si está en uso),
  botón «+», formularios (filas de ejercicios reordenables; pasos dinámicos, grupos musculares y varias medias;
  plan con entrenamientos ordenados) y vistas detalladas enlazadas.
- Nutrición (nutricionista y admin) con sub-pestañas por categoría; formulario con kcal calculadas en vivo,
  aviso de discrepancia > 10 % y reparto de comidas que debe sumar 100; detalle con dónut.
- Usuarios: lista alfabética con búsqueda, filtro de rol y *chips* de planes; Asignar (morado) para clientes y
  Modificar (gris) / Eliminar (rojo) / «+» solo para el admin; ficha completa; alta y edición (admin).
- Asignaciones: pendientes por rol (el admin, agrupados), estado vacío, ficha con datos y respuestas relevantes
  para el rol, historial de peso, selector de plan, «Crear plan nuevo» con vuelta y preselección, confirmación de
  asignación y de reemplazo.
- Estadísticas (admin): KPIs, popularidad de ejercicios (barras horizontales moradas), crecimiento mensual
  (barras verdes) y selector de año.
- Test de claves i18n usadas en el código.

**Verificación**
- Vitest: 89 tests en verde.
- Playwright: 19 tests en verde (nuevos: E2E 2, E2E 5, E2E 6, reemplazo de plan, «Crear plan nuevo»,
  catálogo con ejercicio + entrenamiento y estadísticas).
- ESLint, Prettier, `tsc` y `vite build` OK.

**Problemas encontrados y resueltos con los E2E**
- Las rutas `/:id` capturaban `new` (p. ej. `/app/users/new` abría una ficha con id `NaN` para un entrenador):
  los parámetros de id solo aceptan dígitos (`:id(\d+)`).
- Los formularios de edición se reinicializaban al recargar los datos al entrar en la vista y borraban lo
  escrito: `useFormInit` rellena el formulario una sola vez por entidad.
- Guardar una edición no navegaba porque la página destino ya estaba en la pila de Ionic: `useLeaveForm` vuelve
  atrás tras editar y solo sustituye la vista al crear.

## Fase 7 — Calidad y pulido

**Hecho**
- Regresiones de los errores conocidos: las 11 tienen test en verde (nuevos: #8 *scroll* y #3 en E2E sobre pantallas de
  cliente y admin).
- Accesibilidad: auditoría axe-core (WCAG 2.1 A/AA) sin violaciones críticas ni serias; corregidos el
  *skeleton* sin rol, la región desplazable sin acceso por teclado y la semántica del calendario.
- PWA: *manifest*, iconos y *service worker* básico (D-41).
- Pulido visual revisado con capturas en móvil y escritorio: etiquetas de pestañas legibles, sub-pestañas sin
  recortes, título del calendario, plural de «ejercicio(s)», números de la motivación con formato local e
  imágenes demo con acentos.
- Rendimiento: presupuestos de consultas en los endpoints de lectura clave (`tests/test_performance.py`).
- Seguridad: `check --deploy` limpio y añadido a la CI. Eliminadas las copias de `toNumber`.
- Robustez: `useResource` descarta respuestas obsoletas.

**Verificación**
- Backend: 569 tests en verde, cobertura 98,6 %; `ruff`, `black`, `check --deploy` OK.
- Frontend: Vitest 92 tests; Playwright 22 tests (incluye accesibilidad y regresiones); ESLint, Prettier, `tsc`,
  `vite build` OK.

**Problema encontrado y resuelto**
- Carrera en `useResource`: la recarga al entrar en la vista podía resolverse después de una búsqueda y
  sobrescribir sus resultados. Ahora solo la última petición actualiza el estado (test unitario dedicado).
- Un E2E falló una vez porque una petición de login se quedó colgada en el *proxy* de Vite sin llegar a Django;
  al repetirlo pasó (la CI tiene `retries: 1`).

## Fase 8 — Despliegue y documentación

**Hecho**
- Imágenes de producción multi-etapa (D-45):
  - backend: gunicorn, whitenoise, usuario sin privilegios y `HEALTHCHECK`;
  - frontend: nginx con *fallback* de la SPA y *proxy* de la API.
- `docker-compose.prod.yml` para probar el stack de producción en local (D-46).
- `render.yaml` con API, *static site* y PostgreSQL 16 (D-47).
- *Settings*: `RENDER_EXTERNAL_HOSTNAME` en `ALLOWED_HOSTS` y CSRF; `SERVE_MEDIA` solo para el stack local.
- CI: *job* `docker` que construye las imágenes `prod`, levanta el stack y hace una prueba de humo (D-48).
- `SEED_DEMO=1` por defecto en desarrollo (D-49).
- Documentación:
  - `README.md` completo: arranque con y sin Docker, usuarios demo, tests, despliegue en Render paso a paso,
    bucket de GCS y cuenta de servicio, variables de entorno.
  - `docs/API.md`: convenciones, autenticación, formato de errores, permisos y endpoints, con enlace a
    OpenAPI.
  - `docs/ARCHITECTURE.md`: 10 diagramas Mermaid (despliegue, capas, entidad-relación, estados, secuencia de
    entrenamiento, frontend, navegación por rol y CI).

**Verificación**
- Backend: 574 tests en verde, cobertura 98,8 % (5 nuevos en `test_settings.py`: *host* de Render, *settings* endurecidos, clave
  obligatoria, configuración de GCS y media del stack local); `ruff`, `black`, `makemigrations --check`,
  `check --deploy` y validación de OpenAPI OK.
- Frontend: Vitest 92 tests; Playwright 24 tests en verde (la auditoría de accesibilidad pasa de 1 a 3 tests);
  ESLint, Prettier, `tsc` y `vite build` OK.
- *Settings* de producción probados sin Docker:
  - `collectstatic`: 154 ficheros copiados y 444 post-procesados;
  - `/api/v1/health` 200 con cabeceras de seguridad;
  - `/api/v1/me` 401;
  - `Host` no permitido → 400;
  - estáticos con *hash* servidos por whitenoise con caché inmutable.
- Los 11 diagramas Mermaid de `docs/` se renderizan sin errores (mermaid 11 en Chromium).
- YAML de `render.yaml`, `docker-compose*.yml` y CI validados.

**Problema encontrado y resuelto**
- La auditoría de accesibilidad empezó a fallar por contraste en la etiqueta de la pestaña recién pulsada:
  axe medía 4,3:1, con texto `#1a7a43` sobre `#daeae1`. No es un defecto de la interfaz.
  - **Qué medía axe:** el fondo era el *ripple* de Ionic (el verde primario al 16 %), que se desvanece en
    unos 300 ms. Los colores estables cumplen: 7:1 sin seleccionar y 5,4:1 seleccionada.
  - **Por qué lo veía:** el cambio de pestaña es una navegación interna de la SPA, así que
    `waitForLoadState('networkidle')` ya estaba cumplido y la auditoría se ejecutaba de inmediato.
  - **Corrección:** antes de auditar, el test espera a que no quede ningún indicador de carga ni ningún
    *ripple*. La auditoría se ha dividido en tres tests (pantallas públicas, cliente y admin) para no superar
    el límite de 60 s. El mensaje de fallo ahora incluye los colores y el ratio que mide axe.
- El servidor de Vite se cayó a mitad de una ejecución de los E2E, y el test de estadísticas falló con «Sin
  conexión». Al reiniciar Vite, ese test pasó en las dos repeticiones.

**Pendiente fuera de esta máquina**
- `docker compose up` (desarrollo y producción) no puede ejecutarse aquí (D-02): lo cubre el *job* `docker`,
  que correrá en cuanto el repositorio tenga remoto en GitHub.
- El primer despliegue real en Render requiere la cuenta, el bucket de GCS y la clave de la cuenta de
  servicio.

## Fase 9 — Líneas futuras

**Hecho** (las cuatro líneas, en su orden de prioridad; D-50 a D-53)
1. **Recuperación de contraseña por email.**
   - Enlace de un solo uso que caduca a los 60 min y email en el idioma de la app.
   - Respuesta idéntica exista o no la cuenta, y límite de peticiones propio.
   - Al cambiarla se cierran todas las sesiones.
   - Por defecto el email se escribe en la consola; con SMTP configurado se envía.
   - Pantallas «¿Has olvidado tu contraseña?» y «Nueva contraseña».
2. **Días de entrenamiento elegidos por el cliente.**
   - Selector de días desde el plan semanal.
   - Los días elegidos sustituyen al reparto por defecto en el plan, el calendario de Progreso y la cuenta
     atrás.
   - Si cambia el número de días semanales, se vuelve al reparto por defecto.
3. **Biblioteca de alimentos.**
   - Valores por 100 g: kcal, macros, fibra, azúcares, grasas saturadas y nueve micronutrientes.
   - Gestión por nutricionista y admin; consulta por el cliente desde Nutrición.
   - 31 alimentos demo con valores aproximados de referencia.
4. **Gamificación.**
   - Ocho insignias calculadas con datos existentes (sesiones, ciclos, pesos y objetivo), que no se retiran.
   - Tarjeta en Progreso y página de insignias.
   - Aviso al ganarlas al completar un entrenamiento o registrar el peso.

**Verificación**
- Backend: 714 tests en verde, con cobertura del 98,8 %.
  - Nuevos: `test_password_reset.py`, `test_training_days.py`, `test_food.py` y `test_badges.py`, además de
    10 endpoints más en la matriz de permisos.
  - Pasan ruff, black, `makemigrations --check` (3 migraciones nuevas) y la validación de OpenAPI.
- Frontend: Vitest en verde (tests nuevos de esquemas, alimentos, insignias, días de la semana y conversión
  de claves); ESLint, Prettier, `tsc` y `vite build` OK.
- E2E: los 32 tests de Playwright en verde.
  - Nuevos: `password-reset`, `training-days`, `foods` y `badges`.
  - La auditoría de accesibilidad incluye las páginas nuevas.

**Problemas encontrados y resueltos**
- `toSnake` perdía las palabras de una sola letra al volver a *snake_case* (`vitaminAUg` → `vitamin_aug`).
  Ahora separa cada mayúscula, y hay un test de ida y vuelta.
- En los E2E, Ionic mantiene visibles dos páginas durante la transición y había campos y botones repetidos.
  Los tests esperan a que la página anterior se oculte.
- Los datos de referencia de la leche daban más azúcares que hidratos; se ajustaron para cumplir la
  validación.

## Fase 10 — Puesta en producción (fase 1 del plan de mejora)

**Hecho** (D-54 a D-60; guía en `docs/OPERATIONS.md`)
1. **Seguridad de los límites de peticiones.** Se podían esquivar con una cabecera `X-Forwarded-For` falsa;
   ahora la API solo usa la dirección que añade el *proxy* (`NUM_PROXIES`). Tiene tests de regresión.
2. **Dependencias.** `pip-audit` y `npm audit` en la CI, y Dependabot con 14 días de espera.
3. **Monitorización.** Sentry en backend y frontend, activado solo con DSN y sin datos personales. Un
   *workflow* comprueba la disponibilidad cada 15 minutos.
4. **Copias de seguridad.**
   - `backup_database` en un bucket privado, con 14 días de retención.
   - `restore_drill` comprueba la restauración tabla a tabla.
   - Un *cron* nocturno en Render hace la copia.
   - La CI repite la restauración real con los datos demo y dentro de la imagen de producción.
5. **Sesión.** El *refresh token* pasa a una cookie `httpOnly` con defensa CSRF, y en Render la API se sirve
   bajo el mismo origen mediante un *rewrite*. Las sesiones de versiones anteriores se migran sin pedir login.
6. **CSP y cabeceras de seguridad.**
   - Una única definición se aplica en nginx, Render y `vite preview`, y un E2E comprueba el *build* bajo
     la CSP.
   - Se ha corregido la herencia de cabeceras de nginx.
   - Zod funciona en modo `jitless`.
7. **RGPD.**
   - Consentimiento versionado de la política y consentimiento expreso y separado para los datos de salud.
   - Exportación de todos los datos y borrado de la cuenta por el cliente.
   - Purga de las cuentas dadas de baja.
   - Política de privacidad pública en tres idiomas.

**Verificación**
- Backend: 757 tests en verde, incluida la restauración real con PostgreSQL 16, y cobertura del 98,8 %.
  Pasan ruff, black, `makemigrations --check`, OpenAPI, `check --deploy` y `pip-audit`.
- Frontend: Vitest en verde (sesión, monitorización, cabeceras, consentimiento…); ESLint, Prettier, `tsc`,
  `vite build` y `npm audit` OK.
- E2E en el servidor de desarrollo (incluidos los nuevos de privacidad) y, contra el *build* de producción con
  CSP, la CSP sin violaciones y los flujos principales.

**Problemas encontrados y resueltos**
- **Límites esquivables** con `X-Forwarded-For` (punto 1).
- **Cabeceras de nginx:** las `location` con `add_header` propio no heredaban las cabeceras de seguridad.
- **Violaciones de la CSP:** la comprobación de `eval` de Zod y las URLs de media con el puerto del backend
  por `changeOrigin`.
- **Alta de usuarios por el admin:** exigía el consentimiento de salud (lo detectó el E2E). Ahora lo da el
  usuario en su primer acceso.
- **`@sentry/react`** choca con react-router 5: se usa `@sentry/browser`.

**Pendiente fuera de esta máquina** (requiere las cuentas de la persona responsable)
- Repositorio en GitHub y primera ejecución de la CI.
- *Staging* en Render, buckets de GCS, SMTP y Sentry.
- Las comprobaciones de *staging* de `docs/OPERATIONS.md`, en especial `NUM_PROXIES` con el *rewrite* y las
  subidas grandes.
- Revisión legal de la política de privacidad y contratos de encargado del tratamiento.

## Fase 11 — Rendimiento y robustez (fase 2 del plan de mejora)

**Hecho** (D-61 a D-66)
1. **Bundle más ligero.**
   - *Tree-shaking* real de Ionic: de 296 a 224 kB comprimidos.
   - Páginas cargadas por rol: el código propio inicial baja de 43 a 13 kB comprimidos.
   - En total, la carga antes del login pasa de unos 425 a unos 323 kB comprimidos (un 24 % menos).
2. **Imágenes.** Se recodifican a WebP (512 px las de perfil y 1600 px el resto) sin metadatos: se elimina el
   EXIF, incluida la posición GPS.
3. **Entrenamiento sin conexión.**
   - Copias locales del plan, los entrenamientos y los ejercicios.
   - Cola de marcas que se envía al volver la red.
   - Aviso de falta de conexión.
   - La sesión resiste una recarga sin red.
4. **E2E sobre el *build* de producción** (`E2E_PREVIEW=1`) y sin animaciones (`prefers-reduced-motion`, una
   mejora de accesibilidad). La CI ejecuta así toda la suite en unos 3,5 minutos, frente a los 5–6 de antes.
5. **Prueba de carga con k6 en la CI.** 20 clientes virtuales durante 30 s sobre el *stack* Docker de
   producción, con umbrales de errores y de percentil 95.

**Verificación**
- Backend: 764 tests en verde (nuevos: `test_images.py`) y cobertura del 98,8 %.
- Frontend: 115 tests de Vitest (nuevos: copias sin conexión y cola de marcas); ESLint, Prettier, `tsc` y
  `vite build` OK.
- E2E: 37 tests en verde sobre el *build* de producción. Nuevo: `offline.spec.ts`, que recarga sin red, marca
  un ejercicio, sincroniza y lo comprueba en el servidor.

**Problemas encontrados y resueltos**
- El texto de los términos del registro salía cortado («…»), porque le faltaba el ajuste en varias líneas.
- Un clic que no abría el desplegable de un *select* hacía fallar los E2E de forma intermitente; la ayuda de
  los tests lo reintenta.

## Fase 12 — Producto (fase 3 del plan de mejora)

**Hecho** (D-67 a D-72)
1. **Series reales y récords.**
   - El cliente anota repeticiones y kilos de cada serie en el entrenamiento del día o en la ficha del
     ejercicio. El editor se rellena con el plan y la carga de la última vez, y funciona sin conexión.
   - Al completar el entrenamiento se anuncian los récords batidos.
   - La ficha del ejercicio muestra «Tu progreso»: récord, 1RM estimado, gráfica de la carga máxima y las
     últimas sesiones.
   - Progreso › Entreno lista los récords.
2. **Adherencia para el personal.**
   - Desde Usuarios, la lista de clientes ordenada por quién necesita ayuda: inactivos, en riesgo y al día.
   - Para cada cliente: días entrenados frente a los programados en 28 días, último entreno y variación de
     peso.
   - La ficha del cliente muestra las últimas cuatro semanas.
3. **Notas con el equipo.**
   - Un hilo asíncrono por cliente, desde Perfil o desde el estado del plan.
   - Aviso en el plan semanal cuando hay notas nuevas.
   - El personal ve el hilo en la ficha del cliente y una bandeja de notas sin leer en Usuarios.
4. **Recordatorios.**
   - Hora de entreno propia de cada cliente (también para la cuenta atrás).
   - Email opcional en la hora previa, los días de entreno y solo si aún no ha entrenado: *cron* horario
     `entrenanutricion-reminders` en Render.
   - El idioma de la app se guarda en la cuenta y los emails se escriben en él.
5. **Verificación del correo** al registrarse.
   - Enlace firmado de 7 días, con reenvío y aviso en la app mientras falte.
   - Las cuentas creadas por un admin y las existentes se dan por verificadas.
   - Los recordatorios solo van a direcciones confirmadas.

Las notas, los recordatorios y el idioma entran en la exportación de datos. La política de privacidad
(versión `2026-11`, aún sin publicar) ya menciona las series, las notas y los emails de confirmación y de
recordatorio. Si se cambia después de abrir la app al público, hay que subir la versión (`docs/OPERATIONS.md`).

**Verificación**
- Backend: 915 tests en verde y cobertura del 99 %. Nuevos: `test_sets.py`, `test_adherence.py`,
  `test_notes.py`, `test_reminders.py` y `test_email_verification.py`. La matriz de permisos incluye
  las 16 combinaciones nuevas de método y ruta.
- Frontend: 136 tests de Vitest. Nuevos: editor de series, cola con series, textos de récords, tarjeta de
  adherencia, hilo de notas e idioma de la cuenta. ESLint, Prettier, `tsc` y `vite build` OK.
- E2E: 43 tests en verde sobre el *build* de producción (unos 5 minutos en local). Nuevos: `sets.spec.ts`, `adherence.spec.ts`,
  `notes.spec.ts`, `reminders.spec.ts` y `verify-email.spec.ts`. La auditoría de accesibilidad incluye las
  pantallas nuevas.

**Problemas encontrados y resueltos**
- `ExerciseLog.reps_completed` guardaba las repeticiones de una serie. Con series reales pasa a ser el total,
  y la migración convierte los registros antiguos.
- Faltaba el límite `notes` en los *settings* de test, que definen los suyos: escribir una nota daba 500. Lo
  detectaron los tests; los límites nuevos se añaden ahora en los dos sitios.
- Varios campos `status` y `role` con opciones distintas colisionaban en el esquema OpenAPI. Se resuelve con
  `ENUM_NAME_OVERRIDES` (`AdherenceStatusEnum`, `UserStatusEnum`, `RoleEnum`).
- En la base de datos de desarrollo, las sesiones que crean los E2E duplicaban días entrenados. La
  adherencia cuenta días, no sesiones.

## Fase 13 — Nutrición avanzada (fase 4 del plan de mejora)

**Hecho** (D-73 a D-75)
1. **Menú de ejemplo.**
   - El nutricionista compone un día de comidas por plan con alimentos de la biblioteca, en gramos.
   - Ve en vivo los totales de cada comida y del día frente a los objetivos del plan, con un aviso si se sale
     del ±10 %.
   - El cliente lo ve en Macronutrientes.
2. **Diario de comidas.**
   - El cliente anota lo que come, día a día, desde la biblioteca o copiando una comida o el día entero del
     menú. Puede cambiar los gramos y borrar.
   - Ve lo consumido frente al objetivo (calorías y macros) y los últimos 7 días.
   - El personal ve ese resumen en la ficha del cliente.
3. **Lista de la compra.**
   - Generada desde el menú para 1, 3, 7 o 14 días, por categorías.
   - Las marcas quedan en el dispositivo, funciona sin conexión y se puede compartir.

Un alimento que está en algún menú ya no se puede borrar (`409 food_in_use`). El diario entra en la
exportación de datos y en la política de privacidad. La demo incluye menús para todos los planes y una semana
de diario del cliente de demostración.

**Verificación**
- Backend: 1000 tests en verde y cobertura del 99 %. Nuevos: `test_menus.py` y `test_food_log.py`. La matriz
  de permisos incluye las 11 combinaciones nuevas de método y ruta.
- Frontend: 141 tests de Vitest. Nuevos: raciones, sumas y desviaciones, esquemas, menú y resumen del
  diario. ESLint, Prettier, `tsc` y `vite build` OK.
- E2E: 47 tests en verde sobre el *build* de producción. Nuevo: `nutrition-plus.spec.ts` (menú del
  nutricionista, diario y lista de la compra del cliente, resumen para el personal). La auditoría de
  accesibilidad incluye las pantallas nuevas.

**Problemas encontrados y resueltos**
- La vista del diario llamaba al servicio con un nombre de argumento distinto (`date` frente a `on_date`) y
  devolvía 500. Lo detectaron los tests.
- El selector de alimentos reiniciaba su estado en un efecto (lo prohíbe la regla de ESLint de React). Ahora
  lo hace en el evento `onWillPresent` del modal.
- En el editor de menús la columna de gramos se desalineaba según el ancho de las calorías; las columnas
  tienen ahora un ancho fijo.

## Fase 14 — Contenido en tres idiomas

**Hecho** (D-76, D-77)
1. **Catálogo traducible.**
   - Ejercicios (con sus pasos), entrenamientos, planes de entrenamiento, planes nutricionales y alimentos
     tienen inglés y catalán además del español.
   - La API responde en el idioma de la app, y en español si falta la traducción.
   - El personal traduce desde la sección «Traducciones» de cada formulario.
   - Las listas buscan en todos los idiomas y ordenan por el nombre traducido.
   - El recordatorio por email sale en el idioma de la cuenta.
2. **Demo traducida:** 25 ejercicios, 6 entrenamientos, 3 planes de entrenamiento, 6 planes nutricionales y
   31 alimentos, en inglés y catalán.
3. **App instalada en el idioma del usuario** (un `manifest` por idioma).
4. **Ramas de fase con nombre en inglés.**

**Verificación**
- Backend: 1019 tests en verde. Nuevos: `test_translations.py` (idiomas y respaldo en español, pasos,
  edición y validación, búsqueda y orden, pantallas del cliente y del personal, email y estadísticas) y
  cobertura de traducciones de la demo en `test_seed.py`.
- Frontend: 146 tests de Vitest. Nuevos: sección de traducciones, recarga al cambiar de idioma y
  `manifests`.
- E2E: 50 tests en verde sobre el *build* de producción. Nuevo: `content-language.spec.ts` (el catálogo
  de la demo en inglés y catalán, y el entrenador traduce un ejercicio que se ve en inglés).

**Problemas encontrados y resueltos**
- Ordenar por el nombre traducido mezclaba tipos de texto en la base de datos. La expresión indica ahora el
  tipo del resultado.
- El historial de sesiones debe conservar el nombre con que se guardó la sesión. En español se muestra la
  copia, y la traducción solo en otros idiomas.
- **Guardar quedaba bloqueado sin aviso** al editar alimentos, planes o entrenamientos, y al crear ejercicios
  con pasos. Lo detectó la suite E2E.
  - Causas: los formularios enviaban una lista de pasos vacía donde no hay pasos, y el esquema rechazaba
    las traducciones de pasos vacías.
  - Solución:
    - el servidor ignora los valores vacíos y devuelve los errores por idioma y campo
      (`translations.en.name`), que el formulario muestra en su sitio;
    - la sección de traducciones avisa si hay errores en el otro idioma.
- **Con más de 100 clientes pendientes no se podía llegar a los más recientes**, porque Asignaciones muestra
  los 100 más antiguos. La pantalla tiene ahora un buscador, como Usuarios. Salió en local, donde la base de
  datos acumula los clientes que crean los E2E.

## Comprobación del proceso completo (6 de noviembre de 2026)

**Qué se comprobó**
- **Recorrido completo en el navegador** sobre el *build* de producción con su CSP (`e2e/journey.spec.ts`,
  nuevo).
  - Un cliente nuevo se registra, confirma el email, escribe al equipo y recibe la respuesta.
  - Recibe los dos planes, completa su primer entrenamiento con cargas y ve su progreso.
  - Usa el menú, el diario y la lista de la compra, activa los recordatorios, exporta sus datos y se da de
    baja.
  - Por el camino, el entrenador, el nutricionista y el admin hacen su parte.
  - El test vigila los errores de consola, las respuestas 5xx y las violaciones de la CSP.
- **Emails** (en la consola de desarrollo): confirmación del registro, recuperación de contraseña y
  recordatorio de entreno, en el idioma de la cuenta y una sola vez al día.
- **Operación:**
  - `check --deploy` con los *settings* de producción, sin avisos.
  - Copia de seguridad y restauración de prueba (38 tablas, 7539 filas).
  - Purga RGPD y recordatorios en modo de prueba.
- **Suites:**
  - Backend: 1000 tests en verde.
  - Frontend: 142 tests de Vitest.
  - E2E: 48 tests en verde sobre el *build* de producción.

**Problema encontrado y resuelto**
- **Síntoma.** El formulario inicial provocaba unas 90 violaciones de la CSP («Executing inline event handler»)
  en el *build* de producción. No impedían usarlo y la prueba de CSP existente no pasaba por ahí.
- **Causa.** El envoltorio de React de Ionic comprueba si el navegador conoce un evento con
  `setAttribute('on…', 'return;')`. Con `onKeyDown` en los chips de selección múltiple, ese atributo es un
  *handler* en línea real y la CSP lo bloquea.
- **Solución.**
  - El teclado se escucha en el contenedor nativo (delegación) y los chips no reciben `onKeyDown`.
  - Una regla de ESLint impide volver a pasar eventos nativos compuestos a componentes `Ion*`.
  - Hay un test de teclado para los chips.

## Fase 15 — Endurecimiento de seguridad

Corrige la auditoría de seguridad del 6 de noviembre de 2026: riesgo medio, sin hallazgos críticos ni altos,
13 medios y 18 bajos.

**Hecho** (D-78 a D-85)
1. **Subidas acotadas:** 40 megapíxeles por imagen, `413` para cuerpos mayores que el vídeo más grande y 100
   peticiones con ficheros por hora y usuario.
2. **Límites y acceso:**
   - contadores compartidos entre procesos (caché en la base de datos);
   - 10 fallos de inicio de sesión por hora y cuenta;
   - contraseñas comunes o parecidas al nombre o al email rechazadas;
   - cambiar o recuperar la contraseña cierra todas las sesiones al momento;
   - el *refresh* solo se lee de la cookie;
   - sin admin de Django ni documentación de la API en producción.
3. **Producción y datos personales:**
   - claves robustas y email que envía, o no arranca;
   - logs de acceso sin *query strings*, *referers* ni navegador;
   - `no-store` en la API;
   - copias con su propia cuenta de servicio, de solo escritura;
   - la purga nocturna borra también las fotos de las cuentas;
   - registro de los accesos del equipo a los datos de salud;
   - `DEMO_PASSWORD` fuera de desarrollo;
   - asunto de los recordatorios saneado.
4. **Frontend:** la sesión caducada borra las copias del dispositivo, `returnTo` solo dentro de la app y un
   *service worker* que solo guarda los estáticos.
5. **Cadena de suministro y despliegue:**
   - *locks* de Python con *hashes*;
   - imágenes por *digest* (nginx pasa a la rama estable 1.30);
   - huella de la clave de PostgreSQL;
   - `.dockerignore` sin secretos ni tests;
   - puertos locales en `127.0.0.1`;
   - HSTS en el *static site*;
   - CI con *token* de solo lectura y acciones por SHA.

**Verificación**
- Backend: 1081 tests en verde y 2 que en Windows se saltan, y que corren en la CI: la restauración real
  (esa ejecución no tenía `PG_BIN_DIR`) y la línea del log de gunicorn (necesita Unix). Cobertura del 98 %.
  - Nuevos ficheros: `test_uploads.py` y `test_health_data_access.py`.
  - Pruebas nuevas en `test_auth.py` (contraseñas y límite por cuenta), `test_settings.py` (claves, email,
    gunicorn, `no-store`, admin, documentación y caché), `test_me.py` y `test_password_reset.py` (fin de la
    sesión), `test_backups.py`, `test_seed.py`, `test_reminders.py` y `test_images.py`.
- Frontend: 155 tests de Vitest. Nuevos: errores de subida (`MediaPicker`), sesión caducada (`AuthContext`),
  *service worker*, `returnTo` y HSTS.
- E2E: 53 tests en verde sobre el *build* de producción. Nuevos: `uploads.spec.ts` (bomba de descompresión
  en la foto de perfil y entrenamiento creado una sola vez) y el registro con una contraseña parecida al
  nombre en `auth.spec.ts`.
- `check --deploy` con los *settings* de producción y el esquema OpenAPI, sin avisos. `pip-audit` sin
  vulnerabilidades sobre el *lock*.
- *Lock* de Python: las 90 versiones son las del entorno probado. Se instala con `--require-hashes`, y los
  ficheros para Linux se descargan con sus *hashes* comprobados.
- Sin Docker en esta máquina (D-02): los Dockerfiles, nginx y el *compose* de producción los prueba el *job*
  `docker` de la CI.

**Problemas encontrados y resueltos**
- **Las fotos de las cuentas purgadas se quedaban en el bucket.** El *cron* nocturno no tenía `USE_GCS`, así
  que la purga intentaba borrar los ficheros de un disco local que no existe.
- **nginx 1.27 llevaba año y medio sin parches:** era una versión de desarrollo. Se pasa a la estable.
- **Un nombre de entrenamiento con un salto de línea impedía enviar el recordatorio:** Django rechaza los
  asuntos de varias líneas.
- **Un E2E usaba una contraseña nueva parecida a su propio email** (`e2e.password…` y `N3w#Password`). El
  validador nuevo la rechazó con razón; se cambió el dato de la prueba, no la regla.

**Bloque 8: lo que quedó fuera del primer plan** (D-87)
- **Doble envío:** dos peticiones iguales a la vez ya no dan un 500 en el formulario inicial, el alta de
  cuentas ni las imágenes de los ejercicios.
- **Datos acotados:** pesos de los últimos 5 años, 60 anotaciones del diario por día y récords calculados en
  la base de datos.
- **Recuperación de contraseña:** el email sale después de responder, para que el tiempo de respuesta no
  revele qué cuentas existen.
- **nginx sin root** (`nginx-unprivileged`, puerto 8080).
- **Verificación:**
  - Backend: 1094 tests en verde y 2 saltados en Windows (13 nuevos), con una cobertura del 98 %. Los
    nuevos fallan con el código anterior, también los de concurrencia, que lanzan dos peticiones reales a la
    vez.
  - Frontend: 155 tests de Vitest.
- **Pendiente:** CMEK en el bucket de copias (externo) y la adherencia del personal, que se calcula en
  memoria (rendimiento).

**Segunda auditoría y bloques 9 a 11** (D-88)
- **Resultado de la auditoría:** 29/100 (antes 57/100), sin hallazgos críticos ni altos.
- **Inicio de sesión:** fallos por cuenta e IP con tope total, contraseñas de 128 caracteres como máximo, límite en
  la renovación y el cierre de sesión, y la app solo cierra la sesión si la API la rechaza.
- **Personal y datos:** entrenadores y nutricionistas solo ven clientes, el registro de accesos cubre notas y
  diario con una fila por hora, y la descarga de datos tiene límite.
- **Despliegue:** versiones exactas de Python y Node, solo *wheels*, huella de la clave de PostgreSQL en la CI e
  identificadores SQL seguros en las copias.
- **Verificación:**
  - Backend: 1107 tests en verde y 2 saltados en Windows, con una cobertura del 99 %.
  - Frontend: 158 tests de Vitest.
  - E2E: 53 tests en verde sobre el *build* de producción.
- **Problema encontrado y resuelto:** con el nuevo límite, un 429 en la renovación habría cerrado la sesión y
  borrado las copias del dispositivo, porque la app trataba cualquier fallo como sesión caducada.

**Tercera auditoría y último bloque** (D-89)
- **Resultado de la auditoría:** 24/100 (antes 29/100 y 57/100), sin hallazgos críticos ni altos y sin hallazgos
  medios en el código de la app.
- **Corregido:** dos pestañas ya no cierran la sesión al renovarla a la vez, un email de recuperación cada 2 minutos
  por dirección, diario limitado a los últimos 5 años, la clave de PostgreSQL debe ser la única del fichero y npm
  no ejecuta scripts de instalación.
- **Verificación:**
  - Backend: 1112 tests en verde y 2 saltados en Windows, con una cobertura del 99 %.
  - Frontend: 159 tests de Vitest.
  - E2E: 53 tests en verde sobre el *build* de producción.

**Cuarta auditoría** (24/100, sin hallazgos críticos, altos ni medios en el código de la app)
- **Corregido:** el registro de accesos a los datos de salud ya no depende del rol de la cuenta (D-83).

**Pendiente de la persona responsable (configuración externa, ver `OPERATIONS.md`)**
- SMTP en el grupo `entrenanutricion-smtp`.
- Segunda cuenta de servicio de GCS (`GS_BACKUP_CREDENTIALS_JSON`), y regla de ciclo de vida, política de
  retención y cifrado con clave propia (CMEK) en el bucket de copias.
- `GS_BUCKET_NAME` en el *cron* de copias.
- *Workflow permissions* de solo lectura en GitHub.

## Fase 16 — Ilustración de bienvenida

- La pantalla de bienvenida muestra dos tarjetas, unas pesas y una manzana unidas por «+». Sustituyen a unas pesas
  que se salían de su círculo sobre una barra gris sin función.

## Fase 17 — Aplicación más visual

Más gráficos y menos listas de números, en cuatro bloques (D-90).

**Hecho**
1. **Progreso del cliente.** La pestaña Entrenos abre con las cifras de las últimas 12 semanas y tres gráficos:
   sesiones y kilos levantados por semana, y músculos trabajados en las últimas 4 semanas
   (`GET /me/progress/stats`).
2. **Inicio y diario del cliente.**
   - Entrenamiento: anillos del plan, de la semana y de la racha, y la semana de lunes a domingo. El panel
     devuelve `week` y `streak_weeks`.
   - Diario: anillos de calorías y macros frente al objetivo, y los últimos 7 días en barras con el objetivo.
3. **Equipo.**
   - Adherencia: resumen con cifras, un donut por estado y un histograma por tramos (`distribution`,
     `average_percent`).
   - Ficha: anillo de adherencia y entrenos por semana.
   - Usuarios: iniciales en color cuando no hay foto y el estado con icono.
4. **Administración.**
   - Cifras con icono y su variación frente a los mismos días del mes anterior.
   - Donuts de clientes por estado y por objetivo.
   - Sesiones por mes y planes con más clientes (`GET /statistics/sessions`, `GET /statistics/plan-popularity`).

**Arreglos de paso**
- Las notas sin leer de la bandeja del personal se cortan en dos líneas: el estilo de Ionic hacía que se
  montaran sobre la fecha.
- En la ficha del cliente, las notas sin leer al abrirla conservan la marca «Nueva» durante la visita. La
  recarga al entrar en la vista podía quitarla al instante, porque ya se habían marcado como leídas.

**Verificación**
- Backend: 1138 tests en verde y 2 saltados en Windows, con una cobertura del 99 %.
- Frontend: 167 tests de Vitest; lint, formato, tipos y esquema OpenAPI correctos.
- E2E: 51 tests en verde; los 2 de la CSP y sin conexión se ejecutan sobre el *build* de producción (CI).
- Auditoría de accesibilidad (axe) sin hallazgos en las pantallas nuevas.

**Quinta auditoría** (12/100, antes 24/100; sin hallazgos críticos ni altos, D-91)
- **Corregido:**
  - la adherencia registra el acceso al peso de los clientes;
  - el compose de producción pide su propia contraseña de base de datos;
  - la imagen vuelve a comprobar los *hashes* al instalar los *wheels*;
  - la CI limita la duración de sus trabajos.
- **Verificación:**
  - Backend: 1141 tests en verde y 2 saltados en Windows, con una cobertura del 99 %.
  - E2E de adherencia, personal, recorrido completo y accesibilidad en verde.
  - Las imágenes Docker y el compose de producción se comprueban en la CI (aquí no hay Docker).

## Definition of Done

- [x] Las 25 historias de usuario tienen entrada en `TRACEABILITY.md` con endpoint, pantalla y test.
- [x] Requisitos funcionales y no funcionales (usabilidad, TLS, política de contraseñas, código modular).
- [x] Los 11 errores conocidos tienen test de regresión en verde.
- [x] Las 8 mejoras de usabilidad: marcar como hecho desde el detalle, cronómetro de descanso, barra
      de progreso arriba, barra superior fija (también en estadísticas), sub-pestañas fijas en nutrición y
      entrenamientos, vistas detalladas, paleta revisada y texto en los iconos de la barra inferior.
- [x] Cobertura del backend ≥ 90 % (99 %). La CI de GitHub (backend, frontend, E2E sobre el *build* de
      producción e imágenes Docker) se ejecuta en cada cambio de `main`, de las ramas de fase y de las PR.
- [x] La app funciona en ES, EN y CA sin claves sin traducir.
- [ ] `docker compose up` + `seed_demo`. La configuración está completa (con `SEED_DEMO=1` por defecto), pero
      esta máquina no tiene Docker (D-02).
      - Verificado el mismo flujo sin Docker: Postgres 16, `migrate` y `seed_demo`.
      - El *job* `docker` de la CI levanta el stack de producción y le hace una prueba de humo.
- [x] `render.yaml` y README de despliegue (Render, GCS y variables de entorno). Falta el primer despliegue
      real, que requiere las cuentas de Render y Google Cloud.
