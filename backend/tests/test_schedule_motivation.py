from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.utils import timezone

from apps.progress.motivation import (
    build_motivation,
    session_milestone,
    weight_key,
    weight_progress_pct,
)
from apps.training.schedule import (
    scheduled_dates_in_month,
    target_datetime,
    training_dates_from,
    training_weekdays,
)

MON, TUE, WED, THU, FRI, SAT = range(6)


class TestDefaultCalendar:
    @pytest.mark.parametrize(
        ("days", "weekdays"),
        [
            (1, (MON,)),
            (2, (MON, THU)),
            (3, (MON, WED, FRI)),
            (4, (MON, TUE, THU, FRI)),
            (5, (MON, TUE, WED, THU, FRI)),
            (6, (MON, TUE, WED, THU, FRI, SAT)),
            (None, (MON, WED, FRI)),
        ],
    )
    def test_default_weekdays(self, days, weekdays):
        assert training_weekdays(days) == weekdays

    def test_training_dates_from_a_non_training_day(self):
        # 2026-11-03 is a Tuesday.
        dates = training_dates_from(date(2026, 11, 3), (MON, WED, FRI), 4)

        assert dates == [
            date(2026, 11, 4),
            date(2026, 11, 6),
            date(2026, 11, 9),
            date(2026, 11, 11),
        ]

    def test_scheduled_dates_in_month(self):
        dates = scheduled_dates_in_month(2026, 11, (MON,), since=date(2026, 11, 10))

        assert dates == [date(2026, 11, 16), date(2026, 11, 23), date(2026, 11, 30)]

    def test_target_datetime_uses_configured_time(self, settings):
        settings.DEFAULT_TRAINING_TIME = "07:45"

        target = target_datetime(date(2026, 11, 2))

        assert timezone.localtime(target).replace(tzinfo=None) == datetime(2026, 11, 2, 7, 45)


class TestMotivation:
    @pytest.mark.parametrize(
        ("sessions", "milestone"),
        [(0, 0), (1, 1), (4, 1), (5, 5), (9, 5), (10, 10), (30, 25), (75, 50), (250, 100)],
    )
    def test_session_milestones(self, sessions, milestone):
        assert session_milestone(sessions) == milestone

    @pytest.mark.parametrize(
        ("goal", "current", "key"),
        [
            ("lose_weight", "80", "not_started"),
            ("lose_weight", "81", "not_started"),
            ("lose_weight", "78", "started"),
            ("lose_weight", "77.5", "halfway"),
            ("lose_weight", "75", "reached"),
            ("lose_weight", "74", "reached"),
            ("gain_muscle", "83", "halfway"),
            ("maintain", "80.8", "maintain_on_track"),
            ("maintain", "82", "maintain_off_track"),
        ],
    )
    def test_weight_keys(self, goal, current, key):
        initial = Decimal("80")
        target = {"lose_weight": Decimal("75"), "gain_muscle": Decimal("85")}.get(goal, initial)

        assert weight_key(goal, initial, target, Decimal(current)) == f"motivation.weight.{key}"

    def test_weight_progress_edge_cases(self):
        assert weight_progress_pct("maintain", Decimal(80), Decimal(80), Decimal(79)) is None
        assert weight_progress_pct("lose_weight", Decimal(80), Decimal(75), None) is None
        assert weight_key("lose_weight", Decimal(80), Decimal(75), None) is None

    def test_build_motivation(self):
        details = SimpleNamespace(
            goal="lose_weight", initial_weight_kg=Decimal("80"), target_weight_kg=Decimal("75")
        )

        result = build_motivation(12, details, Decimal("77"))

        assert result == {
            "keys": ["motivation.sessions.t10", "motivation.weight.halfway"],
            "params": {"sessions": 12, "remaining_kg": 2.0, "weight_progress_pct": 60},
        }

    def test_build_motivation_without_details(self):
        assert build_motivation(0) == {
            "keys": ["motivation.sessions.t0"],
            "params": {"sessions": 0},
        }
