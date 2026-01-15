# Testing Guide

Этот проект включает комплексный набор тестов для проверки всех компонентов REST API.

## 📋 Типы тестов

### 1. Unit тесты (pytest)

Unit тесты используют SQLite in-memory базу данных и не требуют запущенных Docker контейнеров.

**Покрытие:**
- ✅ Все API endpoints (Organizations, Buildings, Activities)
- ✅ API Key аутентификация
- ✅ Гео-поиск (радиус и bounding box)
- ✅ Иерархический поиск по деятельности
- ✅ Фильтрация и комбинирование параметров
- ✅ Валидация данных
- ✅ Edge cases и error handling

**Расположение:** `tests/`

**Структура:**
```
tests/
├── __init__.py
├── conftest.py                    # Fixtures и конфигурация
├── test_organizations.py          # Тесты организаций
├── test_buildings.py              # Тесты зданий
├── test_activities.py             # Тесты деятельности
├── test_auth.py                   # Тесты аутентификации
├── test_geo_search.py             # Тесты гео-поиска
└── test_hierarchical_search.py    # Тесты иерархического поиска
```

### 2. Integration тесты (bash)

Integration тесты выполняют реальные HTTP запросы к работающему API в Docker контейнерах.

**Покрытие:**
- ✅ End-to-end тестирование всех endpoints
- ✅ Реальная PostgreSQL база данных
- ✅ Полный жизненный цикл запроса

**Расположение:** `test_api.sh`

## 🚀 Запуск тестов

### Быстрый старт

```bash
# Установить dev зависимости (включая pytest)
make install-dev

# Запустить все тесты
make test
```

### Unit тесты (pytest)

```bash
# Запустить все unit тесты
make test-unit

# Или напрямую через pytest
pytest

# С подробным выводом
pytest -v

# Запустить конкретный файл
pytest tests/test_organizations.py

# Запустить конкретный тест
pytest tests/test_organizations.py::TestOrganizationsList::test_get_all_organizations

# Запустить тесты с фильтром по имени
pytest -k "auth"
pytest -k "geo_search"

# Показать покрытие кода (если установлен pytest-cov)
pytest --cov=app --cov-report=html
```

### Integration тесты (bash)

```bash
# Сначала запустить Docker контейнеры
make up

# Запустить интеграционные тесты
make test-api

# Или напрямую
bash test_api.sh
```

## 📊 Детали тестирования

### Конфигурация pytest

Настройки pytest находятся в файле [pytest.ini](pytest.ini):
- Автоматический поиск тестов в `tests/`
- Формат имен: `test_*.py`, `Test*`, `test_*`
- Подробный вывод с короткими traceback
- Поддержка маркеров для категоризации тестов

### Fixtures

Основные fixtures определены в [tests/conftest.py](tests/conftest.py):

- `db` - SQLAlchemy сессия с in-memory SQLite
- `client` - FastAPI TestClient с database override
- `auth_headers` - Валидные заголовки API Key
- `sample_buildings` - Тестовые здания (3 шт)
- `sample_activities` - Иерархия деятельности (5 уровней)
- `sample_organizations` - Тестовые организации (3 шт)

### Test coverage

#### Organizations endpoints (`test_organizations.py`)
- Получение списка организаций
- Фильтрация по зданию, имени, деятельности
- Иерархический поиск по parent activity
- Гео-поиск (радиус и bounding box)
- Комбинирование фильтров
- Получение организации по ID
- Структура response

**Тестов:** 13

#### Buildings endpoints (`test_buildings.py`)
- Получение списка зданий
- Фильтрация по адресу, индексу, кадастровому номеру
- Гео-поиск зданий
- Получение здания по ID
- Точность координат

**Тестов:** 11

#### Activities endpoints (`test_activities.py`)
- Получение списка деятельности
- Фильтрация по имени, parent_id, level
- Получение корневых activities
- Трехуровневая иерархия
- Связи parent-child
- Уникальность имен

**Тестов:** 15

