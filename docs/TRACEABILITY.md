# Trazabilidad

Relación entre historias de usuario / requisitos, endpoints, pantallas y tests.
Las rutas de API llevan el prefijo `/api/v1`. Estado: ⏳ pendiente · ✅ implementado y probado.

## Historias de usuario

| US | Historia | Endpoint(s) | Pantalla(s) | Tests | Estado |
|---|---|---|---|---|---|
| US-01 | Registro de cliente | `POST /auth/register`, `GET /auth/email-exists` | Registro (`pages/auth/RegisterPage.tsx`) | `test_auth.py::TestRegister`, `::TestEmailExists`, `validation/*.test.ts`, `e2e/client.spec.ts` (E2E 1, email duplicado) | ✅ |
| US-03 | Login con «Recordar sesión» | `POST /auth/login`, `/auth/refresh`, `/auth/logout` | Login (`pages/auth/LoginPage.tsx`) | `test_auth.py::TestLogin`, `::TestRefreshAndLogout`, `api/client.test.ts`, `api/tokens.test.ts`, `e2e/auth.spec.ts` | ✅ |
| US-04 | Formulario de onboarding (6 pasos) | `POST/GET/PUT /me/onboarding` | Onboarding (`pages/client/OnboardingPage.tsx`) | `test_onboarding.py`, `validation/onboarding.test.ts`, `e2e/client.spec.ts` (E2E 1) | ✅ |
| US-05 | Plan semanal con bloqueo | `GET /me/training-plan` | Entrenamiento (`TrainingPlanPage.tsx`) | `test_training_client.py::TestMyTrainingPlan`, `test_schedule_motivation.py::TestDefaultCalendar`, `e2e/client.spec.ts` (E2E 3) | ✅ |
| US-06 | Entrenamiento del día | `GET /me/training-plan/workouts/{id}`, `PUT …/exercises/{we}`, `POST …/complete` | Entrenamiento del día (`WorkoutDayPage.tsx`) | `test_training_client.py::TestWorkoutDay`, `::TestCompleteWorkout`, `hooks/timers.test.tsx` (% del día), `e2e/client.spec.ts` (E2E 3) | ✅ |
| US-07 | Detalle de ejercicio | `GET /me/exercises/{id}` | Detalle de ejercicio (`ExerciseDetailPage.tsx`: carrusel, círculos, cronómetro, marcar hecho) | `test_training_client.py::TestExerciseDetail`, `hooks/timers.test.tsx`, `e2e/client.spec.ts` | ✅ |
| US-08 | Macronutrientes | `GET /me/nutrition-plan` | Macronutrientes (`NutritionPage.tsx`) | `test_mealplan.py::TestMyNutritionPlan`, `::TestCalculations`, `components/client-components.test.tsx`, `e2e/client.spec.ts` | ✅ |
| US-09 | Perfil | `GET /me`, `GET /me/weight-records` | Perfil (`pages/shared/ProfilePage.tsx`) | `test_me.py::TestMe`, `test_progress.py::TestWeightRecords`, `e2e/profile.spec.ts` | ✅ |
| US-10 | Editar perfil | `PATCH /me/profile`, `PUT /me/photo` | Editar perfil (`EditProfilePage.tsx`) | `test_me.py::TestProfileUpdate`, `::TestProfilePhoto`, `e2e/profile.spec.ts` | ✅ |
| US-12 | Cambiar contraseña | `PUT /me/password` | Modal de contraseña (`ChangePasswordModal.tsx`) | `test_me.py::TestPasswordChange`, `e2e/profile.spec.ts` | ✅ |
| US-13 | Información del ejercicio (modal) | `GET /me/exercises/{id}` | Modal «Exercise information» (`ExerciseInfoModal.tsx`) | `test_training_client.py::TestExerciseDetail`, `e2e/client.spec.ts` | ✅ |
| US-14 | Crear entrenamiento | `POST /workouts`, `PUT /workouts/{id}/media` | Formulario de entrenamiento (`WorkoutFormPage.tsx`) | `test_workout.py::TestWorkoutCrud`, `::TestWorkoutMedia`, `e2e/staff.spec.ts` (ejercicio + entrenamiento) | ✅ |
| US-15 | Modificar entrenamiento | `PUT/PATCH /workouts/{id}` | Formulario de entrenamiento (`WorkoutFormPage.tsx`) | `test_workout.py::TestWorkoutCrud::test_update_diffs_rows_by_id` | ✅ |
| US-16 | Eliminar entrenamiento | `DELETE /workouts/{id}` | Lista de entrenamientos (`CatalogPage.tsx`, confirmación + motivo si está en uso) | `test_workout.py::TestWorkoutDelete` | ✅ |
| US-17 | Gestionar ejercicios | `/exercises`, `/exercises/{id}`, `/exercises/{id}/media` | Ejercicios (`CatalogPage.tsx`, `ExerciseFormPage.tsx`, detalle) | `test_exercise.py`, `e2e/staff.spec.ts` | ✅ |
| US-18 | Gestionar planes de entrenamiento | `/training-plans`, `/training-plans/{id}` | Planes (`CatalogPage.tsx`, `PlanFormPage.tsx`, detalle) | `test_trainingplan.py` | ✅ |
| US-19 | Vistas detalladas de catálogo | `GET /exercises/{id}`, `/workouts/{id}`, `/training-plans/{id}`, `/meal-plans/{id}`, `/users/{id}` | Detalles (`CatalogDetailPages.tsx`, `MealPlanDetailPage.tsx`, `UserDetailPage.tsx`) | `test_exercise.py::TestExerciseCrud::test_retrieve`, `test_trainingplan.py::…::test_detail_avoids_n_plus_one`, `e2e/staff.spec.ts` | ✅ |
| US-20 | Lista de usuarios | `GET /users`, `GET /users/{id}` | Usuarios (`UsersPage.tsx`), detalle (`UserDetailPage.tsx`) | `test_user.py::TestUserList`, `::TestUserDetail`, `e2e/staff.spec.ts` (E2E 6) | ✅ |
| US-21 | Crear usuario (admin) | `POST /users` | Crear usuario (`UserCreatePage`) | `test_user.py::TestUserAdministration` (`creates…`, `every_field_is_required`), `e2e/staff.spec.ts` (E2E 5) | ✅ |
| US-22 | Modificar / eliminar usuario (admin) | `PATCH/DELETE /users/{id}` | Modificar usuario (`UserEditPage`) | `test_user.py::TestUserAdministration`, `e2e/staff.spec.ts` (E2E 5) | ✅ |
| US-23 | Asignar planes | `GET /assignments/pending`, `POST /users/{id}/assign-*` | Asignaciones (`AssignmentsPage.tsx`), ficha (`AssignmentDetailPage.tsx`) | `test_assignments.py`, `test_mealplan.py::TestAssignNutritionPlan`, `e2e/staff.spec.ts` (E2E 2, reemplazo, «Crear plan nuevo») | ✅ |
| US-24 | Estadísticas | `GET /statistics/*` | Estadísticas (`StatisticsPage.tsx`) | `test_statistics.py`, `e2e/staff.spec.ts` | ✅ |
| US-25 | Crear plan nutricional | `POST /meal-plans` | Formulario de plan nutricional (`MealPlanFormPage.tsx`, kcal en vivo) | `test_mealplan.py::TestMealPlanCrud`, `e2e/staff.spec.ts` | ✅ |
| US-26 | Modificar plan nutricional | `PUT/PATCH /meal-plans/{id}` | Formulario de plan nutricional (`MealPlanFormPage.tsx`) | `test_mealplan.py::TestMealPlanCrud` | ✅ |
| US-27 | Listar / ver / eliminar planes nutricionales | `GET /meal-plans?category=`, `GET/DELETE /meal-plans/{id}` | Nutrición (`MealPlansPage.tsx`), detalle (`MealPlanDetailPage.tsx`) | `test_mealplan.py::TestMealPlanCrud` (`list_by_category`, `delete_is_logical`) | ✅ |

