import re

from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import WEIGHT_RANGE_KG
from apps.accounts.serializers import WeightPointSerializer
from apps.core.utils import HISTORY_YEARS, FileUrlField, years_before
from apps.progress import adherence
from apps.progress.models import BadgeCode
from apps.training.models import WorkoutSession
from apps.training.serializers import MotivationSerializer, SessionWorkoutNameMixin

WEIGHT_HISTORY_YEARS = HISTORY_YEARS


MONTH_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


class DashboardQuerySerializer(serializers.Serializer):
    month = serializers.CharField(required=False)

    def validate_month(self, value):
        match = MONTH_RE.match(value)
        if not match:
            raise serializers.ValidationError("Use the YYYY-MM format.", code="invalid_month")
        return int(match.group(1)), int(match.group(2))


class NextWorkoutSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="Id of the user's workout (UserPlanWorkout).")
    workout_name = serializers.CharField()
    scheduled_date = serializers.DateField()
    target_datetime = serializers.DateTimeField()


class WeekDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    scheduled = serializers.BooleanField(help_text="A training day of the client's calendar.")
    completed = serializers.BooleanField(help_text="At least one workout was completed that day.")


class DashboardSerializer(serializers.Serializer):
    month = serializers.CharField()
    completed_days = serializers.ListField(child=serializers.DateField())
    scheduled_days = serializers.ListField(child=serializers.DateField())
    next_workout = NextWorkoutSerializer(allow_null=True)
    plan_name = serializers.CharField()
    plan_progress = serializers.IntegerField()
    cycle = serializers.IntegerField()
    total_sessions = serializers.IntegerField()
    week = WeekDaySerializer(many=True, help_text="This week, Monday to Sunday.")
    streak_weeks = serializers.IntegerField(
        help_text="Weeks in a row, within the current plan, with every scheduled session done."
    )
    motivation = MotivationSerializer()


class WeekStatsSerializer(serializers.Serializer):
    start = serializers.DateField(help_text="Monday of the week.")
    sessions = serializers.IntegerField()
    minutes = serializers.IntegerField()
    volume_kg = serializers.FloatField(
        help_text="Repetitions × kilos of the sets with load logged that week."
    )


class MuscleGroupStatsSerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    sets = serializers.IntegerField(help_text="Sets of the last 28 days that worked this group.")


class TrainingStatsSerializer(serializers.Serializer):
    weeks = WeekStatsSerializer(many=True, help_text="The last 12 weeks, oldest first.")
    muscle_groups = MuscleGroupStatsSerializer(many=True, help_text="Most worked first.")


class SessionHistorySerializer(SessionWorkoutNameMixin, serializers.ModelSerializer):
    class Meta:
        model = WorkoutSession
        fields = [
            "id",
            "workout_id",
            "workout_name",
            "cycle",
            "completed_at",
            "total_sets",
            "total_reps",
            "duration_minutes",
        ]


class WeightRecordInputSerializer(serializers.Serializer):
    weight_kg = serializers.DecimalField(
        max_digits=5,
        decimal_places=1,
        min_value=WEIGHT_RANGE_KG[0],
        max_value=WEIGHT_RANGE_KG[1],
    )
    date = serializers.DateField(required=False)

    def validate_date(self, value):
        today = timezone.localdate()
        if value > today:
            raise serializers.ValidationError(
                "The date cannot be in the future.", code="future_date"
            )
        # One record per day, and only for the last years: the history stays bounded.
        if value < years_before(today, WEIGHT_HISTORY_YEARS):
            raise serializers.ValidationError(
                f"The date cannot be more than {WEIGHT_HISTORY_YEARS} years ago.",
                code="date_too_old",
            )
        return value


class WeightSummarySerializer(serializers.Serializer):
    goal = serializers.CharField()
    initial_weight_kg = serializers.FloatField()
    target_weight_kg = serializers.FloatField()
    current_weight_kg = serializers.FloatField(allow_null=True)
    records = WeightPointSerializer(many=True)


def badge_codes_field():
    return serializers.ListField(
        child=serializers.ChoiceField(choices=BadgeCode.choices),
        help_text="Badges awarded by this request (translated by code in the app).",
    )


class WeightRecordResultSerializer(WeightSummarySerializer):
    new_badges = badge_codes_field()


class BadgeSerializer(serializers.Serializer):
    code = serializers.ChoiceField(choices=BadgeCode.choices)
    earned = serializers.BooleanField()
    awarded_at = serializers.DateTimeField(allow_null=True)
    current = serializers.IntegerField()
    target = serializers.IntegerField()


class BadgesSerializer(serializers.Serializer):
    earned_count = serializers.IntegerField()
    total = serializers.IntegerField()
    new_badges = badge_codes_field()
    badges = BadgeSerializer(many=True)


# --- Adherence (staff, phase 12) -----------------------------------------------------------------


class AdherenceQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=adherence.STATUSES, required=False)
    search = serializers.CharField(required=False, allow_blank=True, max_length=100)


class AdherenceUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField(source="get_full_name")
    email = serializers.EmailField()
    profile_photo_url = FileUrlField(source="profile_photo")


class AdherenceWeekSerializer(serializers.Serializer):
    start = serializers.DateField()
    end = serializers.DateField()
    sessions = serializers.IntegerField()
    scheduled = serializers.IntegerField()


class AdherenceRowSerializer(serializers.Serializer):
    user = AdherenceUserSerializer()
    plan_name = serializers.CharField()
    plan_started = serializers.DateField()
    sessions = serializers.IntegerField(
        help_text="Days trained in the last 28 days (since the plan started)."
    )
    scheduled = serializers.IntegerField(help_text="Training days the weekly calendar scheduled.")
    adherence_percent = serializers.IntegerField(
        allow_null=True, help_text="Null while nothing has been scheduled yet."
    )
    last_session_date = serializers.DateField(allow_null=True)
    days_since_last_session = serializers.IntegerField(allow_null=True)
    current_weight_kg = serializers.FloatField(allow_null=True)
    weight_change_kg = serializers.FloatField(
        allow_null=True, help_text="Against the weight of 28 days ago (or the initial one)."
    )
    status = serializers.ChoiceField(choices=adherence.STATUSES)


class ClientAdherenceSerializer(AdherenceRowSerializer):
    weeks = AdherenceWeekSerializer(many=True, help_text="Last four weeks, oldest first.")


class AdherenceCountSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=adherence.STATUSES)
    count = serializers.IntegerField()


class AdherenceBandSerializer(serializers.Serializer):
    low = serializers.IntegerField(help_text="Lowest percentage of the band.")
    high = serializers.IntegerField(help_text="Highest percentage of the band.")
    count = serializers.IntegerField()


class AdherenceListSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    counts = AdherenceCountSerializer(
        many=True, help_text="Clients per status, worst first (before the status filter)."
    )
    distribution = AdherenceBandSerializer(
        many=True,
        help_text="Clients per band of 20 points of adherence (before the status filter); "
        "clients with nothing scheduled yet are left out.",
    )
    average_percent = serializers.IntegerField(
        allow_null=True, help_text="Mean adherence of those clients (before the status filter)."
    )
    results = AdherenceRowSerializer(many=True)
