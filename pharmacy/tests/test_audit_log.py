from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from pharmacy.audit_log import (
    log_auth_failure,
    log_auth_success,
    log_purchase,
    log_validation_error,
)

User = get_user_model()


@pytest.mark.django_db
def test_log_auth_success():
    with patch('pharmacy.audit_log.logger') as mock_logger:
        log_auth_success('tester', request=None)
    mock_logger.info.assert_called_once()
    assert 'AUTH success' in mock_logger.info.call_args[0][0]
    assert 'tester' in mock_logger.info.call_args[0][1]


@pytest.mark.django_db
def test_log_auth_failure():
    with patch('pharmacy.audit_log.logger') as mock_logger:
        log_auth_failure('bad_user', request=None)
    mock_logger.warning.assert_called_once()
    assert 'AUTH failure' in mock_logger.warning.call_args[0][0]


@pytest.mark.django_db
def test_log_purchase():
    with patch('pharmacy.audit_log.logger') as mock_logger:
        log_purchase('buyer', 'MED-1', 2, '20.00', request=None)
    mock_logger.info.assert_called_once()
    assert 'PURCHASE' in mock_logger.info.call_args[0][0]


@pytest.mark.django_db
def test_log_validation_error():
    with patch('pharmacy.audit_log.logger') as mock_logger:
        log_validation_error('registration', {'phone': ['ошибка']}, request=None)
    mock_logger.warning.assert_called_once()
    assert 'VALIDATION' in mock_logger.warning.call_args[0][0]


@pytest.mark.django_db
def test_login_signal_logs(client, customer_user):
    with patch('pharmacy.audit_log.logger') as mock_logger:
        assert client.login(username='test_customer', password='testpass123')
    assert mock_logger.info.called
    assert any(
        'AUTH success' in str(call)
        for call in mock_logger.info.call_args_list
    )
