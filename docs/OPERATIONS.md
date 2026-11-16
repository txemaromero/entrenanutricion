# Operación de entrenanutricion

Guía para poner la aplicación en producción y mantenerla: comprobaciones previas, monitorización, copias de
seguridad, seguridad y protección de datos. El despliegue básico está en el [README](../README.md#despliegue-en-render)
y las decisiones técnicas, en [`DECISIONS.md`](DECISIONS.md) (D-54 a D-60 y, de seguridad, D-78 a D-85).

## 1. Lista de comprobación antes de abrir la app al público

Hazla primero en un entorno de *staging* (un Blueprint aparte, con otros nombres de servicio) y repítela en
producción.

**Código y CI**
- [ ] El repositorio está en GitHub y la CI está en verde. La CI incluye los E2E, la CSP sobre el *build* de
      producción, las imágenes Docker y la restauración de prueba.
- [ ] Dependabot está activo (*Settings › Code security*) y las alertas de seguridad llegan a alguien.
- [ ] *Settings › Actions › General › Workflow permissions* está en «Read repository contents
      permission»: cualquier *workflow* nuevo empieza con solo lectura.

**Servicios externos**
- [ ] Hay dos buckets privados de Google Cloud Storage, con prevención de acceso público y acceso uniforme:
      uno para los ficheros multimedia y otro para las copias de seguridad.
- [ ] El bucket de copias tiene una regla de ciclo de vida que borra los objetos de más de 14 días y una
      política de retención de 14 días (bloqueada con *Bucket Lock* una vez probada).
- [ ] El bucket de copias cifra con una clave propia de Cloud KMS (CMEK, *Encryption › Customer-managed
      key*). Da a la cuenta de servicio de Cloud Storage del proyecto el rol
      `roles/cloudkms.cryptoKeyEncrypterDecrypter` sobre esa clave. Sin acceso a la clave, ni siquiera quien
      llegue al bucket puede leer las copias (D-87).
- [ ] Hay dos cuentas de servicio, cada una con permisos solo sobre su bucket (D-82):
  - ficheros: `roles/storage.objectAdmin` en el bucket de ficheros; su clave, en el grupo
    `entrenanutricion-gcs`;
  - copias: `roles/storage.objectCreator` en el bucket de copias; su clave, en `GS_BACKUP_CREDENTIALS_JSON`
    del *cron* `entrenanutricion-backup`.

  La cuenta de los ficheros no tiene ningún permiso sobre el bucket de copias.
- [ ] El *cron* `entrenanutricion-backup` tiene el mismo `GS_BUCKET_NAME` que la API (la purga borra las fotos
      de las cuentas).
- [ ] El grupo `entrenanutricion-smtp` tiene `EMAIL_HOST`, `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD`, y
      `DEFAULT_FROM_EMAIL` usa un dominio verificado (SPF/DKIM). Lo usan la API y el *cron*
      `entrenanutricion-reminders`. Sin SMTP, producción no arranca salvo con `ALLOW_CONSOLE_EMAIL=1`, que
      solo vale para pruebas. Se comprueba con un registro nuevo (llega el email de confirmación) y con un
      «¿Has olvidado tu contraseña?» real.
- [ ] Sentry tiene dos proyectos: `SENTRY_DSN` en la API y `VITE_SENTRY_DSN` en el *static site* (después,
      hay que volver a desplegar). Hay reglas de alerta (apartado 2).
- [ ] La comprobación de disponibilidad está activa con las variables del repositorio `HEALTHCHECK_URL`
      (`https://<web>/api/v1/health`) y `WEB_URL` (`https://<web>/`).

**Datos legales**
- [ ] `VITE_PRIVACY_CONTROLLER` y `VITE_PRIVACY_CONTACT` del *static site* tienen los datos reales del
      responsable y el email de privacidad.
- [ ] Un asesor ha revisado la política de privacidad (`privacy.*` en `frontend/src/i18n/locales/`). Ver
      apartado 5.

**Comprobaciones en staging**
- [ ] **Sesión:**
  - Tras iniciar sesión, `entrenanutricion_refresh` aparece en las cookies con `HttpOnly`, `Secure` y
    `SameSite=Lax`, y sin un `refresh` en `localStorage`.
  - Recargar la página mantiene la sesión.
- [ ] **Límites de peticiones** (`NUM_PROXIES`):
  - Desde un dispositivo, el login falla con 429 al 11.º intento erróneo en un minuto. Desde otro dispositivo,
    en ese mismo minuto, se puede iniciar sesión con otra cuenta.
  - Con una misma cuenta, el 11.º fallo en una hora da 429 en ese dispositivo; desde otro se sigue pudiendo
    entrar (D-88).
  - Si el segundo dispositivo también recibe 429, el *rewrite* del *static site* añade un salto: sube
    `NUM_PROXIES` a `2` en la API y repite la prueba.
- [ ] **CSP:** la consola del navegador no muestra errores `Content-Security-Policy` al recorrer la app con un
      cliente y con un admin (incluidas las imágenes de GCS).
- [ ] **Copias:** el *cron* `entrenanutricion-backup` ha dejado una copia en el bucket y la restauración de
      prueba con esa copia funciona (apartado 3).
- [ ] **Recordatorios:** con un cliente de prueba (email confirmado, recordatorios activados y la hora de
      entreno dentro de la hora siguiente), la siguiente ejecución del *cron* `entrenanutricion-reminders`
      envía el email. En sus logs aparece «1 training reminder(s) sent.». Para revisar sin enviar:
      `python manage.py send_training_reminders --dry-run`.
- [ ] **Subidas:** se puede subir un vídeo de hasta 50 MB a través del *rewrite* `/api/*`. Si el *proxy* lo
      corta, pasa al plan B del apartado 4.
- [ ] **Superficie mínima:** `/admin/`, `/api/docs/` y `/api/schema/` responden 404. Las respuestas de
      `/api/` llevan `Cache-Control: no-store` y la web, `Strict-Transport-Security`.

## 2. Monitorización

| Qué | Dónde | Notas |
|---|---|---|
| Errores del backend | Sentry (`SENTRY_DSN`) | Sin datos personales: ni usuario, ni cuerpos, ni cookies, ni cabeceras de autenticación, ni *query strings* (`apps/core/monitoring.py`). La *release* es el *commit* desplegado (`RENDER_GIT_COMMIT`). |
| Errores del frontend | Sentry (`VITE_SENTRY_DSN`) | El SDK se carga solo si hay DSN. `dataCollection` está desactivado y se filtran los *tokens* de los enlaces de recuperación (`src/monitoring.ts`). |
| Disponibilidad | GitHub Actions `uptime.yml`, cada 15 min | Comprueba que `/health` responde con la base de datos operativa y que se sirve la web. Si falla, GitHub avisa por email a quien vigile el repositorio. |
| Salud del servicio | Render (*health check* `/api/v1/health`) | Render reinicia la instancia si deja de responder. |
| Logs | Render (*Logs*) | Logs JSON del backend. El log de acceso no guarda la parte de la URL tras «?», el *referer* ni el navegador (`backend/gunicorn.conf.py`). Los fallos de envío de emails se registran sin datos personales (solo el id del usuario). |
| Recordatorios | Render (*Logs* del *cron* `entrenanutricion-reminders`) | Cada ejecución escribe cuántos recordatorios ha enviado. |

Reglas de alerta recomendadas en Sentry:
- *Issue* nueva en `production`.
- Más de 10 eventos en 5 minutos.
- Cualquier error en `apps.accounts` (autenticación).

Activa también el aviso semanal.

## 3. Copias de seguridad y restauración

- **Qué:** `python manage.py backup_database` hace un `pg_dump` en formato *custom* de toda la base de datos.
- **Cuándo:** cada noche a las 02:30 UTC (*cron* `entrenanutricion-backup` de `render.yaml`). Después se
  ejecuta la purga de cuentas caducadas (apartado 5).
- **Dónde:** en el bucket privado `GS_BACKUP_BUCKET_NAME`, con nombres `entrenanutricion-AAAAMMDD-HHMMSS.dump`.
  El *job* usa su propia cuenta de servicio (`GS_BACKUP_CREDENTIALS_JSON`), que solo puede crear objetos:
  no puede leer ni borrar las copias.
- **Retención:** 14 días. En Render las borra la regla de ciclo de vida del bucket (`BACKUP_PRUNE=0`). Con
  `BACKUP_DIR` (sin bucket), el propio comando borra las de más de `BACKUP_RETENTION_DAYS` días.
- **Contenido:** las copias contienen datos de salud. Nunca las guardes en un sitio público ni las compartas.

### Restauración de prueba (verificar una copia)

La CI ya hace una restauración de prueba en cada *push*, con los datos demo y dentro de la imagen de
producción. Una vez al mes, repítela con una copia real:

Descarga la copia con una cuenta que pueda leer el bucket (la del *job* no puede):

```bash
gcloud storage cp gs://<bucket-backups>/entrenanutricion-20261105-023000.dump ./backup.dump
# Con una base local o desechable (DATABASE_URL) y el cliente de PostgreSQL 16:
python manage.py restore_drill --dump ./backup.dump
```

`restore_drill` necesita permiso `CREATEDB`:
1. Crea una base temporal `<base>_restore_drill` y restaura en ella la copia.
2. Comprueba que están todas las tablas e informa de las filas.
3. La borra al terminar (`--keep` la conserva).

Sin `--dump`, primero hace una copia de la base actual y exige que coincidan todas las filas.

### Restauración real (desastre)

1. **No sobrescribas la base dañada:** crea una nueva (en Render: *New › PostgreSQL*, versión 16).
2. Restaura la copia:
   ```bash
   pg_restore --no-owner --no-privileges --dbname "<URL externa de la base nueva>" backup.dump
   ```
3. Cambia el `DATABASE_URL` de la API y del *cron* a la base nueva y vuelve a desplegar.
4. Comprueba `/api/v1/health`, inicia sesión con un admin y revisa las estadísticas.
5. Las sesiones (`refresh tokens`) son las de la copia: avisa a los usuarios de que quizá tengan que volver a
   entrar.

Los planes de pago de Render también hacen copias propias de la base gestionada. Estas copias lógicas son una
segunda capa, independiente del proveedor.

## 4. Seguridad

**Sesión** (D-58)
- El *access token* (15 min) vive solo en memoria.
- El *refresh token* va en la cookie `httpOnly` `entrenanutricion_refresh`, con `Path=/api/v1/auth/` y
  `SameSite=Lax`, de modo que JavaScript no puede leerlo.
- Con «Recordar sesión», la cookie dura 7 días; sin esa opción, desaparece al cerrar el navegador.
- `/auth/refresh` y `/auth/logout` exigen la cabecera `X-Requested-With: entrenanutricion`, que una página de
  otro sitio no puede enviar sin pasar el control CORS. El *refresh* solo se acepta desde la cookie.
- Cambiar o recuperar la contraseña cierra todas las demás sesiones al momento, también los *access tokens*
  ya emitidos (D-80).

**Mismo sitio**
- La cookie con `SameSite=Lax` necesita que la web y la API compartan sitio. En Render se consigue con el
  *rewrite* `/api/*` del *static site*.
- **Plan B**, si el *rewrite* no sirve (subidas grandes o latencia): usa dominios propios del mismo sitio
  (`app.ejemplo.com` y `api.ejemplo.com`):
  - `VITE_API_URL=https://api.ejemplo.com/api/v1`;
  - añade ese origen a `connect-src` de la CSP;
  - `CORS_ALLOWED_ORIGINS=https://app.ejemplo.com`.

**CSP** (D-59)
- La política está en `frontend/security-headers.ts` y se repite en `frontend/docker/security-headers.conf`
  (nginx) y en `render.yaml`. Un test comprueba que las tres coinciden.
- Para permitir un dominio nuevo (CDN, otra API…), cambia las tres copias y ejecuta:
  ```bash
  npm run build && npx vite preview   # en otra terminal:
  E2E_BASE_URL=http://127.0.0.1:4173 npx playwright test e2e/csp.spec.ts
  ```

**Límites de peticiones** (D-79)
- Por IP en login, registro, recuperación de contraseña, comprobación de email y renovación de sesión; por
  usuario en el cambio de contraseña, las subidas de ficheros y la descarga de datos; por cuenta e IP en los
  fallos de inicio de sesión, con un tope total por cuenta.
- La IP es la que añade el último *proxy* (`NUM_PROXIES`). Nunca la que envía el cliente.
- Los contadores están en la tabla `django_cache` de la base de datos, común a todos los procesos. La crea
  `migrate`.

**Superficie expuesta en producción**
- Sin admin de Django ni documentación de la API (`ADMIN_ENABLED`, `API_DOCS_PUBLIC`; actívalos solo en
  *staging*).
- Producción no arranca con una clave secreta débil o publicada, ni con un *backend* de email que no envía
  (D-81).
- Subidas: 5 MB por imagen, 50 MB por vídeo, 40 megapíxeles por imagen y `413` para cuerpos mayores (D-78).

**Dependencias** (D-85)
- Dependabot propone actualizaciones semanales de versiones con al menos 14 días.
- La CI falla con vulnerabilidades en el backend y con las moderadas o peores en el código que se distribuye.
- Python se instala desde *locks* con *hashes* (`--require-hashes`). Tras cambiar `requirements*.in`, regenera
  los *locks* con el comando del README.
- npm no ejecuta scripts de instalación (`frontend/.npmrc`). Si un paquete nuevo los necesitara, hay que
  decidirlo expresamente.
- Las imágenes Docker y las acciones de GitHub están fijadas por *digest* o SHA. Para actualizar a mano una
  imagen, cambia la etiqueta y el *digest* a la vez.
- Antes de aceptar una PR de Dependabot de Python, regenera los *locks* con `uv` en esa rama: Dependabot los
  rehace solo para Linux.
- Dependabot no propone los saltos que se planifican (D-86): Django 6 (hasta la 6.2 LTS), Ionic 9 con
  react-router 6 y React 19, Python, Node y PostgreSQL de versión mayor y la siguiente estable de nginx (1.32,
  en primavera de 2027).

**Rotación de secretos**
- `DJANGO_SECRET_KEY`: cambiarla invalida los enlaces de recuperación y confirmación pendientes y, si no hay
  `JWT_SIGNING_KEY`, cierra todas las sesiones.
- `JWT_SIGNING_KEY`: cambiarla cierra todas las sesiones.
- Claves de las cuentas de servicio de GCS (ficheros y copias): crea la nueva, actualiza la variable y borra
  la antigua.
- Contraseña SMTP y DSN de Sentry.

## 5. Protección de datos (RGPD)

**Bases y consentimientos**
- Se registra la versión de la política aceptada y la fecha (`privacy_policy_version`, `privacy_accepted_at`).
- En el caso de los clientes, también se registra el consentimiento expreso y separado para los datos de salud
  (art. 9.2.a), con su fecha (`health_consent_at`).

**Publicar una política nueva**
1. Cambia los textos `privacy.*` en los tres idiomas.
2. Sube `PRIVACY_POLICY_VERSION` (API) y `VITE_PRIVACY_POLICY_VERSION` (*static site*) al mismo valor.
3. Despliega. Al entrar, cada usuario verá la política nueva y tendrá que aceptarla.

**Derechos**

| Derecho | Cómo se ejerce |
|---|---|
| Acceso y portabilidad | Perfil › Descargar mis datos (`GET /me/export`, JSON completo). |
| Rectificación | Perfil › Modificar. |
| Supresión (clientes) | Perfil › Eliminar mi cuenta (`DELETE /me/account`, con contraseña): se borran la cuenta y todos sus datos, ficheros incluidos. |
| Supresión (personal) | La hace un admin: baja en Usuarios y, para borrarla ya, `purge_inactive_accounts --days 0`. |
| Oposición y limitación | Por email al contacto de privacidad. |
| Retirada del consentimiento | Equivale a eliminar la cuenta: sin datos de salud no se pueden preparar los planes. |

**Accesos del equipo a los datos de salud** (D-83)
- Cuando un profesional ve la ficha de un cliente con su formulario inicial, sus notas o el resumen de su
  diario, queda registrado quién, a quién y cuándo (sin los valores), como mucho una vez por hora.
- Los admins lo consultan en `GET /api/v1/users/{id}/health-data-accesses`; el cliente lo ve en la descarga
  de sus datos.
- Ante una sospecha de acceso indebido, revisa ese registro del cliente afectado.

**Conservación**
- Las cuentas dadas de baja por un admin se borran definitivamente a los `ACCOUNT_RETENTION_DAYS` (365) días,
  con `purge_inactive_accounts`, que se ejecuta cada noche. Se borran también sus ficheros y su registro de
  accesos.
- Las copias de seguridad guardan los datos borrados durante sus 14 días de retención; la política lo indica.

**Pendiente de la persona responsable (no técnico)**
- **Revisión legal** de la política (es una plantilla), de las bases jurídicas y de los plazos.
- **Contratos de encargado del tratamiento** con Render, Google Cloud, el proveedor de email y Sentry, y
  revisión de sus transferencias internacionales.
- **Registro de actividades de tratamiento** y, como hay datos de salud a escala, valorar una evaluación de
  impacto (EIPD) y la designación de un delegado de protección de datos.

**Brechas de seguridad**
- Si hay una brecha que afecte a datos personales, documéntala y notifícala a la AEPD en 72 horas.
- Si hay riesgo alto para las personas afectadas (los datos de salud lo suelen implicar), comunícaselo también
  a ellas.
- Medidas inmediatas:
  - Rotar los secretos (apartado 4); cambiar la clave secreta cierra todas las sesiones.
  - Revisar Sentry y los logs.
