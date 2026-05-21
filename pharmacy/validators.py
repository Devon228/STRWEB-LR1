import re
from datetime import date

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

PHONE_PATTERN = re.compile(r'^\+375 \(29\) \d{3}-\d{2}-\d{2}$')
MIN_ADULT_AGE = 18


def validate_belarus_phone(value):
    if not value or not PHONE_PATTERN.match(value):
        raise ValidationError(
            _('Телефон должен быть в формате +375 (29) XXX-XX-XX.'),
            code='invalid_phone',
        )


def validate_not_future_datetime(value):
    """Дата и время не могут быть в будущем (включая «завтра»)."""
    if value is None:
        return
    now = timezone.now()
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    if value > now:
        raise ValidationError(
            _('Дата не может быть в будущем.'),
            code='future_datetime',
        )


def validate_adult_age(birth_date):
    if birth_date is None:
        return
    today = date.today()
    age = today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )
    if age < MIN_ADULT_AGE:
        raise ValidationError(
            _('Возраст должен быть не менее %(min_age)s лет.'),
            code='underage',
            params={'min_age': MIN_ADULT_AGE},
        )
