## Локальная разработка (Windows 11) — backend в `.venv`

Этот документ описывает удобный и воспроизводимый сценарий разработки в Cursor на Windows 11:
- backend запускается из **`.venv`** (Python 3.12+)
- база данных — SQLite по умолчанию (файл `data/app.db` создаётся автоматически); при желании можно задать `DATABASE_URL` и работать с Postgres
- frontend — Vite dev server

---

### 0) Предварительные требования
- Python **3.12+** установлен и доступен как `py -3.12`
- Node.js **18+** (у вас стоит 22 — отлично)
- (Опционально) Docker Desktop — если хотите поднять внешнюю БД (Postgres) или запускать всё в контейнерах

---

### 1) Переменные окружения (`.env`)
В корне проекта:

```powershell
copy .env.example .env
```

Заполните минимум:
- `API_SECRET_KEY` (длинный случайный)
- `ADMIN_INITIAL_PASSWORD`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (если нужен Telegram)
- (опционально) `DATABASE_URL` — если нужен внешний Postgres/другая БД вместо SQLite
- (опционально) `ADMIN_ROUTE_SECRET` (если хотите “маскировать” админку)

---

### 2) База данных
- По умолчанию используется SQLite, файл `data/app.db` создаётся автоматически при старте.
- Если хотите работать с внешним Postgres, задайте `DATABASE_URL` и поднимите БД любым удобным способом (Docker/local).

---

### 3) Backend: создать и активировать `.venv`
В корне проекта:

```powershell
py -3.12 -m venv .venv
```

Активировать:

```powershell
.\.venv\Scripts\Activate.ps1
```

Если PowerShell запрещает запуск скриптов, выполните один раз:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### 4) Backend: установить зависимости

```powershell
python -m pip install -U pip
python -m pip install -r apps\api\requirements.txt -r apps\api\requirements-dev.txt
```

---

### 5) Backend: запустить API в dev-режиме

```powershell
cd apps\api
..\..\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8011
```

Проверка:
- health: `http://localhost:8011/api/health`

Админка (API):
- `POST /api/admin/login`
- `GET /api/admin/me`

---

### 6) Frontend: запустить Vite dev server
В отдельном терминале:

```powershell
cd apps\web
npm install --no-fund --no-audit
```

Чтобы фронтенд в dev ходил на API по `http://localhost:8011`, создайте файл:
`apps/web/.env.local` со строкой:

```text
VITE_API_BASE=http://localhost:8011
```

Запуск:

```powershell
npm run dev
```

Открыть:
- игра: `http://localhost:5174`
- админка: `http://localhost:5174/admin`
- если задан `ADMIN_ROUTE_SECRET`: `http://localhost:5174/admin/<секрет>`

---

### 7) Важно про “маскировку” админки
Если `ADMIN_ROUTE_SECRET` задан:
- открывайте админку только по `/admin/<секрет>`
- фронтенд автоматически добавит заголовок `X-Admin-Route-Secret`
- без него бекенд отдаст **404** на `/api/admin/*`

---

### 8) Типовые команды проверки (по желанию)
Backend:

```powershell
cd apps\api
..\..\.venv\Scripts\python -m pytest -q
..\..\.venv\Scripts\python -m pip_audit -r requirements.txt
```

Frontend:

```powershell
cd apps\web
npm audit --omit=dev --audit-level=high
npm run build
```


