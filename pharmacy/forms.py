from datetime import date

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

from pharmacy.models import (
    Customer,
    Employee,
    Medication,
    MedicationCategory,
    PharmacyDepartment,
    PickupPoint,
    Purchase,
    Review,
    Sale,
    Supplier,
)
from pharmacy.roles import GROUP_CUSTOMER, GROUP_EMPLOYEE, Role, ensure_role_groups
from pharmacy.validators import (
    validate_adult_age,
    validate_belarus_phone,
    validate_not_future_datetime,
)

User = get_user_model()

PHONE_HTML_PATTERN = r'\+375 \(29\) [0-9]{3}-[0-9]{2}-[0-9]{2}'
PHONE_PLACEHOLDER = '+375 (29) XXX-XX-XX'
PHONE_TITLE = 'Формат: +375 (29) XXX-XX-XX'


class BelarusPhoneField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 22)
        kwargs.setdefault('label', 'Телефон')
        widget = forms.TextInput(
            attrs={
                'pattern': PHONE_HTML_PATTERN,
                'placeholder': PHONE_PLACEHOLDER,
                'title': PHONE_TITLE,
                'required': 'required',
            },
        )
        kwargs.setdefault('widget', widget)
        super().__init__(*args, **kwargs)

    def clean(self, value):
        value = super().clean(value)
        validate_belarus_phone(value)
        return value


class AdultBirthDateField(forms.DateField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label', 'Дата рождения')
        kwargs.setdefault(
            'help_text',
            'Вам должно быть не менее 18 лет.',
        )
        kwargs.setdefault(
            'widget',
            forms.DateInput(
                attrs={
                    'type': 'date',
                    'required': 'required',
                },
            ),
        )
        super().__init__(*args, **kwargs)

    def clean(self, value):
        value = super().clean(value)
        try:
            validate_adult_age(value)
        except ValidationError as exc:
            raise ValidationError(exc.messages, code=exc.code) from exc
        return value


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={'required': 'required'}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'required': 'required'}),
    )


class RegistrationForm(UserCreationForm):
    ROLE_CHOICES = (
        (Role.CUSTOMER, 'Покупатель'),
        (Role.EMPLOYEE, 'Сотрудник'),
    )

    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'required': 'required'}),
    )
    first_name = forms.CharField(
        label='Имя',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'required': 'required'}),
    )
    last_name = forms.CharField(
        label='Фамилия',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'required': 'required'}),
    )
    account_role = forms.ChoiceField(
        label='Роль',
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
    )
    birth_date = AdultBirthDateField()
    phone = BelarusPhoneField()
    department = forms.ModelChoiceField(
        label='Отдел аптеки',
        queryset=PharmacyDepartment.objects.all(),
        required=False,
        empty_label='— выберите отдел —',
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'password1',
            'password2',
            'account_role',
            'birth_date',
            'phone',
            'department',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ('username', 'password1', 'password2'):
            self.fields[field_name].widget.attrs['required'] = 'required'

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get('account_role')
        department = cleaned.get('department')
        if role == Role.EMPLOYEE and not department:
            self.add_error(
                'department',
                'Для регистрации сотрудника необходимо выбрать отдел.',
            )
        if role == Role.CUSTOMER and department:
            cleaned['department'] = None
        return cleaned

    def save(self, commit=True):
        ensure_role_groups()
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            self._create_profile(user)
        return user

    def _create_profile(self, user):
        role = self.cleaned_data['account_role']
        birth_date = self.cleaned_data['birth_date']
        phone = self.cleaned_data['phone']
        if role == Role.CUSTOMER:
            from pharmacy.models import Customer

            Customer.objects.create(
                user=user,
                birth_date=birth_date,
                phone=phone,
            )
            user.groups.add(Group.objects.get(name=GROUP_CUSTOMER))
        elif role == Role.EMPLOYEE:
            Employee.objects.create(
                user=user,
                department=self.cleaned_data['department'],
                position='Сотрудник',
                birth_date=birth_date,
                phone=phone,
            )
            user.groups.add(Group.objects.get(name=GROUP_EMPLOYEE))


class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        label='Оценка',
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(
            attrs={
                'min': 1,
                'max': 5,
                'required': 'required',
            },
        ),
    )
    text = forms.CharField(
        label='Текст отзыва',
        widget=forms.Textarea(
            attrs={
                'rows': 5,
                'required': 'required',
                'minlength': 10,
            },
        ),
    )

    class Meta:
        model = Review
        fields = ('rating', 'text')

    def save(self, commit=True):
        review = super().save(commit=False)
        user = self.initial.get('user')
        if user:
            review.user = user
            review.author_name = user.get_full_name() or user.username
        if commit:
            review.save()
        return review


