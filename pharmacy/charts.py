import base64
import logging
import os
from io import BytesIO

import matplotlib

os.environ.setdefault('MPLCONFIGDIR', '/tmp/matplotlib')

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate

from pharmacy.models import MedicationCategory, Sale

logger = logging.getLogger('pharmacy.charts')


def _fig_to_data_uri(fig):
    """PNG в data URI — работает на Render без раздачи /media/."""
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode('ascii')
    return f'data:image/png;base64,{encoded}'


def generate_sales_by_date_chart():
    """Линейный график суммы продаж по датам. Возвращает data URI для шаблона."""
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
    return _fig_to_data_uri(fig)


def generate_category_popularity_chart():
    """Столбчатая диаграмма популярности категорий. Возвращает data URI."""
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
    return _fig_to_data_uri(fig)
