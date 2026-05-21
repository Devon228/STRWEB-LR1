from django.utils import timezone

from pharmacy.time_utils import get_session_timezone


class UserTimezoneMiddleware:
    """Активирует часовой пояс пользователя из session для timezone.now() / localtime()."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz = get_session_timezone(request)
        timezone.activate(tz)
        try:
            return self.get_response(request)
        finally:
            timezone.deactivate()
