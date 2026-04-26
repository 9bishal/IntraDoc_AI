"""
Serializers for the chat app.
"""

from rest_framework import serializers
from .models import ChatLog


class ChatQuerySerializer(serializers.Serializer):
    """Serializer for incoming chat queries."""

    query = serializers.CharField(
        max_length=2000,
        help_text='The question to ask the AI.',
    )
    department = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text='The department to search in (e.g., hr, finance, legal, graph).'
    )
    history = serializers.ListField(
        child=serializers.CharField(max_length=2000),
        required=False,
        default=list,
        help_text='Recent chat history (e.g. past queries).'
    )


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat API responses."""

    query = serializers.CharField()
    response = serializers.CharField()
    chunks_used = serializers.IntegerField()
    departments_searched = serializers.ListField(child=serializers.CharField())


class ChatLogSerializer(serializers.ModelSerializer):
    """Serializer for chat history."""

    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ChatLog
        fields = ('id', 'username', 'query', 'response', 'timestamp')
        read_only_fields = fields
