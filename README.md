# Airlines Data Pipeline

## Описание

1, 2, 3 задание я реализовал в `./docker-entrypoint-initdb.d\initdb.sql`

4 задание можно найти в `./code\from_api_to_csv.py`

5 задание это dag airflow


**Поток данных:**

1. Получение данных из API о полетах и телеметрии (имитация api)
2. Добавление меток времени загрузки, форматирование данных
3. - Сохранение в S3 (MinIO) в формате CSV
   - Загрузка в ClickHouse с использованием временных таблиц для идемпотентности
   - Перезапись партиций для обеспечения консистентности данных


**Таблицы ClickHouse:**

- **`flights`** — информация о полетах (ID рейса, самолета, аэропорты, время отправления/прибытия)
- **`telemetry`** — телеметрические данные самолетов (параметры: температура двигателя, высота, скорость)

**Представления (Views):**

- **`v_flights`** — агрегированная статистика по задержкам рейсов по самолетам
- **`v_telemetry`** — агрегированная телеметрия по рейсам (максимальная высота, средняя скорость, время достижения 1000м)


## Быстрый старт

### Требования

- **Docker** версии 20.10 или выше
- **Docker Compose** версии 2.0 или выше

### Установка

1. **Клонируйте репозиторий**:
   ```bash
   git clone <repository-url>
   cd airlines_pipeline
   ```

2. **Создайте файл `.env`** в корне проекта:
   ```env
   AIRFLOW_UID=50000
   ```

3. **Запустите проект**:
   ```bash
   docker-compose up -d
   ```
   Дождитесь инициализации(может занять несколько минут)

4. **Откройте MinIo Ui**
   - URL: http://localhost:9000 
   - Логин: `minioadmin`
   - Пароль: `minioadmin`
   
   - Создайте бакет `prod`
   - Создайте `Access Key` и `Secret Key`

6. **Откройте Airflow UI**:
   - URL: http://localhost:8080
   - Логин: `airflow` (или значение из `.env`)
   - Пароль: `airflow` (или значение из `.env`)

   Добавьте Variable для доступа к S3 `ACCESS_KEY` и `SECRET_KEY`

   Добавьте Connection для Телеграма: Admin → Connections. 
      - Host: Ваш id в Телеграм или id группы
      - Password: Токен Телеграм бота

7. **Запускаем DAG** `flights_and_telemetry` в веб-интерфейсе Airflow

**Доступ к сервисам:**

- **Airflow Web UI**: http://localhost:8080
- **MinIO UI**: http://localhost:9000 (логин: `minioadmin`, пароль: `minioadmin`)
- **ClickHouse HTTP**: http://localhost:8123

**Остановка проекта:**
```bash
docker-compose down
```

**Остановка с удалением volumes (удалит все данные):**
```bash
docker-compose down -v
```
