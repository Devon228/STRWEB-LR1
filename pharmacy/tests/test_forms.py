from datetime import date
from unittest.mock import patch

import pytest

from pharmacy.forms import RegistrationForm
from pharmacy.roles import Role

FROZEN_TODAY = date(2026, 5, 21)
VALID_PHONE = '+375 (29) 555-66-77'


@pytest.mark.django_db
@pytest.mark.parametrize(
    'phone,valid',
    [
        ('+375 (29) 123-45-67', True),
        ('+375 (29) 12-45-67', False),
        ('invalid-phone', False),
    ],
)
def test_registration_form_phone(phone, valid, department):
    ensure_groups()
    suffix = ''.join(c for c in phone if c.isdigit())[:10] or '000'
    data = _base_registration_data(department, phone=phone, username=f'phone_{suffix}')
    form = RegistrationForm(data=data)
    with patch('pharmacy.validators.date') as mock_date:
        mock_date.today.return_value = FROZEN_TODAY
        assert form.is_valid() is valid


@pytest.mark.django_db
def test_registration_form_age_shows_field_error(department):
    ensure_groups()
    data = _base_registration_data(
        department,
        birth_date=date(2008, 6, 21).isoformat(),
        username='age_under',
    )
    form = RegistrationForm(data=data)
    with patch('pharmacy.validators.date') as mock_date:
        mock_date.today.return_value = FROZEN_TODAY
        assert not form.is_valid()
        assert 'birth_date' in form.errors
        assert any('18' in msg for msg in form.errors['birth_date'])


@pytest.mark.django_db
@pytest.mark.parametrize(
    'birth_date,valid,label',
    [
        (date(2008, 6, 21), False, '17y11m'),
        (date(2008, 5, 21), True, '18y'),
    ],
)
def test_registration_form_age(birth_date, valid, label, department):
    ensure_groups()
    data = _base_registration_data(
        department,
        birth_date=birth_date.isoformat(),
        username=f'age_{label}',
    )
    form = RegistrationForm(data=data)
    with patch('pharmacy.validators.date') as mock_date:
        mock_date.today.return_value = FROZEN_TODAY
        assert form.is_valid() is valid


def ensure_groups():
    from pharmacy.roles import ensure_role_groups

    ensure_role_groups()


def _base_registration_data(
    department,
    phone=VALID_PHONE,
    birth_date='1990-01-01',
    username='newuser_form',
):
    return {
        'username': username,
        'email': 'new@test.by',
        'first_name': 'Новый',
        'last_name': 'Юзер',
        'password1': 'ComplexPass123!',
        'password2': 'ComplexPass123!',
        'account_role': Role.CUSTOMER,
        'birth_date': birth_date,
        'phone': phone,
        'department': '',
    }
