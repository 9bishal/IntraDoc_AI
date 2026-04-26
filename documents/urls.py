"""
URL configuration for the documents app.
"""

from django.urls import path
from .views import DocumentUploadView, DocumentListView, DocumentStatsView

app_name = 'documents'

urlpatterns = [
    path('upload/', DocumentUploadView.as_view(), name='upload'),
    path('', DocumentListView.as_view(), name='list'),
    path('stats/', DocumentStatsView.as_view(), name='stats'),
]
