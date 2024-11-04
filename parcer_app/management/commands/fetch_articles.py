import asyncio
import aiohttp
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from bs4 import BeautifulSoup
from parcer_app.models import Hub, HubSelectors, Post


from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
import asyncio

class ArticleFetcher:
    def __init__(self, hub, command):
        self.hub = hub
        self.selectors = None
        self.semaphore = asyncio.Semaphore(5)
        self.fetched_articles = []
        self.command = command

    async def initialize(self):
        try:
            self.selectors = await sync_to_async(HubSelectors.objects.get)(hub=self.hub)
        except HubSelectors.DoesNotExist:
            self.command.stdout.write(self.command.style.ERROR(f"Селекторы для хаба {self.hub.name} не найдены"))
            self.selectors = None

    async def fetch_hub_page(self, session):
        await self.initialize()
        if not self.selectors:
            self.command.stdout.write(self.command.style.ERROR("Ошибка: селекторы не были загружены"))
            return

        try:
            async with session.get(self.hub.url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    await self.parse_hub_page(html_content, session)
                else:
                    self.command.stdout.write(self.command.style.ERROR(f"Не удалось получить страницу {self.hub.url}: Статус {response.status}"))
        except Exception as e:
            self.command.stdout.write(self.command.style.ERROR(f"Ошибка при запросе {self.hub.url}: {e}"))

    async def parse_hub_page(self, html_content, session):
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            article_links = soup.select(self.selectors.article_selector)
            
            if not article_links:
                self.command.stdout.write(self.command.style.ERROR(f"Селектор {self.selectors.article_selector} не нашел статьи на странице {self.hub.url}"))
                return
            
            tasks = [
                self.fetch_article_data(link.get('href'), session)
                for link in article_links if link.get('href')
            ]
            await asyncio.gather(*tasks)

            await self.store_articles_bulk()
        except Exception as e:
            self.command.stdout.write(self.command.style.ERROR(f"Ошибка при парсинге страницы хаба {self.hub.url}: {e}"))

    async def fetch_article_data(self, url, session):
        async with self.semaphore:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        await self.parse_article_page(url, html_content)
                    else:
                        self.command.stdout.write(self.command.style.ERROR(f"Не удалось получить статью {url}: Код статуса {response.status}"))
            except Exception as e:
                self.command.stdout.write(self.command.style.ERROR(f"Ошибка при получении статьи {url}: {e}"))

    async def parse_article_page(self, url, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')

        # Извлечение данных с использованием селекторов
        title_element = soup.select_one(self.selectors.title_selector)
        author_element = soup.select_one(self.selectors.author_selector)
        author_url_element = soup.select_one(self.selectors.author_url_selector)
        publication_date_element = soup.select_one(self.selectors.publication_date_selector)
        content_elements = soup.select_one(self.selectors.content_selector)

        # Извлечение текста и атрибутов
        title = title_element.get_text(strip=True) if title_element else "Без названия"
        author = author_element.get_text(strip=True) if author_element else "Аноним"
        author_url = author_url_element.get('href') if author_url_element else "#"
        publication_date = (
            publication_date_element.get('datetime') if publication_date_element and publication_date_element.get('datetime') else
            publication_date_element.get('title') if publication_date_element else None
        )

        tags = ['p', 'pre', 'code', 'blockquote', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        if content_elements:
            nested_content = "\n".join(
                element.get_text(strip=True) for element in content_elements.find_all(tags)
            )

            if nested_content.strip():
                content = nested_content
            else:
                content = content_elements.get_text(strip=True)
        else:
            content = "Без содержания"

        self.fetched_articles.append({
            'title': title,
            'author': author,
            'author_url': author_url,
            'publication_date': publication_date,
            'post_url': url,
            'content': content,
        })

    @sync_to_async
    @transaction.atomic
    def store_articles_bulk(self):
        existing_urls = set(Post.objects.filter(hub=self.hub).values_list('post_url', flat=True))

        unique_articles = [
            article for article in self.fetched_articles if article['post_url'] not in existing_urls
        ]

        posts_to_create = [
            Post(
                hub=self.hub,
                title=article['title'],
                author_name=article['author'],
                author_url=article['author_url'],
                post_url=article['post_url'],
                publication_date=self._parse_publication_date(article['publication_date']),
                content=article['content']
            )
            for article in unique_articles
        ]

        if posts_to_create:
            Post.objects.bulk_create(posts_to_create)
            self.command.stdout.write(self.command.style.SUCCESS(f"Добавлено {len(posts_to_create)} новых статей"))

    def _parse_publication_date(self, publication_date):
        if publication_date:
            try:
                publication_date_dt = timezone.datetime.fromisoformat(publication_date)
                return timezone.make_aware(publication_date_dt)
            except ValueError:
                return timezone.now()
        return timezone.now()

    async def output_results(self):
        self.command.stdout.write(self.command.style.SUCCESS(f"\nСтатьи хаба: {self.hub.name}"))
        for article in self.fetched_articles:
            self.command.stdout.write(f"- {article['title']} (Автор: {article['author']}, Дата: {article['publication_date']}) [Ссылка: {article['post_url']}]")


class Command(BaseCommand):
    help = 'Запрашивает данные со всех хабов и сохраняет их в базу данных'

    async def fetch_all_hubs(self):
        hubs = await sync_to_async(list)(Hub.objects.all())
        fetchers = []

        for hub in hubs:
            fetcher = ArticleFetcher(hub, self)
            await fetcher.initialize()
            if fetcher.selectors:
                fetchers.append(fetcher)

        if not fetchers:
            self.stdout.write(self.style.ERROR("Нет доступных хабов для обработки"))
            return

        async with aiohttp.ClientSession() as session:
            tasks = [fetcher.fetch_hub_page(session) for fetcher in fetchers]
            await asyncio.gather(*tasks)

            for fetcher in fetchers:
                await fetcher.output_results()

    def handle(self, *args, **kwargs):
        asyncio.run(self.fetch_all_hubs())
        self.stdout.write(self.style.SUCCESS('Успешно!\n'))