## Errores conocidos (regresión)

| # | Error | Test(s) | Estado |
|---|---|---|---|
| 1 | 405 en POST/PUT de planes nutricionales | `test_mealplan.py::TestMealPlanCrud::test_create_and_update_work_for_nutritionist_and_admin` | ✅ |
| 2 | Modificación de usuarios no se guardaba | `test_user.py::TestUserAdministration::test_patch_persists_and_returns_new_data`, `e2e/staff.spec.ts` (E2E 5) | ✅ |
| 3 | Textos con formato de variable | `i18n/i18n.test.ts` (paridad), `i18n/keys-used.test.ts` (toda clave usada existe), `components/client-components.test.tsx` (enums traducidos), `e2e/regressions.spec.ts::regression #3` (ninguna pantalla muestra claves ni identificadores) | ✅ |
| 4 | Checkboxes se desmarcaban | `test_training_client.py::TestWorkoutDay::test_checkbox_state_is_persisted_and_rehydrated`, `e2e/client.spec.ts` (E2E 3 recarga al 100 %) | ✅ |
| 5 | Acceso a ejercicios bloqueados | `test_training_client.py::TestWorkoutDay::test_locked_workout_is_forbidden`, `::TestExerciseDetail::test_exercise_only_in_locked_workouts_is_forbidden`, `e2e/client.spec.ts` (la tarjeta bloqueada no navega) | ✅ |
| 6 | Perfil no se actualizaba tras editar | `e2e/profile.spec.ts::editing the profile is reflected immediately` | ✅ |
| 7 | Gráfica de peso no se refrescaba | `test_progress.py::TestWeightRecords::test_post_returns_the_updated_series`, `components/client-components.test.tsx` (redibujado), `e2e/client.spec.ts` (E2E 4) | ✅ |
| 8 | *Scroll* inicial en detalle de ejercicio | `e2e/regressions.spec.ts::regression #8` | ✅ |
| 9 | Error genérico al reasignar | `test_assignments.py::TestAssignTrainingPlan::test_second_assignment_requires_replace`, `test_mealplan.py::TestAssignNutritionPlan::test_reassignment_conflict_and_replace`, `e2e/staff.spec.ts` (confirmación de reemplazo) | ✅ |
| 10 | Varios botones de la barra activos | `auth/routing.test.ts` (ninguna ruta de pestaña es prefijo de otra), `e2e/auth.spec.ts` (una sola `.tab-selected`) | ✅ |
| 11 | Staff no admin podía gestionar usuarios | `test_user.py::TestStaffCannotManageUsers`, `test_permissions.py`, `e2e/staff.spec.ts` (E2E 6) | ✅ |

