import calendar
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.utils import timezone as dj_timezone

MONTHS_RU = (
    '',
    'Январь',
    'Февраль',
    'Март',
    'Апрель',
    'Май',
    'Июнь',
    'Июль',
    'Август',
    'Сентябрь',
    'Октябрь',
    'Ноябрь',
    'Декабрь',
)

WEEKDAYS_RU = (
    'Понедельник',
    'Вторник',
    'Среда',
    'Четверг',
    'Пятница',
    'Суббота',
    'Воскресенье',
)


def resolve_timezone(tz_name=None):
    name = tz_name or settings.TIME_ZONE
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return ZoneInfo(settings.TIME_ZONE)


def get_session_timezone(request):
    return resolve_timezone(request.session.get('user_timezone'))


def format_date_dd_mm_yyyy(dt, tz=None):
    """Формат DD/MM/YYYY для aware или naive datetime."""
    if dt is None:
        return '—'
    if tz is not None:
        if dj_timezone.is_naive(dt):
            dt = dj_timezone.make_aware(dt, ZoneInfo('UTC'))
        dt = dt.astimezone(tz)
    elif dj_timezone.is_aware(dt):
        dt = dj_timezone.localtime(dt)
    return dt.strftime('%d/%m/%Y')


def format_datetime_dd_mm_yyyy_hm(dt, tz=None):
    if dt is None:
        return '—'
    if tz is not None:
        if dj_timezone.is_naive(dt):
            dt = dj_timezone.make_aware(dt, ZoneInfo('UTC'))
        dt = dt.astimezone(tz)
    elif dj_timezone.is_aware(dt):
        dt = dj_timezone.localtime(dt)
    return dt.strftime('%d/%m/%Y %H:%M')


def now_in_timezone(tz):
    return dj_timezone.now().astimezone(tz)


def build_text_calendar(year, month, tz=None):
    """Текстовый календарь месяца (понедельник — первый день недели)."""
    cal = calendar.Calendar(firstweekday=0)
    month_name = MONTHS_RU[month]
    header = f'{month_name} {year}'
    if tz:
        today = now_in_timezone(tz).date()
    else:
        today = dj_timezone.localdate()
    lines = [header, '=' * len(header)]
    lines.append('Пн  Вт  Ср  Чт  Пт  Сб  Вс')
    for week in cal.monthdays2calendar(year, month):
        cells = []
        for day, weekday in week:
            if day == 0:
                cells.append('   ')
            elif day == today.day and month == today.month and year == today.year:
                cells.append(f'[{day:2d}]')
            else:
                cells.append(f'{day:3d}')
        lines.append(' '.join(cells))
    return '\n'.join(lines)


def current_moment_context(request):
    user_tz = get_session_timezone(request)
    utc_tz = ZoneInfo('UTC')
    now_utc = dj_timezone.now().astimezone(utc_tz)
    now_user = now_utc.astimezone(user_tz)
    local_today = now_user.date()
    return {
        'user_timezone_name': str(user_tz),
        'current_date_utc': format_date_dd_mm_yyyy(now_utc, utc_tz),
        'current_date_user': format_date_dd_mm_yyyy(now_user, user_tz),
        'current_datetime_user': format_datetime_dd_mm_yyyy_hm(now_user, user_tz),
        'text_calendar': build_text_calendar(
            local_today.year,
            local_today.month,
            user_tz,
        ),
        'weekday_name': WEEKDAYS_RU[local_today.weekday()],
    }
