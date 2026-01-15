# REST API Справочник Организаций

> Тестовое задание: Создание REST API приложения для справочника Организаций, Зданий и Деятельности

## Описание

REST API приложение для управления справочником организаций с поддержкой:
- Иерархической классификации видов деятельности (до 3 уровней)
- Географического поиска по координатам (радиус и прямоугольная область)
- Статической авторизации через API ключ
- Древовидной структуры деятельностей

## Стек технологий

- **FastAPI** - современный веб-фреймворк
- **Pydantic** - валидация данных
- **SQLAlchemy** - ORM для работы с БД
- **Alembic** - система миграций
- **PostgreSQL** - база данных
- **Docker** - контейнеризация

## Модели данных

### Организация
- Название (например: ООО "Рога и Копыта")
- Телефоны (массив: 2-222-222, 3-333-333, 8-923-666-13-13)
- Здание (связь с конкретным зданием)
- Деятельность (может заниматься несколькими видами)

### Здание
- Адрес (например: г. Москва, ул. Ленина 1, офис 3)
- Географические координаты (широта и долгота)

### Деятельность
- Название
- Древовидная структура (вложенность до 3 уровней)
- Пример дерева:
  ```
  Еда
  ├── Мясная продукция
  └── Молочная продукция
  Автомобили
  ├── Грузовые
  └── Легковые
      ├── Запчасти
      └── Аксессуары
  ```

## Быстрый старт

### Развертывание (один команда)

```bash
docker-compose up --build
```

Приложение будет доступно:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Остановка

```bash
docker-compose down

# Полная очистка (включая данные БД)
docker-compose down -v
```

## Авторизация

Все запросы требуют заголовок с API ключом:

```
X-API-Key: your-secret-key
```

Ключ можно изменить в файле `docker-compose.yml` (переменная `API_KEY`).

## Реализованные методы API

### 1. Список организаций в конкретном здании
```http
GET /organizations?building_id=1
```

### 2. Организации по виду деятельности (с вложенными)
```http
GET /organizations?activity_id=1
```
**Важно**: Автоматически включает все дочерние виды деятельности.
Например, поиск по "Еда" вернёт организации с "Мясная продукция" и "Молочная продукция".

### 3. Поиск организаций по названию
```http
GET /organizations?name=Рога
```
Частичное совпадение, регистронезависимый поиск.

### 4. Географический поиск

**Радиус** (в метрах от точки):
```http
GET /organizations?lat=55.7558&lon=37.6173&radius=1000
```

**Прямоугольная область** (bounding box):
```http
GET /organizations?lat_min=55.74&lat_max=55.76&lon_min=37.59&lon_max=37.63
```

### 5. Список всех зданий
```http
GET /buildings
```

### 6. Информация об организации по ID
```http
GET /organizations/1
```
Возвращает полную информацию: здание, все виды деятельности, телефоны.

### 7. Список видов деятельности
```http
GET /activities
```

**С древовидной структурой**:
```http
GET /activities?include_tree=true
```

## Примеры запросов

### cURL

```bash
# Все организации
curl -H "X-API-Key: your-secret-key" http://localhost:8000/organizations

# Поиск по деятельности (иерархический)
curl -H "X-API-Key: your-secret-key" \
  "http://localhost:8000/organizations?activity_id=1"

# Гео-поиск (радиус 1км от Красной площади)
curl -H "X-API-Key: your-secret-key" \
  "http://localhost:8000/organizations?lat=55.7539&lon=37.6208&radius=1000"

# Детальная информация
curl -H "X-API-Key: your-secret-key" \
  http://localhost:8000/organizations/1 | jq
```

### Python

```python
import requests

API_KEY = "your-secret-key"
BASE_URL = "http://localhost:8000"
headers = {"X-API-Key": API_KEY}

# Поиск по виду деятельности
response = requests.get(
    f"{BASE_URL}/organizations",
    headers=headers,
    params={"activity_id": 1}
)
organizations = response.json()
```

## Swagger UI (интерактивная документация)

1. Откройте http://localhost:8000/docs
2. Нажмите "Authorize" и введите API ключ: `your-secret-key`
3. Тестируйте все методы в браузере

## Архитектура проекта

