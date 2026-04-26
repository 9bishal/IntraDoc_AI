"""
ChatLog model to record user queries and LLM responses.
"""

from django.conf import settings
from django.db import models


class ChatLog(models.Model):
    """Records each user query and the AI-generated response."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_logs',
    )
    query = models.TextField(help_text='The user query text.')
    response = models.TextField(help_text='The AI-generated response.')
    context_chunks = models.TextField(
        blank=True,
        default='',
        help_text='The context chunks used to generate the response.',
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Chat by {self.user.username} at {self.timestamp:%Y-%m-%d %H:%M}"
