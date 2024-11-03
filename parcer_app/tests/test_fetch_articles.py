from asgiref.sync import sync_to_async
from django.test import TestCase
from unittest.mock import patch, AsyncMock, MagicMock
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
        self.article_url_1 = 'https://example.com/hub1/article/1'
        self.article_url_2 = 'https://example.com/hub1/article/2'

        self.mock_command = MagicMock()

    @patch('aiohttp.ClientSession')
    async def test_fetch_hub_page_success(self, MockClientSession):
        fetcher = ArticleFetcher(self.hub, self.mock_command)
        
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
            <time datetime="2024-01-01" class="pub-date">2024-01-01</time>
            <div class="content"><p>This is the content of the article.</p></div>
        </html>
        """)

        # Настройка поведения контекстного менеджера
        mock_session.get.return_value.__aenter__.side_effect = [mock_hub_response, mock_article_response]

        await fetcher.fetch_hub_page(mock_session)

        # Проверка количества вызовов
        self.assertEqual(mock_session.get.call_count, 2)

        # Проверка вызовов с правильными URL
        mock_session.get.assert_any_call(self.hub.url)
        mock_session.get.assert_any_call(self.article_url_1)

        # Проверка, что статьи были загружены
        self.assertEqual(len(fetcher.fetched_articles), 1)
        self.assertEqual(fetcher.fetched_articles[0]['post_url'], self.article_url_1)

    @patch('aiohttp.ClientSession')
    async def test_fetch_article_data_success(self, MockClientSession):
        fetcher = ArticleFetcher(self.hub, self.mock_command)
        
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
            <time datetime="2024-01-01" class="pub-date">2024-01-01</time>
            <div class="content"><p>This is the content of the article.</p></div>
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
        self.assertEqual(article['post_url'], self.article_url_1)
        self.assertEqual(article['content'], 'This is the content of the article.')


    @patch('aiohttp.ClientSession')
    async def test_parse_article_page_and_store_data(self, MockClientSession):
        fetcher = ArticleFetcher(self.hub, self.mock_command)
        
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
            <time datetime="2024-01-01" class="pub-date">2024-01-01</time>
            <div class="content"><p>This is the content of the article.</p></div>
        </html>
        """)

        # Настройка поведения контекстного менеджера
        mock_session.get.return_value.__aenter__.side_effect = [mock_hub_response, mock_article_response]

        await fetcher.fetch_hub_page(mock_session)

        post = await sync_to_async(Post.objects.get)(post_url=self.article_url_1)
        self.assertEqual(post.title, 'Title')
        self.assertEqual(post.author_name, 'Test Author')
        self.assertEqual(post.publication_date.strftime('%Y-%m-%d'), '2024-01-01')
        self.assertEqual(post.content, 'This is the content of the article.')

    @patch('aiohttp.ClientSession')
    async def test_fetch_multiple_articles_success(self, MockClientSession):
        fetcher = ArticleFetcher(self.hub, self.mock_command)
        mock_session = MockClientSession()

        # Настройка моков для страницы хаба и двух успешных статей
        mock_hub_response = AsyncMock()
        mock_hub_response.status = 200
        mock_hub_response.text = AsyncMock(return_value=f'<html><a href="{self.article_url_1}">Article 1</a><a href="{self.article_url_2}">Article 2</a></html>')

        mock_article_response_1 = AsyncMock()
        mock_article_response_1.status = 200
        mock_article_response_1.text = AsyncMock(return_value="""
        <html>
            <h1 class="title">Title 1</h1>
            <a class="author_url" href="https://example.com/hub1/author/1">
                <span class="author">Author 1</span>
            </a>
            <time datetime="2024-01-01" class="pub-date">2024-01-01</time>
            <div class="content"><p>Content 1</p></div>
        </html>
        """)

        mock_article_response_2 = AsyncMock()
        mock_article_response_2.status = 200
        mock_article_response_2.text = AsyncMock(return_value="""
        <html>
            <h1 class="title">Title 2</h1>
            <a class="author_url" href="https://example.com/hub1/author/2">
                <span class="author">Author 2</span>
            </a>
            <time datetime="2024-01-02" class="pub-date">2024-01-02</time>
            <div class="content"><p>Content 2</p></div>
        </html>
        """)

        # Настройка поведения контекстного менеджера
        mock_session.get.return_value.__aenter__.side_effect = [mock_hub_response, mock_article_response_1, mock_article_response_2]

        await fetcher.fetch_hub_page(mock_session)

        # Проверка, что обе статьи были успешно загружены
        self.assertEqual(len(fetcher.fetched_articles), 2)
        article_1 = fetcher.fetched_articles[0]
        article_2 = fetcher.fetched_articles[1]

        self.assertEqual(article_1['title'], 'Title 1')
        self.assertEqual(article_2['title'], 'Title 2')

    @patch('aiohttp.ClientSession')
    async def test_fetch_multiple_articles_failure(self, MockClientSession):
        fetcher = ArticleFetcher(self.hub, self.mock_command)
        mock_session = MockClientSession()

        # Настройка моков для страницы хаба и двух неуспешных статей
        mock_hub_response = AsyncMock()
        mock_hub_response.status = 200
        mock_hub_response.text = AsyncMock(return_value=f'<html><a href="{self.article_url_1}">Article 1</a><a href="{self.article_url_2}">Article 2</a></html>')

        mock_article_response_1 = AsyncMock()
        mock_article_response_1.status = 404
        mock_article_response_2 = AsyncMock()
        mock_article_response_2.status = 500

        # Настройка поведения контекстного менеджера
        mock_session.get.return_value.__aenter__.side_effect = [mock_hub_response, mock_article_response_1, mock_article_response_2]

        await fetcher.fetch_hub_page(mock_session)

        # Проверка, что ни одна статья не была успешно загружена
        self.assertEqual(len(fetcher.fetched_articles), 0)

    @patch('aiohttp.ClientSession')
    async def test_fetch_mixed_success_failure(self, MockClientSession):
        fetcher = ArticleFetcher(self.hub, self.mock_command)
        mock_session = MockClientSession()

        # Настройка моков для страницы хаба, одна статья успешная, другая нет
        mock_hub_response = AsyncMock()
        mock_hub_response.status = 200
        mock_hub_response.text = AsyncMock(return_value=f'<html><a href="{self.article_url_1}">Article 1</a><a href="{self.article_url_2}">Article 2</a></html>')

        mock_article_response_1 = AsyncMock()
        mock_article_response_1.status = 200
        mock_article_response_1.text = AsyncMock(return_value="""
        <html>
            <h1 class="title">Title 1</h1>
            <a class="author_url" href="https://example.com/hub1/author/1">
                <span class="author">Author 1</span>
            </a>
            <time datetime="2024-01-01" class="pub-date">2024-01-01</time>
            <div class="content"><p>Content 1</p></div>
        </html>
        """)

        mock_article_response_2 = AsyncMock()
        mock_article_response_2.status = 500

        # Настройка поведения контекстного менеджера
        mock_session.get.return_value.__aenter__.side_effect = [mock_hub_response, mock_article_response_1, mock_article_response_2]

        await fetcher.fetch_hub_page(mock_session)

        # Проверка, что только одна статья была успешно загружена
        self.assertEqual(len(fetcher.fetched_articles), 1)
        article_1 = fetcher.fetched_articles[0]
        self.assertEqual(article_1['title'], 'Title 1')