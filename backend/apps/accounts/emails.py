"""Transactional emails. The text lives here (es/en/ca) because emails are rendered by the backend."""

import logging
import unicodedata

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger("apps.api")

SUPPORTED_LANGUAGES = ("es", "en", "ca")
DEFAULT_LANGUAGE = "es"
SUBJECT_TEXT_LIMIT = 80


def header_text(value: str, limit: int = SUBJECT_TEXT_LIMIT) -> str:
    """Text typed by staff (a workout name) made safe for an email header.

    One line (a line break would make Django refuse the whole email), without control or invisible
    characters (bidi overrides can disguise the subject) and at most `limit` characters.
    """
    text = " ".join(value.split())
    text = "".join(char for char in text if not unicodedata.category(char).startswith("C"))
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


PASSWORD_RESET = {
    "es": {
        "subject": "Restablece tu contraseña de entrenanutricion",
        "body": (
            "Hola, {name}:\n\n"
            "Hemos recibido una solicitud para restablecer la contraseña de tu cuenta.\n"
            "Abre este enlace para elegir una nueva. Solo sirve una vez y caduca en {minutes} "
            "minutos:\n\n{link}\n\n"
            "Si no lo has pedido tú, ignora este mensaje: tu contraseña no cambiará.\n\n"
            "El equipo de entrenanutricion"
        ),
    },
    "en": {
        "subject": "Reset your entrenanutricion password",
        "body": (
            "Hi {name},\n\n"
            "We received a request to reset the password of your account.\n"
            "Open this link to choose a new one. It works only once and expires in {minutes} "
            "minutes:\n\n{link}\n\n"
            "If you did not ask for it, ignore this message: your password will not change.\n\n"
            "The entrenanutricion team"
        ),
    },
    "ca": {
        "subject": "Restableix la contrasenya d'entrenanutricion",
        "body": (
            "Hola, {name}:\n\n"
            "Hem rebut una sol·licitud per restablir la contrasenya del teu compte.\n"
            "Obre aquest enllaç per triar-ne una de nova. Només serveix una vegada i caduca "
            "d'aquí a {minutes} minuts:\n\n{link}\n\n"
            "Si no ho has demanat tu, ignora aquest missatge: la contrasenya no canviarà.\n\n"
            "L'equip d'entrenanutricion"
        ),
    },
}


def language_from_header(header: str | None) -> str:
    """First supported language of an Accept-Language header (the app always sends one)."""
    for part in (header or "").split(","):
        code = part.split(";")[0].strip().lower().split("-")[0]
        if code in SUPPORTED_LANGUAGES:
            return code
    return DEFAULT_LANGUAGE


def send_password_reset_email(user, link: str, language: str) -> bool:
    """Send the reset link. Failures are logged, never shown (the response must not leak them)."""
    texts = PASSWORD_RESET.get(language, PASSWORD_RESET[DEFAULT_LANGUAGE])
    body = texts["body"].format(
        name=user.first_name or user.email,
        link=link,
        minutes=settings.PASSWORD_RESET_TIMEOUT // 60,
    )
    try:
        send_mail(texts["subject"], body, settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception:
        logger.exception("Could not send the password reset email", extra={"user_id": user.pk})
        return False
    return True


TRAINING_REMINDER = {
    "es": {
        "subject": "Hoy toca entrenar: {workout}",
        "body": (
            "Hola, {name}:\n\n"
            "Hoy es día de entreno. Te espera «{workout}» a las {time}.\n\n"
            "Abre tu plan: {link}\n\n"
            "¡Ánimo! Cada sesión cuenta.\n\n"
            "Si no quieres recibir estos recordatorios, desactívalos en tu perfil.\n\n"
            "El equipo de entrenanutricion"
        ),
    },
    "en": {
        "subject": "Today is a training day: {workout}",
        "body": (
            "Hi {name},\n\n"
            "Today is a training day. «{workout}» is waiting for you at {time}.\n\n"
            "Open your plan: {link}\n\n"
            "Keep it up! Every session counts.\n\n"
            "If you do not want these reminders, turn them off in your profile.\n\n"
            "The entrenanutricion team"
        ),
    },
    "ca": {
        "subject": "Avui toca entrenar: {workout}",
        "body": (
            "Hola, {name}:\n\n"
            "Avui és dia d'entrenament. T'espera «{workout}» a les {time}.\n\n"
            "Obre el teu pla: {link}\n\n"
            "Ànims! Cada sessió compta.\n\n"
            "Si no vols rebre aquests recordatoris, desactiva'ls al teu perfil.\n\n"
            "L'equip d'entrenanutricion"
        ),
    },
}


def send_training_reminder_email(user, workout: str, at) -> bool:
    """Reminder of a training day in the user's language. Failures are logged."""
    texts = TRAINING_REMINDER.get(user.language, TRAINING_REMINDER[DEFAULT_LANGUAGE])
    subject = texts["subject"].format(workout=header_text(workout))
    body = texts["body"].format(
        name=user.first_name or user.email,
        workout=workout,
        time=at.strftime("%H:%M"),
        link=f"{settings.FRONTEND_URL}/app/training",
    )
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception:
        logger.exception("Could not send the training reminder", extra={"user_id": user.pk})
        return False
    return True


EMAIL_VERIFICATION = {
    "es": {
        "subject": "Confirma tu correo de entrenanutricion",
        "body": (
            "Hola, {name}:\n\n"
            "Gracias por registrarte. Confirma que esta dirección es tuya abriendo este enlace "
            "(caduca en {days} días):\n\n{link}\n\n"
            "La usaremos para recuperar tu cuenta y, si los activas, para tus recordatorios.\n\n"
            "Si no te has registrado tú, ignora este mensaje.\n\n"
            "El equipo de entrenanutricion"
        ),
    },
    "en": {
        "subject": "Confirm your entrenanutricion email",
        "body": (
            "Hi {name},\n\n"
            "Thanks for signing up. Confirm this address is yours by opening this link "
            "(it expires in {days} days):\n\n{link}\n\n"
            "We will use it to recover your account and, if you turn them on, for your "
            "reminders.\n\n"
            "If you did not sign up, ignore this message.\n\n"
            "The entrenanutricion team"
        ),
    },
    "ca": {
        "subject": "Confirma el teu correu d'entrenanutricion",
        "body": (
            "Hola, {name}:\n\n"
            "Gràcies per registrar-te. Confirma que aquesta adreça és teva obrint aquest enllaç "
            "(caduca d'aquí a {days} dies):\n\n{link}\n\n"
            "La farem servir per recuperar el teu compte i, si els actives, per als teus "
            "recordatoris.\n\n"
            "Si no t'has registrat tu, ignora aquest missatge.\n\n"
            "L'equip d'entrenanutricion"
        ),
    },
}


def send_email_verification_email(user, link: str, language: str) -> bool:
    """Link to confirm the address of a new account. Failures are logged."""
    texts = EMAIL_VERIFICATION.get(language, EMAIL_VERIFICATION[DEFAULT_LANGUAGE])
    body = texts["body"].format(
        name=user.first_name or user.email,
        link=link,
        days=settings.EMAIL_VERIFICATION_MAX_AGE // 86400,
    )
    try:
        send_mail(texts["subject"], body, settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception:
        logger.exception("Could not send the verification email", extra={"user_id": user.pk})
        return False
    return True
