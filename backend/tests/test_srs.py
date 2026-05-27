from app.services.srs import DEFAULT_EASE, MIN_EASE, SrsState, sm2


def fresh() -> SrsState:
    return SrsState(ease=DEFAULT_EASE, interval_days=0, repetitions=0, lapses=0)


def test_first_successful_review_schedules_one_day():
    s = sm2(fresh(), quality=4)
    assert s.interval_days == 1
    assert s.repetitions == 1
    assert s.lapses == 0


def test_second_successful_review_schedules_six_days():
    s = sm2(fresh(), quality=4)
    s = sm2(s, quality=4)
    assert s.interval_days == 6
    assert s.repetitions == 2


def test_third_review_multiplies_interval_by_ease():
    s = sm2(fresh(), quality=4)
    s = sm2(s, quality=4)
    s = sm2(s, quality=4)
    assert s.interval_days == round(6 * s.ease)


def test_lapse_resets_interval_and_repetitions_and_increments_lapses():
    s = sm2(fresh(), quality=4)
    s = sm2(s, quality=4)
    s = sm2(s, quality=0)
    assert s.interval_days == 1
    assert s.repetitions == 0
    assert s.lapses == 1


def test_ease_is_floored_at_min_ease_after_many_hard_reviews():
    s = fresh()
    for _ in range(50):
        s = sm2(s, quality=3)
    assert s.ease >= MIN_EASE


def test_easy_review_increases_ease():
    s = sm2(fresh(), quality=5)
    assert s.ease > DEFAULT_EASE


def test_hard_review_decreases_ease():
    s = sm2(fresh(), quality=3)
    assert s.ease < DEFAULT_EASE


def test_invalid_quality_raises():
    import pytest

    with pytest.raises(ValueError):
        sm2(fresh(), quality=7)
