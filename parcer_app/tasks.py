from celery import shared_task
from .management.commands.fetch_articles import Command
from celery import current_app
import asyncio

@shared_task
def fetch_articles():
    print("Запуск парсера для всех хабов...")
    fetch_command = Command()
    asyncio.run(fetch_command.fetch_all_hubs())
    print("Успешно!")

@shared_task
def schedule_fetching():
    current_app.send_task('parcer_app.tasks.fetch_articles', countdown=0)
