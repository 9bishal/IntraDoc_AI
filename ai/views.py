"""
AI app views — health check, index stats, and cache stats.
"""

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .llm import check_ollama_health
from .vector import get_vector_store
from .cache import get_search_cache


class HealthCheckView(APIView):
    """
    GET /api/health/

    System health check endpoint. Returns status of:
    - Django application
    - Ollama LLM
    - FAISS indexes
    - Search cache
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Check Ollama
        ollama_status = check_ollama_health()

        # Check FAISS
        try:
            vector_store = get_vector_store()
            faiss_stats = vector_store.get_index_stats()
            faiss_healthy = True
        except Exception as e:
            faiss_stats = {'error': str(e)}
            faiss_healthy = False

        # Check Cache
        cache_stats = get_search_cache().stats()

        return Response({
            'status': 'healthy',
            'services': {
                'django': True,
                'ollama': ollama_status,
                'faiss': {
                    'healthy': faiss_healthy,
                    'indexes': faiss_stats,
                },
                'cache': cache_stats,
            },
        })
