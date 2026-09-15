from django.db import migrations

PARTNERS = [
    (
        'Белфармация',
        'https://www.belpharm.by',
        'https://dummyimage.com/240x80/1d4ed8/ffffff&text=Belpharm',
        'Республиканское предприятие, производство и оптовая поставка лекарств.',
    ),
    (
        'Борисовский завод медпрепаратов',
        'https://www.borimed.com',
        'https://dummyimage.com/240x80/1d4ed8/ffffff&text=Borimed',
        'Отечественный производитель готовых лекарственных средств.',
    ),
    (
        'Минскинтеркапс',
        'https://www.minskintercaps.by',
        'https://dummyimage.com/240x80/1d4ed8/ffffff&text=Minskintercaps',
        'Производство капсулированных препаратов и витаминов.',
    ),
    (
        'Фармтехнология',
        'https://www.pharmtech.by',
        'https://dummyimage.com/240x80/1d4ed8/ffffff&text=Pharmtech',
        'Инфузионные растворы и стерильные лекарственные формы.',
    ),
    (
        'Лекфарм',
        'https://www.lekpharm.by',
        'https://dummyimage.com/240x80/1d4ed8/ffffff&text=Lekpharm',
        'Разработка и выпуск импортозамещающих препаратов.',
    ),
    (
        'БелАсептика',
        'https://www.belaseptika.by',
        'https://dummyimage.com/240x80/1d4ed8/ffffff&text=Belaseptika',
        'Антисептики, дезинфекция и медицинские изделия.',
    ),
    (
        'Диалек',
        'https://dialek.by',
        'https://dummyimage.com/240x80/1d4ed8/ffffff&text=Dialek',
        'Белорусский производитель инсулинов и диабетических средств.',
    ),
    (
        'МедСофт',
        'https://medsoft.by',
        'https://dummyimage.com/240x80/1d4ed8/ffffff&text=Medsoft',
        'ИТ-партнёр: автоматизация аптечного учёта и заказов.',
    ),
]


def create_partners(apps, schema_editor):
    Partner = apps.get_model('pharmacy', 'Partner')
    for name, website_url, logo_url, description in PARTNERS:
        Partner.objects.get_or_create(
            name=name,
            defaults={
                'website_url': website_url,
                'logo_url': logo_url,
                'description': description,
            },
        )


def remove_partners(apps, schema_editor):
    Partner = apps.get_model('pharmacy', 'Partner')
    Partner.objects.filter(name__in=[item[0] for item in PARTNERS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pharmacy', '0004_partner'),
    ]

    operations = [
        migrations.RunPython(create_partners, remove_partners),
    ]
