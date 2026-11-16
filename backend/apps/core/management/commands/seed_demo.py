"""Idempotent demo data: catalog, staff, clients in every state and a client with history."""

import random
import textwrap
import unicodedata
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

from apps.accounts import services
from apps.accounts.models import (
    DietPreferences,
    Goal,
    HealthInfo,
    Role,
    User,
    UserDetails,
)
from apps.assignments.services import (
    assign_nutrition_plan,
    assign_training_plan,
    recompute_user_status,
)
from apps.core import demo_data, demo_translations
from apps.notes.models import Note
from apps.notes.services import add_note
from apps.nutrition.diary import add_entry
from apps.nutrition.menus import portion
from apps.nutrition.models import Food, FoodLogEntry, MealPlan, MealPlanItem
from apps.progress.models import WeightRecord
from apps.training import schedule
from apps.training.constants import MUSCLE_GROUPS
from apps.training.models import (
    Exercise,
    ExerciseLog,
    ExerciseMedia,
    ExerciseSet,
    ExerciseStep,
    MuscleGroup,
    TrainingPlan,
    TrainingPlanWorkout,
    UserPlanWorkout,
    UserWorkoutStatus,
    Workout,
    WorkoutExercise,
    WorkoutSession,
)

PALETTE = ["#1f8a4c", "#2d6cdf", "#7b3fbf", "#c2410c", "#0f766e", "#be123c", "#4d7c0f"]
GOALS = [Goal.LOSE_WEIGHT, Goal.GAIN_MUSCLE, Goal.MAINTAIN]
SESSION_TIME = time(18, 30)


def placeholder_image(title: str, index: int) -> ContentFile:
    """Generated cover (no third-party images): solid colour with the title."""
    image = Image.new("RGB", (640, 400), PALETTE[index % len(PALETTE)])
    draw = ImageDraw.Draw(image)
    font, text = None, title
    for name in ("DejaVuSans.ttf", "arial.ttf", "Arial.ttf"):
        try:
            font = ImageFont.truetype(name, 44)
            break
        except OSError:
            continue
    if font is None:
        # Pillow's built-in font only covers ASCII: drop accents ("días" → "dias").
        font = ImageFont.load_default(size=44)
        text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    lines = textwrap.wrap(text, width=18)
    line_height = 56
    top = (400 - line_height * len(lines)) // 2
    for position, line in enumerate(lines):
        width = draw.textlength(line, font=font)
        draw.text(((640 - width) / 2, top + position * line_height), line, fill="white", font=font)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"{slugify(title) or 'cover'}.png")


