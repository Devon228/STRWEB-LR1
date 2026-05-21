from datetime import date
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from django.utils import timezone

from pharmacy.validators import (
    validate_adult_age,
    validate_belarus_phone,
    validate_not_future_datetime,
)

FROZEN_TODAY = date(2026, 5, 21)


@pytest.mark.parametrize(
    'phone,should_raise',
    [
        ('+375 (29) 123-45-67', False),
        ('+375 (29) 999-99-99', False),
        ('+375 (29) 123-45-6', True),
        ('375 (29) 123-45-67', True),
        ('+375 (33) 123-45-67', True),
        ('+375 (29) 1234567', True),
        ('', True),
        ('invalid', True),
    ],
)
def test_validate_belarus_phone(phone, should_raise):
    if should_raise:
        with pytest.raises(ValidationError) as exc:
            validate_belarus_phone(phone)
        assert exc.value.code == 'invalid_phone'
    else:
        validate_belarus_phone(phone)


@pytest.mark.parametrize(
    'birth_date,should_raise,label',
    [
        (date(2008, 6, 21), True, '17_years_11_months'),
        (date(2008, 5, 21), False, 'exactly_18_years'),
        (date(2000, 1, 1), False, 'clearly_adult'),
        (date(2010, 12, 31), True, 'under_18'),
        (None, False, 'none_skipped'),
    ],
)
def test_validate_adult_age(birth_date, should_raise, label):
    with patch('pharmacy.validators.date') as mock_date:
        mock_date.today.return_value = FROZEN_TODAY
        if should_raise:
            with pytest.raises(ValidationError) as exc:
                validate_adult_age(birth_date)
            assert exc.value.code == 'underage'
        else:
            validate_adult_age(birth_date)


@pytest.mark.django_db
def test_validate_not_future_datetime_rejects_tomorrow():
    tomorrow = timezone.now() + timezone.timedelta(days=1)
    with pytest.raises(ValidationError) as exc:
        validate_not_future_datetime(tomorrow)
    assert exc.value.code == 'future_datetime'


@pytest.mark.django_db
def test_validate_not_future_datetime_accepts_now():
    validate_not_future_datetime(timezone.now())
