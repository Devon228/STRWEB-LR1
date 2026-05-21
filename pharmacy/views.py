import logging
from decimal import Decimal
from zoneinfo import ZoneInfo

from asgiref.sync import async_to_sync
from django import forms
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from pharmacy.forms import (
    LoginForm,
    MedicationFilterForm,
    MedicationForm,
    PurchaseForm,
    RegistrationForm,
    ReviewForm,
)
from pharmacy.mixins import (
    CustomerRequiredMixin,
    EmployeeRequiredMixin,
    OwnerRequiredMixin,
)
from pharmacy.models import (
    AdditionalService,
    Article,
    CompanyInfo,
    ContactPerson,
    Glossary,
    Medication,
    MedicationCategory,
    PickupPoint,
    PromoCode,
    Purchase,
    Review,
    Sale,
    Vacancy,
)
from pharmacy.charts import (
    generate_category_popularity_chart,
    generate_sales_by_date_chart,
)
from pharmacy.audit_log import log_purchase, log_validation_error
from pharmacy.concurrency import load_game_assets
from pharmacy.roles import Role, get_user_role
from pharmacy.services.currency import fetch_exchange_rates
from pharmacy.services.weather import fetch_weather, get_weather_cached
from pharmacy.statistics import compute_pharmacy_statistics
from pharmacy.time_utils import (
    format_date_dd_mm_yyyy,
    get_session_timezone,
    current_moment_context,
)

logger = logging.getLogger('pharmacy')


class HomeView(TemplateView):
    template_name = 'pharmacy/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_article'] = (
            Article.objects.filter(is_published=True)
            .order_by('-published_at')
            .first()
        )
        if self.request.user.is_authenticated:
            context['weather'] = get_weather_cached()
        return context


class AboutView(TemplateView):
    template_name = 'pharmacy/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = CompanyInfo.objects.order_by('-updated_at').first()
        return context


class NewsListView(ListView):
    model = Article
    template_name = 'pharmacy/news_list.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        return Article.objects.filter(is_published=True).order_by('-published_at')


class NewsDetailView(DetailView):
    model = Article
    template_name = 'pharmacy/news_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return Article.objects.filter(is_published=True)


class GlossaryListView(ListView):
    model = Glossary
    template_name = 'pharmacy/glossary_list.html'
    context_object_name = 'entries'


class ContactListView(ListView):
    model = ContactPerson
    template_name = 'pharmacy/contact_list.html'
    context_object_name = 'contacts'

    def get_queryset(self):
        return ContactPerson.objects.filter(is_active=True)


class PrivacyView(TemplateView):
    template_name = 'pharmacy/privacy.html'


class VacancyListView(ListView):
    model = Vacancy
    template_name = 'pharmacy/vacancy_list.html'
    context_object_name = 'vacancies'

    def get_queryset(self):
        return Vacancy.objects.filter(is_active=True)


