import asyncio
import aiohttp
from django.core.management.base import BaseCommand
from django.utils import timezone
from bs4 import BeautifulSoup
from parcer_app.models import Hub, HubSelectors, Post

class ArticleFetcher:
    def __init__(self, hub):
        self.hub = hub
        self.selectors = HubSelectors.objects.get(hub=self.hub)

    async def fetch_hub_page(self, session):
        try:
            async with session.get(self.hub.url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    await self.parse_hub_page(html_content, session)
                else:
                    print(f"Failed to fetch {self.hub.url}: Status code {response.status}")
        except Exception as e:
            print(f"Error fetching {self.hub.url}: {e}")

    async def parse_hub_page(self, html_content, session):
        soup = BeautifulSoup(html_content, 'html.parser')
        article_links = soup.select(self.selectors.article_selector)

        tasks = [self.fetch_article_data(link.get('href'), session) for link in article_links if link.get('href')]
        await asyncio.gather(*tasks)

    async def fetch_article_data(self, url, session):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    self.parse_article_page(url, html_content)
                else:
                    print(f"Failed to fetch article {url}: Status code {response.status}")
        except Exception as e:
            print(f"Error fetching article {url}: {e}")

    def parse_article_page(self, url, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        title = soup.select_one(self.selectors.title_selector).get_text(strip=True)
        author = soup.select_one(self.selectors.author_selector).get_text(strip=True)
        author_url = soup.select_one(self.selectors.author_selector).get('href')
        publication_date = soup.select_one(self.selectors.publication_date_selector).get_text(strip=True)
        content = soup.select_one(self.selectors.content_selector).get_text(strip=True)

        # Сохранение данных в базу, если статья еще не существует
        Post.objects.update_or_create(
            post_url=url,
            defaults={
                'hub': self.hub,
                'title': title,
                'author_name': author,
                'author_url': author_url,
                'publication_date': timezone.datetime.strptime(publication_date, '%Y-%m-%d %H:%M:%S'),
                'content': content
            }
        )

class Command(BaseCommand):
    help = 'Fetches articles from all hubs and saves them to the database'

    async def fetch_all_hubs(self):
        hubs = Hub.objects.all()
        async with aiohttp.ClientSession() as session:
            tasks = [ArticleFetcher(hub).fetch_hub_page(session) for hub in hubs]
            await asyncio.gather(*tasks)

    def handle(self, *args, **kwargs):
        asyncio.run(self.fetch_all_hubs())
        self.stdout.write(self.style.SUCCESS('Articles successfully fetched!'))
