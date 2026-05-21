# Диаграмма предметной области «Аптека»

Стиль — UML class diagram (как в учебном примере библиотеки MDN).

```mermaid
classDiagram
    class User {
        +String username
        +String email
    }

    class MedicationCategory {
        +String name
        +String description
        +__str__() String
    }

    class PharmacyDepartment {
        +String name
        +String description
        +int floor
        +__str__() String
    }

    class Supplier {
        +String name
        +String contact_person
        +String phone
        +String email
        +__str__() String
    }

    class Medication {
        +String code
        +String name
        +String instruction
        +String description
        +Decimal price
        +Image photo
        +MedicationCategory categories 0..*
        +Supplier suppliers 0..*
        +__str__() String
    }

    class Employee {
        +User user 1
        +PharmacyDepartment department 1
        +String position
        +Date birth_date
        +String phone
        +Supplier suppliers 0..*
        +__str__() String
    }

    class Customer {
        +User user 1
        +Date birth_date
        +String phone
        +__str__() String
    }

    class Sale {
        +Medication medication 1
        +Employee employee 1
        +int quantity
        +DateTime sold_at
        +Decimal total_amount
        +__str__() String
    }

    class Article {
        +String title
        +String summary
        +String content
        +DateTime published_at
        +__str__() String
    }

    class CompanyInfo {
        +String title
        +String about_text
        +__str__() String
    }

    class Glossary {
        +String question
        +String answer
        +DateTime added_at
        +__str__() String
    }

    class ContactPerson {
        +String full_name
        +String job_description
        +String phone
        +String email
        +__str__() String
    }

    class Vacancy {
        +String title
        +String description
        +__str__() String
    }

    class Review {
        +String author_name
        +int rating
        +String text
        +__str__() String
    }

    class PromoCode {
        +String code
        +int discount_percent
        +Date valid_from
        +Date valid_until
        +bool is_archived
        +__str__() String
    }

    User "1" -- "1" Employee : OneToOne
    User "1" -- "1" Customer : OneToOne
    PharmacyDepartment "1" -- "0..*" Employee : ForeignKey
    Employee "1" -- "0..*" Sale : ForeignKey
    Medication "1" -- "0..*" Sale : ForeignKey
    Medication "0..*" -- "0..*" MedicationCategory : ManyToMany
    Medication "0..*" -- "0..*" Supplier : ManyToMany
    Employee "0..*" -- "0..*" Supplier : ManyToMany
```

## Типы связей (п.3 ТЗ)

| Тип | Реализация |
|-----|------------|
| **OneToOne** | `Employee.user`, `Customer.user` |
| **ForeignKey** | `Sale.employee`, `Sale.medication`, `Employee.department` |
| **ManyToMany** | `Medication.categories`, `Medication.suppliers`, `Employee.suppliers` |

## Отличие сущностей

- **Employee** — сотрудник аптеки (продажи, отдел, поставщики).
- **ContactPerson** — контакты для публичной страницы сайта (не связан с `User`).
- **Customer** — покупатель (клиент = покупатель).
