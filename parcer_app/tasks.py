from celery import shared_task
import asyncio
from .management.commands.fetch_articles import Command
from .models import Hub
from celery import current_app

@shared_task
def fetch_articles(hub_id):
    fetch_command = Command()
    asyncio.run(fetch_command.fetch_all_hubs(hub_id))

def schedule_fetching():
    hubs = Hub.objects.all()
    for hub in hubs:
        current_app.send_task('parcer_app.tasks.fetch_articles', args=[hub.id], countdown=hub.fetch_interval * 60)
