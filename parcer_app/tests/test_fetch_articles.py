from asgiref.sync import sync_to_async
from django.test import TestCase
from unittest.mock import patch, AsyncMock
from parcer_app.models import Hub, HubSelectors, Post
from parcer_app.management.commands.fetch_articles import ArticleFetcher

class ArticleFetcherTests(TestCase):

    def setUp(self):
        self.hub = Hub.objects.create(name='Хаб 1', url='https://example.com/hub1')
        self.selectors = HubSelectors.objects.create(
            hub=self.hub, 
            article_selector='a',
            title_selector='.title',
            author_selector='.author',
            author_url_selector='.author_url',
            publication_date_selector='.pub-date',
            content_selector='.content'
        )
        self.article_url = 'https://example.com/hub1/article/1'

    @patch('aiohttp.ClientSession')
    async def test_fetch_hub_page_success(self, MockClientSession):
        fetcher = ArticleFetcher(self.hub)
        
        mock_session = MockClientSession()

        # Настройка моков для страницы хаба и статьи
        mock_hub_response = AsyncMock()
        mock_hub_response.status = 200
        mock_hub_response.text = AsyncMock(return_value='<html><a href="https://example.com/hub1/article/1">Article 1</a></html>')

        mock_article_response = AsyncMock()
        mock_article_response.status = 200
        mock_article_response.text = AsyncMock(return_value="""
        <html>
            <h1 class="title">Title</h1>
            <a class="author_url" href="https://example.com/hub1/author/1">
                <span class="author">Test Author</span>
            </a>
            <time class="pub-date">2024-01-01</time>
            <div class="content">This is the content of the article.</div>
        </html>
        """)

        # Настройка поведения контекстного менеджера
        mock_session.get.return_value.__aenter__.side_effect = [mock_hub_response, mock_article_response]

        await fetcher.fetch_hub_page(mock_session)

        # Проверка количества вызовов
        self.assertEqual(mock_session.get.call_count, 2)

        # Проверка вызовов с правильными URL
        mock_session.get.assert_any_call(self.hub.url)
        mock_session.get.assert_any_call(self.article_url)

        # Проверка, что статьи были загружены
        self.assertEqual(len(fetcher.fetched_articles), 1)
        self.assertEqual(fetcher.fetched_articles[0]['post_url'], self.article_url)

    @patch('aiohttp.ClientSession')
    async def test_fetch_article_data_success(self, MockClientSession):
        fetcher = ArticleFetcher(self.hub)
        
        mock_session = MockClientSession()

        # Настройка моков для страницы хаба и статьи
        mock_hub_response = AsyncMock()
        mock_hub_response.status = 200
        mock_hub_response.text = AsyncMock(return_value='<html><a href="https://example.com/hub1/article/1">Article 1</a></html>')

        mock_article_response = AsyncMock()
        mock_article_response.status = 200
        mock_article_response.text = AsyncMock(return_value="""
        <html>
            <h1 class="title">Title</h1>
            <a class="author_url" href="https://example.com/hub1/author/1">
                <span class="author">Test Author</span>
            </a>
            <time class="pub-date">2024-01-01</time>
            <div class="content">This is the content of the article.</div>
        </html>
        """)

        # Настройка поведения контекстного менеджера
        mock_session.get.return_value.__aenter__.side_effect = [mock_hub_response, mock_article_response]

        await fetcher.fetch_hub_page(mock_session)

        # Проверка, что данные были загружены
        self.assertEqual(len(fetcher.fetched_articles), 1)
        article = fetcher.fetched_articles[0]
        self.assertEqual(article['title'], 'Title')
        self.assertEqual(article['author'], 'Test Author')
        self.assertEqual(article['author_url'], 'https://example.com/hub1/author/1')
        self.assertEqual(article['publication_date'], '2024-01-01')
        self.assertEqual(article['post_url'], self.article_url)
        self.assertEqual(article['content'], 'This is the content of the article.')


    @patch('aiohttp.ClientSession')
    async def test_parse_article_page_and_store_data(self, MockClientSession):
        fetcher = ArticleFetcher(self.hub)
        
        mock_session = MockClientSession()

        # Настройка моков для страницы хаба и статьи
        mock_hub_response = AsyncMock()
        mock_hub_response.status = 200
        mock_hub_response.text = AsyncMock(return_value='<html><a href="https://example.com/hub1/article/1">Article 1</a></html>')

        mock_article_response = AsyncMock()
        mock_article_response.status = 200
        mock_article_response.text = AsyncMock(return_value="""
        <html>
            <h1 class="title">Title</h1>
            <a class="author_url" href="https://example.com/hub1/author/1">
                <span class="author">Test Author</span>
            </a>
            <time class="pub-date">2024-01-01</time>
            <div class="content">This is the content of the article.</div>
        </html>
        """)

        # Настройка поведения контекстного менеджера
        mock_session.get.return_value.__aenter__.side_effect = [mock_hub_response, mock_article_response]

        await fetcher.fetch_hub_page(mock_session)

        post = await sync_to_async(Post.objects.get)(post_url=self.article_url)
        self.assertEqual(post.title, 'Title')
        self.assertEqual(post.author_name, 'Test Author')
        self.assertEqual(post.publication_date.strftime('%Y-%m-%d'), '2024-01-01')
        self.assertEqual(post.content, 'This is the content of the article.')