class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = 'pharmacy/register.html'
    success_url = reverse_lazy('pharmacy:home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('pharmacy:home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Регистрация прошла успешно.')
        return redirect(self.success_url)

    def form_invalid(self, form):
        log_validation_error('registration', form.errors, self.request)
        return super().form_invalid(form)


class PharmacyLoginView(LoginView):
    form_class = LoginForm
    template_name = 'pharmacy/login.html'
    redirect_authenticated_user = True


class PharmacyLogoutView(LogoutView):
    next_page = reverse_lazy('pharmacy:home')


class CategoryListView(ListView):
    model = MedicationCategory
    template_name = 'pharmacy/category_list.html'
    context_object_name = 'categories'


class MedicationListView(ListView):
    model = Medication
    template_name = 'pharmacy/medication_list.html'
    context_object_name = 'medications'
    paginate_by = 20

    def get_queryset(self):
        role = get_user_role(self.request.user)
        if role == Role.OWNER:
            qs = Medication.objects.prefetch_related('categories')
        else:
            qs = Medication.objects.filter(is_available=True).prefetch_related(
                'categories',
            )
        self.filter_form = MedicationFilterForm(self.request.GET)
        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get('q'):
                term = data['q']
                qs = qs.filter(
                    Q(name__icontains=term)
                    | Q(description__icontains=term)
                    | Q(code__icontains=term),
                )
            if data.get('category'):
                qs = qs.filter(categories=data['category'])
            if data.get('price_min') is not None:
                qs = qs.filter(price__gte=data['price_min'])
            if data.get('price_max') is not None:
                qs = qs.filter(price__lte=data['price_max'])
            sort = data.get('sort') or 'name'
            if sort == 'price_asc':
                qs = qs.order_by('price', 'name')
            elif sort == 'price_desc':
                qs = qs.order_by('-price', 'name')
            else:
                qs = qs.order_by('name')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        context['user_role'] = get_user_role(self.request.user)
        context['is_owner'] = context['user_role'] == Role.OWNER
        return context


class MedicationDetailView(DetailView):
    model = Medication
    template_name = 'pharmacy/medication_detail.html'
    context_object_name = 'medication'
    slug_field = 'code'
    slug_url_kwarg = 'code'

    def get_queryset(self):
        role = get_user_role(self.request.user)
        if role == Role.OWNER:
            return Medication.objects.prefetch_related('categories', 'suppliers')
        return Medication.objects.filter(is_available=True).prefetch_related(
            'categories',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role = get_user_role(self.request.user)
        context['user_role'] = role
        context['can_buy'] = role == Role.CUSTOMER
        context['is_owner'] = role == Role.OWNER
        return context


class MedicationCreateView(OwnerRequiredMixin, CreateView):
    model = Medication
    form_class = MedicationForm
    template_name = 'pharmacy/medication_form.html'
    success_url = reverse_lazy('pharmacy:medication_list')

    def form_valid(self, form):
        messages.success(self.request, 'Медикамент создан.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Создание медикамента'
        return context


class MedicationUpdateView(OwnerRequiredMixin, UpdateView):
    model = Medication
    form_class = MedicationForm
    template_name = 'pharmacy/medication_form.html'
    slug_field = 'code'
    slug_url_kwarg = 'code'
    success_url = reverse_lazy('pharmacy:medication_list')

    def form_valid(self, form):
        messages.success(self.request, 'Медикамент обновлён.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Редактирование медикамента'
        return context


class MedicationDeleteView(OwnerRequiredMixin, DeleteView):
    model = Medication
    template_name = 'pharmacy/medication_confirm_delete.html'
    slug_field = 'code'
    slug_url_kwarg = 'code'
    success_url = reverse_lazy('pharmacy:medication_list')

    def form_valid(self, form):
        messages.success(self.request, 'Медикамент удалён.')
        return super().form_valid(form)


class PromoListView(ListView):
    model = PromoCode
    template_name = 'pharmacy/promo_list.html'
    context_object_name = 'promos'

    def get_queryset(self):
        return PromoCode.objects.order_by('-valid_from')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        promos = context['promos']
        context['active_promos'] = [p for p in promos if p.is_active]
        context['archived_promos'] = [p for p in promos if not p.is_active]
        return context


class AdditionalServiceListView(ListView):
    model = AdditionalService
    template_name = 'pharmacy/service_list.html'
    context_object_name = 'services'

    def get_queryset(self):
        return AdditionalService.objects.filter(is_active=True)


class ReviewListView(ListView):
    model = Review
    template_name = 'pharmacy/review_list.html'
    context_object_name = 'reviews'
    paginate_by = 10


class ReviewCreateView(CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'pharmacy/review_form.html'
    success_url = reverse_lazy('pharmacy:review_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(
                request,
                'Войдите или зарегистрируйтесь, чтобы оставить отзыв.',
            )
            return redirect(f"{reverse('pharmacy:login')}?next={request.path}")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.author_name = (
            self.request.user.get_full_name() or self.request.user.username
        )
        messages.success(self.request, 'Отзыв отправлен.')
        return super().form_valid(form)


class PickupPointListView(CustomerRequiredMixin, ListView):
    model = PickupPoint
    template_name = 'pharmacy/pickup_list.html'
    context_object_name = 'pickup_points'

    def get_queryset(self):
        return PickupPoint.objects.filter(is_active=True)


class PurchaseListView(CustomerRequiredMixin, ListView):
    model = Purchase
    template_name = 'pharmacy/purchase_list.html'
    context_object_name = 'purchases'

    def get_queryset(self):
        return Purchase.objects.filter(
            customer=self.request.user.customer_profile,
        ).select_related('medication', 'pickup_point')


class PurchaseCreateView(CustomerRequiredMixin, CreateView):
    form_class = PurchaseForm
    template_name = 'pharmacy/purchase_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.medication = get_object_or_404(
            Medication,
            code=kwargs['code'],
            is_available=True,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['medication'] = self.medication
        kwargs['customer'] = self.request.user.customer_profile
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['medication'] = self.medication
        return context

    def get_success_url(self):
        messages.success(self.request, 'Покупка оформлена.')
        return reverse('pharmacy:purchase_list')

    def form_valid(self, form):
        purchase = form.save()
        log_purchase(
            self.request.user.username,
            self.medication.code,
            purchase.quantity,
            purchase.total_amount,
            self.request,
        )
        return redirect(self.get_success_url())


class EmployeeSaleListView(EmployeeRequiredMixin, ListView):
    model = Sale
    template_name = 'pharmacy/employee_sales.html'
    context_object_name = 'sales'

    def get_queryset(self):
        return Sale.objects.filter(
            employee=self.request.user.employee_profile,
        ).select_related('medication', 'employee')


class EmployeeSupplierListView(EmployeeRequiredMixin, TemplateView):
    template_name = 'pharmacy/employee_suppliers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['suppliers'] = self.request.user.employee_profile.suppliers.all()
        return context


class OwnerDashboardView(OwnerRequiredMixin, TemplateView):
    template_name = 'pharmacy/owner_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total = Sale.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal(
            '0',
        )
        by_department = (
            Sale.objects.values('employee__department__name')
            .annotate(revenue=Sum('total_amount'), sales_count=Count('id'))
            .order_by('-revenue')
        )
        context['total_revenue'] = total
        context['revenue_by_department'] = by_department
        context['medications_count'] = Medication.objects.count()
        context['sales_count'] = Sale.objects.count()
        return context


class TimezoneForm(forms.Form):
    user_timezone = forms.ChoiceField(
        label='Часовой пояс',
        choices=[],
    )

    def __init__(self, *args, current_tz=None, **kwargs):
        super().__init__(*args, **kwargs)
        popular = [
            'Europe/Minsk',
            'UTC',
            'Europe/Moscow',
            'Europe/Warsaw',
            'Europe/Kiev',
        ]
        choices = [(tz, tz) for tz in popular]
        self.fields['user_timezone'].choices = choices
        if current_tz and current_tz not in popular:
            self.fields['user_timezone'].choices.insert(
                0,
                (current_tz, current_tz),
            )


class AnalyticsView(OwnerRequiredMixin, TemplateView):
    template_name = 'pharmacy/analytics.html'

    def post(self, request, *args, **kwargs):
        tz = request.POST.get('user_timezone', 'Europe/Minsk')
        if tz:
            request.session['user_timezone'] = tz
            messages.success(request, f'Часовой пояс: {tz}')
        return redirect('pharmacy:analytics')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_tz = get_session_timezone(self.request)
        context.update(current_moment_context(self.request))
        context['timezone_form'] = TimezoneForm(
            current_tz=str(user_tz),
            initial={'user_timezone': str(user_tz)},
        )

        context['weather'] = fetch_weather()
        exchange = fetch_exchange_rates(base='USD', targets=('BYN', 'EUR'))
        context['exchange'] = exchange
        context['stats'] = compute_pharmacy_statistics()

        context['chart_errors'] = []
        try:
            context['chart_sales_url'] = generate_sales_by_date_chart()
            context['chart_categories_url'] = generate_category_popularity_chart()
        except Exception as exc:
            logger.exception('Chart generation failed: %s', exc)
            context['chart_sales_url'] = ''
            context['chart_categories_url'] = ''
            context['chart_errors'].append(str(exc))

        utc_tz = ZoneInfo('UTC')
        medications_dates = []
        for med in Medication.objects.order_by('name'):
            medications_dates.append({
                'code': med.code,
                'name': med.name,
                'price': med.price,
                'created_utc': format_date_dd_mm_yyyy(med.created_at, utc_tz),
                'created_user': format_date_dd_mm_yyyy(med.created_at, user_tz),
                'updated_utc': format_date_dd_mm_yyyy(med.updated_at, utc_tz),
                'updated_user': format_date_dd_mm_yyyy(med.updated_at, user_tz),
            })
        context['medications_dates'] = medications_dates

        if exchange.ok and 'BYN' in exchange.rates:
            rate_byn = exchange.rates['BYN']
            samples = []
            for med in Medication.objects.order_by('name')[:5]:
                price_usd = med.price / rate_byn
                samples.append({
                    'name': med.name,
                    'price_byn': med.price,
                    'price_usd': round(price_usd, 2),
                })
            context['price_samples_usd'] = samples
            context['usd_to_byn'] = rate_byn

        return context


def concurrency_demo_view(request):
    """Демо задачи В: asyncio, конкурентная подгрузка игровых текстур."""
    simulation = async_to_sync(load_game_assets)()
    return render(
        request,
        'pharmacy/concurrency_demo.html',
        simulation,
    )
