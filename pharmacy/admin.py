from django.contrib import admin
from django.db.models import Sum

from pharmacy.models import (
    AdditionalService,
    Article,
    CompanyInfo,
    ContactPerson,
    Customer,
    Employee,
    Glossary,
    Medication,
    MedicationCategory,
    PharmacyDepartment,
    PickupPoint,
    PromoCode,
    Purchase,
    Review,
    Sale,
    Supplier,
    Vacancy,
)


class SaleInline(admin.TabularInline):
    model = Sale
    extra = 0
    fields = ('medication', 'quantity', 'sold_at', 'total_amount')
    autocomplete_fields = ('medication',)
    show_change_link = True


@admin.register(MedicationCategory)
class MedicationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'medications_count', 'updated_at')
    search_fields = ('name', 'description')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('medications')

    @admin.display(description='Медикаментов')
    def medications_count(self, obj):
        return obj.medications.count()


@admin.register(PharmacyDepartment)
class PharmacyDepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'floor', 'employees_count', 'department_revenue')
    search_fields = ('name', 'description')
    list_filter = ('floor',)

    @admin.display(description='Сотрудников')
    def employees_count(self, obj):
        return obj.employees.count()

    @admin.display(description='Выручка отдела')
    def department_revenue(self, obj):
        total = Sale.objects.filter(employee__department=obj).aggregate(
            total=Sum('total_amount'),
        )['total']
        return total or 0


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'contact_person',
        'phone',
        'email',
        'medications_count',
        'employees_count',
    )
    search_fields = ('name', 'contact_person', 'email', 'address')
    list_filter = ('name',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('medications', 'employees')

    @admin.display(description='Медикаментов')
    def medications_count(self, obj):
        return obj.medications.count()

    @admin.display(description='Сотрудников')
    def employees_count(self, obj):
        return obj.employees.count()


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'price',
        'is_available',
        'categories_list',
        'updated_at',
    )
    list_filter = ('is_available', 'categories', 'suppliers')
    search_fields = ('code', 'name', 'description', 'instruction')
    filter_horizontal = ('categories', 'suppliers')
    readonly_fields = ('created_at', 'updated_at')
    inlines = (SaleInline,)
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'code',
                    'name',
                    'price',
                    'is_available',
                    'photo',
                ),
            },
        ),
        ('Описание', {'fields': ('instruction', 'description')}),
        ('Связи', {'fields': ('categories', 'suppliers')}),
        (
            'Даты',
            {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',),
            },
        ),
    )

    @admin.display(description='Категории')
    def categories_list(self, obj):
        return ', '.join(c.name for c in obj.categories.all())


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'department',
        'position',
        'phone',
        'employee_revenue',
    )
    list_filter = ('department', 'position')
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'phone',
        'position',
    )
    autocomplete_fields = ('user', 'department')
    filter_horizontal = ('suppliers',)
    inlines = (SaleInline,)
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Выручка сотрудника')
    def employee_revenue(self, obj):
        total = obj.sales.aggregate(total=Sum('total_amount'))['total']
        return total or 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'birth_date', 'age_display')
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'phone',
    )
    autocomplete_fields = ('user',)
    readonly_fields = ('created_at', 'updated_at', 'age_display')

    @admin.display(description='Возраст')
    def age_display(self, obj):
        return obj.age


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        'medication',
        'employee',
        'quantity',
        'total_amount',
        'sold_at',
    )
    list_filter = (
        'sold_at',
        'employee__department',
        'medication__categories',
    )
    search_fields = (
        'medication__code',
        'medication__name',
        'employee__user__username',
    )
    autocomplete_fields = ('medication', 'employee')
    date_hierarchy = 'sold_at'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'summary', 'is_published', 'published_at')
    list_filter = ('is_published', 'published_at')
    search_fields = ('title', 'summary', 'content')
    date_hierarchy = 'published_at'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ('title', 'updated_at')
    search_fields = ('title', 'about_text', 'requisites')


@admin.register(Glossary)
class GlossaryAdmin(admin.ModelAdmin):
    list_display = ('question', 'added_at')
    search_fields = ('question', 'answer')
    date_hierarchy = 'added_at'


@admin.register(ContactPerson)
class ContactPersonAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('full_name', 'job_description', 'email', 'phone')


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'rating', 'published_at', 'user')
    list_filter = ('rating', 'published_at')
    search_fields = ('author_name', 'text')
    date_hierarchy = 'published_at'


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'kind',
        'discount_percent',
        'valid_from',
        'valid_until',
        'is_archived',
        'active_badge',
    )
    list_filter = ('kind', 'is_archived')
    search_fields = ('code', 'description')
    date_hierarchy = 'valid_from'

    @admin.display(description='Статус', boolean=True)
    def active_badge(self, obj):
        return obj.is_active


@admin.register(PickupPoint)
class PickupPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'address', 'phone')


@admin.register(AdditionalService)
class AdditionalServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'customer',
        'medication',
        'quantity',
        'total_amount',
        'pickup_point',
        'purchased_at',
    )
    list_filter = ('purchased_at', 'pickup_point')
    search_fields = (
        'customer__user__username',
        'medication__code',
        'medication__name',
    )
    autocomplete_fields = ('customer', 'medication', 'pickup_point')
    date_hierarchy = 'purchased_at'


admin.site.site_header = 'Администрирование аптеки'
admin.site.site_title = 'Аптека'
admin.site.index_title = 'Управление данными'
