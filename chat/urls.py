"""
URL configuration for the chat app.
"""

from django.urls import path
from .views import ChatView, ChatHistoryView

app_name = 'chat'

urlpatterns = [
    path('', ChatView.as_view(), name='chat'),
    path('history/', ChatHistoryView.as_view(), name='history'),
]
