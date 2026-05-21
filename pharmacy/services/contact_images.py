"""URL фото контактов: загруженный файл или внешний placeholder."""
from django.conf import settings

DEFAULT_TAGS = 'person,portrait,professional'


def external_contact_photo_url(contact_pk, width=300, height=300):
    tags = getattr(settings, 'CONTACT_IMAGE_TAGS', DEFAULT_TAGS)
    return (
        f'https://loremflickr.com/{width}/{height}/{tags}/all'
        f'?lock={contact_pk}'
    )
