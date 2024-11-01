from django.db import models
from django.core.exceptions import ValidationError


class Hub(models.Model):
    name = models.CharField(
        max_length=255,
        help_text='Название хаба',
        verbose_name='Название хаба',
        null=False,
        blank=False
    )
    url = models.URLField(
        help_text='Ссылка на хаб',
        verbose_name='Ссылка на хаб',
        null=False,
        blank=False
    )
    fetch_interval = models.IntegerField(
        default=10,
        help_text='Интервал обновления',
        verbose_name='Интервал обновления',
        null=False,
        blank=False
    )
    last_fetched = models.DateTimeField(
        help_text='Время последнего обновления',
        verbose_name='Время последнего обновления',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Хаб'
        verbose_name_plural = 'Хабы'
        ordering = ('name',)

    def clean(self):
        if self.fetch_interval <= 0:
            raise ValidationError('Интервал обновления должен быть больше нуля.')

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, name='{self.name}')>"

class HubSelectors(models.Model):
    hub = models.ForeignKey(
        Hub,
        on_delete=models.CASCADE,
        verbose_name='Хаб',
        help_text='Хаб', 
        related_name='selectors',
        null=False,
        blank=False
    )
    article_selector = models.CharField(
        max_length=255, 
        help_text='CSS-селектор для статей',
        verbose_name='CSS-селектор для статей',
        null=True,
        blank=True
    )
    title_selector = models.CharField(
        max_length=255, 
        help_text='CSS-селектор для заголовка',
        verbose_name='CSS-селектор для заголовка',
        null=True,
        blank=True
    )
    author_selector = models.CharField(
        max_length=255, 
        help_text='CSS-селектор для автора',
        verbose_name='CSS-селектор для автора',
        null=True,
        blank=True
    )
    author_url_selector = models.CharField(
        max_length=255, 
        help_text='CSS-селектор для ссылки на автора',
        verbose_name='CSS-селектор для ссылки на автора',
        null=True,
        blank=True
    )
    publication_date_selector = models.CharField(
        max_length=255, 
        help_text='CSS-селектор для даты публикации',
        verbose_name='CSS-селектор для даты публикации',
        null=True,
        blank=True
    )
    content_selector = models.CharField(
        max_length=255, 
        help_text='CSS-селектор для содержимого',
        verbose_name='CSS-селектор для содержимого',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Селектор'
        verbose_name_plural = 'Селекторы'
        ordering = ('hub',)

    def __str__(self):
        return self.hub.name

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, hub='{self.hub}')>"

class Post(models.Model):
    title = models.CharField(
        max_length=255,
        help_text='Заголовок поста',
        verbose_name='Заголовок поста',
        null=False,
        blank=False
    )
    author_name = models.CharField(
        max_length=255,
        help_text='Имя автора',
        verbose_name='Имя автора',
        null=False,
        blank=False
    )
    author_url = models.URLField(
        help_text='Ссылка на автора',
        verbose_name='Ссылка на автора',
        null=False,
        blank=False
    )
    post_url = models.URLField(
        unique=True,
        help_text='Ссылка на пост',
        verbose_name='Ссылка на пост',
        null=False,
        blank=False
    )
    publication_date = models.DateTimeField(
        help_text='Дата публикации',
        verbose_name='Дата публикации',
        null=False,
        blank=False
    )
    content = models.TextField(
        help_text='Содержание поста',
        verbose_name='Содержание поста',
        null=False,
        blank=False
    )
    hub = models.ForeignKey(
        Hub,
        on_delete=models.CASCADE,
        help_text='Хаб',
        verbose_name='Хаб',
        null=False,
        blank=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Время создания',
        verbose_name='Время создания',
        null=False,
        blank=False
    )

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ('-publication_date',)

    def __str__(self):
        return self.title
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, title='{self.title}')>"
