"""Today's maximum from a daily weather forecast."""

from datetime import UTC, date, timedelta, timezone

from core.forecast import ForecastMaximum, today_max


def test_today_max_uses_the_local_date():
    zone = timezone(timedelta(hours=2))
    forecast = [{"datetime": "2026-11-18T23:30:00-08:00", "temperature": 31}]
    assert today_max(forecast, date(2026, 11, 19), zone) == 31


def test_today_max_skips_missing_bad_and_future_entries():
    zone = UTC
    forecast = [
        {"datetime": "2026-11-19T12:00:00+00:00"},
        {"datetime": "2026-11-19T12:00:00+00:00", "temperature": "unknown"},
        {"datetime": "2026-11-20T12:00:00+00:00", "temperature": 29},
    ]
    assert today_max(forecast, date(2026, 11, 19), zone) is None


def test_forecast_maximum_keeps_today_after_failure_and_drops_yesterday():
    forecast = ForecastMaximum()
    today = date(2026, 11, 18)
    forecast.update(30.0, today)
    assert forecast.today(today) == 30.0
    forecast.update(None, today)
    assert forecast.today(today) == 30.0

    tomorrow = today + timedelta(days=1)
    forecast.update(None, tomorrow)
    assert forecast.today(tomorrow) is None
