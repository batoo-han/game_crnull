## Деплой на Ubuntu Server через Docker

### Что разворачиваем
- `api`: FastAPI + SQLite (файл `data/app.db` в volume). Миграции не требуются для SQLite. При необходимости можно задать `DATABASE_URL` (например, Postgres).
- `web`: Nginx, раздаёт сборку фронтенда и проксирует `/api` на `api:8000`.

### Порты (по умолчанию)
- Web (игра): `8080` на хосте (`80` в контейнере).
- API (для отладки): `8000` на хосте (`8000` в контейнере).

### Подготовка сервера (Ubuntu)
1) Установить Docker и docker compose plugin:
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
```
Перелогиньтесь в SSH, чтобы группа docker применилась.

2) Склонировать проект на сервер (git clone/rsync).

3) Создать `.env` из шаблона и заполнить секреты:
```bash
cp .env.example .env
```
Минимум:
- `API_SECRET_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `ADMIN_INITIAL_PASSWORD`
- (опционально) `ADMIN_ROUTE_SECRET` для скрытого URL админки
- (опционально) `DATABASE_URL`, если нужен внешний Postgres/другая БД вместо SQLite

4) Собрать и поднять:
```bash
docker compose -f infra/docker-compose.yml up -d --build
```

5) Проверить:
- Игра: `http://<ваш_хост>:8080`
- Админка: `http://<ваш_хост>:8080/admin` или `/admin/<секрет>` если задан `ADMIN_ROUTE_SECRET`

### Данные и volume
- SQLite хранится в `data/app.db`, вынесен в volume `api_data` (см. compose).
- Для бэкапа достаточно скопировать `data/app.db` (или весь volume).

### Первичная админка
- При первом старте создаётся админ, если его ещё нет.
- Логин: `ADMIN_USERNAME` (по умолчанию `admin`), пароль: `ADMIN_INITIAL_PASSWORD`.
- После первого входа смените пароль в админке.

### Безопасность
- Не коммитьте `.env`, держите его только на сервере.
- В проде включайте `APP_ENV=prod` (secure cookies).
- Настройте домен + HTTPS (Nginx/Traefik/Cloudflare).
- Ограничьте SSH-доступ, держите токены и чат-ID только в `.env`.