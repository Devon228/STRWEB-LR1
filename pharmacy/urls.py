from django.urls import re_path

from pharmacy import views

app_name = 'pharmacy'

urlpatterns = [
    re_path(r'^$', views.HomeView.as_view(), name='home'),
    re_path(r'^about/$', views.AboutView.as_view(), name='about'),
    re_path(r'^news/$', views.NewsListView.as_view(), name='news_list'),
    re_path(
        r'^news/(?P<pk>\d+)/$',
        views.NewsDetailView.as_view(),
        name='news_detail',
    ),
    re_path(r'^glossary/$', views.GlossaryListView.as_view(), name='glossary_list'),
    re_path(r'^contacts/$', views.ContactListView.as_view(), name='contact_list'),
    re_path(r'^privacy/$', views.PrivacyView.as_view(), name='privacy'),
    re_path(r'^vacancies/$', views.VacancyListView.as_view(), name='vacancy_list'),
    re_path(r'^register/$', views.RegisterView.as_view(), name='register'),
    re_path(r'^login/$', views.PharmacyLoginView.as_view(), name='login'),
    re_path(r'^logout/$', views.PharmacyLogoutView.as_view(), name='logout'),
    re_path(r'^categories/$', views.CategoryListView.as_view(), name='category_list'),
    re_path(r'^medications/$', views.MedicationListView.as_view(), name='medication_list'),
    re_path(
        r'^medications/create/$',
        views.MedicationCreateView.as_view(),
        name='medication_create',
    ),
    re_path(
        r'^medications/(?P<code>[\w-]+)/edit/$',
        views.MedicationUpdateView.as_view(),
        name='medication_edit',
    ),
    re_path(
        r'^medications/(?P<code>[\w-]+)/delete/$',
        views.MedicationDeleteView.as_view(),
        name='medication_delete',
    ),
    re_path(
        r'^medications/(?P<code>[\w-]+)/buy/$',
        views.PurchaseCreateView.as_view(),
        name='purchase_create',
    ),
    re_path(
        r'^medications/(?P<code>[\w-]+)/$',
        views.MedicationDetailView.as_view(),
        name='medication_detail',
    ),
    re_path(r'^promos/$', views.PromoListView.as_view(), name='promo_list'),
    re_path(r'^services/$', views.AdditionalServiceListView.as_view(), name='service_list'),
    re_path(r'^reviews/$', views.ReviewListView.as_view(), name='review_list'),
    re_path(r'^reviews/add/$', views.ReviewCreateView.as_view(), name='review_add'),
    re_path(r'^pickup/$', views.PickupPointListView.as_view(), name='pickup_list'),
    re_path(r'^purchases/$', views.PurchaseListView.as_view(), name='purchase_list'),
    re_path(
        r'^employee/sales/$',
        views.EmployeeSaleListView.as_view(),
        name='employee_sales',
    ),
    re_path(
        r'^employee/sales/add/$',
        views.EmployeeSaleCreateView.as_view(),
        name='employee_sale_create',
    ),
    re_path(
        r'^employee/suppliers/$',
        views.EmployeeSupplierListView.as_view(),
        name='employee_suppliers',
    ),
    re_path(
        r'^employee/purchases/$',
        views.StaffPurchaseListView.as_view(),
        name='staff_purchase_list',
    ),
    re_path(
        r'^employee/purchases/add/$',
        views.StaffPurchaseCreateView.as_view(),
        name='staff_purchase_create',
    ),
    re_path(r'^owner/$', views.OwnerDashboardView.as_view(), name='owner_dashboard'),
    re_path(r'^analytics/$', views.AnalyticsView.as_view(), name='analytics'),
    re_path(
        r'^concurrency-demo/$',
        views.concurrency_demo_view,
        name='concurrency_demo',
    ),
    re_path(r'^set-timezone/$', views.set_timezone_view, name='set_timezone'),
]
