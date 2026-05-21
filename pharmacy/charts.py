import logging
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.conf import settings
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate

from pharmacy.models import MedicationCategory, Sale

logger = logging.getLogger('pharmacy.charts')

ANALYTICS_DIR = 'analytics'


def _analytics_dir():
    path = Path(settings.MEDIA_ROOT) / ANALYTICS_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_sales_by_date_chart():
    """Линейный график суммы продаж по датам."""
    rows = (
        Sale.objects.annotate(day=TruncDate('sold_at'))
        .values('day')
        .annotate(total=Sum('total_amount'))
        .order_by('day')
    )
    days = [str(r['day']) for r in rows if r['day']]
    totals = [float(r['total'] or 0) for r in rows if r['day']]
    if not days:
        days = ['нет данных']
        totals = [0]

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(days, totals, marker='o', color='#2a6f97')
    ax.set_title('Продажи по датам (BYN)')
    ax.set_xlabel('Дата')
    ax.set_ylabel('Сумма')
    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()
    filename = 'sales_by_date.png'
    filepath = _analytics_dir() / filename
    fig.savefig(filepath, dpi=100)
    plt.close(fig)
    logger.info('Chart saved: %s', filepath)
    return f'{settings.MEDIA_URL}{ANALYTICS_DIR}/{filename}'


def generate_category_popularity_chart():
    """Столбчатая диаграмма популярности категорий по числу продаж."""
    rows = (
        MedicationCategory.objects.annotate(
            sales_count=Count('medications__sales', distinct=True),
        )
        .filter(sales_count__gt=0)
        .order_by('-sales_count')[:10]
    )
    names = [r.name for r in rows] or ['нет данных']
    counts = [r.sales_count for r in rows] or [0]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(names, counts, color='#e76f51')
    ax.set_title('Популярность категорий (число продаж)')
    ax.set_xlabel('Категория')
    ax.set_ylabel('Продажи')
    plt.xticks(rotation=30, ha='right')
    fig.tight_layout()
    filename = 'category_popularity.png'
    filepath = _analytics_dir() / filename
    fig.savefig(filepath, dpi=100)
    plt.close(fig)
    logger.info('Chart saved: %s', filepath)
    return f'{settings.MEDIA_URL}{ANALYTICS_DIR}/{filename}'