## Líneas futuras (Fase 9)

| # | Línea | Endpoint(s) | Pantalla(s) | Tests | Estado |
|---|---|---|---|---|---|
| 1 | Recuperación de contraseña por email (token de un solo uso con caducidad, email por consola en desarrollo, enlace en el login) | `POST /auth/password-reset`, `POST /auth/password-reset/confirm` | Login (enlace «¿Has olvidado tu contraseña?»), `pages/auth/ForgotPasswordPage.tsx`, `pages/auth/ResetPasswordPage.tsx` | `test_password_reset.py`, `test_permissions.py`, `validation/schemas.test.ts`, `e2e/password-reset.spec.ts`, `e2e/accessibility.spec.ts` | ✅ |
| 2 | Selección personalizada de días de entrenamiento (sustituye al reparto por defecto) | `GET/PUT /me/training-days`, `GET /me/training-plan` (`training_days`), `GET /me/progress/dashboard` | Plan semanal (`components/training/TrainingDaysModal.tsx`), ficha de usuario del personal | `test_training_days.py`, `test_permissions.py`, `i18n/format.test.ts`, `e2e/training-days.spec.ts` | ✅ |
| 3 | Biblioteca de alimentos (calorías, macros y micronutrientes) | `GET/POST /foods`, `GET/PUT/PATCH/DELETE /foods/{id}` | `pages/shared/FoodPages.tsx` (personal y cliente), `pages/nutritionist/FoodFormPage.tsx` | `test_food.py`, `test_permissions.py`, `test_seed.py`, `utils/foods.test.ts`, `api/case.test.ts`, `e2e/foods.spec.ts`, `e2e/accessibility.spec.ts` | ✅ |
| 4 | Gamificación (insignias) | `GET /me/badges`, `POST …/workouts/{id}/complete` y `POST /me/weight-records` (`new_badges`) | Progreso › Control (`components/progress/Badges.tsx`), `pages/client/BadgesPage.tsx` | `test_badges.py`, `test_permissions.py`, `utils/badges.test.ts`, `e2e/badges.spec.ts`, `e2e/accessibility.spec.ts` | ✅ |

