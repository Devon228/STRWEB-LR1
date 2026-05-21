from django.utils import timezone

from pharmacy.roles import ROLE_LABELS, get_user_role
from pharmacy.time_utils import get_session_timezone


def user_role(request):
    role = get_user_role(request.user)
    return {
        'current_role': role,
        'current_role_label': ROLE_LABELS.get(role, role),
    }


def site_timezone(request):
    """
    Текущий момент в поясе пользователя (django.utils.timezone).
    Middleware уже активировал пояс из session.
    """
    user_tz = get_session_timezone(request)
    now = timezone.localtime(timezone.now())
    return {
        'user_timezone': str(user_tz),
        'user_timezone_name': str(user_tz),
        'user_now': now,
    }
