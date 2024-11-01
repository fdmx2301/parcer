from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('parcer/admin/')),
    path('parcer/', lambda request: redirect('parcer/admin/')),
    path('parcer/admin/', admin.site.urls),
]
