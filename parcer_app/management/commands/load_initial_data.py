import json
from django.core.management.base import BaseCommand
from django.db import transaction
from parcer_app.models import Hub, HubSelectors


class Command(BaseCommand):
    help = 'Загружает начальные данные в базу данных из initial_data.json'

    def handle(self, *args, **kwargs):
        try:
            with open('initial_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("Ошибка: файл 'initial_data.json' не найден")
        except json.JSONDecodeError:
            raise ValueError("Ошибка: неправильный формат JSON в 'initial_data.json'")

        with transaction.atomic():
            created_objects = {}

            for entry in data:
                model = entry['model']
                fields = entry['fields']
                pk = entry['pk']

                if model == 'parcer_app.hub':
                    if not all(key in fields for key in ('name', 'url')):
                        raise ValueError("Для модели 'Hub' отсутствует одно из обязательных полей: 'name', 'url'")
                    
                    hub, created = Hub.objects.update_or_create(
                        id=pk,
                        defaults={
                            'name': fields['name'],
                            'url': fields['url'],
                            'last_fetched': fields['last_fetched']
                        }
                    )

                    '''
                    if created:
                        print(f'Создан новый Hub с ID {pk}')
                    else:
                        print(f'Обновлён существующий Hub с ID {pk}')
                    '''
                    created_objects[pk] = hub
                    

                elif model == 'parcer_app.hubselectors':
                    hub_id = fields['hub']
                    hub = created_objects.get(hub_id)

                    if not hub:
                        raise ValueError(f"Hub с ID {hub_id} не был загружен ранее")
                    
                    hub_selector, created = HubSelectors.objects.update_or_create(
                        id=pk,
                        defaults={
                            'hub': hub,
                            'article_selector': fields['article_selector'],
                            'title_selector': fields['title_selector'],
                            'author_selector': fields['author_selector'],
                            'author_url_selector': fields['author_url_selector'],
                            'publication_date_selector': fields['publication_date_selector'],
                            'content_selector': fields['content_selector']
                        }
                    )

                    '''
                    if created:
                        print(f'Создан новый HubSelector с ID {pk}')
                    else:
                        print(f'Обновлён существующий HubSelector с ID {pk}')
                    '''

        print('Начальные данные успешно загружены.')