#### Authentication (`test_auth.py`)
- Валидный API key
- Отсутствующий API key (422)
- Невалидный API key (403)
- Пустой API key
- Case-insensitive header
- Защита всех endpoints
- Публичные документационные endpoints

**Тестов:** 12

#### Geo-search (`test_geo_search.py`)
- Расчет Haversine distance
- Симметрия дистанции
- Короткие и длинные дистанции
- Bounding box calculation
- Radius search (buildings и organizations)
- Bounding box search
- Edge cases (zero radius, negative, inverted bbox)
- Частичные geo параметры

**Тестов:** 20

#### Hierarchical search (`test_hierarchical_search.py`)
- Метод `get_all_descendants()`
- Поиск по root возвращает все
- Поиск по middle level
- Поиск по leaf activity
- Разные ветки дерева
- Организации с multiple activities
- Трехуровневая иерархия
- Комбинирование с другими фильтрами
- Проверка консистентности уровней
- Отсутствие циклических ссылок

**Тестов:** 16

**Всего unit тестов:** 87+

## 🎯 Test data

### Sample Buildings (3)
1. Москва, ул. Ленина, 1 (55.7558, 37.6173)
2. Москва, ул. Пушкина, 10 (55.7600, 37.6200)
3. Санкт-Петербург, Невский пр., 1 (59.9343, 30.3351)

### Sample Activities (5, 3-level hierarchy)
```
Продукты питания (L1)
├── Мясная продукция (L2)
│   ├── Говядина (L3)
│   └── Свинина (L3)
└── Молочная продукция (L2)
```

### Sample Organizations (3)
1. ООО "Рога и Копыта" - Building 1, Activities: Мясная, Говядина
2. ИП "Молочный рай" - Building 2, Activities: Молочная
3. АО "Универсал" - Building 1, Activities: Продукты, Мясная, Молочная

## ✅ Continuous Testing

### Pre-commit checks

```bash
# Форматирование
make format

# Линтинг
make lint

# Type checking
make check-types

# Тесты
make test-unit
```

### CI/CD integration

Для интеграции в CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Install dependencies
  run: make install-dev

- name: Run linting
  run: make lint

- name: Run type checks
  run: make check-types

- name: Run unit tests
  run: pytest --cov=app --cov-report=xml

- name: Start services
  run: make up

- name: Run integration tests
  run: make test-api

- name: Cleanup
  run: make down
```

## 🐛 Debugging tests

### Запуск с pdb

```bash
# Остановиться на первом failed тесте
pytest --pdb

# Остановиться на первой ошибке
pytest -x --pdb
```

### Verbose output

```bash
# Максимальная детализация
pytest -vv

# Показать print statements
pytest -s

# Показать locals в traceback
pytest -l
```

### Конкретные тесты

```bash
# Один класс
pytest tests/test_organizations.py::TestOrganizationsList

# Один метод
pytest tests/test_organizations.py::TestOrganizationsList::test_get_all_organizations
```

## 📈 Best practices

1. **Изоляция тестов**: Каждый тест использует свежую DB сессию
2. **Фикстуры**: Переиспользование test data через fixtures
3. **Именование**: Понятные имена тестов описывают проверяемое поведение
4. **Arrange-Act-Assert**: Четкая структура каждого теста
5. **Edge cases**: Проверка граничных условий и ошибок
6. **No dependencies**: Тесты не зависят друг от друга

## 🔧 Troubleshooting

### Тесты падают с database errors

Убедитесь, что не запущены Docker контейнеры, конфликтующие с test DB:
```bash
make down
pytest
```

### Import errors

Установите dev dependencies:
```bash
make install-dev
```

### Test data issues

Fixtures создают fresh data для каждого теста. Если нужно debug:
```python
def test_something(db, sample_organizations):
    # Добавить print для проверки
    print(f"Organizations: {[o.name for o in sample_organizations]}")
```

## 📚 Дополнительные ресурсы

- [pytest documentation](https://docs.pytest.org/)
- [FastAPI testing guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy testing](https://docs.sqlalchemy.org/en/14/orm/session_basics.html#session-frequently-asked-questions)
