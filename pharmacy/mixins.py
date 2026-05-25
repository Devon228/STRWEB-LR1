from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from pharmacy.roles import Role, get_user_role


class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        role = get_user_role(request.user)
        if role not in self.allowed_roles:
            raise PermissionDenied(
                'Недостаточно прав для просмотра этой страницы.',
            )
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class CustomerRequiredMixin(RoleRequiredMixin):
    allowed_roles = (Role.CUSTOMER,)


class EmployeeRequiredMixin(RoleRequiredMixin):
    allowed_roles = (Role.EMPLOYEE,)


class EmployeeOrOwnerRequiredMixin(RoleRequiredMixin):
    """Сотрудник или владелец (superuser) — продажи, заказы."""

    allowed_roles = (Role.EMPLOYEE, Role.OWNER)


class OwnerRequiredMixin(RoleRequiredMixin):
    allowed_roles = (Role.OWNER,)


class StaffRequiredMixin(RoleRequiredMixin):
    """Сотрудник аптеки или владелец (superuser)."""

    allowed_roles = (Role.EMPLOYEE, Role.OWNER)