class PurchaseForm(forms.ModelForm):
    quantity = forms.IntegerField(
        label='Количество',
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'min': 1, 'required': 'required'}),
    )
    pickup_point = forms.ModelChoiceField(
        label='Точка самовывоза',
        queryset=PickupPoint.objects.filter(is_active=True),
        widget=forms.Select(attrs={'required': 'required'}),
    )

    class Meta:
        model = Purchase
        fields = ('quantity', 'pickup_point')

    def __init__(self, *args, medication=None, customer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.medication = medication
        self.customer = customer

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if self.medication and not self.medication.is_available:
            raise ValidationError('Медикамент недоступен для покупки.')
        return quantity

    def save(self, commit=True):
        purchase = super().save(commit=False)
        purchase.customer = self.customer
        purchase.medication = self.medication
        purchase.total_amount = self.medication.price * purchase.quantity
        if commit:
            purchase.save()
        return purchase


class EmployeeSaleForm(forms.ModelForm):
    """Продажа в зале — оформляет текущий сотрудник."""

    sold_at = forms.DateTimeField(
        label='Дата продажи',
        input_formats=['%Y-%m-%dT%H:%M', '%d/%m/%Y %H:%M', '%d.%m.%Y %H:%M'],
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'required': 'required'},
            format='%Y-%m-%dT%H:%M',
        ),
        validators=[validate_not_future_datetime],
    )
    medication = forms.ModelChoiceField(
        label='Медикамент',
        queryset=Medication.objects.filter(is_available=True).order_by('name'),
    )
    quantity = forms.IntegerField(label='Количество', min_value=1, initial=1)

    class Meta:
        model = Sale
        fields = ('medication', 'quantity', 'sold_at')

    def __init__(self, *args, employee=None, owner_picks_employee=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        if owner_picks_employee:
            self.fields['employee'] = forms.ModelChoiceField(
                label='Сотрудник',
                queryset=Employee.objects.select_related('user').order_by(
                    'user__last_name',
                    'user__first_name',
                ),
            )

    def clean_sold_at(self):
        sold_at = self.cleaned_data['sold_at']
        if timezone.is_naive(sold_at):
            sold_at = timezone.make_aware(
                sold_at,
                timezone.get_current_timezone(),
            )
        validate_not_future_datetime(sold_at)
        return sold_at

    def clean(self):
        cleaned = super().clean()
        medication = cleaned.get('medication')
        if medication and not medication.is_available:
            raise ValidationError('Медикамент недоступен для продажи.')
        if 'employee' in self.fields and not cleaned.get('employee'):
            self.add_error('employee', 'Выберите сотрудника.')
        return cleaned

    def save(self, commit=True):
        sale = super().save(commit=False)
        if 'employee' in self.fields:
            sale.employee = self.cleaned_data['employee']
        else:
            sale.employee = self.employee
        sale.total_amount = sale.medication.price * sale.quantity
        if commit:
            sale.save()
        return sale


class StaffPurchaseForm(forms.ModelForm):
    """Оформление заказа сотрудником с указанием даты покупки."""

    purchased_at = forms.DateTimeField(
        label='Дата покупки',
        input_formats=['%Y-%m-%dT%H:%M', '%d/%m/%Y %H:%M', '%d.%m.%Y %H:%M'],
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local', 'required': 'required'},
            format='%Y-%m-%dT%H:%M',
        ),
        validators=[validate_not_future_datetime],
    )
    customer = forms.ModelChoiceField(
        label='Покупатель',
        queryset=Customer.objects.select_related('user').order_by('user__username'),
    )
    medication = forms.ModelChoiceField(
        label='Медикамент',
        queryset=Medication.objects.filter(is_available=True).order_by('name'),
    )
    pickup_point = forms.ModelChoiceField(
        label='Точка самовывоза',
        queryset=PickupPoint.objects.filter(is_active=True),
    )
    quantity = forms.IntegerField(label='Количество', min_value=1, initial=1)

    class Meta:
        model = Purchase
        fields = (
            'customer',
            'medication',
            'pickup_point',
            'quantity',
            'purchased_at',
        )

    def clean_purchased_at(self):
        purchased_at = self.cleaned_data['purchased_at']
        if timezone.is_naive(purchased_at):
            purchased_at = timezone.make_aware(
                purchased_at,
                timezone.get_current_timezone(),
            )
        validate_not_future_datetime(purchased_at)
        return purchased_at

    def clean(self):
        cleaned = super().clean()
        medication = cleaned.get('medication')
        quantity = cleaned.get('quantity')
        if medication and quantity and not medication.is_available:
            raise ValidationError('Медикамент недоступен для покупки.')
        return cleaned

    def save(self, commit=True):
        purchase = super().save(commit=False)
        purchase.total_amount = purchase.medication.price * purchase.quantity
        if commit:
            purchase.save()
        return purchase


class MedicationForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        label='Категории',
        queryset=MedicationCategory.objects.all(),
        required=False,
        widget=forms.SelectMultiple,
    )
    suppliers = forms.ModelMultipleChoiceField(
        label='Поставщики',
        queryset=Supplier.objects.all(),
        required=False,
        widget=forms.SelectMultiple,
    )

    class Meta:
        model = Medication
        fields = (
            'code',
            'name',
            'instruction',
            'description',
            'price',
            'photo',
            'is_available',
            'categories',
            'suppliers',
        )
        widgets = {
            'instruction': forms.Textarea(attrs={'rows': 4}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
        }


class MedicationFilterForm(forms.Form):
    q = forms.CharField(
        label='Поиск',
        required=False,
        widget=forms.TextInput(
            attrs={'placeholder': 'Название, описание или код'},
        ),
    )
    category = forms.ModelChoiceField(
        label='Категория',
        queryset=MedicationCategory.objects.all(),
        required=False,
        empty_label='Все категории',
    )
    price_min = forms.DecimalField(
        label='Цена от',
        required=False,
        min_value=0,
        decimal_places=2,
    )
    price_max = forms.DecimalField(
        label='Цена до',
        required=False,
        min_value=0,
        decimal_places=2,
    )
    sort = forms.ChoiceField(
        label='Сортировка',
        required=False,
        choices=(
            ('name', 'По названию'),
            ('price_asc', 'Цена по возрастанию'),
            ('price_desc', 'Цена по убыванию'),
        ),
        initial='name',
    )

