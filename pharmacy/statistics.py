from decimal import Decimal
from statistics import mean, median, multimode

from django.db.models import Count, Sum

from pharmacy.models import Customer, Medication, MedicationCategory, Sale


def _decimal_list(values):
    return [float(v) for v in values if v is not None]


def _safe_mean(values):
    data = _decimal_list(values)
    return round(mean(data), 2) if data else None


def _safe_median(values):
    data = _decimal_list(values)
    return round(median(data), 2) if data else None


def _safe_mode(values):
    data = _decimal_list(values)
    if not data:
        return None
    modes = multimode(data)
    return ', '.join(str(round(m, 2)) for m in sorted(set(modes)))


def compute_pharmacy_statistics():
    """Агрегированная статистика предметной области аптеки."""
    medications_alpha = list(
        Medication.objects.order_by('name').values('code', 'name', 'price'),
    )
    total_sales = Sale.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal(
        '0',
    )
    sale_amounts = list(
        Sale.objects.values_list('total_amount', flat=True),
    )
    customer_ages = [
        c.age for c in Customer.objects.all() if c.age is not None
    ]
    categories_stats = (
        MedicationCategory.objects.annotate(
            sales_count=Count('medications__sales', distinct=True),
            revenue=Sum('medications__sales__total_amount'),
        )
        .filter(sales_count__gt=0)
        .order_by('-sales_count')
    )
    popular = categories_stats.first()
    profitable = (
        MedicationCategory.objects.annotate(
            revenue=Sum('medications__sales__total_amount'),
        )
        .filter(revenue__isnull=False)
        .order_by('-revenue')
        .first()
    )
    return {
        'medications_alpha': medications_alpha,
        'total_sales_amount': total_sales,
        'sales_mean': _safe_mean(sale_amounts),
        'sales_median': _safe_median(sale_amounts),
        'sales_mode': _safe_mode(sale_amounts),
        'sales_count': len(sale_amounts),
        'customer_age_mean': round(mean(customer_ages), 1) if customer_ages else None,
        'customer_age_median': (
            round(median(customer_ages), 1) if customer_ages else None
        ),
        'customers_count': len(customer_ages),
        'popular_category': popular,
        'profitable_category': profitable,
        'categories_breakdown': list(categories_stats),
    }