class DemoSeeder:
    def __init__(self, today: date, password: str = demo_data.DEMO_PASSWORD):
        self.today = today
        self.password = password

    # --- Catalog ---------------------------------------------------------------------------------

    def ensure_muscle_groups(self) -> dict[str, MuscleGroup]:
        for slug, name in MUSCLE_GROUPS:
            MuscleGroup.objects.update_or_create(slug=slug, defaults={"name": name})
        return {group.slug: group for group in MuscleGroup.objects.all()}

    def ensure_exercises(self, groups) -> dict[str, Exercise]:
        exercises = {}
        for index, row in enumerate(demo_data.EXERCISES):
            name, slugs, description, steps, technique, mistakes, benefits = row
            exercise, created = Exercise.objects.get_or_create(
                name=name,
                defaults={
                    "description": description,
                    "technique": technique,
                    "common_mistakes": mistakes,
                    "benefits": benefits,
                },
            )
            if created:
                exercise.muscle_groups.set(groups[slug] for slug in slugs)
                ExerciseStep.objects.bulk_create(
                    ExerciseStep(exercise=exercise, order=position, text=text)
                    for position, text in enumerate(steps, start=1)
                )
            if not exercise.media.exists():
                ExerciseMedia.objects.create(
                    exercise=exercise, file=placeholder_image(name, index), order=1
                )
            exercises[name] = exercise
        return exercises

    def ensure_workouts(self, exercises) -> dict[str, Workout]:
        workouts = {}
        for index, (name, description, items) in enumerate(demo_data.WORKOUTS):
            workout, created = Workout.objects.get_or_create(
                name=name, defaults={"description": description}
            )
            if created:
                WorkoutExercise.objects.bulk_create(
                    WorkoutExercise(
                        workout=workout,
                        exercise=exercises[exercise_name],
                        order=position,
                        sets=sets,
                        reps=reps,
                        rest_seconds=rest,
                    )
                    for position, (exercise_name, sets, reps, rest) in enumerate(items, start=1)
                )
                workout.media = placeholder_image(name, index)
                workout.save()
            workouts[name] = workout
        return workouts

    def ensure_training_plans(self, workouts) -> dict[str, TrainingPlan]:
        plans = {}
        for index, row in enumerate(demo_data.TRAINING_PLANS):
            name, description, goal, difficulty, equipment, weeks, sequence = row
            plan, created = TrainingPlan.objects.get_or_create(
                name=name,
                defaults={
                    "description": description,
                    "goal": goal,
                    "difficulty": difficulty,
                    "equipment": equipment,
                    "duration_weeks": weeks,
                },
            )
            if created:
                TrainingPlanWorkout.objects.bulk_create(
                    TrainingPlanWorkout(plan=plan, workout=workouts[workout_name], order=position)
                    for position, workout_name in enumerate(sequence, start=1)
                )
                plan.media = placeholder_image(name, index + 3)
                plan.save()
            plans[goal] = plan
        return plans

    def ensure_foods(self) -> None:
        for name, category, *values in demo_data.FOODS:
            Food.objects.get_or_create(
                name=name,
                defaults={
                    "category": category,
                    **dict(zip(demo_data.FOOD_COLUMNS, values, strict=True)),
                },
            )

    def ensure_meal_plans(self) -> dict[str, MealPlan]:
        plans = {}
        for row in demo_data.MEAL_PLANS:
            name, category, label, kcal, proteins, carbs, fats, distribution, description = row
            plan, _ = MealPlan.objects.get_or_create(
                name=name,
                defaults={
                    "category": category,
                    "diet_label": label,
                    "calories": kcal,
                    "proteins_g": proteins,
                    "carbs_g": carbs,
                    "fats_g": fats,
                    "meal_distribution": distribution,
                    "description": description,
                },
            )
            plans.setdefault(category, plan)
        return plans

    # --- Users -----------------------------------------------------------------------------------

    def ensure_user(self, email, first_name, last_name, role, **extra) -> tuple[User, bool]:
        user = User.objects.filter(email=email).first()
        if user is not None:
            # Demo users always have the current consents (no consent screen in the demo).
            if user.consent_required:
                services.record_consent(user, health_data=True)
            if user.email_verified_at is None:
                user.email_verified_at = timezone.now()
                user.save(update_fields=["email_verified_at", "updated_at"])
            return user, False
        create = User.objects.create_superuser if role == Role.ADMIN else User.objects.create_user
        user = create(
            email=email,
            password=self.password,
            first_name=first_name,
            last_name=last_name,
            role=role,
            birth_date=extra.pop("birth_date", date(1990, 1, 1)),
            gender=extra.pop("gender", "O"),
            terms_accepted_at=timezone.now(),
            privacy_policy_version=settings.PRIVACY_POLICY_VERSION,
            privacy_accepted_at=timezone.now(),
            health_consent_at=timezone.now(),
            email_verified_at=timezone.now(),
            **extra,
        )
        return user, True

    def ensure_staff(self) -> dict[str, User]:
        staff = {}
        for email, first_name, last_name, role in demo_data.STAFF_USERS:
            staff[role], _ = self.ensure_user(email, first_name, last_name, role)
        return staff

    def onboard(self, user, goal, weight_kg, change_kg, days, on_date) -> None:
        if UserDetails.objects.filter(user=user).exists():
            return
        UserDetails.objects.create(
            user=user,
            height_cm=170,
            initial_weight_kg=weight_kg,
            goal=goal,
            target_weight_change_kg=0 if goal == Goal.MAINTAIN else change_kg,
            weekly_training_days=days,
            daily_training_time="1_2h",
            physical_activity_level="moderate",
            usual_exercise_types=["strength", "cardio"],
            available_equipment=["full_gym"],
            training_preference="gym",
        )
        DietPreferences.objects.create(
            user=user,
            diet_type="omnivore",
            food_restrictions=["none"],
            meals_per_day=4,
            macronutrient_intake_self_assessment="balanced",
        )
        HealthInfo.objects.create(user=user, medical_conditions=["none"], supplements=["none"])
        WeightRecord.objects.get_or_create(
            user=user, date=on_date, defaults={"weight_kg": weight_kg}
        )
        recompute_user_status(user)

    def assign(self, user, training_plan, meal_plan, staff, started: date) -> None:
        if not user.training_plans.filter(is_current=True).exists():
            assignment = assign_training_plan(user, training_plan, staff[Role.TRAINER])
            assignment.date_started = started
            assignment.save(update_fields=["date_started"])
        if not user.nutrition_plans.filter(is_current=True).exists():
            assign_nutrition_plan(user, meal_plan, staff[Role.NUTRITIONIST])

    def history(self, user, start: date, end: date, skip_ratio: float) -> int:
        """Completed sessions on the default calendar between `start` and `end` (inclusive)."""
        if WorkoutSession.objects.filter(user=user).exists() or end < start:
            return 0
        assignment = user.training_plans.select_related("plan").get(is_current=True)
        rows = list(
            UserPlanWorkout.objects.filter(user_plan=assignment)
            .select_related("plan_workout__workout")
            .order_by("plan_workout__order")
        )
        weekdays = schedule.training_weekdays(
            user.details.weekly_training_days, user.details.training_days
        )
        rng = random.Random(user.email)
        sessions: list[WorkoutSession] = []
        day = start
        while day <= end:
            if day.weekday() in weekdays and rng.random() >= skip_ratio:
                row = rows[len(sessions) % len(rows)]
                cycle = len(sessions) // len(rows) + 1
                sessions.append(self._session(user, assignment, row, day, cycle))
            day += timedelta(days=1)
        self._apply_sequence_state(assignment, rows, sessions)
        return len(sessions)

    def _session(self, user, assignment, row, day, cycle: int) -> WorkoutSession:
        workout = row.plan_workout.workout
        items = list(workout.items.select_related("exercise"))
        moment = timezone.make_aware(datetime.combine(day, SESSION_TIME))
        session = WorkoutSession.objects.create(
            user=user,
            user_plan=assignment,
            workout=workout,
            workout_name=workout.name,
            cycle=cycle,
            completed_at=moment,
            total_sets=sum(item.sets for item in items),
            total_reps=sum(item.sets * item.reps for item in items),
            duration_minutes=45,
        )
        logs = ExerciseLog.objects.bulk_create(
            ExerciseLog(
                user=user,
                workout=workout,
                exercise=item.exercise,
                session=session,
                date=day,
                sets_completed=item.sets,
                reps_completed=item.sets * item.reps,
                rest_time=item.rest_seconds,
            )
            for item in items
        )
        ExerciseSet.objects.bulk_create(
            ExerciseSet(log=log, number=number, reps=item.reps)
            for log, item in zip(logs, items, strict=True)
            for number in range(1, item.sets + 1)
        )
        return session

    def apply_demo_loads(self, user) -> None:
        """Progressive loads for the weighted exercises of the demo sessions (once)."""
        sets = list(
            ExerciseSet.objects.filter(
                log__user=user,
                weight_kg__isnull=True,
                log__exercise__name__in=list(demo_data.DEMO_LOADS),
            )
            .select_related("log__exercise")
            .order_by("log__date", "log_id", "number")
        )
        sessions_seen: dict[int, list[int]] = {}
        for entry in sets:
            logs = sessions_seen.setdefault(entry.log.exercise_id, [])
            if entry.log_id not in logs:
                logs.append(entry.log_id)
            start, step = demo_data.DEMO_LOADS[entry.log.exercise.name]
            increases = min((len(logs) - 1) // 2, demo_data.DEMO_LOAD_STEPS)
            entry.weight_kg = Decimal(str(start + step * increases))
        ExerciseSet.objects.bulk_update(sets, ["weight_kg"])

    def _apply_sequence_state(self, assignment, rows, sessions) -> None:
        total = len(rows)
        done_in_cycle = len(sessions) % total
        for position, row in enumerate(rows):
            if position < done_in_cycle:
                row.status = UserWorkoutStatus.COMPLETED
                row.completed_at = sessions[len(sessions) - done_in_cycle + position].completed_at
            else:
                row.status = (
                    UserWorkoutStatus.AVAILABLE
                    if position == done_in_cycle
                    else UserWorkoutStatus.LOCKED
                )
                row.completed_at = None
        UserPlanWorkout.objects.bulk_update(rows, ["status", "completed_at"])
        full_cycles = len(sessions) // total
        assignment.cycle = full_cycles + 1
        assignment.progress = round(done_in_cycle * 100 / total)
        if full_cycles:
            last_of_cycle = sessions[full_cycles * total - 1].completed_at
            assignment.date_completed = timezone.localdate(last_of_cycle)
        assignment.save(update_fields=["cycle", "progress", "date_completed"])

    def weights(self, user, start: date, end: date, start_kg: float, end_kg: float) -> None:
        rng = random.Random(f"weight-{user.email}")
        weeks = max((end - start).days // 7, 1)
        for week in range(weeks + 1):
            day = min(start + timedelta(weeks=week), end)
            value = start_kg + (end_kg - start_kg) * week / weeks + rng.uniform(-0.3, 0.3)
            WeightRecord.objects.get_or_create(
                user=user, date=day, defaults={"weight_kg": Decimal(f"{value:.1f}")}
            )

    def ensure_main_clients(self, training_plans, meal_plans, staff) -> None:
        for email, first, last, gender, birth, status in demo_data.MAIN_CLIENTS:
            joined_days_ago = {"active": 100, "pending_assignment": 14, "pending_onboarding": 0}
            joined = self.today - timedelta(days=joined_days_ago[status])
            user, _ = self.ensure_user(
                email,
                first,
                last,
                Role.CLIENT,
                gender=gender,
                birth_date=date.fromisoformat(birth),
                date_joined=timezone.make_aware(datetime.combine(joined, time(10))),
            )
            if status == "pending_onboarding":
                continue
            self.onboard(user, Goal.LOSE_WEIGHT, Decimal("78.0"), Decimal("6.0"), 3, joined)
            if status != "active":
                continue
            started = self.today - timedelta(days=91)
            self.assign(
                user, training_plans[Goal.LOSE_WEIGHT], meal_plans["weight_loss"], staff, started
            )
            user.refresh_from_db()
            self.history(user, started, self.today - timedelta(days=1), skip_ratio=0.15)
            self.apply_demo_loads(user)
            self.weights(user, joined, self.today - timedelta(days=1), 78.0, 74.6)

    def ensure_extra_clients(self, training_plans, meal_plans, staff) -> None:
        categories = {
            Goal.LOSE_WEIGHT: "weight_loss",
            Goal.GAIN_MUSCLE: "muscle_gain",
            Goal.MAINTAIN: "maintenance",
        }
        for index, row in enumerate(demo_data.EXTRA_CLIENTS):
            first, last, gender, year_offset, month, status = row
            year = self.today.year + year_offset
            if year == self.today.year:
                month = min(month, self.today.month)
            day = (
                min(10, self.today.day)
                if (year, month)
                == (
                    self.today.year,
                    self.today.month,
                )
                else 10
            )
            joined = date(year, month, day)
            email = f"{slugify(first)}.{slugify(last)}@demo.entrenanutricion.dev"
            user, _ = self.ensure_user(
                email,
                first,
                last,
                Role.CLIENT,
                gender=gender,
                birth_date=date(1985 + index % 15, 1 + index % 12, 1 + index % 28),
                date_joined=timezone.make_aware(datetime.combine(joined, time(10))),
            )
            if status == "pending_onboarding":
                continue
            goal = GOALS[index % len(GOALS)]
            self.onboard(user, goal, Decimal(65 + index), Decimal("4.0"), 2 + index % 4, joined)
            if status != "active":
                continue
            self.assign(user, training_plans[goal], meal_plans[categories[goal]], staff, joined)
            user.refresh_from_db()
            end = min(joined + timedelta(days=35), self.today - timedelta(days=1))
            self.history(user, joined, end, skip_ratio=0.3)
            self.apply_demo_loads(user)

    def ensure_notes(self, staff) -> None:
        """A conversation for the demo client and unread notes for the staff inbox (once)."""
        main = User.objects.get(email=demo_data.MAIN_CLIENTS[0][0])
        others = User.objects.filter(
            email__endswith="@demo.entrenanutricion.dev", status="active", is_active=True
        ).order_by("id")[: len(demo_data.DEMO_INBOX_NOTES)]
        threads = [(main, demo_data.DEMO_NOTES)] + [
            (client, [("client", 1 + index, False, text)])
            for index, (client, text) in enumerate(
                zip(others, demo_data.DEMO_INBOX_NOTES, strict=False)
            )
        ]
        now = timezone.now()
        for client, notes in threads:
            if Note.objects.filter(client=client).exists():
                continue
            for author, days_ago, read, body in notes:
                note = add_note(client, client if author == "client" else staff[author], body)
                written = now - timedelta(days=days_ago, hours=3)
                Note.objects.filter(pk=note.pk).update(
                    created_at=written, read_at=written + timedelta(hours=2) if read else None
                )

    def ensure_menus(self) -> None:
        """A sample day menu for every plan without one, scaled to its calories."""
        foods = {food.name: food for food in Food.objects.all()}
        for plan in MealPlan.objects.filter(menu_items__isnull=True):
            template = demo_data.DEMO_MENUS[plan.category]
            kcal = sum(portion(foods[name], grams)["calories"] for _, name, grams in template)
            factor = Decimal(plan.calories) / kcal
            MealPlanItem.objects.bulk_create(
                MealPlanItem(
                    meal_plan=plan,
                    meal=meal,
                    food=foods[name],
                    grams=max(5, int(round(grams * factor / 5)) * 5),
                    order=index,
                )
                for index, (meal, name, grams) in enumerate(template)
            )

    def ensure_food_log(self) -> None:
        """The demo client followed the menu (more or less) the last days."""
        user = User.objects.get(email=demo_data.MAIN_CLIENTS[0][0])
        if FoodLogEntry.objects.filter(user=user).exists():
            return
        plan = user.nutrition_plans.get(is_current=True).plan
        items = list(plan.menu_items.select_related("food"))
        rng = random.Random(f"food-log-{user.email}")
        for offset in range(demo_data.DEMO_FOOD_LOG_DAYS, 0, -1):
            day = self.today - timedelta(days=offset)
            for item in items:
                if item.meal == "snacks" and rng.random() < 0.3:
                    continue
                grams = max(5, int(round(item.grams * rng.uniform(0.8, 1.2) / 5)) * 5)
                add_entry(user, day, item.meal, item.food, grams)

    def ensure_translations(self) -> None:
        """English and Catalan texts of the demo catalog (only where there are none yet)."""
        catalog = (
            (Exercise, demo_translations.EXERCISES),
            (Workout, demo_translations.WORKOUTS),
            (TrainingPlan, demo_translations.TRAINING_PLANS),
            (MealPlan, demo_translations.MEAL_PLANS),
        )
        for model, texts in catalog:
            for item in model.objects.filter(name__in=list(texts), translations={}):
                item.translations = texts[item.name]
                item.save(update_fields=["translations", "updated_at"])
        for food in Food.objects.filter(name__in=list(demo_translations.FOODS), translations={}):
            names = demo_translations.FOODS[food.name]
            food.translations = {language: {"name": name} for language, name in names.items()}
            food.save(update_fields=["translations", "updated_at"])

    def run(self) -> None:
        groups = self.ensure_muscle_groups()
        exercises = self.ensure_exercises(groups)
        workouts = self.ensure_workouts(exercises)
        training_plans = self.ensure_training_plans(workouts)
        meal_plans = self.ensure_meal_plans()
        self.ensure_foods()
        self.ensure_translations()
        staff = self.ensure_staff()
        self.ensure_main_clients(training_plans, meal_plans, staff)
        self.ensure_extra_clients(training_plans, meal_plans, staff)
        self.ensure_notes(staff)
        self.ensure_menus()
        self.ensure_food_log()


def demo_password() -> str:
    """The public README password only in development: elsewhere it would open every demo account,
    an admin among them."""
    if settings.DEBUG:
        return settings.DEMO_PASSWORD or demo_data.DEMO_PASSWORD
    password = settings.DEMO_PASSWORD
    if not password or password == demo_data.DEMO_PASSWORD:
        raise CommandError(
            "Outside development the demo accounts need a password of their own: set DEMO_PASSWORD "
            "(not the one published in the README)."
        )
    try:
        validate_password(password)
    except ValidationError as exc:
        raise CommandError("DEMO_PASSWORD is too weak: " + " ".join(exc.messages)) from exc
    return password


class Command(BaseCommand):
    help = (
        "Load idempotent demo data. Development uses the password in the README; elsewhere "
        "(--allow-production) the demo accounts get DEMO_PASSWORD."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--allow-production",
            action="store_true",
            help="Run even when DEBUG is off (never use real users' environments).",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["allow_production"]:
            raise CommandError("seed_demo only runs with DEBUG enabled (or --allow-production).")
        password = demo_password()
        with transaction.atomic():
            DemoSeeder(timezone.localdate(), password).run()
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data ready: {User.objects.count()} users, {Exercise.objects.count()} "
                f"exercises, {Workout.objects.count()} workouts, "
                f"{TrainingPlan.objects.count()} training plans, "
                f"{MealPlan.objects.count()} meal plans, {Food.objects.count()} foods, "
                f"{WorkoutSession.objects.count()} sessions."
            )
        )
