import logging

logger = logging.getLogger('pharmacy.app')


def _client_ip(request):
    if request is None:
        return 'unknown'
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def log_auth_success(username, request=None):
    logger.info(
        'AUTH success user=%s ip=%s',
        username,
        _client_ip(request),
    )


def log_auth_failure(username, request=None, reason='invalid_credentials'):
    logger.warning(
        'AUTH failure user=%s ip=%s reason=%s',
        username or 'unknown',
        _client_ip(request),
        reason,
    )


def log_logout(username, request=None):
    logger.info(
        'AUTH logout user=%s ip=%s',
        username,
        _client_ip(request),
    )


def log_purchase(username, medication_code, quantity, total_amount, request=None):
    logger.info(
        'PURCHASE user=%s medication=%s qty=%s total=%s ip=%s',
        username,
        medication_code,
        quantity,
        total_amount,
        _client_ip(request),
    )


def log_validation_error(form_name, errors, request=None):
    logger.warning(
        'VALIDATION form=%s ip=%s errors=%s',
        form_name,
        _client_ip(request),
        errors,
    )
