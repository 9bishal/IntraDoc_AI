"""
Serializers for document upload and listing.
"""

from rest_framework import serializers
from .models import Document, Department


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading a document."""

    department = serializers.ChoiceField(choices=Department.choices)

    class Meta:
        model = Document
        fields = ('id', 'file', 'department', 'uploaded_by', 'upload_date',
                  'filename', 'is_processed', 'chunk_count')
        read_only_fields = ('id', 'uploaded_by', 'upload_date', 'filename',
                            'is_processed', 'chunk_count')

    def validate_file(self, value):
        """Ensure the uploaded file is a PDF."""
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError('Only PDF files are supported.')
        # Max file size: 20MB
        max_size = 20 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f'File size exceeds the 20MB limit. Got {value.size / (1024*1024):.1f}MB.'
            )
        return value

    def validate_department(self, value):
        # Backward-compatible alias: frontend may send "finance".
        if (value or '').lower() == 'finance':
            return Department.ACCOUNTS
        return value


class DocumentListSerializer(serializers.ModelSerializer):
    """Serializer for listing documents."""

    uploaded_by_username = serializers.CharField(
        source='uploaded_by.username', read_only=True
    )

    class Meta:
        model = Document
        fields = ('id', 'filename', 'department', 'uploaded_by',
                  'uploaded_by_username', 'upload_date', 'is_processed',
                  'chunk_count')
        read_only_fields = fields
