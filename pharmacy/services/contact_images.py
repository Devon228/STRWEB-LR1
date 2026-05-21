"""URL фото контактов: загруженный файл или аватар по ФИО."""
from urllib.parse import quote


def external_contact_photo_url(
    contact_pk=None,
    email=None,
    full_name=None,
    width=150,
    height=150,
):
    """UI Avatars — стабильные портреты-заглушки без API-ключа."""
    label = full_name or email or f'Контакт {contact_pk}'
    size = max(width, height)
    return (
        'https://ui-avatars.com/api/'
        f'?name={quote(label)}'
        f'&size={size}'
        '&background=1d4ed8'
        '&color=ffffff'
        '&bold=true'
    )
