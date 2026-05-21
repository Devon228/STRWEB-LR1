import pytest
from datetime import timedelta

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from asgiref.sync import async_to_sync
from pharmacy.concurrency import load_game_assets
from pharmacy.models import Article, ContactPerson


@pytest.mark.django_db
def test_concurrency_demo_page(client):
    response = client.get(reverse('pharmacy:concurrency_demo'))
    assert response.status_code == 200
    assert 'Asyncio' in response.content.decode()


@pytest.mark.django_db
def test_home_page(client):
    assert client.get(reverse('pharmacy:home')).status_code == 200


@pytest.mark.django_db
def test_home_shows_timezone_and_article_image(client):
    article = Article.objects.create(
        title='Тестовая новость',
        summary='Краткое описание новости.',
        content='Полный текст.',
        is_published=True,
    )
    response = client.get(reverse('pharmacy:home'))
    content = response.content.decode()
    assert response.status_code == 200
    assert settings.TIME_ZONE in content
    assert 'user_now' not in content
    assert article.display_image_url in content
    assert '<img' in content


@pytest.mark.django_db
def test_staff_purchase_create_rejects_future_date(
    client,
    employee_user,
    customer_user,
    medication,
    pickup_point,
):
    client.force_login(employee_user)
    future = timezone.now() + timedelta(days=2)
    response = client.post(
        reverse('pharmacy:staff_purchase_create'),
        {
            'customer': customer_user.customer_profile.pk,
            'medication': medication.pk,
            'pickup_point': pickup_point.pk,
            'quantity': 1,
            'purchased_at': future.strftime('%Y-%m-%dT%H:%M'),
        },
    )
    assert response.status_code == 200
    assert 'будущем' in response.content.decode()


@pytest.mark.django_db
def test_staff_purchase_create_success(
    client,
    employee_user,
    customer_user,
    medication,
    pickup_point,
):
    client.force_login(employee_user)
    local_past = timezone.localtime(timezone.now()) - timedelta(hours=1)
    response = client.post(
        reverse('pharmacy:staff_purchase_create'),
        {
            'customer': customer_user.customer_profile.pk,
            'medication': medication.pk,
            'pickup_point': pickup_point.pk,
            'quantity': 2,
            'purchased_at': local_past.strftime('%Y-%m-%dT%H:%M'),
        },
    )
    assert response.status_code == 302
    from pharmacy.models import Purchase

    purchase = Purchase.objects.latest('pk')
    assert purchase.quantity == 2
    expected = timezone.make_aware(
        local_past.replace(tzinfo=None),
        timezone.get_current_timezone(),
    )
    assert purchase.purchased_at.replace(second=0, microsecond=0) == expected.replace(
        second=0,
        microsecond=0,
    )


@pytest.mark.django_db
def test_ensure_contacts_adds_missing(db):
    from pharmacy.contact_seed import CONTACTS_SEED
    from pharmacy.management.commands.seed_data import Command

    ContactPerson.objects.all().delete()
    ContactPerson.objects.create(
        full_name='Светлана Мороз',
        job_description='Консультации.',
        phone='+375 (29) 101-01-01',
        email='info@zdorovie-plus.by',
    )
    cmd = Command()
    created, _photos = cmd._ensure_contacts()
    assert ContactPerson.objects.filter(is_active=True).count() == len(CONTACTS_SEED)
    assert created == len(CONTACTS_SEED) - 1


@pytest.mark.django_db
def test_contact_list_shows_photo_for_each(client):
    for i in range(10):
        ContactPerson.objects.create(
            full_name=f'Контакт {i}',
            job_description='Консультации клиентов.',
            phone=f'+375 (29) {100 + i:03d}-{10 + i:02d}-{10 + i:02d}',
            email=f'contact{i}@example.by',
        )
    response = client.get(reverse('pharmacy:contact_list'))
    content = response.content.decode()
    assert response.status_code == 200
    assert content.count('<img') == 10


@pytest.mark.django_db
def test_news_list_always_has_images(client):
    Article.objects.create(
        title='Новость 1',
        summary='Описание первой новости.',
        content='Текст.',
    )
    response = client.get(reverse('pharmacy:news_list'))
    assert response.status_code == 200
    assert response.content.decode().count('<img') >= 1


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
