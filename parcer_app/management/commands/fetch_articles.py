import asyncio
import aiohttp
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parcer_app.models import Hub, HubSelectors, Post

class ArticleFetcher:
    def __init__(self, hub, command):
        self.hub = hub
        self.selectors = None
        self.semaphore = asyncio.Semaphore(5)
        self.fetched_articles = []
        self.command = command

    async def initialize(self):
        print(f"Инициализация селекторов для хаба {self.hub.name}...")
        try:
            self.selectors = await sync_to_async(HubSelectors.objects.get)(hub=self.hub)
            print(f"Селекторы для хаба {self.hub.name} успешно загружены.")
        except HubSelectors.DoesNotExist:
            print(f"Селекторы для хаба {self.hub.name} не найдены")
            self.selectors = None

    async def fetch_hub_page(self, session):
        print(f"Запрашиваем страницу хаба: {self.hub.url}...")
        await self.initialize()
        if not self.selectors:
            print("Ошибка: селекторы не были загружены")
            return

        try:
            async with session.get(self.hub.url) as response:
                if response.status == 200:
                    print(f"Страница хаба {self.hub.url} успешно загружена.")
                    html_content = await response.text()
                    await self.parse_hub_page(html_content, session)
                else:
                    print(f"Не удалось получить страницу {self.hub.url}: Статус {response.status}")
        except Exception as e:
            print(f"Ошибка при запросе {self.hub.url}: {e}")

    async def parse_hub_page(self, html_content, session):
        print(f"Парсинг страницы хаба {self.hub.url}...")
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            article_links = soup.select(self.selectors.article_selector)

            if not article_links:
                print(f"Селектор {self.selectors.article_selector} не нашел статьи на странице {self.hub.url}")
                return

            tasks = [
                self.fetch_article_data(urljoin(self.hub.url, link.get('href')), session)
                for link in article_links if link.get('href')
            ]
            await asyncio.gather(*tasks)

            await self.store_articles_bulk()
        except Exception as e:
            print(f"Ошибка при парсинге страницы хаба {self.hub.url}: {e}")

    async def fetch_article_data(self, url, session):
        print(f"Запрашиваем статью: {url}...")
        async with self.semaphore:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        print(f"Статья {url} успешно загружена.")
                        html_content = await response.text()
                        await self.parse_article_page(url, html_content)
                    else:
                        print(f"Не удалось получить статью {url}: Код статуса {response.status}")
            except Exception as e:
                print(f"Ошибка при получении статьи {url}: {e}")

    async def parse_article_page(self, url, html_content):
        print(f"Парсим страницу: {url}")

        if not html_content:
            print(f"HTML контент пуст для страницы: {url}")
            return

        soup = BeautifulSoup(html_content, 'html.parser')

        # Извлечение данных с использованием селекторов
        try:
            title_element = soup.select_one(self.selectors.title_selector)
            title = title_element.get_text(strip=True).replace("\n", " ").strip() if title_element else None
            if title is None:
                raise ValueError("Заголовок не найден.")
        except Exception as e:
            print(f"Ошибка при извлечении заголовка на странице {url}: {e}")
            title = "Без названия"

        try:
            author_element = soup.select_one(self.selectors.author_selector)
            author = author_element.get_text(strip=True).replace("\n", " ").strip() if author_element else None
            if author is None:
                raise ValueError("Автор не найден.")
        except Exception as e:
            print(f"Ошибка при извлечении автора на странице {url}: {e}")
            author = "Аноним"

        try:
            author_url_element = soup.select_one(self.selectors.author_url_selector)
            author_url = author_url_element.get('href', '#') if author_url_element else "#"

            if author_url == "#":
                raise ValueError("URL автора не найден")
        except Exception as e:
            print(f"Ошибка при извлечении URL автора на странице {url}: {e}")
            author_url = "#"

        try:
            publication_date_element = soup.select_one(self.selectors.publication_date_selector)
            publication_date = (
                publication_date_element.get('datetime') if publication_date_element and publication_date_element.get('datetime') else
                publication_date_element.get('title') if publication_date_element else None
            )
            if publication_date is None:
                raise ValueError("Дата публикации не найдена.")
        except Exception as e:
            print(f"Ошибка при извлечении даты публикации на странице {url}: {e}")
            publication_date = None

        try:
            content_elements = soup.select_one(self.selectors.content_selector)
            if content_elements:
                tags = ['p', 'pre', 'code', 'blockquote', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
                nested_content = "\n".join(
                    element.get_text(strip=True) for element in content_elements.find_all(tags)
                )

                content = nested_content.strip() if nested_content.strip() else content_elements.get_text(strip=True)
            else:
                raise ValueError("Содержимое не найдено.")
        except Exception as e:
            print(f"Ошибка при извлечении содержимого на странице {url}: {e}")
            content = "Без содержания"

        # Добавление в список извлеченных статей
        self.fetched_articles.append({
            'title': title,
            'author': author,
            'author_url': author_url,
            'publication_date': publication_date,
            'post_url': url,
            'content': content,
        })

        print(f"Статья успешно обработана: {title}")



    @sync_to_async
    @transaction.atomic
    def store_articles_bulk(self):
        print(f"Сохранение {len(self.fetched_articles)} статей в базу данных...")
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
            print(f"Добавлено {len(posts_to_create)} новых статей")
        else:
            print("Нет новых статей для добавления.")

    def _parse_publication_date(self, publication_date):
        if publication_date:
            try:
                publication_date_dt = timezone.datetime.fromisoformat(publication_date)
                return timezone.make_aware(publication_date_dt)
            except ValueError:
                return timezone.now()
        return timezone.now()

    async def output_results(self):
        print(f"\nСтатьи хаба: {self.hub.name}")
        for article in self.fetched_articles:
            print(f"- {article['title']} (Автор: {article['author']}, Дата: {article['publication_date']}) [Ссылка: {article['post_url']}]")

class Command(BaseCommand):
    help = 'Запрашивает данные со всех хабов и сохраняет их в базу данных'

    async def fetch_all_hubs(self):
        print("Запуск парсера для всех хабов...")
        hubs = await sync_to_async(list)(Hub.objects.all())
        fetchers = []

        for hub in hubs:
            fetcher = ArticleFetcher(hub, self)
            await fetcher.initialize()
            if fetcher.selectors:
                fetchers.append(fetcher)

        if not fetchers:
            print("Нет доступных хабов для обработки")
            return

        async with aiohttp.ClientSession() as session:
            tasks = [fetcher.fetch_hub_page(session) for fetcher in fetchers]
            await asyncio.gather(*tasks)

            for fetcher in fetchers:
                await fetcher.output_results()

    def handle(self, *args, **kwargs):
        asyncio.run(self.fetch_all_hubs())
        print('Успешно!\n')