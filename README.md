# Steam Cases Backend

Backend-проект для сервиса открытия кейсов с ключами активации игр Steam.

## Стек

- Django: модели, ORM, миграции и административная панель.
- FastAPI: REST API для SPA/мобильного клиента.
- PostgreSQL: единая реляционная база данных для Django и FastAPI.
- JWT (PyJWT): access-токены для клиентской аутентификации.
- pytest + pytest-django + FastAPI TestClient: базовые API-тесты.
- Docker / Docker Compose: PostgreSQL + Django Admin + FastAPI.

## Архитектура

```text
steam_case_backend/
├── django_project/        # Django project: settings, admin URL, WSGI/ASGI
├── fastapi_app/           # FastAPI REST API
├── shared/                # Общие Django ORM модели + admin + migrations; views/serializers intentionally unused
├── tests/                 # API tests
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

FastAPI загружает Django через `django.setup()` и использует те же ORM-модели и ту же PostgreSQL БД.

## Важная модель связи CaseItem

`Case.items` реализован как ManyToMany через промежуточную модель `CaseItem`.
Поле `CaseItem.weight` хранит относительный вес выпадения предмета.

Например:

- Item A: weight=70
- Item B: weight=25
- Item C: weight=5

Шансы: 70%, 25%, 5%.

API деталей кейса вычисляет `chance_percent` как `weight / sum(weights) * 100`.

## Поведение при отсутствии ключа

Переменная:

```env
CASE_NO_KEY_POLICY=item_only
```

Варианты:

- `item_only`: открытие успешно, `Opening.key = null`, клиент получает предмет без ключа.
- `error`: запрос завершается HTTP 409, баланс не списывается и `Opening` не создаётся.

Для реального коммерческого сервиса обычно безопаснее использовать `error` либо отдельный механизм отложенной выдачи.

## Локальный запуск

### 1. PostgreSQL

Создайте базу и пользователя:

```sql
CREATE DATABASE steam_cases;
CREATE USER steam_cases WITH PASSWORD 'steam_cases';
GRANT ALL PRIVILEGES ON DATABASE steam_cases TO steam_cases;
```

### 2. Python environment

Рекомендуется Python 3.12+.

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Установка зависимостей:

```bash
pip install -r requirements.txt
```

### 3. Environment

```bash
cp .env.example .env
```

Измените как минимум:

```env
DJANGO_SECRET_KEY=<long-random-secret>
JWT_SECRET_KEY=<different-long-random-secret>
POSTGRES_PASSWORD=<your-db-password>
```

### 4. Миграции

```bash
python manage.py migrate
```

При последующих изменениях моделей:

```bash
python manage.py makemigrations shared
python manage.py migrate
```

### 5. Django superuser

```bash
python manage.py createsuperuser
```

### 6. Django Admin

```bash
python manage.py runserver 0.0.0.0:8000
```

Админка:

```text
http://127.0.0.1:8000/admin/
```

### 7. FastAPI

В отдельном терминале:

```bash
uvicorn fastapi_app.main:app --reload --host 0.0.0.0 --port 8001
```

Swagger UI:

```text
http://127.0.0.1:8001/docs
```

OpenAPI JSON:

```text
http://127.0.0.1:8001/openapi.json
```

Health check:

```text
GET http://127.0.0.1:8001/health
```

## Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

После запуска:

- Django Admin: `http://127.0.0.1:8000/admin/`
- FastAPI Swagger: `http://127.0.0.1:8001/docs`
- PostgreSQL: `localhost:5432`

Создание superuser внутри контейнера:

```bash
docker compose exec django python manage.py createsuperuser
```

## REST API

Базовый prefix:

```text
/api/v1
```

### Auth

#### POST `/api/v1/auth/register`

```json
{
  "username": "nick",
  "email": "nick@example.com",
  "password": "StrongPass123!"
}
```

Возвращает JWT и пользователя.

#### POST `/api/v1/auth/login`

```json
{
  "username": "nick",
  "password": "StrongPass123!"
}
```

#### POST `/api/v1/auth/token`

OAuth2 password form endpoint для Swagger Authorize.

Поля form-data:

```text
username=nick
password=StrongPass123!
```

#### GET `/api/v1/auth/me`

Header:

```text
Authorization: Bearer <token>
```

### Cases

#### GET `/api/v1/cases`

Параметры:

- `min_price`
- `max_price`
- `rarity=common|rare|epic|legendary`
- `limit` (1..100)
- `offset`

Пример:

```text
GET /api/v1/cases?min_price=1&max_price=50&rarity=epic&limit=20&offset=0
```

#### GET `/api/v1/cases/{case_id}`

Возвращает предметы, их веса и вычисленные проценты выпадения.

#### POST `/api/v1/cases/{case_id}/open`

