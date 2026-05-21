from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from pharmacy.validators import validate_adult_age, validate_belarus_phone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class MedicationCategory(TimeStampedModel):
    name = models.CharField('Название', max_length=120, unique=True)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Категория медикаментов'
        verbose_name_plural = 'Категории медикаментов'
        ordering = ['name']

    def __str__(self):
        return self.name


class PharmacyDepartment(TimeStampedModel):
    name = models.CharField('Название отдела', max_length=120, unique=True)
    description = models.TextField('Описание', blank=True)
    floor = models.PositiveSmallIntegerField('Этаж', default=1)

    class Meta:
        verbose_name = 'Отдел аптеки'
        verbose_name_plural = 'Отделы аптеки'
        ordering = ['name']

    def __str__(self):
        return self.name


class Supplier(TimeStampedModel):
    name = models.CharField('Название', max_length=200, unique=True)
    contact_person = models.CharField('Контактное лицо', max_length=120, blank=True)
    phone = models.CharField(
        'Телефон',
        max_length=22,
        blank=True,
        validators=[validate_belarus_phone],
    )
    email = models.EmailField('Email', blank=True)
    address = models.CharField('Адрес', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'
        ordering = ['name']

    def __str__(self):
        return self.name


class Medication(TimeStampedModel):
    code = models.CharField('Код', max_length=32, unique=True, db_index=True)
    name = models.CharField('Название', max_length=200)
    instruction = models.TextField('Инструкция')
    description = models.TextField('Описание')
    price = models.DecimalField(
        'Стоимость (BYN)',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    photo = models.ImageField('Фото', upload_to='medications/', blank=True)
    categories = models.ManyToManyField(
        MedicationCategory,
        related_name='medications',
        verbose_name='Категории',
        blank=True,
    )
    suppliers = models.ManyToManyField(
        Supplier,
        related_name='medications',
        verbose_name='Поставщики',
        blank=True,
    )
    is_available = models.BooleanField('В наличии', default=True)

    class Meta:
        verbose_name = 'Медикамент'
        verbose_name_plural = 'Медикаменты'
        ordering = ['name']

    def __str__(self):
        return f'{self.code} — {self.name}'


class Employee(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        verbose_name='Пользователь',
    )
    department = models.ForeignKey(
        PharmacyDepartment,
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name='Отдел',
    )
    position = models.CharField('Должность', max_length=120)
    birth_date = models.DateField('Дата рождения')
    phone = models.CharField(
        'Телефон',
        max_length=22,
        validators=[validate_belarus_phone],
    )
    suppliers = models.ManyToManyField(
        Supplier,
        related_name='employees',
        verbose_name='Поставщики',
        blank=True,
    )

    class Meta:
        verbose_name = 'Сотрудник аптеки'
        verbose_name_plural = 'Сотрудники аптеки'
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def clean(self):
        super().clean()
        validate_adult_age(self.birth_date)

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = timezone.localdate()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )


class Customer(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        verbose_name='Пользователь',
    )
    birth_date = models.DateField('Дата рождения')
    phone = models.CharField(
        'Телефон',
        max_length=22,
        validators=[validate_belarus_phone],
    )

    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def clean(self):
        super().clean()
        validate_adult_age(self.birth_date)

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = timezone.localdate()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )


class Sale(TimeStampedModel):
    medication = models.ForeignKey(
        Medication,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name='Медикамент',
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name='Сотрудник',
    )
    quantity = models.PositiveIntegerField(
        'Количество',
        validators=[MinValueValidator(1)],
    )
    sold_at = models.DateTimeField('Дата продажи', default=timezone.now)
    total_amount = models.DecimalField(
        'Сумма',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )

    class Meta:
        verbose_name = 'Продажа'
        verbose_name_plural = 'Продажи'
        ordering = ['-sold_at']

    def __str__(self):
        return (
            f'{self.medication.code} × {self.quantity} '
            f'({self.total_amount} BYN)'
        )

    def save(self, *args, **kwargs):
        if self.total_amount is None and self.medication_id and self.quantity:
            self.total_amount = self.medication.price * self.quantity
        super().save(*args, **kwargs)


class PickupPoint(TimeStampedModel):
    name = models.CharField('Название', max_length=120)
    address = models.CharField('Адрес', max_length=255)
    phone = models.CharField(
        'Телефон',
        max_length=22,
        validators=[validate_belarus_phone],
    )
    working_hours = models.CharField('Часы работы', max_length=120)
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        verbose_name = 'Точка самовывоза'
        verbose_name_plural = 'Точки самовывоза'
        ordering = ['name']

    def __str__(self):
        return self.name


