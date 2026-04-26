from django.contrib import admin
from .models import ChatLog


@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'timestamp')
    list_filter = ('user', 'timestamp')
    search_fields = ('query', 'response')
    ordering = ('-timestamp',)
