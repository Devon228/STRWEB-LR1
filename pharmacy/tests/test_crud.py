from decimal import Decimal

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_owner_can_create_medication(client, owner_user, category):
    client.force_login(owner_user)
    url = reverse('pharmacy:medication_create')
    response = client.post(
        url,
        {
            'code': 'NEW-100',
            'name': 'Новый препарат',
            'instruction': 'Инструкция',
            'description': 'Описание',
            'price': '25.50',
            'is_available': True,
            'categories': [category.pk],
        },
    )
    assert response.status_code == 302
    from pharmacy.models import Medication

    assert Medication.objects.filter(code='NEW-100').exists()


@pytest.mark.django_db
def test_customer_cannot_create_medication(client, customer_user, category):
    client.force_login(customer_user)
    url = reverse('pharmacy:medication_create')
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_owner_can_update_medication(client, owner_user, medication):
    client.force_login(owner_user)
    url = reverse('pharmacy:medication_edit', kwargs={'code': medication.code})
    response = client.post(
        url,
        {
            'code': medication.code,
            'name': 'Обновлённое имя',
            'instruction': medication.instruction,
            'description': medication.description,
            'price': '15.00',
            'is_available': True,
            'categories': list(medication.categories.values_list('pk', flat=True)),
        },
    )
    assert response.status_code == 302
    medication.refresh_from_db()
    assert medication.name == 'Обновлённое имя'
    assert medication.price == Decimal('15.00')


@pytest.mark.django_db
def test_owner_can_delete_medication(client, owner_user, medication):
    client.force_login(owner_user)
    url = reverse('pharmacy:medication_delete', kwargs={'code': medication.code})
    response = client.post(url)
    assert response.status_code == 302
    from pharmacy.models import Medication

    assert not Medication.objects.filter(pk=medication.pk).exists()