## Producto (fase 12, plan de mejora)

| # | Funcionalidad | Endpoint(s) | Pantalla(s) | Tests | Estado |
|---|---|---|---|---|---|
| 1 | Series reales y récords personales | `PUT …/exercises/{item_id}` (`sets`), `GET /me/training-plan/workouts/{id}` (`logged_sets`, `last_sets`), `POST …/complete` (`new_records`), `GET /me/records`, `GET /me/exercises/{id}/history` | Entrenamiento del día y ficha de ejercicio (`components/training/SetsEditor.tsx`, `ExerciseProgress.tsx`, `charts/LoadChart.tsx`), Progreso › Entreno (`progress/RecordsCard.tsx`) | `test_sets.py`, `test_seed.py`, `test_privacy.py`, `SetsEditor.test.tsx`, `offline/marks.test.ts`, `utils/sets.test.ts`, `e2e/sets.spec.ts`, `e2e/accessibility.spec.ts` | ✅ |
| 2 | Adherencia de los clientes (personal) | `GET /adherence`, `GET /users/{id}/adherence` | `pages/shared/AdherencePage.tsx`, ficha del usuario (`components/staff/Adherence.tsx`) | `test_adherence.py`, `test_permissions.py`, `staff/Adherence.test.tsx`, `e2e/adherence.spec.ts`, `e2e/accessibility.spec.ts` | ✅ |
| 3 | Notas asíncronas cliente ↔ equipo | `GET/POST /me/notes`, `GET /me/notes/unread`, `POST /me/notes/read`, `GET/POST /users/{id}/notes`, `POST /users/{id}/notes/read`, `GET /notes/inbox` | `pages/client/NotesPage.tsx`, `components/notes/` (hilo, acceso del cliente, bandeja y ficha del personal) | `test_notes.py`, `test_privacy.py`, `test_seed.py`, `test_permissions.py`, `notes/NotesThread.test.tsx`, `e2e/notes.spec.ts`, `e2e/accessibility.spec.ts` | ✅ |
| 4 | Hora de entreno y recordatorios por email | `GET/PUT /me/reminders`, `GET /me/progress/dashboard` (`target_datetime`), `PATCH /me/profile` (`language`), comando `send_training_reminders` | Perfil (`components/profile/RemindersCard.tsx`), `auth/useAccountLanguage.ts` | `test_reminders.py`, `test_permissions.py`, `auth/useAccountLanguage.test.ts`, `e2e/reminders.spec.ts` | ✅ |
| 5 | Verificación del email al registrarse | `POST /auth/register` (envía el enlace), `POST /auth/verify-email`, `POST /me/verify-email/resend` | `pages/auth/VerifyEmailPage.tsx`, `components/EmailVerificationBanner.tsx` | `test_email_verification.py`, `e2e/verify-email.spec.ts`, `e2e/accessibility.spec.ts` | ✅ |

## Nutrición avanzada (fase 13, plan de mejora)

