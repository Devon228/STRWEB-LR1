from django.contrib.auth.models import Group

GROUP_CUSTOMER = 'customer'
GROUP_EMPLOYEE = 'employee'


class Role:
    ANONYMOUS = 'anonymous'
    CUSTOMER = 'customer'
    EMPLOYEE = 'employee'
    OWNER = 'owner'


ROLE_LABELS = {
    Role.ANONYMOUS: 'Гость',
    Role.CUSTOMER: 'Покупатель',
    Role.EMPLOYEE: 'Сотрудник',
    Role.OWNER: 'Владелец (superuser)',
}


def ensure_role_groups():
    Group.objects.get_or_create(name=GROUP_CUSTOMER)
    Group.objects.get_or_create(name=GROUP_EMPLOYEE)


def get_user_role(user):
    if not user.is_authenticated:
        return Role.ANONYMOUS
    if user.is_superuser:
        return Role.OWNER
    if hasattr(user, 'employee_profile'):
        return Role.EMPLOYEE
    if hasattr(user, 'customer_profile'):
        return Role.CUSTOMER
    return Role.ANONYMOUS


def user_has_role(user, *roles):
    return get_user_role(user) in roles
