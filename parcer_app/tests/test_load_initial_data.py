from django.test import TestCase
from django.core.management import call_command
from parcer_app.models import Hub, HubSelectors
import json
from unittest.mock import mock_open, patch

class LoadInitialDataTest(TestCase):
    
    # Test 1: Успешная загрузка initial data
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps([
        {
            "model": "parcer_app.hub",
            "pk": 1,
            "fields": {
                "name": "Test Hub",
                "url": "http://example.com",
                "last_fetched": None
            }
        },
        {
            "model": "parcer_app.hubselectors",
            "pk": 1,
            "fields": {
                "hub": 1,
                "article_selector": ".article",
                "title_selector": ".title",
                "author_selector": ".author",
                "author_url_selector": ".author_url",
                "publication_date_selector": ".pub_date",
                "content_selector": ".content",
            }
        }
    ]))
    def test_load_initial_data(self, mock_file):
        call_command('load_initial_data')

        hub = Hub.objects.get(pk=1)
        self.assertEqual(hub.name, "Test Hub")
        self.assertEqual(hub.url, "http://example.com")
        
        selector = HubSelectors.objects.get(pk=1)
        self.assertEqual(selector.article_selector, ".article")
        self.assertEqual(selector.title_selector, ".title")
        self.assertEqual(selector.author_selector, ".author")
        self.assertEqual(selector.author_url_selector, ".author_url")
        self.assertEqual(selector.publication_date_selector, ".pub_date")
        self.assertEqual(selector.content_selector, ".content")


    # Test 2: Создание Hub с некорректным ID
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps([
        {
            "model": "parcer_app.hubselectors",
            "pk": 1,
            "fields": {
                "hub": 999,
                "article_selector": ".article",
                "title_selector": ".title",
                "author_selector": ".author",
                "author_url_selector": ".author_url",
                "publication_date_selector": ".pub-date",
                "content_selector": ".content"
            }
        }
    ]))
    def test_missing_foreign_key(self, mock_file):
        with self.assertRaisesMessage(ValueError, "Hub с ID 999 не был загружен ранее"):
            call_command('load_initial_data')


    # Test 3: Обновление данных
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps([
        {
            "model": "parcer_app.hub",
            "pk": 1,
            "fields": {
                "name": "Updated Hub",
                "url": "http://example.com",
                "last_fetched": None
            }
        }
    ]))
    def test_update_existing_data(self, mock_file):
        Hub.objects.create(pk=1, name="Test Hub", url="http://example.com")
        
        call_command('load_initial_data')
        
        hub = Hub.objects.get(pk=1)
        self.assertEqual(hub.name, "Updated Hub")


    # Test 4: Отсутсвует обязательное поле
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps([
        {
            "model": "parcer_app.hub",
            "pk": 1,
            "fields": {
                # 'name': "Test Hub",
                "url": "http://example.com",
                "last_fetched": None
            }
        }
    ]))
    def test_missing_required_fields(self, mock_file):
        with self.assertRaisesMessage(ValueError, "Для модели 'Hub' отсутствует одно из обязательных полей"):
            call_command('load_initial_data')


    # Test 5: Отсутсвует файл initial_data.json
    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_missing_initial_data_file(self, mock_file):
        with self.assertRaisesMessage(FileNotFoundError, "Ошибка: файл 'initial_data.json' не найден"):
            call_command('load_initial_data')


    # Test 6: Неверный формат JSON
    @patch("builtins.open", new_callable=mock_open, read_data="INVALID JSON")
    def test_invalid_json_format(self, mock_file):
        with self.assertRaisesMessage(ValueError, "Ошибка: неправильный формат JSON в 'initial_data.json'"):
            call_command('load_initial_data')
