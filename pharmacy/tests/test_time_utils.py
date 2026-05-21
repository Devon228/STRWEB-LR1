from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from pharmacy.time_utils import (
    build_text_calendar,
    format_date_dd_mm_yyyy,
    get_session_timezone,
    resolve_timezone,
)


def test_format_date_dd_mm_yyyy_utc():
    dt = datetime(2024, 3, 5, 12, 0, tzinfo=ZoneInfo('UTC'))
    assert format_date_dd_mm_yyyy(dt, ZoneInfo('UTC')) == '05/03/2024'


def test_resolve_timezone_fallback():
    tz = resolve_timezone('Invalid/Zone')
    assert str(tz) == 'Europe/Minsk'


@pytest.mark.django_db
def test_get_session_timezone_from_session(rf):
    request = rf.get('/')
    request.session = {'user_timezone': 'UTC'}
    assert str(get_session_timezone(request)) == 'UTC'


def test_build_text_calendar_contains_month():
    text = build_text_calendar(2026, 5)
    assert 'Май' in text
    assert '2026' in text


def test_article_display_image_url_external():
    from pharmacy.models import Article
    from pharmacy.services.article_images import external_article_image_url

    article = Article(pk=7, title='t', summary='s')
    assert article.display_image_url == external_article_image_url(7)
    assert 'pharmacy' in article.display_image_url