class AdditionalService(TimeStampedModel):
    name = models.CharField('Название', max_length=120)
    description = models.TextField('Описание')
    price = models.DecimalField(
        'Стоимость (BYN)',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        verbose_name = 'Дополнительная услуга'
        verbose_name_plural = 'Дополнительные услуги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Purchase(TimeStampedModel):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='purchases',
        verbose_name='Покупатель',
    )
    medication = models.ForeignKey(
        Medication,
        on_delete=models.PROTECT,
        related_name='purchases',
        verbose_name='Медикамент',
    )
    pickup_point = models.ForeignKey(
        PickupPoint,
        on_delete=models.PROTECT,
        related_name='purchases',
        verbose_name='Точка самовывоза',
    )
    quantity = models.PositiveIntegerField(
        'Количество',
        validators=[MinValueValidator(1)],
    )
    total_amount = models.DecimalField(
        'Сумма',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    purchased_at = models.DateTimeField('Дата покупки', default=timezone.now)

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        ordering = ['-purchased_at']

    def __str__(self):
        return f'{self.medication.code} — {self.customer}'


class Article(TimeStampedModel):
    title = models.CharField('Заголовок', max_length=200)
    summary = models.CharField(
        'Краткое содержание',
        max_length=300,
        help_text='Одно предложение для списка новостей.',
    )
    content = models.TextField('Полный текст', blank=True)
    image = models.ImageField('Изображение', upload_to='articles/', blank=True)
    published_at = models.DateTimeField('Дата публикации', default=timezone.now)
    is_published = models.BooleanField('Опубликовано', default=True)

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    @property
    def display_image_url(self):
        if self.image:
            return self.image.url
        from pharmacy.services.article_images import external_article_image_url

        return external_article_image_url(self.pk)


class CompanyInfo(TimeStampedModel):
    title = models.CharField('Заголовок', max_length=200, default='О компании')
    about_text = models.TextField('Текст о компании')
    video_url = models.URLField('Ссылка на видео', blank=True)
    logo = models.ImageField('Логотип', upload_to='company/', blank=True)
    history = models.TextField('История по годам', blank=True)
    requisites = models.TextField('Реквизиты', blank=True)

    class Meta:
        verbose_name = 'Информация о компании'
        verbose_name_plural = 'Информация о компании'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class Glossary(TimeStampedModel):
    question = models.CharField('Вопрос', max_length=300)
    answer = models.TextField('Ответ')
    added_at = models.DateTimeField('Дата добавления', default=timezone.now)

    class Meta:
        verbose_name = 'Термин / FAQ'
        verbose_name_plural = 'Словарь терминов'
        ordering = ['-added_at']

    def __str__(self):
        return self.question


class ContactPerson(TimeStampedModel):
    full_name = models.CharField('ФИО', max_length=200)
    photo = models.ImageField('Фото', upload_to='contacts/', blank=True)
    job_description = models.TextField('Выполняемые работы')
    phone = models.CharField(
        'Телефон',
        max_length=22,
        validators=[validate_belarus_phone],
    )
    email = models.EmailField('Email')
    is_active = models.BooleanField('Отображать на сайте', default=True)

    class Meta:
        verbose_name = 'Контакт на сайте'
        verbose_name_plural = 'Контакты'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class Vacancy(TimeStampedModel):
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание')
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Review(TimeStampedModel):
    author_name = models.CharField('Имя', max_length=120)
    rating = models.PositiveSmallIntegerField(
        'Оценка',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    text = models.TextField('Текст отзыва')
    published_at = models.DateTimeField('Дата', default=timezone.now)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reviews',
        verbose_name='Пользователь',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-published_at']

    def __str__(self):
        return f'{self.author_name} ({self.rating}/5)'


class PromoCode(TimeStampedModel):
    class PromoKind(models.TextChoices):
        PROMO = 'promo', 'Промокод'
        COUPON = 'coupon', 'Купон'

    code = models.CharField('Код', max_length=50, unique=True)
    description = models.TextField('Описание', blank=True)
    kind = models.CharField(
        'Тип',
        max_length=10,
        choices=PromoKind.choices,
        default=PromoKind.PROMO,
    )
    discount_percent = models.PositiveSmallIntegerField(
        'Скидка, %',
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    valid_from = models.DateField('Действует с')
    valid_until = models.DateField('Действует до')
    is_archived = models.BooleanField('В архиве', default=False)

    class Meta:
        verbose_name = 'Промокод / купон'
        verbose_name_plural = 'Промокоды и купоны'
        ordering = ['-valid_from']

    def __str__(self):
        status = 'архив' if self.is_archived else 'активен'
        return f'{self.code} ({status})'

    @property
    def is_active(self):
        today = timezone.localdate()
        return (
            not self.is_archived
            and self.valid_from <= today <= self.valid_until
        )