| # | Funcionalidad | Endpoint(s) | Pantalla(s) | Tests | Estado |
|---|---|---|---|---|---|
| 1 | Menú de ejemplo de cada plan | `GET/PUT /meal-plans/{id}/menu`, `GET /me/nutrition-plan/menu`, `DELETE /foods/{id}` (`409 food_in_use`) | `pages/nutritionist/MenuEditorPage.tsx`, detalle del plan, Macronutrientes (`components/nutrition/MenuView.tsx`, `FoodPicker.tsx`) | `test_menus.py`, `test_seed.py`, `test_permissions.py`, `nutrition-phase13.test.tsx`, `e2e/nutrition-plus.spec.ts`, `e2e/accessibility.spec.ts` | ✅ |
| 2 | Diario de comidas | `GET/POST /me/food-log`, `PATCH/DELETE /me/food-log/{id}`, `POST /me/food-log/copy-menu`, `GET /me/food-log/summary`, `GET /users/{id}/food-log/summary` | `pages/client/FoodDiaryPage.tsx`, ficha del usuario (`components/nutrition/DiarySummaryCard.tsx`) | `test_food_log.py`, `test_permissions.py`, `nutrition-phase13.test.tsx`, `e2e/nutrition-plus.spec.ts`, `e2e/accessibility.spec.ts` | ✅ |
| 3 | Lista de la compra | `GET /me/shopping-list` | `pages/client/ShoppingListPage.tsx` | `test_menus.py::TestClient`, `nutrition-phase13.test.tsx` (`formatGrams`), `e2e/nutrition-plus.spec.ts`, `e2e/accessibility.spec.ts` | ✅ |

## Contenido en tres idiomas (fase 14)

| # | Funcionalidad | Endpoint(s) | Pantalla(s) | Tests | Estado |
|---|---|---|---|---|---|
| 1 | Catálogo traducible (ejercicios con pasos, entrenamientos, planes de entrenamiento y nutricionales, alimentos) | Todos los del catálogo y del cliente según `Accept-Language`; `translations` en los de gestión | Sección «Traducciones» de los formularios (`components/staff/TranslationsSection.tsx`) | `test_translations.py`, `test_seed.py`, `TranslationsSection.test.tsx`, `e2e/content-language.spec.ts` | ✅ |
| 2 | App instalada en el idioma del usuario | — | `public/manifest*.webmanifest`, `i18n/index.ts` | `i18n/manifests.test.ts`, `i18n/useLanguage.test.tsx` | ✅ |

## Aplicación más visual (fase 17)

| # | Funcionalidad | Endpoint(s) | Pantalla(s) | Tests | Estado |
|---|---|---|---|---|---|
| 1 | Progreso del cliente en gráficos: cifras de 12 semanas, sesiones y kilos por semana, músculos trabajados | `GET /me/progress/stats` | Progreso → Entrenos (`components/progress/TrainingStats.tsx`) | `test_progress_stats.py`, `components/progress/TrainingStats.test.tsx`, `e2e/accessibility.spec.ts` | ✅ |
| 2 | Inicio y diario del cliente: anillos del plan, la semana y la racha; tira de la semana; anillos de calorías y macros; calorías de 7 días frente al objetivo | `GET /me/progress/dashboard` (`week`, `streak_weeks`), `GET /me/food-log`, `GET /me/food-log/summary` | Entrenamiento (`TrainingPlanPage.tsx`, `ProgressRing.tsx`, `training/WeekStrip.tsx`), diario (`FoodDiaryPage.tsx`, `DiarySummaryCard.tsx`) | `test_progress.py::TestDashboard`, `components/progress-visuals.test.tsx`, `nutrition/nutrition-phase13.test.tsx`, `e2e/accessibility.spec.ts`, `e2e/nutrition-plus.spec.ts` | ✅ |
| 3 | Equipo: resumen de la adherencia (cifras, clientes por estado, por tramos), anillos y entrenos por semana en la ficha, avatares con iniciales y estado con icono en la lista de usuarios | `GET /adherence` (`distribution`, `average_percent`), `GET /users/{id}/adherence` | Adherencia (`AdherenceOverview.tsx`, `Adherence.tsx`), ficha (`UserDetailPage.tsx`), usuarios (`UsersPage.tsx`, `Avatar`) | `test_adherence.py::TestEndpoints`, `components/staff/staff-visuals.test.tsx`, `e2e/adherence.spec.ts`, `e2e/accessibility.spec.ts` | ✅ |
| 4 | Administración: cifras con su tendencia, clientes por estado y por objetivo, sesiones por mes y planes con más clientes | `GET /statistics/summary`, `GET /statistics/sessions`, `GET /statistics/plan-popularity` | Estadísticas (`pages/admin/StatisticsPage.tsx`, `StatTiles.tsx`, `charts/DonutChart.tsx`) | `test_statistics.py::TestSummaryAndYears`, `::TestSessionsAndPlans`, `pages/admin/StatisticsPage.test.tsx`, `e2e/staff.spec.ts` | ✅ |

