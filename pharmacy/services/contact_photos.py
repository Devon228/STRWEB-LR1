"""Загрузка фото контактов в media/contacts/."""
import urllib.request
from urllib.parse import quote

from django.core.files.base import ContentFile

from pharmacy.services.contact_images import external_contact_photo_url


def download_contact_photo(contact, timeout=20):
    """Скачивает аватар и сохраняет в ImageField. Возвращает True при успехе."""
    url = external_contact_photo_url(
        contact_pk=contact.pk,
        email=contact.email,
        full_name=contact.full_name,
        width=300,
        height=300,
    )
    request = urllib.request.Request(
        url,
        headers={'User-Agent': 'PharmacySeed/1.0'},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = response.read()
    filename = f'contact_{contact.pk}.png'
    contact.photo.save(filename, ContentFile(data), save=True)
    return True
