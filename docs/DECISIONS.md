# Registro de decisiones

Decisiones tomadas donde la especificación no concreta o donde el entorno obliga a elegir.
Formato: contexto → decisión → consecuencia.

## Entorno y herramientas

### D-01 · Versión de Python
La especificación pide Python 3.12+. La máquina de desarrollo tiene Python 3.15, para el que Django 5.2 no
declara soporte. **Decisión:** Python 3.12 en todos los entornos (imagen `python:3.12-slim` en Docker/Render;
en local, entorno virtual `backend/.venv` creado con `uv venv --python 3.12`).

### D-02 · Entorno local sin Docker
La máquina de desarrollo no tiene Docker. **Decisión:** se entregan `docker-compose.yml` y Dockerfiles completos
(son el camino documentado), y para verificar en local se usa un PostgreSQL 16 portable en `.local/`
(ignorado por git) con los mismos parámetros que el servicio `db` de Compose. Los criterios de salida que
dependen de `docker compose up` se verifican en CI (GitHub Actions) y quedan anotados en `PROGRESS.md`.

### D-03 · Ionic 8 + react-router 5
La última versión de Ionic es la 9, pero la especificación exige Ionic 8. **Decisión:** `@ionic/react` y
`@ionic/react-router` 8.8.x, que requieren `react-router`/`react-router-dom` 5.3.x (API v5: `Route`, `Redirect`,
`IonRouterOutlet`).

### D-04 · TypeScript 6.0
TypeScript 7 (compilador nativo) no está soportado aún por `typescript-eslint` (`<6.1`). **Decisión:** TS 6.0.x.

### D-05 · Lectura de `DATABASE_URL`
**Decisión:** `dj-database-url` (estándar de facto, lo usa Render en sus guías).

### D-06 · Formateo del backend
**Decisión:** `black` formatea y `ruff` hace *lint* (incluye reglas de `isort`). Longitud de línea 100.

### D-07 · Pruebas dependientes de la fecha
**Decisión:** `freezegun` en los tests; los servicios aceptan además `today`/`now` opcionales para ser deterministas.

### D-08 · Numeración de las historias de usuario
**Decisión:** en `TRACEABILITY.md`, las US-14…US-27 se agrupan por áreas: US-14–19 entrenamientos, US-20–22
usuarios, US-23 asignaciones, US-24 estadísticas y US-25–27 nutrición.

## Backend

### D-10 · Formato de error
`{ "code": "...", "message": "...", "fields": { "campo": ["mensaje"] } }`. Además se añade
`field_codes: { "campo": ["codigo"] }` para que el frontend traduzca los errores de campo. Los campos anidados
se aplanan con punto (`diet.meals_per_day`). Los mensajes del backend están en inglés; el frontend traduce
a partir de los códigos.

### D-11 · Validación del tipo real de los ficheros
Sin dependencias nativas (`libmagic` no está disponible en Windows ni en `python:slim` sin paquetes extra).
**Decisión:** imágenes verificadas con Pillow (formato real JPEG/PNG/WEBP); vídeo MP4 verificado por la
firma `ftyp` en los bytes 4–8. Nombres de fichero renombrados a UUID.

### D-12 · Media de entrenamientos y planes
Los entrenamientos y planes se crean con JSON (con listas anidadas); mezclarlo con multipart complica el
contrato. **Decisión:** la media se gestiona en endpoints dedicados: `PUT/DELETE /workouts/{id}/media`,
`PUT/DELETE /training-plans/{id}/media`, `POST /exercises/{id}/media` y `DELETE /exercises/{id}/media/{media_id}`.

### D-13 · Grupos musculares
Son datos de referencia necesarios también en producción. **Decisión:** se cargan con una migración de datos
(y `seed_demo` los asegura de forma idempotente). Cada grupo tiene `slug` en inglés (`biceps`, `lats`…) que el
frontend traduce; `name` guarda el nombre en español.

### D-14 · `diet_label` y `equipment` como enums
El cliente debe ver el tipo de dieta traducido. **Decisión:** `MealPlan.diet_label` es un enum
(`balanced`, `high_protein`, `low_carb`, `low_fat`, `mediterranean`, `vegetarian`, `vegan`, `keto`) y
`TrainingPlan.equipment` reutiliza el enum de equipamiento del onboarding. Ambos se traducen en el frontend.

### D-15 · `ProgressTracking`
Se sustituye por datos derivados de `WeightRecord` y `WorkoutSession`.

### D-16 · Registros de peso
**Decisión:** un registro por usuario y día; un POST con una fecha ya registrada actualiza ese registro
(*upsert*). El peso actual es el último por fecha. El peso inicial vive en `UserDetails.initial_weight_kg`.

### D-17 · Modelo `User` creado en la Fase 0
Django exige que el `AUTH_USER_MODEL` propio exista antes de la primera migración. **Decisión:** el modelo `User`
(email como identificador, roles, estados) se crea en la Fase 0; el resto de `accounts` llega en la Fase 1.

### D-18 · Sesiones y contraseña
- El *refresh token* lleva el *claim* `remember`; su vida es de 7 días con «Recordar sesión» y de 12 h sin él,
  y se mantiene tras cada rotación.
- Credenciales incorrectas y cuenta desactivada devuelven el mismo `401 invalid_credentials` (no se revela
  qué cuentas existen).
- Cambiar la contraseña invalida (*blacklist*) todos los *refresh tokens* del usuario y devuelve un par nuevo
  para la sesión actual.
- `POST /auth/logout` no exige *access token* (puede haber caducado); basta con el *refresh* a invalidar.

### D-19 · Contrato del onboarding
`POST/PUT /me/onboarding` recibe los campos de `UserDetails` en la raíz y dos objetos anidados, `diet`
(`DietPreferences`) y `health` (`HealthInfo`). Reglas añadidas por coherencia: todas las multiselecciones exigen
al menos una opción; «ninguna»/«ninguno» y «sin equipamiento» no se combinan con otras opciones; el texto de
restricciones es obligatorio si se marca alguna restricción y el de condición médica si se marca «otros»;
con objetivo `maintain`, `target_weight_change_kg` se fuerza a 0 y, si no, debe ser > 0 y dejar el peso objetivo
dentro de 30–300 kg. `PUT` no modifica los registros de peso.

### D-20 · Política de nombres y contraseñas compartida
Nombres: letras Unicode separadas por un único espacio, guion o apóstrofo (`^[^\W\d_]+(?:[ '’-][^\W\d_]+)*$`).
Contraseña: ≥ 8 caracteres, una mayúscula, una minúscula, un dígito 0–9 y un símbolo (carácter no alfanumérico
y no espacio). Las mismas reglas se replican en Zod en el frontend.

### D-21 · Contrato de catálogo de entrenamiento
- Los pasos de un ejercicio se intercambian como lista de textos (`steps: ["…", "…"]`); el orden es la posición.
- Las filas hijas (`exercises[]` de un entrenamiento, `workouts[]` de un plan) se ordenan por su posición en la
  lista. Una fila con `id` actualiza la existente, sin `id` se crea y las que faltan se eliminan. Un plan puede
  repetir un entrenamiento.
- Entrenamientos y planes exigen al menos un hijo. «Frecuencia recomendada» (`sessions_per_week`) = número de
  entrenamientos del plan.
- Listados ordenados por nombre; los desactivados se ocultan salvo con `?include_inactive=true`.

### D-22 · Política de borrado
| Entidad | En uso | Sin uso |
|---|---|---|
| Ejercicio | Lógico (`is_active=False`) si está en algún entrenamiento o en el historial | Físico |
| Entrenamiento | `409 workout_in_use` con la lista de planes que lo usan | Físico |
| Plan de entrenamiento | Lógico si alguna vez se asignó (los clientes lo conservan) | Físico |
| Plan nutricional | Siempre lógico | — |

### D-23 · Plan asignado y secuencia
- `/me/training-plan/workouts/{id}` usa el id de `UserPlanWorkout` (único por cliente y posición).
- El estado de la secuencia se normaliza siempre igual: los completados se mantienen, el primer pendiente es
  `available` y el resto `locked`. Se reaplica al editar un plan asignado (las filas nuevas entran bloqueadas).
- Un entrenamiento completado no admite cambios en sus casillas (`409 workout_already_completed`) hasta que el
  ciclo se reinicia.
- `UserTrainingPlan.date_completed` guarda la fecha del último ciclo completado.
- `WorkoutSession.workout_name` es una copia del nombre para que el historial siga siendo legible si el
  entrenamiento cambia o se elimina.
- Hora objetivo de la cuenta atrás: `DEFAULT_TRAINING_TIME` (18:00 por defecto) del día programado.

### D-24 · Planes nutricionales
- Macros en gramos con un decimal (> 0); `calories` entero > 0. La tolerancia del 10 % se mide sobre la suma
  de kcal de los macros: `|calories − Σ| ≤ 0,10 × Σ`. En un `PATCH` se comprueba contra los valores guardados.
- `meal_distribution` exige exactamente `breakfast`, `lunch`, `dinner`, `snacks` (enteros 0–100 que suman 100).
- El reparto por comida reparte las kcal **declaradas** y los gramos de cada macro según el porcentaje.
- `/me/nutrition-plan` solo exige plan nutricional (409 `nutrition_plan_not_assigned`); el borrado lógico de un
  plan no afecta a los clientes que ya lo tienen.

