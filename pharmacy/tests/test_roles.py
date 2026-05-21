import pytest

from pharmacy.roles import Role, get_user_role, user_has_role


@pytest.mark.django_db
def test_anonymous_role(anonymous_user=None):
    from django.contrib.auth.models import AnonymousUser

    assert get_user_role(AnonymousUser()) == Role.ANONYMOUS


@pytest.mark.django_db
def test_customer_role(customer_user):
    assert get_user_role(customer_user) == Role.CUSTOMER
    assert user_has_role(customer_user, Role.CUSTOMER)


@pytest.mark.django_db
def test_employee_role(employee_user):
    assert get_user_role(employee_user) == Role.EMPLOYEE


@pytest.mark.django_db
def test_owner_role(owner_user):
    assert get_user_role(owner_user) == Role.OWNER
