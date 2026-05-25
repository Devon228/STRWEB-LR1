"""Загрузка изображений статей в media/articles/."""
import urllib.request

from django.core.files.base import ContentFile

from pharmacy.services.article_images import external_article_image_url


def download_article_photo(article, timeout=20):
    """Скачивает картинку статьи с LoremFlickr и сохраняет в ImageField."""
    url = external_article_image_url(article.pk, width=640, height=360)
    request = urllib.request.Request(
        url,
        headers={'User-Agent': 'PharmacySeed/1.0'},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read()
    filename = f'article_{article.pk}.jpg'
    article.image.save(filename, ContentFile(data), save=True)
    return True
