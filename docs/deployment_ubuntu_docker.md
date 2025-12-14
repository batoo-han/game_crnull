## Деплой на Ubuntu Server через Docker

### Что будет запущено
Через `infra/docker-compose.yml` поднимаются 2 сервиса:
- `api` (FastAPI + SQLite файл `data/app.db`, автоприменение миграций не требуется)
- `web` (Nginx, раздаёт фронтенд и проксирует `/api` на `api:8000`)

### Порты
- Web (игра): `8080` на хосте (в контейнере `80`)
- API (для отладки): `8000` на хосте (в контейнере `8000`)

### Подготовка (локально Windows 11)
1) Установите Docker Desktop и убедитесь, что он запущен.
2) Скопируйте `.env`:

```bash
copy .env.example .env
```

3) Заполните секреты в `.env`:
- `API_SECRET_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `ADMIN_INITIAL_PASSWORD`
- (Опционально) `ADMIN_ROUTE_SECRET` (если хотите “скрыть” админку за секретным URL)
 - (Опционально) `DATABASE_URL` если нужен свой путь/драйвер; по умолчанию SQLite `data/app.db`.

4) Соберите и запустите:

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

5) Откройте игру в браузере на `http://localhost:8080`.
Админка: `http://localhost:8080/admin`.
Если задан `ADMIN_ROUTE_SECRET`, то: `http://localhost:8080/admin/<секрет>`.

### Подготовка (Ubuntu Server)
1) Установите Docker и docker compose plugin:

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
```

Перелогиньтесь в SSH сессию.

2) Скопируйте проект на сервер (git clone/rsync).
3) Создайте `.env` (на основе `.env.example`) и заполните значения.
4) Запустите:

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

### Первичная инициализация админки
- При первом старте `api` создаёт администратора, если в БД ещё нет ни одного.
- Логин берётся из `ADMIN_USERNAME` (по умолчанию `admin`).
- Пароль берётся из `ADMIN_INITIAL_PASSWORD`.
- В БД хранится только хэш.

ВАЖНО: после первого запуска рекомендуется сменить пароль администратора (в админке есть форма смены пароля).

### Важные замечания по безопасности
- Не публикуйте `.env`.
- В продакшене используйте домен + HTTPS.
- В продакшене `APP_ENV=prod` (включает `secure cookie` для админки).