### D-25 · Gestión de usuarios
- `/users` lista solo usuarios activos (los borrados lógicamente desaparecen y su detalle da 404).
- `PUT` y `PATCH` son equivalentes (actualización parcial). Admiten multipart para la foto.
- El admin no puede cambiar su propio rol ni borrarse a sí mismo (409 `cannot_change_own_role` /
  `cannot_delete_self`), para no quedarse sin administradores.
- El borrado lógico invalida todas las sesiones del usuario. Las asignaciones se conservan para la trazabilidad.
- Cambiar el rol recalcula el estado (staff → `active`; cliente sin onboarding → `pending_onboarding`).
- Los usuarios creados por el admin no tienen `terms_accepted_at` (no hay casilla de términos en ese formulario).

### D-26 · Progreso
- `/me/progress/dashboard` y `/me/progress/history` exigen plan de entrenamiento (409); `/me/weight-records`
  exige onboarding (409 `onboarding_not_completed`) y está disponible también para clientes pendientes, porque
  el Perfil muestra la gráfica de peso.
- Días programados del calendario: los del reparto por defecto desde `date_started` del plan actual.
- `POST /me/weight-records` responde con la serie completa para que la gráfica se redibuje sin otra petición.

### D-27 · Datos de demostración
- `seed_demo` vive en `apps/core/management/commands/` (orquesta todas las apps) y solo se ejecuta con
  `DEBUG=True` salvo que se pase `--allow-production`.
- La contraseña demo exigida (`entrenanutricion#2025`) **no cumple** la política (no tiene mayúscula). Se
  respeta porque la pide la especificación y el seed crea los usuarios sin pasar por el validador; solo existe
  en desarrollo.
- Imágenes *placeholder* generadas con Pillow (color sólido + título); nada con copyright.

## Frontend

### D-30 · URL de la API y proxy de desarrollo
**Decisión:** `VITE_API_URL` por defecto es `/api/v1` y el servidor de Vite hace de proxy de `/api` y `/media`
hacia el backend (`VITE_PROXY_TARGET`), así en desarrollo no hay CORS. En producción (Render) `VITE_API_URL`
es la URL absoluta del backend y CORS queda restringido a la URL del frontend.

### D-31 · Estructura de rutas
- Públicas: `/welcome`, `/login`, `/register`; `/onboarding` solo para clientes `pending_onboarding`.
- Todo lo autenticado cuelga de `/app/*` dentro de `IonTabs`. Cada rol registra **solo** sus rutas
  (`layouts/appRoutes.ts`); cualquier otra ruta redirige a la pestaña inicial del rol (`homePath`). Las reglas son
  funciones puras en `auth/routing.ts` con tests.
