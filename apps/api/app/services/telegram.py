"""
Простой сервис для отправки сообщений в Telegram.

Основан на подходе из Taobao_Scraper:
- Преобразует chat_id в int если это число (как в Taobao_Scraper)
- Использует прямой HTTP запрос к Telegram Bot API через httpx
- Простая логика без сложных проверок
"""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_telegram_message(*, chat_id: str, text: str) -> None:
    """
    Отправляет сообщение в Telegram через Bot API.
    
    Основано на подходе из Taobao_Scraper:
    - Преобразует chat_id в int если это число (как в Taobao_Scraper: self.admin_chat_id = int(admin_chat_id))
    - Использует прямой HTTP запрос к Telegram Bot API
    - Логирует ошибки, но не падает (ошибка Telegram не должна ломать игру)
    
    Args:
        chat_id: ID чата получателя (может быть числом или строкой)
        text: Текст сообщения для отправки
    
    Примеры:
        send_telegram_message(chat_id="123456789", text="Привет!")
        send_telegram_message(chat_id="-1001234567890", text="Сообщение в канал")
    """
    # Проверяем, что токен настроен
    if not settings.telegram_bot_token or settings.telegram_bot_token == "CHANGE_ME":
        logger.warning("Telegram bot token не настроен, пропускаем отправку сообщения")
        return
    
    # Проверяем, что chat_id указан
    if not chat_id or not chat_id.strip():
        logger.warning("Chat ID не указан, пропускаем отправку сообщения")
        return
    
    token = settings.telegram_bot_token
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Преобразуем chat_id в int если это число (как в Taobao_Scraper)
    # В Taobao_Scraper: self.admin_chat_id = int(admin_chat_id) if isinstance(admin_chat_id, str) else admin_chat_id
    try:
        # Числовой chat_id → int (быстрее и ближе к Taobao_Scraper)
        chat_id_to_send = int(chat_id) if not chat_id.startswith("@") else chat_id
    except (ValueError, TypeError):
        chat_id_to_send = chat_id
    
    # Подготовка данных для отправки
    payload = {
        "chat_id": chat_id_to_send,
        "text": text,
    }
    
    try:
        logger.info(
            "Отправка сообщения в Telegram",
            extra={
                "chat_id": chat_id,
                "chat_id_to_send": chat_id_to_send,
                "text_length": len(text),
            }
        )
        
        # Отправляем запрос с коротким таймаутом (как в Taobao_Scraper)
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(url, json=payload)
            
            # Проверяем ответ
            if resp.status_code == 200:
                resp_data = resp.json()
                if resp_data.get("ok"):
                    logger.info(
                        "Сообщение успешно отправлено в Telegram",
                        extra={"chat_id": chat_id}
                    )
                    return
                else:
                    # Ошибка от Telegram API
                    error_description = resp_data.get("description", "Неизвестная ошибка")
                    error_code = resp_data.get("error_code", "unknown")
                    
                if "chat not found" in error_description.lower() and isinstance(chat_id_to_send, int) and chat_id_to_send > 0:
                    variants_to_try = [
                        -chat_id_to_send,
                        int(f"-100{chat_id_to_send}"),
                    ]
                    for variant in variants_to_try:
                        try:
                            variant_resp = client.post(url, json={"chat_id": variant, "text": text})
                            if variant_resp.status_code == 200 and variant_resp.json().get("ok"):
                                logger.info("Отправлено в группу", extra={"original_chat_id": chat_id, "group_id": variant})
                                return
                        except Exception:
                            continue
                    username = settings.telegram_chat_username or ""
                    if username:
                        username_to_send = username if username.startswith("@") else f"@{username}"
                        try:
                            resp_username = client.post(url, json={"chat_id": username_to_send, "text": text})
                            if resp_username.status_code == 200 and resp_username.json().get("ok"):
                                logger.info("Отправлено по username", extra={"username": username_to_send})
                                return
                        except Exception:
                            pass
                    # Если есть username группы/канала в настройках - пробуем его
                    username = settings.telegram_chat_username or ""
                    if username:
                        username_to_send = username if username.startswith("@") else f"@{username}"
                        try:
                            logger.info(f"Пробуем отправить по username из настроек: {username_to_send}")
                            resp_username = client.post(url, json={"chat_id": username_to_send, "text": text})
                            if resp_username.status_code == 200 and resp_username.json().get("ok"):
                                logger.info(
                                    f"✅ Сообщение успешно отправлено по username {username_to_send}",
                                    extra={"original_chat_id": chat_id, "username": username_to_send}
                                )
                                return
                            else:
                                try:
                                    err_u = resp_username.json()
                                    desc_u = err_u.get("description", resp_username.text or "Неизвестная ошибка")
                                except Exception:
                                    desc_u = resp_username.text or "Неизвестная ошибка"
                                logger.warning(
                                    f"Отправка по username {username_to_send} не сработала: {desc_u}",
                                    extra={"username": username_to_send, "status_code": resp_username.status_code, "error": desc_u}
                                )
                        except Exception as e:
                            logger.warning(f"Ошибка при попытке отправки по username {username_to_send}: {e}", exc_info=True)
                    
                    logger.error(
                        f"Telegram API вернул ошибку. Chat ID: {chat_id}. "
                        f"Код: {error_code}. Ошибка: {error_description}",
                        extra={
                            "chat_id": chat_id,
                            "error_code": error_code,
                            "error": error_description
                        }
                    )
            else:
                # HTTP ошибка (400, 403 и т.д.)
                try:
                    error_data = resp.json()
                    error_description = error_data.get("description", resp.text or "Неизвестная ошибка")
                    error_code = error_data.get("error_code", resp.status_code)
                except Exception:
                    error_description = resp.text or "Неизвестная ошибка"
                    error_code = resp.status_code
                
                # Если ошибка "chat not found" и chat_id положительное число,
                # пробуем отрицательный вариант (для групп)
                if "chat not found" in error_description.lower() and isinstance(chat_id_to_send, int) and chat_id_to_send > 0:
                    logger.info(
                        f"Chat not found для положительного ID {chat_id_to_send}. "
                        f"Пробуем отрицательный вариант для группы..."
                    )
                    
                    # Пробуем варианты с минусом для группы
                    variants_to_try = [
                        -chat_id_to_send,  # Просто с минусом: -{id}
                        int(f"-100{chat_id_to_send}"),  # Стандартный формат супергрупп: -100{id}
                    ]
                    
                    for variant in variants_to_try:
                        try:
                            logger.info(f"Пробуем вариант: {variant}")
                            variant_payload = {"chat_id": variant, "text": text}
                            variant_resp = client.post(url, json=variant_payload)
                            
                            if variant_resp.status_code == 200:
                                variant_data = variant_resp.json()
                                if variant_data.get("ok"):
                                    logger.info(
                                        f"✅ Сообщение успешно отправлено в группу {variant}",
                                        extra={"original_chat_id": chat_id, "group_id": variant}
                                    )
                                    return
                                else:
                                    variant_error = variant_data.get("description", "Неизвестная ошибка")
                                    logger.debug(f"Вариант {variant} не сработал: {variant_error}")
                            else:
                                logger.debug(f"Вариант {variant} вернул статус {variant_resp.status_code}")
                        except Exception as e:
                            logger.debug(f"Ошибка при попытке отправки в {variant}: {e}")
                            continue
                    
                    logger.warning(
                        f"Не удалось отправить сообщение ни с одним вариантом ID группы. "
                        f"Пробовали: {variants_to_try}"
                    )
                
                logger.error(
                    f"Ошибка HTTP при отправке в Telegram. Chat ID: {chat_id}. "
                    f"Статус: {resp.status_code}. Ошибка: {error_description}",
                    extra={
                        "chat_id": chat_id,
                        "status_code": resp.status_code,
                        "error": error_description
                    }
                )
    
    except httpx.TimeoutException:
        logger.error(
            f"Таймаут при отправке сообщения в Telegram. Chat ID: {chat_id}.",
            exc_info=True
        )
    except httpx.HTTPError as e:
        logger.error(
            f"Ошибка HTTP при отправке в Telegram. Chat ID: {chat_id}. Ошибка: {e}",
            exc_info=True
        )
    except Exception as e:
        logger.error(
            f"Неожиданная ошибка при отправке в Telegram. Chat ID: {chat_id}. Ошибка: {e}",
            exc_info=True
        )

