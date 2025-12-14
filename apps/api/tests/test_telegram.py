"""
Тесты для отправки сообщений в Telegram.

Проверяем простую отправку сообщений через Telegram Bot API.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from app.services.telegram import send_telegram_message
from app.core.config import settings


@pytest.fixture
def mock_settings(monkeypatch):
    """Мокируем настройки для тестов."""
    monkeypatch.setattr(settings, "telegram_bot_token", "test_token_123:ABC")
    monkeypatch.setattr(settings, "telegram_chat_id", "123456789")
    monkeypatch.setattr(settings, "telegram_chat_username", None)


def test_send_telegram_message_success(mock_settings):
    """Тест успешной отправки сообщения."""
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        # Мокируем успешный ответ
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 123}}
        mock_client.post.return_value = mock_response
        
        # Вызываем функцию
        send_telegram_message(chat_id="123456789", text="Test message")
        
        # Проверяем, что был вызван правильный URL
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "https://api.telegram.org/bottest_token_123:ABC/sendMessage"
        
        # Проверяем, что chat_id преобразован в int (как в Taobao_Scraper)
        payload = call_args[1]["json"]
        assert payload["chat_id"] == 123456789  # int, не строка
        assert payload["text"] == "Test message"


def test_send_telegram_message_with_string_chat_id(mock_settings):
    """Тест отправки с chat_id как строкой (должен преобразоваться в int)."""
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_client.post.return_value = mock_response
        
        send_telegram_message(chat_id="123456789", text="Test")
        
        payload = mock_client.post.call_args[1]["json"]
        assert payload["chat_id"] == 123456789  # int


def test_send_telegram_message_with_negative_chat_id(mock_settings):
    """Тест отправки с отрицательным chat_id (канал/группа)."""
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_client.post.return_value = mock_response
        
        send_telegram_message(chat_id="-1001234567890", text="Test")
        
        payload = mock_client.post.call_args[1]["json"]
        assert payload["chat_id"] == -1001234567890  # int


def test_send_telegram_message_with_username(mock_settings):
    """Тест отправки с username (начинается с @)."""
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_client.post.return_value = mock_response
        
        send_telegram_message(chat_id="@my_channel", text="Test")
        
        payload = mock_client.post.call_args[1]["json"]
        assert payload["chat_id"] == "@my_channel"  # строка, не преобразуется


def test_send_telegram_message_api_error(mock_settings):
    """Тест обработки ошибки от Telegram API."""
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        # Мокируем ответ с ошибкой
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ok": False,
            "error_code": 403,
            "description": "Forbidden: bots can't send messages to bots"
        }
        mock_client.post.return_value = mock_response
        
        # Вызываем функцию (не должна упасть)
        send_telegram_message(chat_id="123456789", text="Test")
        
        # Проверяем, что был вызов
        mock_client.post.assert_called_once()


def test_send_telegram_message_http_error(mock_settings):
    """Тест обработки HTTP ошибки (не "chat not found")."""
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        # Мокируем HTTP ошибку (не "chat not found", чтобы не пробовались варианты)
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request: other error"
        mock_response.json.return_value = {
            "ok": False,
            "description": "Bad Request: other error"
        }
        mock_client.post.return_value = mock_response
        
        # Вызываем функцию (не должна упасть)
        send_telegram_message(chat_id="123456789", text="Test")
        
        # Должен быть только один вызов (варианты не пробуются для других ошибок)
        mock_client.post.assert_called_once()


def test_send_telegram_message_timeout(mock_settings):
    """Тест обработки таймаута."""
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        # Мокируем таймаут
        mock_client.post.side_effect = httpx.TimeoutException("Timeout")
        
        # Вызываем функцию (не должна упасть)
        send_telegram_message(chat_id="123456789", text="Test")
        
        mock_client.post.assert_called_once()


def test_send_telegram_message_no_token(mock_settings, monkeypatch):
    """Тест когда токен не настроен."""
    monkeypatch.setattr(settings, "telegram_bot_token", "CHANGE_ME")
    
    with patch("httpx.Client") as mock_client_class:
        # Функция должна вернуться раньше, без вызова API
        send_telegram_message(chat_id="123456789", text="Test")
        
        # Проверяем, что API не вызывался
        mock_client_class.assert_not_called()


def test_send_telegram_message_no_chat_id(mock_settings):
    """Тест когда chat_id не указан."""
    with patch("httpx.Client") as mock_client_class:
        # Функция должна вернуться раньше, без вызова API
        send_telegram_message(chat_id="", text="Test")
        
        # Проверяем, что API не вызывался
        mock_client_class.assert_not_called()


def test_send_telegram_message_group_id_auto_fix(mock_settings):
    """Тест автоматического исправления положительного ID группы на отрицательный."""
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        # Первый вызов: ошибка "chat not found" для положительного ID
        mock_response_1 = Mock()
        mock_response_1.status_code = 200
        mock_response_1.json.return_value = {
            "ok": False,
            "error_code": 400,
            "description": "Bad Request: chat not found"
        }
        
        # Второй вызов: успех с отрицательным ID
        mock_response_2 = Mock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = {"ok": True, "result": {"message_id": 123}}
        
        # Настраиваем последовательность вызовов
        mock_client.post.side_effect = [mock_response_1, mock_response_2]
        
        # Вызываем функцию с положительным ID группы
        send_telegram_message(chat_id="3574583952", text="Test message")
        
        # Проверяем, что было 2 вызова
        assert mock_client.post.call_count == 2
        
        # Первый вызов с положительным ID
        first_call = mock_client.post.call_args_list[0]
        assert first_call[1]["json"]["chat_id"] == 3574583952
        
        # Второй вызов с отрицательным ID
        second_call = mock_client.post.call_args_list[1]
        assert second_call[1]["json"]["chat_id"] == -3574583952


def test_send_telegram_message_group_id_auto_fix_http_400(mock_settings):
    """Тест автоматического исправления при HTTP 400 ошибке."""
    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        # Первый вызов: HTTP 400 с "chat not found"
        mock_response_1 = Mock()
        mock_response_1.status_code = 400
        mock_response_1.json.return_value = {
            "ok": False,
            "error_code": 400,
            "description": "Bad Request: chat not found"
        }
        mock_response_1.text = "Bad Request: chat not found"
        
        # Второй вызов: успех с отрицательным ID
        mock_response_2 = Mock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = {"ok": True}
        
        mock_client.post.side_effect = [mock_response_1, mock_response_2]
        
        send_telegram_message(chat_id="3574583952", text="Test")
        
        # Проверяем, что было 2 вызова
        assert mock_client.post.call_count == 2
        
        # Второй вызов с отрицательным ID
        second_call = mock_client.post.call_args_list[1]
        assert second_call[1]["json"]["chat_id"] == -3574583952


def test_send_telegram_message_username_fallback(mock_settings, monkeypatch):
    """Тест fallback на username из настроек после неудачных вариантов с числами."""
    # Указываем username в настройках
    monkeypatch.setattr(settings, "telegram_chat_username", "Game_Group_BTH")

    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_client
        
        # Последовательность: основной (chat not found), два варианта с минусом (chat not found), затем успех по username
        resp_main = Mock()
        resp_main.status_code = 200
        resp_main.json.return_value = {"ok": False, "description": "Bad Request: chat not found", "error_code": 400}
        
        resp_var1 = Mock()
        resp_var1.status_code = 200
        resp_var1.json.return_value = {"ok": False, "description": "Bad Request: chat not found", "error_code": 400}
        
        resp_var2 = Mock()
        resp_var2.status_code = 200
        resp_var2.json.return_value = {"ok": False, "description": "Bad Request: chat not found", "error_code": 400}
        
        resp_username = Mock()
        resp_username.status_code = 200
        resp_username.json.return_value = {"ok": True, "result": {"message_id": 321}}

        mock_client.post.side_effect = [resp_main, resp_var1, resp_var2, resp_username]

        send_telegram_message(chat_id="3574583952", text="Test")

        # Ожидаем 4 вызова: основной, два варианта, username
        assert mock_client.post.call_count == 4
        username_call = mock_client.post.call_args_list[3]
        assert username_call[1]["json"]["chat_id"] == "@Game_Group_BTH"
