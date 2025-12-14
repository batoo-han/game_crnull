<div align="center">
  <h1>game_crnull — крестики-нолики с подарками и промокодами</h1>
  <p>Играй, побеждай, собирай подарки — и получай промокоды. Уведомления прилетают в Telegram.</p>
  <!-- Скрин: сохранить свой файл в docs/imgs/screenshot_gifts.png и заменить путь -->
  <img src="docs/imgs/screenshot_gifts.png" alt="Скрин: три подарка собраны" width="720"/>
</div>

---

## О проекте
Браузерная игра «Крестики-нолики» (игрок против компьютера) с:
- Промокодами за победу и за сбор 3 подарков
- Уведомлениями в Telegram (группы/каналы/личные чаты)
- Ярким UI, конфетти, анимацией подарков

## Правила и механики
- Победите бота (уровни: easy / medium / hard) — получите промокод.
- Соберите 3 подарка (появляются под клетками) — тоже получите промокод.
- Промокоды живут ограниченное время (настройка в админке).

## Быстрый старт (локально, Windows 11)
1) Скопировать окружение:
```bash
copy .env.example .env
```
2) Создать и активировать `.venv` и установить зависимости — см. `docs/development_windows_venv.md`.
3) Запустить API и фронт (см. тот же гайд).

## Запуск в Docker (как на сервере)
См. `docs/deployment_ubuntu_docker.md`:
- сборка образа API + фронт
- docker-compose пример
- переменные окружения через `.env`

## Настройка Telegram
- Токен бота: `TELEGRAM_BOT_TOKEN`
- ID чата/канала: `TELEGRAM_CHAT_ID` (для групп/каналов обычно начинается с `-100`)
- Необязательный fallback: `TELEGRAM_CHAT_USERNAME`
- Подробно: `docs/telegram_setup.md`

## Документация (docs/)
- Архитектура: `docs/architecture.md`
- Бизнес-логика: `docs/business_logic.md`
- Руководство пользователя: `docs/user_guide.md`
- Руководство администратора: `docs/admin_guide.md`
- Локальная разработка (Win11 + `.venv`): `docs/development_windows_venv.md`
- Деплой на Ubuntu через Docker: `docs/deployment_ubuntu_docker.md`
- Безопасность: `docs/security_checklist.md`
- Телеграм: `docs/telegram_setup.md`
- Дизайн под ЦА: `docs/design_rationale_25_40_female.md`

## Репозиторий и чистота
- Секреты храним только в `.env` (не коммитить).
- Мусор/сборки/кэш в `.gitignore`.
- Перед пушем: прогонить тесты, проверить линты.

## Стек
- Backend: FastAPI, SQLAlchemy, PostgreSQL
- Frontend: React + Vite, TypeScript, framer-motion
- Тесты: pytest

## Лицензия
MIT