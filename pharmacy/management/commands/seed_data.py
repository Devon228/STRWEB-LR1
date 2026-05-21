from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

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
from pharmacy.roles import GROUP_CUSTOMER, GROUP_EMPLOYEE, ensure_role_groups

User = get_user_model()


class Command(BaseCommand):
    help = 'Наполняет БД демонстрационными данными аптеки и общих страниц.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Удалить демо-данные перед повторным наполнением.',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self._flush()
        elif Medication.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    'Данные уже есть. Используйте --flush для пересоздания.',
                ),
            )
            return
        self._seed()
        self.stdout.write(self.style.SUCCESS('Демо-данные успешно загружены.'))

    def _flush(self):
        models_order = [
            Purchase,
            Sale,
            Review,
            PromoCode,
            Vacancy,
            Glossary,
            ContactPerson,
            Article,
            CompanyInfo,
            Employee,
            Customer,
            Medication,
            AdditionalService,
            PickupPoint,
            Supplier,
            MedicationCategory,
            PharmacyDepartment,
        ]
        for model in models_order:
            model.objects.all().delete()
        User.objects.filter(
            username__in=[
                'admin_demo',
                'emp_ivanov',
                'emp_petrova',
                'cust_sidorenko',
                'cust_kozlov',
            ],
        ).delete()
        self.stdout.write('Демо-данные удалены.')

    def _seed(self):
        ensure_role_groups()
        customer_group = Group.objects.get(name=GROUP_CUSTOMER)
        employee_group = Group.objects.get(name=GROUP_EMPLOYEE)
        self._customer_group = customer_group
        self._employee_group = employee_group
        categories = self._seed_categories()
        departments = self._seed_departments()
        suppliers = self._seed_suppliers()
        medications = self._seed_medications(categories, suppliers)
        employees = self._seed_employees(departments, suppliers)
        customers = self._seed_customers()
        pickup_points = self._seed_pickup_and_services()
        self._seed_sales(medications, employees)
        self._seed_purchases(medications, customers, pickup_points)
        self._seed_common_pages()
        self._seed_promos()

    def _seed_categories(self):
        data = [
            ('Анальгетики', 'Препараты от боли и воспаления.'),
            ('Антибиотики', 'Средства против бактериальных инфекций.'),
            ('Витамины', 'Витаминно-минеральные комплексы.'),
            ('Сердечно-сосудистые', 'Препараты для сердца и сосудов.'),
            ('Противопростудные', 'Средства при ОРВИ и гриппе.'),
        ]
        return [MedicationCategory.objects.create(name=n, description=d) for n, d in data]

    def _seed_departments(self):
        data = [
            ('Рецептурный отдел', 'Отпуск рецептурных препаратов.', 1),
            ('Безрецептурный зал', 'ОТС и витамины.', 1),
            ('Косметика и гигиена', 'Уход и гигиена.', 2),
        ]
        return [
            PharmacyDepartment.objects.create(name=n, description=d, floor=f)
            for n, d, f in data
        ]

    def _seed_suppliers(self):
        data = [
            ('ФармСнаб BY', 'Алексей Кравцов', '+375 (29) 111-11-11'),
            ('МедИмпорт', 'Елена Войтюк', '+375 (29) 222-22-22'),
            ('БелФарм Опт', 'Игорь Левченко', '+375 (29) 333-33-33'),
            ('ВиталЛогистик', 'Марина Савицкая', '+375 (29) 444-44-44'),
        ]
        return [
            Supplier.objects.create(
                name=n,
                contact_person=c,
                phone=p,
                email=f'{c.split()[0].lower()}@supplier.by',
                address='г. Минск, ул. Промышленная, 10',
            )
            for n, c, p in data
        ]

    def _seed_medications(self, categories, suppliers):
        catalog = [
            ('MED-001', 'Парацетамол 500 мг', '12.50', [0], [0, 1]),
            ('MED-002', 'Ибупрофен 200 мг', '14.90', [0], [0]),
            ('MED-003', 'Амоксициллин 500 мг', '18.70', [1], [1]),
            ('MED-004', 'Азитромицин 250 мг', '22.40', [1], [1, 2]),
            ('MED-005', 'Компливит', '9.80', [2], [2]),
            ('MED-006', 'Витрум', '24.60', [2], [2, 3]),
            ('MED-007', 'Эналаприл 10 мг', '11.30', [3], [0, 3]),
            ('MED-008', 'Каптоприл 25 мг', '10.20', [3], [0]),
            ('MED-009', 'Терафлю', '16.50', [4], [1, 2]),
            ('MED-010', 'Ринза', '13.40', [4], [1]),
            ('MED-011', 'Нурофен детский', '17.90', [0], [2]),
            ('MED-012', 'Омега-3 1000 мг', '28.00', [2], [3]),
        ]
        meds = []
        for code, name, price, cat_idx, sup_idx in catalog:
            med = Medication.objects.create(
                code=code,
                name=name,
                instruction=f'Инструкция по применению для {name}.',
                description=f'Описание препарата {name}.',
                price=Decimal(price),
                is_available=True,
            )
            med.categories.set([categories[i] for i in cat_idx])
            med.suppliers.set([suppliers[i] for i in sup_idx])
            meds.append(med)
        return meds

    def _seed_employees(self, departments, suppliers):
        specs = [
            (
                'emp_ivanov',
                'Иван',
                'Иванов',
                departments[0],
                'Фармацевт',
                date(1990, 5, 12),
                '+375 (29) 555-55-55',
                [0, 1],
            ),
            (
                'emp_petrova',
                'Анна',
                'Петрова',
                departments[1],
                'Провизор',
                date(1988, 8, 3),
                '+375 (29) 666-66-66',
                [1, 2, 3],
            ),
        ]
        employees = []
        for username, first, last, dept, pos, bdate, phone, sup_idx in specs:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'email': f'{username}@pharmacy.by',
                },
            )
            user.set_password('demo1234')
            user.save()
            user.groups.add(self._employee_group)
            emp, _ = Employee.objects.get_or_create(
                user=user,
                defaults={
                    'department': dept,
                    'position': pos,
                    'birth_date': bdate,
                    'phone': phone,
                },
            )
            emp.suppliers.set([suppliers[i] for i in sup_idx])
            employees.append(emp)
        return employees

    def _seed_customers(self):
        customers = []
        specs = [
            (
                'cust_sidorenko',
                'Пётр',
                'Сидоренко',
                date(1995, 2, 20),
                '+375 (29) 777-77-77',
            ),
            (
                'cust_kozlov',
                'Ольга',
                'Козлова',
                date(1992, 11, 7),
                '+375 (29) 888-88-88',
            ),
        ]
        for username, first, last, bdate, phone in specs:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'email': f'{username}@mail.by',
                },
            )
            user.set_password('demo1234')
            user.save()
            user.groups.add(self._customer_group)
            customer, _ = Customer.objects.get_or_create(
                user=user,
                defaults={'birth_date': bdate, 'phone': phone},
            )
            customers.append(customer)
        return customers

    def _seed_pickup_and_services(self):
        points = [
            PickupPoint.objects.create(
                name='Филиал «Центр»',
                address='г. Минск, пр-т Независимости, 10',
                phone='+375 (29) 901-01-01',
                working_hours='08:00–22:00',
            ),
            PickupPoint.objects.create(
                name='Филиал «Юг»',
                address='г. Минск, ул. Будённого, 25',
                phone='+375 (29) 902-02-02',
                working_hours='09:00–21:00',
            ),
            PickupPoint.objects.create(
                name='Филиал «Север»',
                address='г. Минск, ул. Купалы, 7',
                phone='+375 (29) 903-03-03',
                working_hours='09:00–20:00',
            ),
        ]
        services = [
            AdditionalService.objects.create(
                name='Консультация фармацевта',
                description='Индивидуальный подбор препаратов.',
                price=Decimal('5.00'),
            ),
            AdditionalService.objects.create(
                name='Измерение давления',
                description='Контроль АД на аппарате в зале.',
                price=Decimal('2.50'),
            ),
            AdditionalService.objects.create(
                name='Доставка на дом',
                description='Доставка заказа в пределах МКАД.',
                price=Decimal('7.00'),
            ),
        ]
        return points

    def _seed_purchases(self, medications, customers, pickup_points):
        if not customers:
            return
        Purchase.objects.create(
            customer=customers[0],
            medication=medications[0],
            pickup_point=pickup_points[0],
            quantity=1,
            total_amount=medications[0].price,
        )
        Purchase.objects.create(
            customer=customers[0],
            medication=medications[4],
            pickup_point=pickup_points[1],
            quantity=2,
            total_amount=medications[4].price * 2,
        )
        if len(customers) > 1:
            Purchase.objects.create(
                customer=customers[1],
                medication=medications[2],
                pickup_point=pickup_points[2],
                quantity=1,
                total_amount=medications[2].price,
            )

    def _seed_sales(self, medications, employees):
        now = timezone.now()
        pairs = [
            (0, 0, 2, 0),
            (1, 0, 1, 2),
            (2, 1, 1, 5),
            (3, 1, 3, 8),
            (4, 0, 4, 12),
            (5, 1, 2, 18),
            (6, 0, 1, 24),
            (7, 1, 2, 30),
            (8, 0, 3, 36),
            (9, 1, 1, 48),
            (10, 0, 2, 60),
            (11, 1, 1, 72),
        ]
        for med_idx, emp_idx, qty, hours_ago in pairs:
            med = medications[med_idx]
            employee = employees[emp_idx]
            Sale.objects.create(
                medication=med,
                employee=employee,
                quantity=qty,
                sold_at=now - timedelta(hours=hours_ago),
                total_amount=med.price * qty,
            )

    def _seed_common_pages(self):
        CompanyInfo.objects.create(
            title='Аптека «Здоровье+»',
            about_text=(
                'Сеть аптек «Здоровье+» работает в Беларуси с 2010 года. '
                'Мы обеспечиваем доступность лекарств и консультации фармацевтов.'
            ),
            history=(
                '2010 — открытие первой аптеки.\n'
                '2015 — запуск онлайн-заказов.\n'
                '2020 — расширение сети до 12 точек.\n'
                '2024 — автоматизация учёта продаж.'
            ),
            requisites=(
                'ООО «Здоровье+»\n'
                'УНП 123456789\n'
                'г. Минск, пр-т Независимости, 1'
            ),
        )
        articles = [
            (
                'Открытие нового филиала',
                'В Минске открылся новый филиал сети «Здоровье+».',
                'Полный текст о торжественном открытии и акциях первого дня.',
            ),
            (
                'Сезон простуд: как подготовиться',
                'Фармацевты рекомендуют заранее пополнить домашнюю аптечку.',
                'Обзор средств профилактики и правил хранения препаратов.',
            ),
            (
                'Скидки на витамины',
                'До конца месяца действует скидка 15% на витаминные комплексы.',
                'Подробности акции уточняйте у провизора в зале.',
            ),
        ]
        for idx, (title, summary, content) in enumerate(articles):
            Article.objects.create(
                title=title,
                summary=summary,
                content=content,
                published_at=timezone.now() - timedelta(days=idx * 3),
                is_published=True,
            )
        faq = [
            (
                'Что такое рецептурный препарат?',
                'Препарат, отпускаемый только по рецепту врача.',
            ),
            (
                'Можно ли вернуть лекарство?',
                'Возврат возможен при сохранении товарного вида и чека.',
            ),
            (
                'Как хранить термолабильные препараты?',
                'Храните в холодильнике при температуре +2…+8 °C.',
            ),
        ]
        for question, answer in faq:
            Glossary.objects.create(question=question, answer=answer)
        contacts = [
            (
                'Светлана Мороз',
                'Консультации по ассортименту и заказам.',
                '+375 (29) 101-01-01',
                'info@zdorovie-plus.by',
            ),
            (
                'Дмитрий Кулак',
                'Вопросы доставки и самовывоза.',
                '+375 (29) 202-02-02',
                'delivery@zdorovie-plus.by',
            ),
            (
                'Екатерина Янковская',
                'Обратная связь и отзывы клиентов.',
                '+375 (29) 303-03-03',
                'feedback@zdorovie-plus.by',
            ),
            (
                'Игорь Левченко',
                'Главный фармацевт, консультации по рецептурным препаратам.',
                '+375 (29) 404-04-04',
                'pharmacist@zdorovie-plus.by',
            ),
            (
                'Ольга Петрова',
                'Оформление заказов и программа лояльности.',
                '+375 (29) 505-05-05',
                'orders@zdorovie-plus.by',
            ),
            (
                'Андрей Савицкий',
                'Работа с поставщиками и закупки.',
                '+375 (29) 606-06-06',
                'supply@zdorovie-plus.by',
            ),
            (
                'Марина Козлова',
                'Консультации по БАДам и витаминам.',
                '+375 (29) 707-07-07',
                'supplements@zdorovie-plus.by',
            ),
            (
                'Павел Жук',
                'Техническая поддержка онлайн-заказов.',
                '+375 (29) 808-08-08',
                'support@zdorovie-plus.by',
            ),
            (
                'Татьяна Волкова',
                'Вопросы по акциям и промокодам.',
                '+375 (29) 909-09-09',
                'promo@zdorovie-plus.by',
            ),
            (
                'Николай Орлов',
                'Приёмка товара и контроль сроков годности.',
                '+375 (29) 110-11-11',
                'warehouse@zdorovie-plus.by',
            ),
            (
                'Юлия Мельник',
                'Корпоративные клиенты и оптовые заказы.',
                '+375 (29) 211-12-12',
                'b2b@zdorovie-plus.by',
            ),
            (
                'Владимир Сидоренко',
                'Руководитель сети, партнёрства и СМИ.',
                '+375 (29) 312-13-13',
                'director@zdorovie-plus.by',
            ),
        ]
        for name, job, phone, email in contacts:
            ContactPerson.objects.create(
                full_name=name,
                job_description=job,
                phone=phone,
                email=email,
            )
        vacancies = [
            ('Фармацевт', 'Требуется опыт работы от 1 года, знание рецептуры.'),
            ('Кладовщик', 'Приёмка товара, учёт на складе.'),
            ('Провизор-стажёр', 'Обучение под руководством наставника.'),
        ]
        for title, description in vacancies:
            Vacancy.objects.create(title=title, description=description)
        reviews = [
            ('Алина', 5, 'Быстро оформили заказ, всё в наличии.'),
            ('Виктор', 4, 'Хорошие цены, но очередь в обед.'),
            ('Наталья', 5, 'Вежливые консультанты, помогли с выбором.'),
        ]
        for name, rating, text in reviews:
            Review.objects.create(
                author_name=name,
                rating=rating,
                text=text,
            )

    def _seed_promos(self):
        today = timezone.localdate()
        promos = [
            ('WINTER15', PromoCode.PromoKind.PROMO, 15, today - timedelta(days=30), today + timedelta(days=30), False),
            ('VITAMIN10', PromoCode.PromoKind.COUPON, 10, today - timedelta(days=10), today + timedelta(days=20), False),
            ('SPRING20', PromoCode.PromoKind.PROMO, 20, today - timedelta(days=120), today - timedelta(days=60), True),
            ('OLD5', PromoCode.PromoKind.COUPON, 5, today - timedelta(days=200), today - timedelta(days=150), True),
        ]
        for code, kind, discount, start, end, archived in promos:
            PromoCode.objects.create(
                code=code,
                kind=kind,
                discount_percent=discount,
                valid_from=start,
                valid_until=end,
                is_archived=archived,
                description=f'Демо-{kind} со скидкой {discount}%.',
            )
