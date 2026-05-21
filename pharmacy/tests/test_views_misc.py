import pytest
from django.conf import settings
from django.urls import reverse

from asgiref.sync import async_to_sync
from pharmacy.concurrency import load_game_assets
from pharmacy.models import Article


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