Требует Bearer token.

Операция выполняется транзакционно:

1. Блокируется запись пользователя.
2. Блокируется кейс и его строки `CaseItem`, чтобы цена/веса не менялись посреди операции.
3. Проверяется баланс.
4. Выбирается предмет по весам.
5. Ищется свободный ключ выбранного предмета.
6. При наличии ключ блокируется и назначается пользователю.
7. Списывается баланс.
8. Создаётся `Opening`.
9. Создаётся debit `Transaction`.

### Inventory

#### GET `/api/v1/inventory`

Возвращает ключи со статусами `assigned` и `used`.

#### POST `/api/v1/inventory/{key_id}/use`

Помечает принадлежащий пользователю назначенный ключ как `used`.

### Opening history

#### GET `/api/v1/openings`

Параметры:

- `limit`
- `offset`

### Balance

#### POST `/api/v1/balance/top-up`

Тестовое пополнение без платёжного провайдера:

```json
{
  "amount": "100.00"
}
```

#### GET `/api/v1/balance/transactions`

История пополнений и списаний.

## Django Admin

Через Django Admin можно:

- создавать/изменять кейсы;
- задавать предметы и веса выпадения через inline `CaseItem`;
- создавать и изменять предметы;
- добавлять Steam keys;
- назначать статус ключей;
- просматривать пользователей;
- просматривать открытия;
- просматривать финансовые транзакции.

Для добавляемого в общий пул ключа:

- `owner = null`
- `status = available`

На уровне БД есть constraint, запрещающий несовместимые комбинации владельца и статуса.

## Tests

```bash
pytest
```

Тесты используют SQLite in-memory только как изолированную тестовую БД.
Продакшен-конфигурация использует PostgreSQL.

Покрыты базовые сценарии:

- регистрация и хеширование пароля;
- логин;
- пополнение баланса;
- список/детали кейса;
- открытие кейса и выдача ключа;
- режим открытия без ключа;
- инвентарь;
- перевод ключа в `used`.

## Пример curl

Регистрация:

```bash
curl -X POST http://127.0.0.1:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"nick","email":"nick@example.com","password":"StrongPass123!"}'
```

Пополнение:

```bash
curl -X POST http://127.0.0.1:8001/api/v1/balance/top-up \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"amount":"100.00"}'
```

Открытие:

```bash
curl -X POST http://127.0.0.1:8001/api/v1/cases/1/open \
  -H "Authorization: Bearer <TOKEN>"
```

## Что стоит добавить перед production

Этот проект является полноценным запускаемым backend-каркасом, но перед коммерческим запуском рекомендуется добавить:

- refresh tokens и отзыв токенов;
- rate limiting;
- реальный payment provider + webhook verification + idempotency;
- idempotency key для открытия кейса;
- аудит действий администратора;
- шифрование ключей активации at rest либо отдельное secret storage;
- антифрод;
- отдельный ledger вместо доверия только текущему `balance`;
- мониторинг и tracing;
- PostgreSQL-specific integration tests для конкурентного открытия;
- Celery/RQ для фоновых задач;
- Redis для rate limiting/locks/cache;
- HTTPS и reverse proxy;
- CSP/security headers для будущего frontend;
- юридическую проверку механики кейсов в целевых юрисдикциях.

## Встроенный frontend

В проект добавлен готовый SPA-интерфейс без отдельного Node.js-сервера. FastAPI раздаёт статические файлы из `frontend/`.

После запуска Docker Compose открой:

```text
http://127.0.0.1:8001/
```

Доступные пользовательские сценарии:

- регистрация и вход по JWT;
- сохранение сессии в браузере;
- просмотр и фильтрация кейсов;
- просмотр содержимого кейса и шансов выпадения;
- открытие кейса;
- отображение выигранного предмета и ключа;
- просмотр баланса и тестовое пополнение;
- просмотр инвентаря;
- копирование ключа;
- пометка ключа как использованного;
- история открытий.

Административная панель по-прежнему доступна отдельно:

```text
http://127.0.0.1:8000/admin/
```

Swagger/OpenAPI:

```text
http://127.0.0.1:8001/docs
```

### Применение frontend после обновления файлов

Если контейнеры уже были запущены, после замены файлов проекта выполни:

```bash
docker compose down
docker compose up -d --build --force-recreate
```

PostgreSQL volume при этом сохраняется. Не добавляй `-v`, если не хочешь удалить базу.

### Важное замечание про JWT

Текущий frontend хранит access token в `localStorage`, что удобно для локального demo/MVP. Для production-системы, особенно если сайт будет публичным и будет работать с реальными платежами/ключами, стоит рассмотреть короткоживущий access token и refresh token в `HttpOnly; Secure; SameSite` cookie, а также полноценную CSP/XSS-защиту.
