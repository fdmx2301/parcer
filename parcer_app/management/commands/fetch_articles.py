import asyncio
import aiohttp
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from django.utils import timezone
from bs4 import BeautifulSoup
from parcer_app.models import Hub, HubSelectors, Post


from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
import asyncio

class ArticleFetcher:
    def __init__(self, hub):
        self.hub = hub
        self.selectors = None
        self.semaphore = asyncio.Semaphore(5)
        self.fetched_articles = []

    async def initialize(self):
        self.selectors = await sync_to_async(HubSelectors.objects.get)(hub=self.hub)

    async def fetch_hub_page(self, session):
        await self.initialize()
        if not self.selectors:
            print("Ошибка: селекторы не были загружены")
            return

        try:
            async with session.get(self.hub.url) as response:
                # print(f"Запрос к {self.hub.url}, статус: {response.status}")
                if response.status == 200:
                    html_content = await response.text()
                    # print(f"Получено содержимое хаба: {html_content[:100]}...")
                    await self.parse_hub_page(html_content, session)
                else:
                    print(f"Не удалось получить страницу {self.hub.url}: Статус {response.status}")
        except Exception as e:
            print(f"Ошибка при запросе {self.hub.url}: {e}")

    async def parse_hub_page(self, html_content, session):
        soup = BeautifulSoup(html_content, 'html.parser')
        article_links = soup.select(self.selectors.article_selector)
        # print(f"Найденные ссылки на статьи: {[link.get('href') for link in article_links]}")

        tasks = [self.fetch_article_data(link.get('href'), session) for link in article_links if link.get('href')]
        await asyncio.gather(*tasks)

    async def fetch_article_data(self, url, session):
        async with self.semaphore:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        await self.parse_article_page(url, html_content)
                    else:
                        print(f"Не удалось получить статью {url}: Код статуса {response.status}")
            except Exception as e:
                print(f"Ошибка при получении статьи {url}: {e}")

    async def parse_article_page(self, url, html_content):
        # print(f"Парсинг страницы статьи {url}")
        await self._store_article_data(url, html_content)

    @sync_to_async
    def _store_article_data(self, url, html_content):
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
        content = "\n".join(element.get_text(strip=True) for element in content_elements.find_all(['p', 'pre', 'code', 'blockquote'])) if content_elements else "Без содержания"

        self.fetched_articles.append({
            'title': title,
            'author': author,
            'author_url': author_url,
            'publication_date': publication_date,
            'post_url': url,
            'content': content,
        })

        if publication_date:
            try:
                publication_date_dt = timezone.datetime.fromisoformat(publication_date)
                publication_date_dt = timezone.make_aware(publication_date_dt)
            except ValueError:
                publication_date_dt = timezone.now()

        Post.objects.update_or_create(
            post_url=url,
            defaults={
                'hub': self.hub,
                'title': title,
                'author_name': author,
                'author_url': author_url,
                'publication_date': publication_date_dt,
                'content': content
            }
        )

    async def output_results(self):
        print(f"\nСтатьи хаба: {self.hub.name}")
        for article in self.fetched_articles:
            print(f"- {article['title']} (Автор: {article['author']}, Дата: {article['publication_date']}) [Ссылка: {article['post_url']}]")


class Command(BaseCommand):
    help = 'Запрашивает данные со всех хабов и сохраняет их в базу данных'

    async def fetch_all_hubs(self):
        hubs = Hub.objects.all()
        fetchers = [ArticleFetcher(hub) for hub in hubs]
        await asyncio.gather(*(fetcher.initialize() for fetcher in fetchers))
        async with aiohttp.ClientSession() as session:
            tasks = [fetcher.fetch_hub_page(session) for fetcher in fetchers]
            await asyncio.gather(*tasks)

            for fetcher in fetchers:
                await fetcher.output_results()

    def handle(self, *args, **kwargs):
        asyncio.run(self.fetch_all_hubs())
        self.stdout.write(self.style.SUCCESS('Успешно!\n'))
