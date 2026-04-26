from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'department', 'uploaded_by', 'upload_date',
                    'is_processed', 'chunk_count')
    list_filter = ('department', 'is_processed')
    search_fields = ('filename',)
    ordering = ('-upload_date',)
