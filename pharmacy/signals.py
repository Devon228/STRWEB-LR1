from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from pharmacy.audit_log import log_auth_failure, log_auth_success, log_logout


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    log_auth_success(user.username, request)


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    if user is not None:
        log_logout(user.username, request)


@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get('username', 'unknown')
    log_auth_failure(username, request)
