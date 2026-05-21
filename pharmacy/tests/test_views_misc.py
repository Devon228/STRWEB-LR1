import pytest
from django.urls import reverse

from asgiref.sync import async_to_sync
from pharmacy.concurrency import load_game_assets


@pytest.mark.django_db
def test_concurrency_demo_page(client):
    response = client.get(reverse('pharmacy:concurrency_demo'))
    assert response.status_code == 200
    assert 'Asyncio' in response.content.decode()


@pytest.mark.django_db
def test_home_page(client):
    assert client.get(reverse('pharmacy:home')).status_code == 200


@pytest.mark.django_db
def test_medication_list_filter(client, medication):
    url = reverse('pharmacy:medication_list')
    response = client.get(url, {'q': 'Тестовый', 'sort': 'price_asc'})
    assert response.status_code == 200
    assert medication.name.encode() in response.content


@pytest.mark.django_db
def test_customer_purchase(client, customer_user, medication, pickup_point):
    client.force_login(customer_user)
    url = reverse('pharmacy:medication_detail', kwargs={'code': medication.code})
    assert client.get(url).status_code == 200
    buy_url = reverse('pharmacy:purchase_create', kwargs={'code': medication.code})
    response = client.post(
        buy_url,
        {'quantity': 1, 'pickup_point': pickup_point.pk},
    )
    assert response.status_code == 302
    from pharmacy.models import Purchase

    assert Purchase.objects.filter(customer=customer_user.customer_profile).exists()
