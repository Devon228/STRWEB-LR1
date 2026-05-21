"""
URL изображений для новостей: загруженный файл или внешний placeholder по теме «аптека».
"""
from django.conf import settings

DEFAULT_TAGS = 'pharmacy,medicine,apothecary'


def external_article_image_url(article_pk, width=640, height=360):
    """
    Стабильная картинка с Lorem Flickr (без API-ключа) по тегам аптеки.
    lock={pk} — одно и то же фото для статьи при повторных запросах.
    """
    tags = getattr(settings, 'ARTICLE_IMAGE_TAGS', DEFAULT_TAGS)
    return (
        f'https://loremflickr.com/{width}/{height}/{tags}/all'
        f'?lock={article_pk}'
    )