- Secciones del staff: `/app/catalog` (entrenamientos), `/app/meal-plans` (nutrición), `/app/users`,
  `/app/assignments`, `/app/statistics`. Las del cliente: `/app/status`, `/app/training`, `/app/nutrition`,
  `/app/progress` y `/app/profile`. Ninguna ruta de pestaña es prefijo de otra, por lo que `IonTabs` solo marca
  una pestaña activa (regresión #10).

### D-32 · Sesión en el navegador
El *access token* vive solo en memoria; el *refresh* en `localStorage` («Recordar sesión») o `sessionStorage`.
Al recargar se obtiene un *access* nuevo con el *refresh*. El interceptor de axios hace un único refresco para
todas las peticiones con 401 simultáneas y, si falla, cierra la sesión y lleva al login con un aviso.

### D-33 · Carga de datos
Sin librería de caché: el *hook* `useResource` carga al montar y **recarga cada vez que se entra en la vista**
(`useIonViewWillEnter`), porque Ionic mantiene en memoria las páginas visitadas. Tras guardar, las pantallas
actualizan el estado global (`AuthContext.setUser`) con la respuesta del backend.

### D-34 · Tamaño del *bundle*
`@ionic/react` registra todos los *web components* de Ionic (≈1,3 MB minificado, 291 kB gzip). Se separa en un
*chunk* `ionic` cacheable (más `vendor` y `charts`) y se sube el umbral de aviso a 1400 kB. Las traducciones se
cargan por idioma con `import()` dinámico.

### D-35 · Ejecución de Playwright
`playwright.config.ts` arranca (o reutiliza) `runserver` y el servidor de Vite. En Windows, `E2E_PYTHON` debe ser
relativo a `backend/` con barras invertidas (`.venv\Scripts\python.exe`) porque `webServer` usa cmd.exe. Los
localizadores filtran por elementos visibles: Ionic mantiene en el DOM las páginas anteriores ocultas.

### D-36 · Formularios del cliente
- Onboarding: un único formulario de React Hook Form con un esquema Zod **por paso**; «Siguiente» valida
  solo el paso actual y, tras el primer intento, los errores se actualizan en vivo. Así las reglas cruzadas
  (kg a perder/ganar, textos obligatorios condicionados) funcionan aunque los pasos siguientes estén vacíos.
- Los kg a perder/ganar admiten kg o lbs (`1 lb = 0,45359237 kg`, redondeo a 0,1) y se envían siempre en kg.
- Registro: el email se comprueba al salir del campo (`/auth/email-exists`); el botón queda deshabilitado
  mientras el formulario no es válido o el email está registrado. Los términos se muestran en un modal con un
  texto breve (no hay documento legal en la especificación).

### D-37 · Entrenamiento del día
Las casillas se marcan de forma optimista y se confirman con la respuesta del backend (que devuelve el % del
día); si falla, se revierte y se muestra un *toast*. Al completar, un `IonAlert` muestra el mensaje motivacional
y vuelve al plan, que se recarga al entrar.

### D-38 · Datos de los E2E
Cada E2E que modifica datos crea su propio usuario (registro + onboarding) salvo los que validan la demo
(cliente activo). El E2E de peso usa un día pasado aleatorio sin registro, porque un mismo día se sobrescribe.

### D-39 · Pantallas de gestión
- Catálogo de entrenamiento en `/app/catalog` con sub-pestañas (`?tab=workouts|exercises|plans`) y nutrición en
  `/app/meal-plans` (`?category=`): la sub-pestaña activa se guarda en la URL para volver a ella.
- La media de entrenamientos y planes (una por entidad) se aplica al guardar el formulario; la de ejercicios
  (varias) se sube al guardar y la existente se elimina al momento con confirmación.
- «Crear plan nuevo» desde Asignaciones abre el formulario con `?returnTo=` y, al guardar, vuelve a la ficha con
  `?trainingPlan=` / `?mealPlan=` para dejar el plan preseleccionado.
- Asignar con plan previo muestra directamente la confirmación de reemplazo («El usuario ya tiene el plan X.
  ¿Reemplazarlo?») y envía `replace=true`; si el backend devuelve el 409 específico (otro miembro del staff
  asignó entretanto), se pide la misma confirmación.
- Tras asignar, si al cliente ya no le falta nada que ese rol pueda asignar, se vuelve a la lista de pendientes.
- En escritorio las listas de gestión usan una rejilla de tarjetas a varias columnas (la especificación permite,
  pero no exige, tablas).
- Un test (`i18n/keys-used.test.ts`) comprueba que toda clave literal de `t('…')` existe en las traducciones.

## Calidad (Fase 7)

### D-40 · Accesibilidad
- Auditoría automática con axe-core (WCAG 2.1 A/AA) en Playwright sobre pantallas públicas, de cliente y de
  admin; falla con cualquier violación crítica o seria. Se excluyen las páginas que Ionic mantiene ocultas.
- El contenedor de cada página es una región enfocable con el título como nombre: permite desplazar con teclado
  pantallas sin elementos interactivos (Ionic desplaza un elemento interno del *shadow DOM* de `ion-content`).
- El calendario usa la semántica `grid` / `row` / `gridcell`, con filas en `display: contents` para conservar
  la rejilla CSS.

### D-41 · PWA
`manifest.webmanifest`, iconos generados con Pillow (incluido uno *maskable*) y un *service worker* escrito a mano
(`public/sw.js`, sin plugin): *app shell* y `/assets/*` con estrategia *cache-first*, navegación *network-first*
con la *shell* como respaldo sin conexión y nunca `/api` ni `/media` (datos personales). Solo se registra en el
*build* de producción.

### D-42 · Legibilidad de la navegación
Las etiquetas de la barra inferior usan 11 px (10 px con 5 pestañas) y no se recortan con puntos suspensivos;
las sub-pestañas no fuerzan mayúsculas para que «Entrenamientos» quepa en un móvil. Los números de los mensajes
motivacionales se formatean con el idioma activo (2,6 kg).

### D-43 · Imágenes *placeholder*
El seed usa una fuente TrueType del sistema si existe (DejaVu Sans o Arial); si no, la fuente integrada de Pillow,
que solo cubre ASCII, y se quitan los acentos del texto de la imagen.

### D-44 · Revisión de seguridad
`manage.py check --deploy` con los settings de producción no da avisos y se ejecuta en la CI
(`--fail-level WARNING`). Presupuestos de consultas (`tests/test_performance.py`) para dashboard, historial,
nutrición, ficha de usuario, plan del cliente y estadísticas, además de los de los listados.

## Despliegue (Fase 8)

### D-45 · Imágenes Docker multi-etapa
- **Backend.** Un solo `Dockerfile` con cuatro etapas: `base`, `dev`, `builder` y `prod`.
  - `dev` se usa con `docker-compose.yml`: dependencias de desarrollo, código montado y `runserver`.
  - `builder` genera los *wheels* de las dependencias de ejecución.
  - `prod` instala esos *wheels* sin compiladores, ejecuta `collectstatic` en el *build* (con una clave
    ficticia que solo sirve para importar los *settings*), corre como un usuario sin privilegios (uid 1000),
    tiene `HEALTHCHECK` sobre `/api/v1/health` y arranca gunicorn con `PORT` y `WEB_CONCURRENCY`.
- **Frontend.** Etapas `deps`, `dev`, `build` y `prod`. La URL de la API se fija en el *build*
  (`ARG VITE_API_URL`, `/api/v1` por defecto). `prod` es nginx 1.27 con `docker/nginx.conf`:
  - *fallback* de la SPA;
  - *proxy* de `/api` y `/media` a gunicorn;
  - `/assets/*` inmutable y `index.html` y `sw.js` sin caché;
  - cabeceras de seguridad;
  - 60 MB de cuerpo máximo (vídeos de 50 MB).

### D-46 · Stack de producción local
`docker-compose.prod.yml` reproduce producción en una máquina: nginx en `:8080`, gunicorn y PostgreSQL. Es solo
para pruebas:
- Funciona por HTTP, así que desactiva la redirección HTTPS y HSTS por variable de entorno
  (`SECURE_SSL_REDIRECT=0`, `SECURE_HSTS_SECONDS=0`; los valores por defecto de `prod.py` siguen siendo los
  seguros).
- Guarda la media en un volumen y la sirve Django con `SERVE_MEDIA=1`. Esa ruta solo existe si `DEBUG` es
  falso, `SERVE_MEDIA` está activo y no se usa GCS; en Render no se activa.

### D-47 · Render como Blueprint
`render.yaml` define tres recursos en Frankfurt:
- **API.** *Web service* Python con `rootDir: backend`.
  - Build: `pip install` y `collectstatic`. *Pre-deploy*: `migrate`. Arranque: gunicorn.
  - *Health check* en `/api/v1/health`.
- **Frontend.** *Static site* con *rewrite* de la SPA y cabeceras de caché.
- **Base de datos.** PostgreSQL 16 sin acceso externo (`ipAllowList: []`).

Detalles:
- **Se usan los *runtimes* nativos de Render en vez de las imágenes Docker:** los *builds* son más rápidos y
  los ficheros estáticos se publican en la CDN del *static site*. Las imágenes quedan para cualquier otro
  proveedor.
- **Plan `starter` para la API**, porque Render solo ejecuta `preDeployCommand` en instancias de pago. En el
  plan gratuito, el README explica cómo mover `migrate` al `startCommand`.
- **URLs literales en `VITE_API_URL` y `CORS_ALLOWED_ORIGINS`.** `fromService` solo expone el *host* interno
  o el nombre del servicio, no la URL pública `https://…onrender.com`. Si se cambia el nombre de un servicio
  hay que ajustarlas (lo indican el README y un comentario en `render.yaml`).
- **`RENDER_EXTERNAL_HOSTNAME`** (lo inyecta Render) se añade solo a `ALLOWED_HOSTS` y a
  `CSRF_TRUSTED_ORIGINS`, así que no hace falta conocer el dominio de antemano.
- **Secretos.** `DJANGO_SECRET_KEY` se genera (`generateValue`). `GS_BUCKET_NAME` y `GS_CREDENTIALS_JSON`
  se piden en el panel al crear el Blueprint (`sync: false`) y nunca están en el repositorio.

### D-48 · Verificación de Docker en la CI
Docker no está disponible en la máquina de desarrollo (D-02), así que el *job* `docker` de la CI:
- valida los dos ficheros Compose;
- construye las imágenes `prod` y levanta `docker-compose.prod.yml`;
- hace una prueba de humo a través de nginx:
  - `/api/v1/health` con la base de datos accesible;
  - `index.html` en `/` y en una ruta de la SPA;
  - el *manifest*;
  - un 401 en `/api/v1/me` sin sesión.

En local se verificaron los *settings* de producción sin Docker (gunicorn no funciona en Windows):
- `collectstatic` con whitenoise;
- `/api/v1/health` con las cabeceras de seguridad;
- el 400 ante un `Host` no permitido;
- los estáticos con *hash* servidos con caché inmutable.

### D-49 · Datos demo por defecto en desarrollo
`SEED_DEMO` vale `1` por defecto en `docker-compose.yml`, para que `docker compose up` deje la app lista para
probar con los usuarios demo. `seed_demo` es idempotente y se niega a ejecutarse con `DEBUG=False` salvo que se
pase `--allow-production`.


## Líneas futuras (Fase 9)

Se implementan las cuatro líneas futuras previstas, en su orden de prioridad. No se ha añadido nada de lo que
quedaba fuera (chat, 2FA, login social, traducción automática ni microservicios).

### D-50 · Recuperación de contraseña por email
- **Token.** Se usa el generador de Django (`default_token_generator`), sin modelo propio:
  - Es de un solo uso, porque el token depende del *hash* de la contraseña y del último inicio de sesión.
  - Caduca a los `PASSWORD_RESET_TIMEOUT_MINUTES` (60 por defecto).
  - El enlace es `FRONTEND_URL/reset-password?uid=…&token=…`.
- **Petición** (`POST /auth/password-reset`).
  - Responde siempre 204, exista o no la cuenta, para no revelar qué emails están registrados.
  - Las cuentas dadas de baja no reciben email.
  - Tiene límite propio de peticiones (`THROTTLE_PASSWORD_RESET`, 5/min).
  - Un fallo del servidor de correo se registra en el log, pero no cambia la respuesta.
- **Idioma del email.** Se elige con la cabecera `Accept-Language`, que la app envía siempre. Los textos
  (es/en/ca) están en `apps/accounts/emails.py` y no usan gettext, para no depender de `compilemessages`.
- **Envío.** Por defecto se usa el *backend* de consola, que escribe los emails en el log. Para enviarlos
  de verdad se configuran `EMAIL_BACKEND` y las variables SMTP.
- **Confirmación** (`POST /auth/password-reset/confirm`).
  - Aplica la misma política de contraseñas.
  - Cierra todas las sesiones (*blacklist* de los *refresh tokens*).
  - No inicia sesión: el usuario vuelve al login con un aviso de éxito.
- **Enlace en el login.** «¿Has olvidado tu contraseña?» aparece ahora que la función existe, como pedía
  la especificación.

### D-51 · Días de entrenamiento elegidos por el cliente
- **Dónde se guardan.** `UserDetails.training_days` es una lista de días de la semana (lunes = 0). Si está
  vacía se usa el reparto por defecto según los días semanales.
- **Dónde se usan.** El plan semanal, el calendario de Progreso y la cuenta atrás del próximo entrenamiento.
- **Cómo se eligen.** Desde el plan semanal (`PUT /me/training-days`), no en el formulario inicial, donde el
  campo es de solo lectura:
  - El número de días elegidos pasa a ser `weekly_training_days`, entre 1 y 6 (el mismo rango del formulario).
  - Enviar `[]` vuelve a los días recomendados.
- **Coherencia.** Si `weekly_training_days` cambia por otra vía (perfil, admin o formulario), los días
  elegidos ya no encajan. `UserDetails.save()` los descarta y se vuelve al reparto por defecto.
- **Personal.** Ve los días elegidos en la ficha del cliente.

### D-52 · Biblioteca de alimentos
- **Contenido.** Catálogo independiente (`Food`) con valores por 100 g:
  - obligatorios: kcal y macros;
  - opcionales: fibra, azúcares, grasas saturadas y nueve micronutrientes (`null` = dato desconocido).
- **No se vincula a los planes nutricionales.** En esta fase solo se pide el catálogo (los menús llegan con D-73).
- **Validaciones.**
  - Macros ≤ 100 g, azúcares ≤ carbohidratos y saturadas ≤ grasas.
  - Nombre único sin distinguir mayúsculas.
  - No se exige que las kcal cuadren con los macros (la tolerancia del 10 % entre calorías y macros es para los planes):
    con la fibra, el alcohol y los redondeos de las tablas, muchos alimentos reales se desvían más.
- **Permisos.**
  - Lectura: cualquier usuario autenticado, incluidos los clientes, que la consultan desde Nutrición.
  - Escritura: nutricionista y admin, desde Planes nutricionales.
  - El borrado es físico, porque nada referencia a un alimento.
- **Datos demo.** `seed_demo` carga 31 alimentos con valores aproximados de tablas de composición de
  referencia. La interfaz avisa de que son orientativos.
- **Conversión de nombres.** Para que nombres como `vitamin_a_ug` vuelvan bien desde el frontend,
  `toSnake` separa cada mayúscula (`vitaminAUg` → `vitamin_a_ug`). Antes se perdían las palabras de una
  sola letra.

### D-53 · Gamificación con insignias
- **Catálogo.** Ocho insignias fijas, definidas en código (`BadgeCode`). El frontend traduce su nombre y
  descripción por código.

  | Insignia | Se consigue al… |
  |---|---|
  | `first_workout` | Completar el primer entrenamiento |
  | `workouts_10`, `workouts_50`, `workouts_100` | Completar 10, 50 y 100 entrenamientos |
  | `perfect_week` | Hacer en una misma semana ISO (lunes a domingo) tantas sesiones como `weekly_training_days` |
  | `first_cycle` | Completar el plan entero una vez (`cycle` > 1) |
  | `weight_logs_10` | Registrar el peso 10 veces (cuenta el peso del formulario inicial) |
  | `goal_reached` | Alcanzar el peso objetivo; solo con los objetivos de perder peso o ganar músculo |

- **Cálculo y concesión.**
  - Se calculan a partir de datos existentes (`WorkoutSession`, `UserTrainingPlan.cycle`, `WeightRecord`
    y `UserDetails`).
  - Se guardan en `UserBadge` la primera vez que se cumple su condición.
  - No se retiran aunque la cifra baje después, por ejemplo al recuperar peso.
- **Cuándo se evalúan.**
  - Al completar un entrenamiento y al registrar el peso: la respuesta incluye `new_badges` y la app lo
    anuncia.
  - Al consultar `GET /me/badges`, lo que también concede las de clientes con historial previo, como los
    de la demo.
- **Dónde se ven.** En una tarjeta de Progreso › Control con enlace a la página de insignias. Así se
  conservan las tres sub-pestañas de Progreso que fija la especificación.


## Puesta en producción (Fase 10)

Fase 1 del plan de mejora: preparar la aplicación para tener usuarios reales. La guía de operación está en
[`OPERATIONS.md`](OPERATIONS.md).

### D-54 · Identificación del cliente en los límites de peticiones
- **El fallo.** Sin `NUM_PROXIES`, DRF identifica al cliente por la cabecera `X-Forwarded-For` completa, que
  el propio cliente puede escribir. Cambiándola en cada petición se esquivaban los límites de login, registro
  y contraseña.
- **El arreglo.** `NUM_PROXIES` vale `0` por defecto (se ignora la cabecera) y `1` detrás de Render y del nginx
  local. En ese caso se usa la dirección que añade el *proxy*.
- **Pendiente en staging.** Con el *rewrite* `/api/*` puede haber un salto más; `OPERATIONS.md` explica cómo
  comprobarlo y, si hace falta, poner `2`.

### D-55 · Auditoría y actualización de dependencias
- **Auditoría en la CI.**
  - `pip-audit` en el backend: falla con cualquier vulnerabilidad.
  - `npm audit` en el frontend: falla con las moderadas o peores en lo que se distribuye y solo con las
    críticas en las herramientas de desarrollo.
- **Aviso pendiente.** Hay uno moderado de `minimatch`, que llega a través de ESLint y solo afecta a las
  herramientas. La versión corregida tiene menos de dos semanas y exige un salto mayor, así que se deja para
  Dependabot.
- **Dependabot** propone actualizaciones de pip, npm, GitHub Actions y Docker con `cooldown` de 14 días, que es
  la misma regla del proyecto para fijar versiones. Se ha elegido en vez de Renovate porque no requiere
  instalar una app.

### D-56 · Monitorización de errores sin datos personales
- **Activación.** Sentry solo se activa con DSN: `SENTRY_DSN` en la API y `VITE_SENTRY_DSN` en el *build*.
  Sin DSN, el SDK del frontend ni siquiera entra en el *bundle*.
- **Sin datos personales.** Al tratarse datos de salud, no se envían datos del usuario, cuerpos de las
  peticiones, cookies, cabeceras de autenticación ni *query strings*, y se filtran los *tokens* de los enlaces
  de recuperación.
- **SDK del frontend.** Se usa `@sentry/browser` y no `@sentry/react`, cuyo *peer* opcional de react-router
  6–8 choca con el react-router 5 de Ionic. Los errores globales se capturan igual.
- **Disponibilidad.** Un *workflow* programado de GitHub comprueba `/health` (con la base de datos) y la web
  cada 15 minutos. No necesita cuentas externas.

### D-57 · Copias lógicas y restauración automatizada
- **Copia.** `backup_database` hace un `pg_dump` en formato *custom* a un bucket privado propio y conserva 14
  días.
- **Restauración de prueba.** `restore_drill` restaura la copia en una base temporal y compara las filas de
  cada tabla. Se ejecuta en cada CI (datos demo, imagen de producción) y se recomienda una vez al mes con una
  copia real.
- **Programación.** Un *cron* de Render, con la imagen Docker de producción, que ahora incluye el cliente de
  PostgreSQL 16 de PGDG: la misma versión mayor que el servidor, para que `pg_dump` y `pg_restore` sean
  compatibles. Es una capa independiente de las copias que hace Render en sus planes de pago.
- **Credenciales.** La cuenta de servicio de GCS se comparte entre la API y el *cron* con un grupo de
  variables de entorno (`entrenanutricion-gcs`).

### D-58 · *Refresh token* en una cookie httpOnly
- **Por qué.** Con el *refresh* en `localStorage`, un XSS podía robar sesiones de larga duración.
- **Cómo funciona.**
  - El *access token* sigue en memoria y en la cabecera `Authorization`.
  - El *refresh* va en la cookie `entrenanutricion_refresh`: `HttpOnly`, `Secure` (salvo en desarrollo),
    `SameSite=Lax` y `Path=/api/v1/auth/`.
  - Nunca vuelve en el cuerpo de una respuesta.
  - «Recordar sesión» la hace persistente (7 días); si no se marca, es de sesión del navegador.
- **CSRF.** Los endpoints que leen la cookie (`refresh` y `logout`) exigen `X-Requested-With: entrenanutricion`.
  Una página de otro sitio no puede enviarla sin la comprobación CORS. Con `Lax` ya no viajaría la cookie en
  una petición de otro sitio; la cabecera cubre los despliegues con `SameSite=None`.
- **Compatibilidad.**
  - Se sigue aceptando un `refresh` en el cuerpo, para versiones antiguas de la app y herramientas.
  - El frontend envía una sola vez el que hubiera en el almacenamiento y lo borra, así que nadie pierde la
    sesión con el cambio.
  - El *logout* responde siempre 204.
  - El cambio de contraseña conserva «Recordar sesión» leyendo la marca del *access token*.
- **Mismo sitio en Render.** La cookie con `Lax` exige que la web y la API compartan sitio. En Render se logra
  con un *rewrite* `/api/*` del *static site* hacia la API (`VITE_API_URL=/api/v1`): las cookies son de primera
  parte y no dependen del bloqueo de cookies de terceros de Safari. Plan B: dominios propios del mismo sitio.

### D-59 · Content-Security-Policy
- **Directivas.**
  - Solo scripts propios: el *build* no tiene scripts *inline* ni `eval`.
  - Estilos con `'unsafe-inline'`, porque Ionic los inyecta.
  - Imágenes y vídeos propios y de `storage.googleapis.com` (URLs firmadas).
  - `connect-src` propio más la ingesta de Sentry.
  - `frame-ancestors 'none'`, `object-src 'none'`, `base-uri` y `form-action` propios.
  - Junto a la CSP se añaden `Permissions-Policy`, `X-Frame-Options`, `nosniff` y `Referrer-Policy`.
- **Una sola fuente.** `frontend/security-headers.ts` se usa en `vite preview` y se replica en nginx y en
  `render.yaml`; un test verifica que las tres copias coinciden.
- **Comprobación.** Un E2E recorre el *build* de producción y falla ante cualquier violación de la CSP.
  Gracias a él se encontraron dos cosas:
  - **El `eval` de Zod.** Zod 4 comprueba si puede usar `Function` para compilar validadores. Se activa
    `jitless` en un módulo propio del que importan todos los esquemas; una regla de ESLint prohíbe importar
    `z` directamente.
  - **Las URLs de media.** El *proxy* de Vite cambiaba la cabecera `Host` (`changeOrigin`) y las URLs de los
    ficheros apuntaban al puerto del backend. Ahora se conserva, como en nginx.
- **Fallo previo de nginx.** Las `location` con su propio `add_header` no heredan las cabeceras del `server`,
  así que `/`, `/assets/` y `/sw.js` se servían sin cabeceras de seguridad. Ahora todas incluyen un fragmento
  común (`docker/security-headers.conf`) y la CI lo comprueba.

### D-60 · Protección de datos (RGPD)
- **Consentimientos.**
  - El registro pide aceptar términos y política de privacidad y, por separado y de forma expresa, el
    tratamiento de los datos de salud (art. 9.2.a).
  - Se guardan la versión de la política aceptada y las fechas.
  - Las cuentas creadas por un admin, o un cambio de versión de la política (`PRIVACY_POLICY_VERSION`),
    muestran al entrar un consentimiento bloqueante; la única alternativa es cerrar sesión.
- **Derechos.**
  - Exportación completa en JSON (`GET /me/export`): acceso y portabilidad.
  - El cliente puede eliminar su cuenta (`DELETE /me/account`, con contraseña). Se borra todo en cascada,
    también los ficheros. Se ha preferido el borrado real a la anonimización: es más sencillo de explicar y de
    cumplir. A cambio, las estadísticas dejan de contar a quien se va.
  - Las cuentas del personal las gestiona el admin.
- **Conservación.** Las bajas hechas por un admin quedan fechadas (`deactivated_at`) y se borran de verdad a
  los `ACCOUNT_RETENTION_DAYS` (365 por defecto, configurable) con `purge_inactive_accounts`, que se ejecuta
  cada noche tras la copia.
- **Política de privacidad.** Es una página pública en los tres idiomas. Los datos del responsable y del
  contacto se configuran por despliegue. **El texto es una plantilla que debe revisar un asesor**, junto con
  los contratos de encargado del tratamiento (`OPERATIONS.md`, apartado 5).
- **Datos demo.** `seed_demo` registra los consentimientos de los usuarios demo para que la demo no muestre la
  pantalla de consentimiento.


## Rendimiento y robustez (Fase 11)

Fase 2 del plan de mejora.

### D-61 · *Tree-shaking* de Ionic
- **El problema.** `@ionic/react` y `@ionic/core/components` no declaran que sus módulos carezcan de efectos
  secundarios al importarse. El *bundler* conservaba todos los componentes, también los que la app no usa:
  `ion-datetime`, los *pickers*, `ion-menu`, `ion-input-otp`…
- **Por qué es seguro declararlo.** Cada componente se registra al pintarse por primera vez
  (`defineCustomElement`). Se declaran sin efectos secundarios solo esos módulos de componentes, no el resto
  de `@ionic/core`.
- **Resultado.** El *chunk* de Ionic pasa de 296 a 224 kB comprimidos.
- **Verificación.** Toda la suite E2E se ejecuta sobre el *build* de producción. Lo que queda son los estilos
  de los dos modos (ios/md) y las utilidades comunes, que no se pueden quitar sin parchear la librería.

### D-62 · Páginas cargadas por rol
- **Qué.** Las páginas bajo `/app` se importan dinámicamente.
- **Cuándo se cargan.** Al entrar en la zona privada se cargan a la vez todas las páginas del rol (o del
  estado del cliente) y solo entonces se pintan las pestañas.
- **Por qué no `Suspense` en cada ruta.** Dentro del `IonRouterOutlet`, el cambio de la página de reserva a la
  real interfiere con las transiciones de Ionic.
- **Resultado.** El código propio de la carga inicial baja de 43 a 13 kB comprimidos, y un cliente nunca
  descarga los formularios de gestión. La carga antes del login baja de unos 425 a unos 323 kB.
- **Errores.** Si falla la carga, casi siempre porque un despliegue nuevo ha borrado los ficheros antiguos, se
  ofrece recargar.

### D-63 · E2E sobre el *build* de producción y sin animaciones
- **Movimiento reducido.** La app desactiva las animaciones de Ionic si el usuario pide movimiento reducido
  (`prefers-reduced-motion`). Es una mejora de accesibilidad en sí misma.
- **Playwright** emula esa preferencia: no hay transiciones que esperar y la suite pasa de unos 5 a unos 3
  minutos.
- **`E2E_PREVIEW=1`** construye la app y la prueba con `vite preview`, con las cabeceras y la CSP de
  producción. La CI ejecuta así toda la suite. En local, sin la variable, se sigue usando el servidor de
  desarrollo.

### D-64 · Imágenes recodificadas al subirlas
- **Qué se hace.** Las fotos de perfil (512 px) y las imágenes de ejercicios, entrenamientos y planes
  (1600 px) se guardan en WebP:
  - antes se aplica la orientación EXIF;
  - después se descartan todos los metadatos, que pueden incluir la posición GPS y el dispositivo;
  - los vídeos no se tocan.
- **Sin miniaturas aparte.** Ninguna pantalla muestra listas de miniaturas: las imágenes aparecen en
  avatares, portadas y el carrusel de detalle. Con el tamaño acotado basta, y no hacen falta campos ni
  ficheros adicionales.
- **Imágenes ya subidas.** No se reprocesan.

### D-65 · Prueba de carga con k6
- **Escenario.** `load/smoke.js`: 20 clientes virtuales durante 30 s recorren las pantallas principales a
  través de nginx, gunicorn y PostgreSQL, con los datos demo.
- **Umbrales.** Menos de un 1 % de errores y percentil 95 por debajo de 800 ms.
- **Sesión.** Inicia sesión una sola vez, porque el login tiene límite de peticiones.
- **Dónde.** Se ejecuta en el *job* `docker` de la CI. Es una prueba de humo para detectar regresiones de
  rendimiento, no una medida de capacidad; para dimensionar producción, hay que repetirla contra *staging*
  con más usuarios.

### D-66 · Entrenamiento sin conexión
- **Copias locales.** El plan, los entrenamientos y las fichas de ejercicio que el cliente abre se guardan en
  `localStorage`, separados por usuario. Sin red se muestra la última copia con un aviso.
- **Cola de marcas.** Las marcas de «hecho» sin red se guardan en una cola (la última por ejercicio) y se
  envían al volver la conexión. Si la API rechaza una (entrenamiento ya completado, plan cambiado…), se
  descarta.
- **Completar el entrenamiento requiere conexión,** porque crea la sesión, actualiza el progreso y concede
  insignias.
- **La sesión resiste una recarga sin red.** Se abre la app con el último usuario conocido y la sesión se
  refresca al volver la conexión. Solo se cierra si el servidor responde que ha caducado.
- **Privacidad.**
  - Las copias se borran al cerrar sesión y cuando entra otra persona en el mismo dispositivo.
  - El *service worker* sigue sin guardar respuestas de la API.
  - La política de privacidad lo explica.

### D-67 · Series reales y récords personales
- **Qué se registra.** Por cada serie, las repeticiones y, en los ejercicios con carga, los kilos (de 0 a 500,
  con un decimal), hasta 20 series por ejercicio. Se guardan con la marca del ejercicio
  (`ExerciseCompletion.sets`) y, al completar el entrenamiento, pasan a `ExerciseSet` (una fila por serie).
- **Sin series registradas** se guardan las planificadas, sin carga: el historial y las estadísticas siguen
  siendo comparables.
- **Migración.** Los registros anteriores reciben sus series planificadas y `ExerciseLog.reps_completed` pasa a
  ser el total de repeticiones de la sesión (antes eran las de cada serie).
- **Récord:** la serie más pesada (a igualdad de kilos, la de más repeticiones). Solo se anuncia («¡Nuevo
  récord!») si supera una marca anterior con carga; la primera sesión con kilos no cuenta como récord.
- **1RM estimado** con la fórmula de Epley (`kg × (1 + reps / 30)`; con una repetición, el propio peso). Es
  una orientación y así se indica.
- **Ayuda al registrar.** El editor se rellena con las series del plan y los kilos de la última sesión del
  ejercicio («Última vez: …»). Guardar las series marca el ejercicio como hecho. Sin conexión, la marca y las
  series entran en la cola de D-66 (una marca posterior sin series conserva las ya anotadas).

### D-68 · Panel de adherencia para el personal
- **Ventana de 28 días**, o desde el inicio del plan si es posterior. Se comparan los **días entrenados** (dos
  entrenos el mismo día cuentan uno) con los **días programados** por el calendario semanal del cliente
  (elegido o por defecto). Hoy solo cuenta como programado si el cliente ya ha entrenado, porque el día no ha
  terminado.
- **Estados.**
  - *Inactivo:* 7 días o más sin entrenar, contados desde el último entreno o desde la asignación.
  - *En riesgo:* adherencia por debajo del 60 %.
  - *Al día:* el resto.

  Se ordena del peor al mejor, y el recuento por estado no depende del filtro.
- **Variación de peso** frente al último registro de hace 28 días o más (o, si no hay, el peso inicial).
- **Coste.** Se calcula con un número fijo de consultas para todos los clientes con plan y se pagina en
  memoria. Vale para cientos de clientes; con miles convendría precalcularlo.
- Todo el personal ve a todos los clientes (no hay cartera por profesional), igual que en `/users`.

### D-69 · Notas asíncronas en lugar de chat
- **Un hilo por cliente**, compartido por todo el equipo: el cliente escribe «a su equipo» y responde quien
  corresponda. Cada nota guarda una copia del nombre y del rol del autor, para que el hilo se pueda leer aunque
  se borre la cuenta del profesional.
- **Leído por lado.** Al abrir el hilo, el cliente marca como leídas las notas del equipo. Cualquier
  profesional marca como leídas las del cliente, y quedan leídas para todo el equipo (bandeja «Notas sin leer»
  en Usuarios).
- **No es tiempo real.** No hay WebSockets ni sondeo: los avisos se actualizan al entrar en las vistas. Se
  descarta un chat porque cuesta más (infraestructura, moderación, expectativa de respuesta inmediata) para un
  uso que es asíncrono.
- **Límites.** 2000 caracteres. Escribir tiene un límite de peticiones (`THROTTLE_NOTES`, 30 por minuto);
  leer, no. Las notas necesitan conexión.
- **RGPD.** Entran en la exportación y se borran con la cuenta del cliente.

### D-70 · Hora de entreno y recordatorios por email
- **Hora de entreno por cliente** (`UserDetails.training_time`). Si no elige ninguna, se usa
  `DEFAULT_TRAINING_TIME`. La usan la cuenta atrás del próximo entreno y los recordatorios.
- **Recordatorios opcionales**, desactivados por defecto. El *cron* `send_training_reminders` se ejecuta cada
  hora y envía como mucho uno al día por cliente. Lo envía en los `REMINDER_LEAD_MINUTES` (60) anteriores a su
  hora, y solo si ese día le toca entrenar, tiene un entrenamiento pendiente y aún no ha entrenado.
- **Una vez al día**, gracias a `last_reminder_on`. Si el envío falla, no se marca y se reintenta a la hora
  siguiente (si sigue dentro de la ventana).
- **Solo a direcciones confirmadas** (D-72).
- **Sin notificaciones *push*.** Requieren el permiso del navegador, claves VAPID y un servicio de envío; el
  email cubre el caso con menos piezas.

### D-71 · Idioma guardado en la cuenta
- `User.language` (es, en o ca) permite escribir los emails en el idioma de cada usuario.
- Se actualiza al iniciar sesión (cabecera `Accept-Language`), al cambiar de idioma en la app
  (`PATCH /me/profile`, desde `useAccountLanguage`) y al guardar los recordatorios.

### D-72 · Verificación del correo
- **Solo la necesitan las cuentas autorregistradas.** Las que crea un administrador y las que ya existían
  (migración de datos) se consideran verificadas.
- **Enlace firmado** con `django.core.signing`, que identifica la cuenta y su dirección. Caduca a los 7 días
  (`EMAIL_VERIFICATION_MAX_AGE_DAYS`) y abrirlo de nuevo no cambia nada. El reenvío está limitado a 3 por hora.
- **No bloquea el uso.** Un aviso pide confirmar la dirección, pero el cliente puede seguir con el formulario
  y con su plan. Lo único que exige una dirección confirmada son los recordatorios.
- **Restablecer la contraseña** desde el email también confirma la dirección, porque el enlace llegó a ella.

### D-73 · Un menú de ejemplo de un día por plan
- **Un día, no una semana.** El plan define objetivos diarios, así que un día tipo basta para mostrarlos con
  alimentos reales. Un menú semanal multiplicaría por siete el trabajo del nutricionista; la lista de la
  compra multiplica el día (D-74). Si hiciera falta variedad, se podría añadir el día de la semana a
  `MealPlanItem` sin cambiar el resto.
- **Valores en vivo.** Las calorías y los macros salen de la biblioteca: si el nutricionista corrige un
  alimento, cambian todos los menús que lo usan. Por eso un alimento que está en algún menú no se puede borrar
  (`409 food_in_use`, con los planes), igual que un entrenamiento en uso.
- **Guardar no exige cuadrar.** Las calorías del menú se comparan con las del plan (±10 %, como en los planes) y
  la desviación se muestra en vivo, pero se puede guardar un borrador fuera del objetivo. La referencia para
  el cliente siguen siendo los objetivos declarados del plan.
- **Demo.** Tres plantillas (pérdida de peso, ganancia muscular y mantenimiento) que se escalan a las calorías
  de cada plan, en múltiplos de 5 g. Los macros quedan aproximados.

### D-74 · Lista de la compra a partir del menú
- **Contenido.** Son los alimentos del menú multiplicados por los días elegidos (1, 3, 7 o 14), agrupados por
  la categoría de la biblioteca y en crudo, como en el menú.
- **Marcas en el dispositivo.** Lo que el cliente ya ha comprado se guarda con sus copias sin conexión
  (`offlineStore`), así que se borra al cerrar sesión y no viaja al servidor: es una comodidad de quien está
  comprando.
- **Sin conexión.** Funciona con la última copia, como el plan (D-66).
- **Compartir.** Con la Web Share API del móvil, o copiándola al portapapeles si no está disponible. Solo se
  comparten los productos que faltan.

### D-75 · Diario de comidas con los valores copiados
- **Cada anotación copia** el nombre del alimento y los valores de la ración en el momento de anotarla. El
  historial no cambia si el nutricionista corrige o borra el alimento después (`food` pasa a `null`).
  Cambiar los gramos escala los valores copiados.
- **Solo alimentos de la biblioteca**, sin alimentos libres, para que los valores sean fiables. Si falta
  alguno, lo añade el nutricionista.
- **Copiar del menú** una comida o el día entero es la forma rápida de anotar lo previsto y ajustar después.
- **Límites.**
  - No se anotan días futuros.
  - Las raciones van de 1 a 2000 g.
  - Se necesita conexión: el diario no usa la cola sin conexión, para no complicarla con altas y bajas.
- **Objetivos:** los del plan actual, también al mirar días pasados (simplificación).
- **Personal y RGPD.**
  - El personal ve el resumen de los últimos 7 días en la ficha del cliente.
  - El diario entra en la exportación y se borra con la cuenta.
  - Son datos de hábitos alimentarios del cliente, que cubre el consentimiento de datos de salud. La política
    de privacidad lo menciona.

### D-76 · Catálogo en tres idiomas
- **El español es el texto base.** Los campos de siempre (`name`, `description`…) guardan el texto en español.
  Cada elemento del catálogo tiene además un JSON `translations` con el inglés y el catalán, que son
  opcionales. Se traducen:
  - los ejercicios: nombre, descripción, técnica, errores comunes, beneficios y pasos (como lista);
  - los entrenamientos, los planes de entrenamiento y los planes nutricionales: nombre y descripción;
  - los alimentos: el nombre.

  Los grupos musculares ya se traducían en la app por su clave.
- **Se elige JSON y no una columna por idioma** (o una librería como django-modeltranslation): no hay
  migraciones por idioma, y sin traducción se muestra el español, campo a campo y paso a paso.
- **Cada respuesta va en el idioma de la petición.** `LocaleMiddleware` activa el idioma de `Accept-Language`,
  que la app envía siempre. Así salen las pantallas del cliente, el catálogo del personal, los récords, la
  adherencia, las referencias a planes, las estadísticas, los conflictos de borrado y el menú, la lista de la
  compra y el diario. El email de recordatorio usa el idioma de la cuenta (D-71). La app vuelve a pedir los
  datos al cambiar de idioma.
- **Edición.** El personal recibe `translations` con los tres idiomas (`es` incluido) para editar, y envía
  `en` y `ca`. El servidor valida los idiomas, los campos y las longitudes (errores en `translations.<idioma>.<campo>`)
  e ignora los textos vacíos. Los formularios tienen una sección «Traducciones» con el texto en español como
  referencia, y avisan si hay errores en el idioma que no se está viendo.
- **Búsqueda y orden.** Las listas buscan en todos los idiomas y se ordenan por el nombre en el idioma de la
  petición.
- **Copias guardadas.** El nombre del entrenamiento de una sesión y el del alimento del diario se guardan en
  español. Si el elemento sigue existiendo, se muestran traducidos; si no, la copia.
- **Demo.** Todo el catálogo de demostración está traducido (`apps/core/demo_translations.py`) y un test
  comprueba que no falta nada. Las imágenes de muestra de los ejercicios llevan el nombre en español dibujado.

### D-77 · App instalada y ramas en inglés
- **App instalada.** Hay un `manifest` por idioma (es, en, ca) con su descripción. La app cambia el enlace al
  `manifest` y la descripción de la página al cambiar de idioma. Un test los mantiene iguales en lo demás.
- **Ramas.** Las ramas de fase pasan a tener el nombre en inglés, como los *commits* y el resto de ramas
  (`phase/N-name`). Las que ya existían se renombraron solo en local: en GitHub solo está `main`.

## Endurecimiento de seguridad (Fase 15)

La auditoría de seguridad del 6 de noviembre de 2026 dio un riesgo medio: ningún hallazgo crítico ni alto,
13 medios y 18 bajos. Esta fase corrige los que dependen del código y de la configuración. Los que dependen
de cuentas externas (SMTP, cuentas de servicio de GCS, ajustes de GitHub) están en `OPERATIONS.md`.

### D-78 · Subidas limitadas por píxeles, tamaño y ritmo
- **Píxeles.** Una imagen pequeña y muy comprimida puede ocupar gigabytes al decodificarse. Se rechaza a
  partir de 40 megapíxeles (`MAX_IMAGE_PIXELS`), al validarla y al recodificarla, con el código
  `image_too_large`. Pillow trata su aviso de imagen sospechosa como error, y las JPEG grandes se decodifican
  a escala reducida (`draft`) antes de redimensionarlas.
- **Tamaño de la petición.** Un *middleware* rechaza con `413 request_too_large` los cuerpos mayores que el
  vídeo más grande permitido más 1 MB, antes de leerlos. Sin él, el cliente podría enviar gigabytes antes de
  que el *serializer* mirase el tamaño.
- **Ritmo.** Las peticiones con ficheros (multipart) tienen su propio límite por usuario: 100 por hora
  (`THROTTLE_UPLOADS`).
- **Ficheros servidos por Django** (solo el stack local): `nosniff`, y los que no son imágenes se descargan
  (`attachment`) en lugar de abrirse.
- **Frontend.** Los formularios muestran el error de cada fichero en su sitio, y un reintento tras un error
  de subida no vuelve a crear el elemento.

### D-79 · Límites de peticiones compartidos y por cuenta, y contraseñas
- **Contadores compartidos.** Los límites se guardan en una caché en la base de datos (tabla `django_cache`,
  creada por una migración), común a los 3 procesos de gunicorn. Antes cada proceso contaba por su cuenta y
  cada límite valía el triple. Los tests usan una caché en memoria.
- **Fallos de inicio de sesión por cuenta:** 10 por hora (`THROTTLE_LOGIN_ACCOUNT`), vengan de la IP que
  vengan, además del límite por IP. D-88 lo cambia a un recuento por cuenta e IP, con un tope total.
  - Un acierto pone el contador a cero.
  - Un email que no existe cuenta igual, para no revelar qué cuentas existen.
  - La caché guarda un *hash* del email, no la dirección.
- **`/auth/email-exists`** se mantiene (lo usa el registro) con 10 peticiones por minuto en lugar de 60.
- **Contraseñas.** Además de las reglas de longitud y caracteres, se rechazan las 20 000 más comunes
  (`password_too_common`) y las que se parecen al nombre, los apellidos o el email (`password_too_similar`),
  en el registro, las altas del admin, el cambio y la recuperación.

### D-80 · La sesión termina al cambiar la contraseña
- **Antes**, cambiar o recuperar la contraseña invalidaba los *refresh tokens*, pero los *access tokens* ya
  emitidos seguían valiendo hasta 15 minutos.
- **Ahora** la cuenta guarda `password_changed_at`, y la autenticación (`SessionJWTAuthentication`) rechaza
  los *tokens* emitidos antes de ese momento.
- **El *refresh* solo se lee de la cookie.** Se elimina el `{"refresh": "…"}` en el cuerpo que se aceptaba
  por compatibilidad: era una vía sin la protección CSRF de la cookie. El frontend borra el *token* antiguo
  de `localStorage` si lo encuentra.
- **Admin de Django y documentación de la API apagados en producción** (`ADMIN_ENABLED`, `API_DOCS_PUBLIC`).
  La app y los comandos gestionan todo; el admin era un objetivo de fuerza bruta con acceso a datos de salud.
  Un entorno de *staging* puede activarlos.

### D-81 · Producción: claves, emails, logs y datos demo
- **Claves.** Producción no arranca con una `DJANGO_SECRET_KEY` vacía, corta, repetitiva o publicada en el
  repositorio (prefijos `dev-`, `local-`, `test-` o textos como `change-me`).
  - El mínimo es de 32 caracteres, no los 50 que sugiere el *check* de despliegue de Django: las claves que
    generan las plataformas (`generateValue` de Render) pueden ser más cortas y son aleatorias.
  - `JWT_SIGNING_KEY` (opcional) firma las sesiones con una clave propia: cambiarla cierra todas las
    sesiones sin tocar la otra.
  - El *build* de la imagen usa una clave aleatoria desechable, y el stack de producción local exige la suya.
- **Emails.** En producción el valor por defecto es SMTP, y se rechazan los *backends* que no envían (consola,
  fichero, memoria): los enlaces de recuperación y confirmación quedarían en los logs. Un entorno de pruebas
  puede usarlos con `ALLOW_CONSOLE_EMAIL=1`.
- **Logs de acceso** (gunicorn, en `backend/gunicorn.conf.py`, y nginx): método, ruta sin la parte tras «?»,
  estado, tamaño y tiempo. Sin la *query string* (búsquedas por nombre, el email de `email-exists`), sin el
  *referer* (las páginas de recuperación llevan su *token* en la URL) y sin el navegador.
- **Respuestas de la API** con `Cache-Control: no-store`: ningún navegador ni *proxy* guarda copias de datos
  personales.
- **Datos demo.** Fuera de desarrollo, `seed_demo --allow-production` exige `DEMO_PASSWORD`, que no puede ser
  la del README (abriría todas las cuentas demo, una de ellas de admin).
- **Recordatorios.** El nombre del entrenamiento, que escribe el personal, va al asunto en una sola línea,
  sin caracteres de control ni invisibles y con 80 caracteres como máximo. Un salto de línea hacía que Django
  rechazase el email entero.

### D-82 · Copias con su propia cuenta de servicio
- **Antes**, la API y el *cron* de copias compartían la cuenta de servicio de GCS: quien obtuviera la clave
  de la API podía leer y borrar las copias, que contienen datos de salud.
- **Ahora** las copias usan `GS_BACKUP_CREDENTIALS_JSON`, una cuenta que solo puede crear objetos en el bucket
  de copias (`roles/storage.objectCreator`). Nunca se usa la de los ficheros.
- **Retención en el bucket.** Con `BACKUP_PRUNE=0` el *job* no borra: lo hace una regla de ciclo de vida del
  bucket a los 14 días, y una política de retención impide borrarlas antes.
- **Purga con sus ficheros.** El *cron* nocturno borra las cuentas caducadas, pero no tenía `USE_GCS`: las
  fotos de perfil de esas cuentas se quedaban en el bucket. Ahora usa el mismo almacenamiento que la API.

### D-83 · Registro de accesos a los datos de salud
- **Decisión.** El personal sigue viendo los datos de salud de los clientes (los necesita para preparar los
  planes), y cada acceso queda registrado (`HealthDataAccess`).
- **Qué se guarda:** quién (con su rol y nombre, por si su cuenta se borra), a quién y cuándo. Nunca los
  valores.
- **Cuándo:** cada vez que la API muestra a un profesional la ficha de un cliente con su formulario inicial
  (`/users/{id}`, también en las respuestas de las ediciones del admin). El listado no muestra datos de
  salud y no se registra.
- **Quién lo ve:**
  - los admins, en `GET /users/{id}/health-data-accesses`;
  - el cliente, en la descarga de sus datos (art. 15.1.c del RGPD: los destinatarios).
- **Conservación:** se borra con la cuenta del cliente. La política de privacidad lo menciona; no se sube su
  versión, porque no cambia ningún tratamiento.
- **Pendiente:** no hay pantalla en el frontend; el registro se consulta por la API.
- **Ampliado en D-88:** una fila por profesional, cliente y hora, y también las notas y el resumen del diario.
- **Ampliado en D-91:** la adherencia (lista y ficha) muestra el peso, que también es un dato de salud: se
  registran los clientes de la página que lo muestran.
- **No depende del rol:** se registra aunque la cuenta ya no sea de cliente. Antes, un admin podía cambiar el
  rol, ver los datos sin dejar rastro y devolverlo. La cuarta auditoría lo detectó.

### D-84 · Frontend: sesión caducada, `returnTo` y *service worker*
- **Sesión caducada.** Al caducar, se borran del dispositivo las copias para usar sin conexión, igual que al
  cerrar sesión. Para volver a entrar hace falta red, y entonces se descargan otra vez. Las marcas pendientes
  de enviar se pierden (ya se perdían: el envío recibía un 401 y las descartaba).
- **`returnTo`** solo acepta rutas de la app (`/app/…`): ni otros sitios (`//…`, `/\…`), ni `javascript:`,
  ni rutas con `..`, `?` o `#`.
- **Service worker** (v3): solo guarda en caché los scripts, estilos, fuentes e imágenes de `/assets/`, y solo
  si el servidor responde con uno de esos tipos. Si falta un fichero, un *host* puede responder con
  `index.html`, que antes se habría guardado como un script para siempre. Al actualizarse borra las cachés
  anteriores.

### D-85 · Cadena de suministro y despliegue
- **Dependencias de Python con *hashes*.** `requirements.in` y `requirements-dev.in` fijan las directas;
  `requirements.txt` y `requirements-dev.txt` son *locks* generados con `uv pip compile --generate-hashes`,
  con todas las dependencias (también las indirectas) y el *hash* de cada fichero. Docker, Render y la CI
  instalan con `--require-hashes`.
- **Imágenes por *digest*:** python 3.12.16, node 24.22.2, nginx 1.30.6, postgres 16.15 y k6 2.2.0. Dependabot
  propone las nuevas (también en los ficheros de *compose*).
  - Se pasa a nginx 1.30, la rama estable. La 1.27 era una versión de desarrollo sin actualizaciones desde
    abril de 2025.
  - La clave del repositorio de PostgreSQL solo se acepta si tiene la huella publicada en postgresql.org.
- **CI.** El *token* de los *jobs* solo puede leer, `checkout` no lo guarda (`persist-credentials: false`) y
  las acciones están fijadas por SHA. El *job* `docker` genera al vuelo la clave secreta y la contraseña demo.
- **Imágenes.** `.dockerignore` deja fuera los `.env*`, las claves, `.git` y los tests.
- **Local.** `docker compose` publica los puertos solo en `127.0.0.1`. nginx no muestra su versión y pasa las
  mismas cabeceras de *proxy* en `/media` que en `/api`.
- **HSTS** en el *static site* de Render (`STRICT_TRANSPORT_SECURITY` en `security-headers.ts`, con test). No
  va en nginx ni en `vite preview`, que sirven HTTP en local.

### D-86 · Qué actualiza Dependabot y qué se planifica
- **Revisión de las primeras propuestas** (6 de noviembre de 2026): se aceptan las acciones de GitHub en su
  versión 7 (SHA comprobado, más de dos semanas, CI en verde) y sentry-sdk 2.73. Se cierran los saltos de
  versión mayor que exigen un plan.
- **Se planifican, y Dependabot no los propone:**
  - Django 6: la 5.2 es LTS hasta abril de 2028, y el salto será a la 6.2 LTS (abril de 2027);
  - Ionic 9, react-router 6 y React 19: solo funcionan juntos (cada PR por separado falla) y merecen una
    migración propia;
  - las versiones menores y mayores de Python y las mayores de Node: cambian a la vez en la imagen, la CI y
    Render (y en el *lock*, en el caso de Python);
  - PostgreSQL 17 o superior: la base de Render y el `pg_dump` de la imagen son la 16, y el paso es una
    migración con `pg_upgrade`;
  - las versiones menores de nginx: las impares son su rama de desarrollo, y la siguiente estable se sube a
    mano;
  - TypeScript 7: `typescript-eslint` 8.72 solo admite TypeScript menor que 6.1, y su PR no llega a instalar
    las dependencias. Se sube cuando `typescript-eslint` la admita.
- **Revisión del 16 de noviembre de 2026**: se aceptan el grupo de versiones menores del frontend y
  `@hookform/resolvers` 7 (solo cambia el validador de TypeBox, y la app usa el de Zod). Se cierra
  TypeScript 7.
- **Sus PR de Python rehacen los *locks* solo para Linux**: quitaban los paquetes que solo usa Windows. Por
  eso `tzdata` y `colorama` se fijan en los `.in`. Aun así, antes de aceptar una de esas PR se regeneran los
  *locks* con `uv` (comando del README).

### D-87 · Peticiones simultáneas, datos acotados y tiempo de la recuperación
Los hallazgos de la auditoría que no entraron en el primer plan de la fase.
- **Doble envío.** Dos peticiones iguales a la vez ya no dan un 500:
  - el formulario inicial bloquea la fila de la cuenta, y la segunda petición encuentra el formulario
    hecho (`409 onboarding_already_completed`);
  - el alta de una cuenta convierte el choque con el índice único del email en el mismo error del
    formulario (`400 email_taken`);
  - las imágenes de un ejercicio bloquean el ejercicio, y el máximo de 10 se respeta aunque lleguen dos a la
    vez.

  Los tests lo prueban con dos peticiones reales en hilos distintos (`tests/concurrency.py`).
- **Datos por usuario acotados.**
  - Los pesos se pueden anotar para los últimos 5 años (`date_too_old`): la serie no crece sin fin.
  - El diario admite 60 anotaciones por día (`409 food_log_day_full`); «copiar el menú» añade todas o
    ninguna.
  - Los récords los calcula la base de datos (una fila por ejercicio) en lugar de cargar todas las series.
    Ante un empate en el peso y las repeticiones, cuenta el primer día.
- **Recuperación de contraseña.** El email se envía en un hilo, después de responder
  (`apps/core/background.py`). Antes la petición tardaba más cuando la cuenta existía, porque esperaba al
  servidor de correo, y eso revelaba qué emails están registrados. Los tests lo ejecutan en el momento
  (`BACKGROUND_TASKS_INLINE`).
- **nginx sin root.** La imagen del frontend pasa a `nginxinc/nginx-unprivileged`, la variante oficial que
  corre como el usuario `nginx`, en el puerto 8080.
- **Copias cifradas.** Se cifran con una clave gestionada en Google Cloud (CMEK) en el bucket de copias, que
  es configuración externa (`OPERATIONS.md`). La app no las cifra por su cuenta.
- **Queda abierto:** la adherencia que ve el personal se calcula en memoria para todos los clientes con plan.
  Es un problema de rendimiento con muchos clientes, no de seguridad, y se revisará si crece el número de
  clientes.

### D-88 · Segunda auditoría: inicio de sesión, personal y despliegue
La segunda auditoría (puntuación 29/100, antes 57/100, sin hallazgos críticos ni altos) encontró un fallo
de diseño en D-79: con un límite solo por cuenta, cualquiera podía bloquear una cuenta conocida.
- **Fallos de inicio de sesión por cuenta e IP.** 10 por hora y por IP (`THROTTLE_LOGIN_ACCOUNT`), con un tope
  total de cinco veces eso por cuenta (50). Una sola máquina solo se bloquea a sí misma, y un ataque repartido
  sigue teniendo tope. Un acierto o una contraseña nueva ponen la cuenta a cero. La caché guarda solo *hashes*.
- **Contraseñas de 128 caracteres como máximo**, en la API y en los formularios.
- **Renovar y cerrar la sesión tienen límite** (`THROTTLE_SESSION`, 120/min por IP). Es generoso porque una IP
  puede ser una oficina entera.
- **La app solo cierra la sesión si la API la rechaza** (401 o 403). Con un 429, un 5xx o sin red, sigue abierta y
  conserva las copias del dispositivo.
- **Entrenadores y nutricionistas solo ven clientes** en `/users`; el perfil de un compañero responde 404. Esto
  sustituye a la especificación inicial, que les dejaba ver a todos los usuarios. Los entrenadores siguen viendo
  las condiciones médicas de los clientes (D-83).
- **Registro de accesos:** como mucho una fila por profesional, cliente y hora, y cubre también las notas y el
  resumen del diario. La adherencia sí muestra el peso: se registra desde D-91.
- **Descarga de datos:** 5 por hora y usuario (`THROTTLE_DATA_EXPORT`).
- **Versiones exactas** de Python (3.12.16) y Node (24.22.2) en la imagen, la CI y Render.
- **Solo *wheels*** al instalar Python (`--only-binary=:all:`): compilar desde el código fuente descargaría sus
  herramientas sin *hashes*.
- **La CI comprueba la huella** de la clave de PostgreSQL, como ya hacía el Dockerfile.
- **Identificadores SQL** de las herramientas de copias con `psycopg.sql.Identifier`.
- **Descartado, con motivo:**
  - detectar la reutilización del *refresh*: dos pestañas que refrescan a la vez parecerían un robo y cerrarían
    la sesión sin motivo, y el *token* ya va en una cookie httpOnly;
  - un contador de fallos atómico: exigiría una tabla nueva para evitar unos pocos intentos de más, que el
    límite por IP ya acota;
  - un tope de notas por cliente: acabaría cortando su conversación con el equipo, y escribir ya está limitado;
  - separar la copia y la purga en dos *crons*: cuesta otra instancia y las credenciales ya están separadas.

### D-89 · Tercera auditoría: pestañas, emails por dirección y últimos ajustes
La tercera auditoría dio 24/100, sin hallazgos críticos ni altos y sin hallazgos medios en el código de la app. Se
corrigen los que afectan a los usuarios o cuestan poco, y aquí termina el trabajo de la auditoría en el código.
- **Dos pestañas abiertas.** Si renuevan la sesión a la vez, la API rota la cookie para la primera y rechaza la
  segunda. La app reintenta una vez, un segundo después, con la cookie que acaba de recibir la otra pestaña. Antes
  se cerraba la sesión y se borraban las copias del dispositivo.
- **Emails de recuperación:** como mucho uno cada 2 minutos por dirección, sea cual sea la IP. La respuesta no cambia.
- **Diario:** se anota solo en los últimos 5 años (`date_too_old`), igual que los pesos. Se pueden seguir leyendo
  días más antiguos.
- **Clave de PostgreSQL:** en la imagen y en la CI debe ser la única clave del fichero.
- **npm** no ejecuta scripts de instalación (`frontend/.npmrc`). El único paquete que tiene uno, `fsevents`, es
  exclusivo de macOS.
- **No se corrige:**
  - lo que depende del despliegue: la prueba de `NUM_PROXIES` y TLS hacia la base de datos;
  - lo que aporta poco: tabla de caché propia, límite de píxeles más bajo, versiones de `pip` y `apt`, *digests* de
    la CI (se actualizan a mano), o el código de la imagen en propiedad de su usuario;
  - el bloqueo de una cuenta por un ataque repartido, que es el compromiso aceptado en D-88.

### D-90 · Aplicación más visual: un estilo para los gráficos
La persona responsable pidió una aplicación más visual, con más gráficos. Se añaden en las pantallas que eran
listas de cifras, con unas reglas comunes:
- **La forma según el dato.**
  - Una cifra destacada es una tarjeta con icono, no un gráfico.
  - La evolución en el tiempo va en barras o líneas, y el reparto entre pocas partes en un donut.
  - Comparar muchas categorías (músculos, ejercicios, planes) va en barras horizontales ordenadas. Un donut con
    doce porciones no se lee.
  - El avance hacia un objetivo va en un anillo.
- **Un solo eje.** Nunca dos escalas en el mismo gráfico. Los minutos de cada semana van en la descripción de
  la barra, no en un segundo eje.
- **Colores.**
  - Los de estado (al día, en riesgo, inactivo; activo, pendiente) van siempre con su nombre o un icono.
  - Las categorías sin estado (los objetivos) usan los tres primeros colores de una paleta validada para el
    daltonismo en claro y en oscuro (`--en-series-*`). El verde agua no llega a 3:1 sobre blanco, así que su
    donut lleva el nombre y el valor en la leyenda.
- **Marcas discretas.**
  - Barras finas, redondeadas solo en el extremo, y rejilla fina solo en el eje de valores.
  - Fechas en horizontal: se saltan etiquetas antes que inclinarlas.
  - Los nombres largos se acortan en el eje, pero salen completos en la descripción emergente.
- **Accesibilidad.** Cada gráfico tiene una etiqueta y repite sus valores en una tabla oculta para lectores de
  pantalla. Los anillos son SVG con etiqueta.
- **Datos nuevos solo donde hacía falta.**
  - Estadísticas de entrenamiento del cliente (12 semanas y músculos), en tres consultas.
  - La semana y la racha en el panel. La racha cuenta las semanas del plan actual con todas las sesiones
    previstas hechas; la semana en curso suma al completarse y, mientras tanto, no la rompe.
  - Distribución y media de la adherencia.
  - Tendencias, objetivos, sesiones por mes y planes más usados para la administración. Las tendencias comparan
    los mismos días del mes anterior, porque comparar un mes a medias con uno entero no es justo.

### D-91 · Quinta auditoría: el peso en la adherencia y ajustes de despliegue
La quinta auditoría, tras la fase 17, dio 12/100 (antes 24/100), sin hallazgos críticos ni altos. El código nuevo
(gráficos, estadísticas, adherencia) no tiene fallos de inyección ni de permisos.
- **El peso es un dato de salud.** El consentimiento del registro lo incluye, y la adherencia lo mostraba al
  personal sin registrarlo, en contra de D-83. Ahora la lista registra los clientes de la página que muestran
  peso, y la ficha de adherencia al cliente que muestra. Se mantiene como mucho una fila por profesional, cliente
  y hora, con dos consultas por página.
- **Compose de producción sin contraseña publicada:** `POSTGRES_PASSWORD` es obligatoria, como
  `DJANGO_SECRET_KEY`. La CI genera una para cada ejecución.
- **Imagen del backend:** al instalar los *wheels* se vuelven a comprobar los *hashes* del *lock*.
- **CI:** cada trabajo tiene un límite de tiempo, unas tres veces lo que tarda ahora.
- **No se corrige:**
  - **Etapas de desarrollo de Docker sin root.** No se puede probar aquí, porque no hay Docker y la CI solo
    construye producción, y podría romper el entorno de desarrollo (permisos de los volúmenes y de la caché de
    Vite). Solo afectan a desarrollo, con los puertos en `127.0.0.1`.
  - **Lo ya decidido:**
    - el código de la imagen en propiedad de su usuario (D-89);
    - los *locks* de Dependabot (D-86);
    - `/auth/email-exists`, decisión 3 de la fase 15.
