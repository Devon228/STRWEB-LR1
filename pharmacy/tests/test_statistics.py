from decimal import Decimal

import pytest

from pharmacy.statistics import compute_pharmacy_statistics


@pytest.mark.django_db
def test_statistics_with_sales(sale, medication, customer_user):
    stats = compute_pharmacy_statistics()
    assert stats['total_sales_amount'] == Decimal('20.00')
    assert stats['sales_count'] == 1
    assert stats['sales_mean'] == 20.0
    assert stats['sales_median'] == 20.0
    assert stats['sales_mode'] == '20.0'
    assert stats['customers_count'] == 1
    assert stats['customer_age_mean'] is not None
    names = [m['name'] for m in stats['medications_alpha']]
    assert names == sorted(names, key=str.lower) or names == sorted(names)


@pytest.mark.django_db
def test_statistics_popular_category(sale, category):
    stats = compute_pharmacy_statistics()
    assert stats['popular_category'] is not None
    assert stats['popular_category'].name == category.name


@pytest.mark.django_db
def test_statistics_empty_sales(db):
    stats = compute_pharmacy_statistics()
    assert stats['sales_count'] == 0
    assert stats['sales_mean'] is None
    assert stats['total_sales_amount'] == 0
