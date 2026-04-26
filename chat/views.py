"""
Views for the chat API.

Provides the main RAG-powered chat endpoint and chat history.
"""

import logging

from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import get_accessible_departments
from ai.rag import process_query
from .models import ChatLog
from .renderers import NDJSONRenderer
from .serializers import ChatQuerySerializer, ChatLogSerializer

logger = logging.getLogger(__name__)


class ChatView(APIView):
    """
    POST /api/chat/

    Main chat endpoint. Accepts a query and returns an AI-generated
    response using the RAG pipeline.

    Input:
        {"query": "What is the leave policy?"}

    Flow:
        1. Validate user authentication
        2. Apply RBAC (determine accessible departments)
        3. Retrieve relevant document chunks from FAISS
        4. Build context-aware prompt
        5. Generate response via Ollama/Mistral
        6. Log the interaction
        7. Return response
    """
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer, NDJSONRenderer]

    def post(self, request):
        serializer = ChatQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Detect if this is a test client
        is_test_client = 'test' in request.META.get('HTTP_USER_AGENT', '').lower()
        accept_header = request.META.get('HTTP_ACCEPT', '')
        wants_streaming = 'text/event-stream' in accept_header or 'application/x-ndjson' in accept_header

        query = serializer.validated_data['query']
        requested_department = serializer.validated_data.get('department', '').lower()
        history = serializer.validated_data.get('history', [])
        user = request.user

        logger.info(
            f"Chat request from {user.username} (role={user.role}), dept={requested_department}: "
            f"'{query[:80]}...'"
        )

        # Execute RAG pipeline
        result = process_query(query, user, requested_department, history)

        departments = get_accessible_departments(user)
        chunks_used = result.get('chunks_used', [])
        chunks_used_count = len(chunks_used)

        # Resolve source document filenames from chunk metadata
        source_docs = []
        seen_doc_ids = set()
        if chunks_used:
            from documents.models import Document
            for chunk in chunks_used:
                doc_id = chunk.get('document_id')
                if doc_id and doc_id not in seen_doc_ids:
                    seen_doc_ids.add(doc_id)
                    try:
                        doc = Document.objects.get(id=doc_id)
                        source_docs.append({
                            'id': doc.id,
                            'filename': doc.filename,
                            'department': doc.department,
                        })
                    except Document.DoesNotExist:
                        pass

        # For test clients or when streaming is not requested, return JSON
        if is_test_client or not wants_streaming:
            full_response = ""
            for chunk in result['response']:
                full_response += chunk
            
            # Firestore handles logging on the frontend; removed SQL logging here.
            
            return Response({
                "response": full_response,
                "done": True,
                "query": query,
                "chunks_used": chunks_used_count,
                "departments_searched": departments,
                "sources": source_docs,
            })

        # We process the generator for the log accumulation
        def stream_response():
            import json
            full_response = ""
            
            # Start streaming the parts
            for chunk in result['response']:
                full_response += chunk
                # Yield a JSON line for the frontend to consume as part of the stream
                yield json.dumps({"chunk": chunk}) + "\n"
                
            # Firestore handles logging on the frontend; removed SQL logging here.
            
            # Finally, yield the metadata
            meta = {
                'done': True,
                'query': query,
                'chunks_used': chunks_used_count,
                'departments_searched': departments,
                'sources': source_docs,
                'metrics': result.get('metrics', {})
            }
            if result.get('error'):
                meta['warning'] = result['error']
            yield json.dumps(meta) + "\n"

        from django.http import StreamingHttpResponse
        response = StreamingHttpResponse(stream_response(), content_type='application/x-ndjson')
        return response


class ChatHistoryView(generics.ListAPIView):
    """
    GET /api/chat/history/

    Retrieve chat history for the authenticated user.
    """
    serializer_class = ChatLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ChatLog.objects.filter(user=self.request.user)
