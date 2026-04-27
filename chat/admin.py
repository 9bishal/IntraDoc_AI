from django.contrib import admin
from .models import ChatLog


@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'query_preview', 'response_preview', 'timestamp')
    list_filter = ('user', 'timestamp')
    search_fields = ('query', 'response')
    ordering = ('-timestamp',)

    def query_preview(self, obj):
        return obj.query[:50] + '...' if len(obj.query) > 50 else obj.query
    query_preview.short_description = 'Query'

    def response_preview(self, obj):
        return obj.response[:50] + '...' if len(obj.response) > 50 else obj.response
    response_preview.short_description = 'Response'
