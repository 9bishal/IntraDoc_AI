"""
Document model for uploaded PDF files.

Each document belongs to a department (HR, ACCOUNTS, LEGAL) and tracks
who uploaded it and when.
"""

from django.conf import settings
from django.db import models


class Department(models.TextChoices):
    """Enumeration of departments for document classification."""
    HR = 'hr', 'HR'
    ACCOUNTS = 'accounts', 'Accounts'
    LEGAL = 'legal', 'Legal'
    FINANCE = 'finance', 'Finance'


def document_upload_path(instance, filename):
    """Generate upload path: media/documents/<department>/<filename>."""
    return f"documents/{instance.department}/{filename}"


class Document(models.Model):
    """Represents an uploaded PDF document belonging to a department."""

    file = models.FileField(upload_to=document_upload_path)
    department = models.CharField(
        max_length=20,
        choices=Department.choices,
        db_index=True,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='documents',
    )
    upload_date = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255, blank=True)
    is_processed = models.BooleanField(
        default=False,
        help_text='Whether the document has been processed for embeddings.',
    )
    chunk_count = models.IntegerField(
        default=0,
        help_text='Number of text chunks extracted from the document.',
    )

    class Meta:
        db_table = 'documents'
        ordering = ['-upload_date']

    def __str__(self):
        return f"{self.filename} ({self.department})"

    def save(self, *args, **kwargs):
        """Auto-populate filename from the uploaded file."""
        if self.file and not self.filename:
            self.filename = self.file.name.split('/')[-1]
        super().save(*args, **kwargs)
