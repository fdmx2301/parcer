from django.contrib import admin
from .models import Hub, HubSelectors, Post

@admin.register(Hub)
class HubAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'last_fetched'
    ]
    readonly_fields = ('last_fetched',)
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        'hub', 'title', 'post_url', 'author_name', 'publication_date',
        'author_url', 'created_at'
    ]
    list_select_related = ('hub',)
    readonly_fields = (
        'hub', 'title', 'post_url', 'author_name', 'publication_date',
        'author_url', 'created_at',
    )

    list_filter = ('hub', 'publication_date',)
    search_fields = ('title', 'author_name', 'author_url',)

@admin.register(HubSelectors)
class HubSelectorsAdmin(admin.ModelAdmin):
    list_display = [
        'hub', 'article_selector', 'title_selector',
        'author_selector', 'publication_date_selector'
    ]
    list_select_related = ('hub',)
    list_filter = ('hub',)
    search_fields = ('hub',)