```
.
├── app/
│   ├── api/                    # Роуты API
│   │   ├── organizations.py    # Методы для организаций
│   │   ├── buildings.py        # Методы для зданий
│   │   └── activities.py       # Методы для деятельности
│   ├── models/                 # SQLAlchemy модели
│   │   └── models.py           # Building, Activity, Organization
│   ├── schemas/                # Pydantic схемы
│   │   └── schemas.py          # Валидация запросов/ответов
│   ├── core/                   # Основная логика
│   │   ├── database.py         # Подключение к БД
│   │   ├── auth.py             # Авторизация по API ключу
│   │   ├── geo_utils.py        # Гео-поиск (Haversine)
│   │   └── config.py           # Настройки
│   └── main.py                 # FastAPI приложение
├── alembic/                    # Миграции БД
│   └── versions/
│       └── 001_initial_migration.py
├── scripts/
│   └── seed_data.py            # Заполнение тестовыми данными
├── pyproject.toml              # Зависимости (современный стандарт)
├── Dockerfile                  # Docker образ
├── docker-compose.yml          # Оркестрация (app + postgres)
└── README_RU.md                # Эта документация
```

## База данных

### Схема

**buildings** (здания)
- id (PK)
- address (строка)
- latitude (float)
- longitude (float)

**activities** (виды деятельности)
- id (PK)
- name (строка, уникальная)
- parent_id (FK to activities, nullable)
- level (int, макс. 3)

**organizations** (организации)
- id (PK)
- name (строка)
- building_id (FK to buildings)
- phones (массив строк PostgreSQL)

**organization_activity** (связь многие-ко-многим)
- organization_id (FK)
- activity_id (FK)

### Миграции

Миграции применяются автоматически при запуске Docker контейнера:

```bash
# Вручную (если нужно)
alembic upgrade head
```

### Тестовые данные

Автоматически загружаются при первом запуске:
- **3 здания** в Москве
- **8 видов деятельности** (иерархическая структура)
- **5 организаций** с разными характеристиками

Пример организации:
```json
{
  "name": "ООО Рога и Копыта",
  "phones": ["2-222-222", "3-333-333", "8-923-666-13-13"],
  "building": "г. Москва, Блюхера, 32/1",
  "activities": ["Молочная продукция", "Мясная продукция"]
}
```

## Ключевые особенности реализации

### 1. Иерархический поиск по деятельности ⭐

При поиске по виду деятельности автоматически включаются **все дочерние** виды:

```python
# Метод в модели Activity
def get_all_descendants(self):
    descendants = [self.id]
    for child in self.children:
        descendants.extend(child.get_all_descendants())
    return descendants
```

Поиск `activity_id=1` (Еда) → находит организации с:
- Еда (id=1)
- Мясная продукция (id=3)
- Молочная продукция (id=4)

### 2. Ограничение вложенности (3 уровня) ⭐

Уровень вычисляется и хранится в БД:
- Уровень 1: Еда, Автомобили
- Уровень 2: Мясная продукция, Легковые
- Уровень 3: Запчасти, Аксессуары

Максимальная вложенность контролируется на уровне модели.

### 3. Гео-поиск ⭐

**Формула Хаверсина** для точного расчёта расстояний на сфере:

```python
def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    """Возвращает расстояние в метрах"""
    R = 6371000  # Радиус Земли
    # ... математика
    return distance_in_meters
```

Поддерживается:
- Поиск по радиусу (круг)
- Поиск по прямоугольной области (bounding box)

### 4. Авторизация через API ключ ⭐

```python
async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
```

Применяется ко всем endpoint'ам через Dependency Injection.

## Выполнение требований ТЗ

### ✅ Спроектирована БД
- 3 основные таблицы (organizations, buildings, activities)
- 1 связующая таблица (organization_activity)
- Правильные связи и индексы

### ✅ Созданы миграции
- Alembic настроен
- Начальная миграция создаёт все таблицы
- Применяется автоматически в Docker

### ✅ Заполнение тестовыми данными
- Скрипт `scripts/seed_data.py`
- Автоматически выполняется при старте
- Соответствует примерам из ТЗ

