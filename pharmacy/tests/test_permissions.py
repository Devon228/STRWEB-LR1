import pytest
from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.parametrize(
    'url_name,anonymous_code,customer_code,employee_code,owner_code',
    [
        ('pharmacy:medication_list', 200, 200, 200, 200),
        ('pharmacy:purchase_list', 302, 200, 403, 403),
        ('pharmacy:employee_sales', 302, 403, 200, 403),
        ('pharmacy:owner_dashboard', 302, 403, 403, 200),
        ('pharmacy:analytics', 302, 403, 403, 200),
        ('pharmacy:medication_create', 302, 403, 403, 200),
        ('pharmacy:staff_purchase_list', 302, 403, 200, 200),
        ('pharmacy:staff_purchase_create', 302, 403, 200, 200),
    ],
)
def test_role_access_urls(
    client,
    customer_user,
    employee_user,
    owner_user,
    url_name,
    anonymous_code,
    customer_code,
    employee_code,
    owner_code,
):
    url = reverse(url_name)
    assert client.get(url).status_code == anonymous_code
    client.force_login(customer_user)
    assert client.get(url).status_code == customer_code
    client.logout()
    client.force_login(employee_user)
    assert client.get(url).status_code == employee_code
    client.logout()
    client.force_login(owner_user)
    assert client.get(url).status_code == owner_code


@pytest.mark.django_db
def test_anonymous_cannot_buy(client, medication):
    url = reverse('pharmacy:purchase_create', kwargs={'code': medication.code})
    assert client.get(url).status_code == 302
