# Развёртывание проекта «Аптека»

## Локальная разработка (SQLite)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser
python manage.py runserver
```

Без `DATABASE_URL` используется **SQLite** (`db.sqlite3`).

---

## Локальный запуск в Docker (PostgreSQL)

### Требования

- Docker и Docker Compose

### Команды

```bash
# Сборка и запуск web + postgres
docker compose up --build

# В другом терминале: демо-данные и суперпользователь
docker compose exec web python manage.py seed_data
docker compose exec web python manage.py createsuperuser
```

Сайт: http://127.0.0.1:8000/

Остановка:

```bash
docker compose down
```

### Публичный образ для преподавателя (Docker Hub)

```bash
docker build -t YOUR_DOCKERHUB_USER/pharmacy-lr5:latest .
docker login
docker push YOUR_DOCKERHUB_USER/pharmacy-lr5:latest
```

В `docker-compose.yml` можно заменить `build: .` на:

```yaml
image: YOUR_DOCKERHUB_USER/pharmacy-lr5:latest
```

---

## Деплой на Render.com

### 1. Подготовка репозитория GitHub

1. Создайте репозиторий и запушьте проект.
2. Добавьте преподавателя **@AnnBsuir** (anzh52889@gmail.com) в Collaborators с доступом к private repo.

### 2. PostgreSQL на Render

1. Dashboard → **New +** → **PostgreSQL**.
2. Создайте базу (Free tier подойдёт для ЛР).
3. Скопируйте **Internal Database URL** (или External, если БД и Web Service в одном регионе — Internal быстрее).

### 3. Web Service на Render

1. **New +** → **Web Service** → подключите GitHub-репозиторий.
2. Параметры:

| Поле | Значение |
|------|----------|
| **Environment** | Python 3 |
| **Region** | Frankfurt / ближайший к вам |
| **Branch** | `main` |
| **Root Directory** | *(пусто, если проект в корне репо)* |
| **Build Command** | `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate` |
| **Start Command** | `gunicorn PharmacyProject.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120` |

> Render задаёт переменную `$PORT` автоматически — не подставляйте 8000 в Start Command.

### 4. Переменные окружения (Environment)

В разделе **Environment** Web Service добавьте:

| Key | Value | Примечание |
|-----|-------|------------|
| `DATABASE_URL` | `postgres://...` из Render PostgreSQL | **Обязательно** — включает PostgreSQL |
| `SECRET_KEY` | длинная случайная строка | `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `False` | В продакшене всегда False |
| `ALLOWED_HOSTS` | `your-app-name.onrender.com` | Имя вашего сервиса на Render |
| `CSRF_TRUSTED_ORIGINS` | `https://your-app-name.onrender.com` | С протоколом `https://` |
| `LOG_LEVEL` | `INFO` или `DEBUG` / `ERROR` | Уровень логирования |
| `OPENWEATHER_API_KEY` | ваш ключ | Опционально, для виджета погоды |
| `PHARMACY_CITY` | `Minsk` | Опционально |

**Пример:**

```
DATABASE_URL=postgres://user:pass@host/dbname
SECRET_KEY=django-secret-xxxxxxxx
DEBUG=False
ALLOWED_HOSTS=pharmacy-lr5.onrender.com
CSRF_TRUSTED_ORIGINS=https://pharmacy-lr5.onrender.com
LOG_LEVEL=INFO
```

### 5. После первого деплоя

В **Shell** Render (или однократно локально с prod `DATABASE_URL`):

```bash
python manage.py seed_data
python manage.py createsuperuser
```

### 6. Проверка

- Главная: `https://your-app-name.onrender.com/`
- Админка: `https://your-app-name.onrender.com/admin/`
- Аналитика (superuser): `/analytics/`
- Демо asyncio: `/concurrency-demo/`

### 7. Логи на Render

Логи приложения выводятся в **Logs** Web Service (консоль). Файл `app.log` в продакшене не используется — только `StreamHandler`.

---

## Переключение БД (кратко)

| Окружение | `DATABASE_URL` | База |
|-----------|----------------|------|
| Локально `runserver` | не задана | SQLite |
| Docker Compose | задана (`postgres://...`) | PostgreSQL |
| Render.com | задана (из Render Postgres) | PostgreSQL |

---

## Устранение проблем

| Проблема | Решение |
|----------|---------|
| `DisallowedHost` | Добавьте домен Render в `ALLOWED_HOSTS` |
| CSRF 403 | Добавьте `https://...onrender.com` в `CSRF_TRUSTED_ORIGINS` |
| Статика не грузится | Убедитесь, что `collectstatic` в Build Command |
| Нет данных | Выполните `seed_data` в Shell |
| Погода не работает | Задайте `OPENWEATHER_API_KEY` |

---

## Пункт ТЗ: доступ к API

Веб-интерфейс защищён сессиями Django и ролями (`Customer` / `Employee` / `Owner`). Отдельный REST API в проекте не выделен; внешние API (OpenWeather, курсы валют) вызываются только с сервера.