## Recorrido completo

`e2e/journey.spec.ts` recorre la vida entera de un cliente nuevo sobre el *build* de producción:
1. Registro, formulario inicial y confirmación del email.
2. Nota al equipo mientras espera; el entrenador responde y asigna el plan de entrenamiento, y el
   nutricionista, el nutricional.
3. Primer entrenamiento con series y carga, insignia, progreso (sesión, récord y peso).
4. Menú, diario copiado del menú y lista de la compra.
5. Recordatorios y exportación de datos (con todo lo anterior).
6. Adherencia, notas y diario vistos por el personal, y usuarios y estadísticas por el admin.
7. Baja de la cuenta.

Durante todo el recorrido falla si hay errores de JavaScript o de consola, respuestas 5xx o violaciones de la
CSP.

## Matriz de permisos

`backend/tests/test_permissions.py` recorre 48 endpoints × 5 roles (anónimo, cliente, entrenador,
nutricionista, admin) y comprueba 401/403 o acceso según el rol.

## Requisitos no funcionales

| Requisito | Implementación | Verificación | Estado |
|---|---|---|---|
| TLS / cabeceras seguras | `config/settings/prod.py` (SSL redirect, HSTS, cookies seguras, proxy SSL header) | `manage.py check --deploy --fail-level WARNING` en CI | ✅ |
| Política de contraseñas | Validadores de Django (longitud y caracteres, contraseñas comunes, parecido al nombre o al email), 128 caracteres como máximo, + esquema Zod | `test_auth.py::TestRegister::test_password_policy`, `::TestPasswordPolicy`, `::TestPasswordLength`, `validation/schemas.test.ts`, `e2e/auth.spec.ts` | ✅ |
| Hash Argon2 | `PASSWORD_HASHERS` | `test_auth.py::TestSecurity::test_argon2_is_the_production_hasher` | ✅ |
| JWT 15 min + refresh rotado + blacklist | simplejwt + `apps/accounts/tokens.py` | `test_auth.py` (`access_token_lasts_15_minutes`, `rotates_refresh…`, `logout…`) | ✅ |
| La sesión termina al cambiar la contraseña | `password_changed_at` + `apps/accounts/authentication.py` | `test_me.py::…::test_access_tokens_issued_before_the_change_stop_working`, `test_password_reset.py::…::test_access_tokens_issued_before_the_reset_stop_working` | ✅ |
| *Throttling* | DRF `ScopedRateThrottle` (login, registro, contraseña, email-exists, recuperación, notas y confirmación del email), subidas por usuario (`apps/core/throttling.py`), fallos de login por cuenta e IP (`apps/accounts/login_attempts.py`), renovación y cierre de sesión, descarga de datos; contadores en la caché de la base de datos | `test_auth.py::TestSecurity::test_login_is_throttled`, `::TestLoginPerAccount`, `::TestSessionRateLimit`, `test_privacy.py::test_the_data_download_is_limited`, `test_uploads.py::TestUploadRate`, `test_notes.py::…::test_writing_is_throttled`, `test_email_verification.py::…::test_resending_is_throttled`, `test_settings.py::test_the_rate_limits_share_a_cache_table_created_by_migrate` | ✅ |
| Sin N+1 | `select_related`/`prefetch_related` | `django_assert_max_num_queries` en listados de ejercicios, entrenamientos, planes, planes nutricionales, usuarios, pendientes y `/me/training-plan` | ✅ |
| i18n es/en/ca | react-i18next con carga diferida por idioma | `i18n/i18n.test.ts` (paridad de claves y *placeholders*), `i18n/useLanguage.test.tsx`, `components/LanguageMenu.test.tsx`, `e2e/language.spec.ts` | ✅ |
| PWA | `public/manifest.webmanifest`, `public/sw.js` (solo estáticos de `/assets/` por tipo), iconos | `vite build` (incluye *manifest*, SW e iconos), `tests/service-worker.test.ts` | ✅ |
| Accesibilidad (WCAG 2.1 A/AA) | Etiquetas, `aria-label`, foco visible, 44 px, regiones | `e2e/accessibility.spec.ts` (axe-core) | ✅ |
| Desplegable en Render | `render.yaml` (API, *static site*, PostgreSQL 16), `RENDER_EXTERNAL_HOSTNAME` en `ALLOWED_HOSTS` | `tests/test_settings.py` (*host* de Render, *settings* de producción, clave obligatoria) | ✅ (pendiente del primer despliegue real) |
| Imágenes de producción | `backend/Dockerfile` y `frontend/Dockerfile` (etapa `prod`), `docker-compose.prod.yml`, `frontend/docker/nginx.conf` | *Job* `docker` de la CI: *build*, `compose up` y prueba de humo; `test_settings.py::test_media_can_be_served…` | ✅ (pendiente de la primera ejecución de la CI) |
| Media en GCS con URLs firmadas | django-storages (`USE_GCS=1`), bucket privado, `GS_EXPIRATION_MINUTES` | `test_settings.py::test_gcs_storage_uses_a_private_bucket_with_signed_urls`, `test_core.py` (limpieza de ficheros reemplazados o borrados) | ✅ |
| Límites de peticiones no esquivables | `NUM_PROXIES` (DRF) | `test_auth.py::TestSecurity` (cabecera falsa, cliente tras *proxy*) | ✅ |
| Sesión resistente a XSS | *Refresh* en cookie `httpOnly` + cabecera CSRF (`apps/accounts/cookies.py`), *access* en memoria | `test_auth.py::TestRefreshAndLogout`, `api/client.test.ts`, `api/tokens.test.ts`, `e2e/auth.spec.ts` | ✅ |
| Content-Security-Policy y HSTS | `frontend/security-headers.ts`, nginx, `render.yaml` (HSTS en el *static site*); regla de ESLint contra eventos nativos compuestos en componentes de Ionic | `tests/security-headers.test.ts`, `e2e/csp.spec.ts` (*build* de producción), `e2e/journey.spec.ts` (recorrido completo sin errores de consola ni violaciones), *job* `docker` (cabeceras) | ✅ |
| Monitorización sin datos personales | `apps/core/monitoring.py`, `src/monitoring.ts`, `uptime.yml` | `test_settings.py::TestMonitoring`, `monitoring.test.ts` | ✅ |
| Copias y restauración | `backup_database` (cuenta de servicio propia, `BACKUP_PRUNE`), `restore_drill`, *cron* de Render | `test_backups.py` (con restauración real), CI (`e2e` y `docker`) | ✅ |
| Auditoría de dependencias | `pip-audit`, `npm audit`, Dependabot | CI | ✅ |
| Cadena de suministro | *Locks* de Python con *hashes* (`--require-hashes`), imágenes por *digest*, acciones por SHA, *token* de la CI de solo lectura, huella de la clave de PostgreSQL | CI (instalación con *hashes*, *job* `docker`) | ✅ |
| Varias pestañas con la misma sesión | `refreshAccessToken` (reintenta una vez tras un 401) | `api/client.test.ts` | ✅ |
| Emails de recuperación limitados por dirección | `request_password_reset` | `test_password_reset.py::TestEmailsPerAddress` | ✅ |
| El personal solo ve clientes | `UserViewSet.get_queryset` | `test_user.py::…::test_trainers_and_nutritionists_only_see_clients`, `::test_admins_see_everybody` | ✅ |
| La sesión solo termina si la API la rechaza | `src/api/client.ts`, `auth/AuthContext.tsx` | `api/client.test.ts` | ✅ |
| Peticiones simultáneas sin 500 | Bloqueo de fila en el formulario inicial y en las imágenes, índice único del email (`_create_account`) | `tests/concurrency.py` (dos peticiones reales a la vez): `test_onboarding.py::test_a_double_submit_gets_409_not_500`, `test_exercise.py::…::test_two_uploads_at_once_respect_the_limit`; `test_auth.py::TestSameEmailAtOnce` | ✅ |
| Datos por usuario acotados | Pesos y diario de los últimos 5 años, 60 anotaciones del diario por día, récords calculados en la base de datos | `test_progress.py::TestWeightHistoryBound`, `test_food_log.py::TestEntriesPerDay`, `::TestDatesOfTheDiary`, `test_sets.py::TestRecordsInTheDatabase` | ✅ |
| Recuperación sin revelar cuentas por el tiempo | Email enviado en segundo plano (`apps/core/background.py`) | `test_password_reset.py::TestTiming`, `test_core.py::TestBackgroundTasks` | ✅ |
| Subidas acotadas | Límite de píxeles (`apps/core/files.py`, `images.py`), tamaño de la petición (`apps/core/middleware.py`), ritmo por usuario | `test_uploads.py`, `test_images.py`, `components/MediaPicker.test.tsx`, `e2e/uploads.spec.ts` | ✅ |
| Producción endurecida | Claves robustas, email que envía, sin admin ni documentación de la API, `no-store` en la API, logs sin datos personales (`gunicorn.conf.py`, nginx), `DEMO_PASSWORD` | `test_settings.py` (`TestProductionKeys`, `TestProductionEmail`, `TestGunicorn`, `test_api_answers_are_never_stored`, `test_without_admin_nor_docs…`), `test_seed.py`, `test_reminders.py` (asunto) | ✅ |
| RGPD: consentimiento, acceso, supresión y conservación | `POST /me/consent`, `GET /me/export`, `DELETE /me/account`, `purge_inactive_accounts`, `/privacy` | `test_privacy.py`, `validation/onboarding.test.ts`, `e2e/privacy.spec.ts`, `e2e/accessibility.spec.ts` | ✅ |
| RGPD: registro de accesos a los datos de salud | `HealthDataAccess` (ficha, notas, resumen del diario y peso en la adherencia; una fila por profesional, cliente y hora), `GET /users/{id}/health-data-accesses` (admin), `GET /me/export` | `test_health_data_access.py` | ✅ |
| Carga inicial ligera | *Tree-shaking* de Ionic (`vite.config.ts`), páginas por rol (`layouts/appRoutes.ts`, `useRoleRoutes`) | `vite build` (tamaños en `PROGRESS.md`), suite E2E sobre el *build* de producción | ✅ |
| Imágenes optimizadas y sin metadatos | `apps/core/images.py` (WebP, 512/1600 px, sin EXIF) | `test_images.py` | ✅ |
| Entrenamiento sin conexión | `src/offline/` (copias por usuario, cola de marcas, borradas al cerrar o caducar la sesión), aviso de falta de conexión | `offline/offline.test.ts`, `auth/AuthContext.test.tsx`, `e2e/offline.spec.ts` | ✅ |
| Rendimiento bajo carga | `load/smoke.js` (k6) | *Job* `docker` de la CI (percentil 95 < 800 ms, errores < 1 %) | ✅ |
| Movimiento reducido | Animaciones de Ionic desactivadas con `prefers-reduced-motion` | E2E (Playwright emula la preferencia) | ✅ |
