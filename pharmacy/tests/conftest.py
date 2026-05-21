from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from pharmacy.models import (
    Customer,
    Employee,
    Medication,
    MedicationCategory,
    PharmacyDepartment,
    PickupPoint,
    Sale,
    Supplier,
)
from pharmacy.roles import GROUP_CUSTOMER, GROUP_EMPLOYEE, ensure_role_groups

User = get_user_model()

VALID_PHONE = '+375 (29) 123-45-67'
ADULT_BIRTH = date(1990, 3, 15)


@pytest.fixture
def department(db):
    return PharmacyDepartment.objects.create(
        name='Тестовый отдел',
        description='Описание',
        floor=1,
    )


@pytest.fixture
def category(db):
    return MedicationCategory.objects.create(
        name='Тестовая категория',
        description='Категория для тестов',
    )


@pytest.fixture
def supplier(db):
    return Supplier.objects.create(
        name='Тест-поставщик',
        phone=VALID_PHONE,
    )


@pytest.fixture
def medication(db, category, supplier):
    med = Medication.objects.create(
        code='TEST-001',
        name='Тестовый препарат',
        instruction='Инструкция',
        description='Описание',
        price=Decimal('10.00'),
        is_available=True,
    )
    med.categories.add(category)
    med.suppliers.add(supplier)
    return med


@pytest.fixture
def pickup_point(db):
    return PickupPoint.objects.create(
        name='Точка тест',
        address='г. Минск',
        phone=VALID_PHONE,
        working_hours='09:00–18:00',
    )


@pytest.fixture
def customer_user(db):
    ensure_role_groups()
    user = User.objects.create_user(
        username='test_customer',
        password='testpass123',
        first_name='Пётр',
        last_name='Покупатель',
    )
    user.groups.add(Group.objects.get(name=GROUP_CUSTOMER))
    Customer.objects.create(
        user=user,
        birth_date=ADULT_BIRTH,
        phone=VALID_PHONE,
    )
    return user


@pytest.fixture
def employee_user(db, department, supplier):
    ensure_role_groups()
    user = User.objects.create_user(
        username='test_employee',
        password='testpass123',
        first_name='Анна',
        last_name='Сотрудник',
    )
    user.groups.add(Group.objects.get(name=GROUP_EMPLOYEE))
    emp = Employee.objects.create(
        user=user,
        department=department,
        position='Фармацевт',
        birth_date=ADULT_BIRTH,
        phone=VALID_PHONE,
    )
    emp.suppliers.add(supplier)
    return user


@pytest.fixture
def owner_user(db):
    return User.objects.create_superuser(
        username='test_owner',
        password='testpass123',
        email='owner@test.by',
    )


@pytest.fixture
def sale(db, medication, employee_user):
    employee = employee_user.employee_profile
    return Sale.objects.create(
        medication=medication,
        employee=employee,
        quantity=2,
        total_amount=Decimal('20.00'),
    )