### ✅ Реализованы все методы API
- [x] Организации в конкретном здании
- [x] Организации по виду деятельности (с вложенными!)
- [x] Гео-поиск (радиус + прямоугольник)
- [x] Список зданий
- [x] Информация об организации по ID
- [x] Поиск по названию
- [x] Ограничение вложенности (3 уровня)
- [x] Список видов деятельности

### ✅ Docker контейнер
- `docker-compose up` - одна команда для запуска
- PostgreSQL и приложение в отдельных контейнерах
- Автоматические миграции и seed данных
- Health checks для надёжности

### ✅ Документация Swagger UI + ReDoc
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Автоматическая генерация из кода
- Интерактивное тестирование

## Дополнительные возможности

### Современная система сборки
Проект использует `pyproject.toml` (PEP 517/518/621) вместо устаревшего `requirements.txt`:

```bash
# Установка зависимостей
pip install -e .

# С инструментами разработки (black, ruff, mypy, pytest)
pip install -e ".[dev]"
```

### Makefile для удобства

```bash
make help         # Список всех команд
make build        # Собрать Docker образы
make up           # Запустить сервисы
make logs         # Просмотр логов
make test         # Запустить тесты API
make clean        # Полная очистка

# Для разработки
make install-dev  # Установить зависимости
make format       # Форматирование кода (black)
make lint         # Линтинг (ruff)
make check-types  # Проверка типов (mypy)
```

### Готовый тестовый скрипт

```bash
./test_api.sh
```

Автоматически проверяет все endpoint'ы.

## Локальная разработка (без Docker)

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Установите зависимости:
```bash
pip install -e ".[dev]"
```

3. Настройте PostgreSQL и создайте БД `organizations`

4. Создайте `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/organizations
API_KEY=your-secret-key
```

5. Примените миграции:
```bash
alembic upgrade head
```

6. Загрузите тестовые данные:
```bash
python scripts/seed_data.py
```

7. Запустите сервер:
```bash
uvicorn app.main:app --reload
```

## Проверка работоспособности

### Автоматический тест

```bash
# Убедитесь что сервисы запущены
docker-compose up -d

# Запустите тесты
./test_api.sh
```

### Ручная проверка

1. Откройте http://localhost:8000/docs
2. Authorize → введите `your-secret-key`
3. Протестируйте каждый endpoint:
   - ✅ GET /buildings
   - ✅ GET /activities (flat & tree)
   - ✅ GET /organizations (все фильтры)
   - ✅ GET /organizations/{id}

## Производительность

- **Индексы** на всех внешних ключах
- **Eager loading** для связанных данных (избегаем N+1)
- **Connection pooling** через SQLAlchemy
- **Efficient queries** с фильтрацией на уровне БД

## Безопасность

- API ключ для всех endpoint'ов
- Параметризованные запросы (защита от SQL injection)
- Валидация всех входных данных через Pydantic
- CORS настроен правильно

## Дополнительная документация

- [README.md](README.md) - Подробная документация (англ.)
- [QUICK_START.md](QUICK_START.md) - Быстрый старт
- [EXAMPLES.md](EXAMPLES.md) - Примеры использования API
- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Технические детали
- [MIGRATION_TO_PYPROJECT.md](MIGRATION_TO_PYPROJECT.md) - О современной системе сборки

## Технические детали

### Версии
- Python 3.11
- FastAPI 0.109.0
- SQLAlchemy 2.0.25
- PostgreSQL 15

### Особенности кода
- Типизация (type hints)
- Асинхронные endpoint'ы
- Pydantic V2 для валидации
- SQLAlchemy 2.0 (современный синтаксис)

## Troubleshooting

**Порт 8000 занят?**
```yaml
# Измените в docker-compose.yml
ports:
  - "8001:8000"
```

**Нужно пересоздать БД?**
```bash
docker-compose down -v
docker-compose up --build
```

**Проблемы с миграциями?**
```bash
docker-compose exec app alembic upgrade head
```

**Пересоздать тестовые данные?**
```bash
docker-compose exec app python scripts/seed_data.py
```

## Лицензия

Указана в файле [LICENSE](LICENSE)

## Контакты

Вопросы и предложения принимаются через Issues в репозитории.

---

**Статус**: ✅ Все требования ТЗ выполнены
**Версия**: 1.0.0
**Дата**: 2026-01-15
