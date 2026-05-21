from pharmacy.roles import ROLE_LABELS, get_user_role


def user_role(request):
    role = get_user_role(request.user)
    return {
        'current_role': role,
        'current_role_label': ROLE_LABELS.get(role, role),
    }
