from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from pharmacy.models import (
    Customer,
    Employee,
    Medication,
    MedicationCategory,
    PharmacyDepartment,
    Sale,
)
from pharmacy.validators import validate_adult_age

User = get_user_model()
VALID_PHONE = '+375 (29) 111-22-33'


@pytest.mark.django_db
def test_medication_category_str(category):
    assert str(category) == 'Тестовая категория'


@pytest.mark.django_db
def test_medication_m2m_relations(medication, category, supplier):
    assert category in medication.categories.all()
    assert supplier in medication.suppliers.all()
    assert medication in category.medications.all()


@pytest.mark.django_db
def test_employee_one_to_one_user(employee_user, department):
    profile = employee_user.employee_profile
    assert profile.department == department
    assert profile.user == employee_user


@pytest.mark.django_db
def test_customer_one_to_one_user(customer_user):
    profile = customer_user.customer_profile
    assert profile.user == customer_user
    assert profile.age >= 18


@pytest.mark.django_db
def test_sale_foreign_keys(sale, medication, employee_user):
    assert sale.medication == medication
    assert sale.employee == employee_user.employee_profile
    assert sale.total_amount == Decimal('20.00')


@pytest.mark.django_db
def test_sale_auto_total_on_save(medication, employee_user):
    sale = Sale(
        medication=medication,
        employee=employee_user.employee_profile,
        quantity=3,
    )
    sale.save()
    assert sale.total_amount == medication.price * 3


@pytest.mark.django_db
def test_medication_code_unique(medication):
    with pytest.raises(IntegrityError):
        Medication.objects.create(
            code=medication.code,
            name='Дубликат',
            instruction='x',
            description='x',
            price=Decimal('1.00'),
        )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'birth_date,raises',
    [(date(2010, 6, 1), True), (date(1990, 1, 1), False)],
)
def test_customer_clean_age_validation(birth_date, raises):
    user = User.objects.create_user(
        username=f'u{birth_date.year}',
        password='x',
    )
    customer = Customer(
        user=user,
        birth_date=birth_date,
        phone=VALID_PHONE,
    )
    if raises:
        with pytest.raises(ValidationError):
            customer.full_clean()
    else:
        customer.full_clean()
