"""
Views for document upload, listing, and management.
"""

import logging

from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin, can_access_department, get_accessible_departments
from .models import Document
from .serializers import DocumentUploadSerializer, DocumentListSerializer
from .services import process_document

logger = logging.getLogger(__name__)


class DocumentUploadView(generics.CreateAPIView):
    """
    POST /api/documents/upload/

    Upload a PDF document for a department.
    Only ADMIN can upload to any department; others can upload to their own.
    """
    serializer_class = DocumentUploadSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        department = request.data.get('department', '').lower()

        # RBAC check: non-admin users can only upload to their department
        if not can_access_department(request.user, department):
            return Response(
                {'error': f'You do not have permission to upload to the {department} department.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save the document record
        document = serializer.save(uploaded_by=request.user)

        # Process the document (extract text, chunk, embed, index)
        # We use the file from the serializer's validated data directly.
        # This is more robust than reopening it from storage (e.g. Cloudinary)
        # which can fail due to propagation delays or credential issues.
        try:
            uploaded_file = serializer.validated_data.get('file')
            if not uploaded_file:
                 # Fallback to the saved document file if not in validated_data
                uploaded_file = document.file

            result = process_document(
                file_obj=uploaded_file,
                department=document.department,
                document_id=document.id,
            )

            # Update document record
            document.is_processed = True
            document.chunk_count = result.get('chunk_count', 0)
            document.save(update_fields=['is_processed', 'chunk_count'])

            return Response(
                {
                    'message': 'Document uploaded and processed successfully.',
                    'document': DocumentListSerializer(document).data,
                    'processing': result,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            try:
                document.file.close()
            except Exception:
                pass
            logger.error(f"Document processing failed: {str(e)}")
            # Document is saved but not processed
            return Response(
                {
                    'message': 'Document uploaded but processing failed.',
                    'document': DocumentListSerializer(document).data,
                    'error': str(e),
                },
                status=status.HTTP_201_CREATED,
            )


class DocumentListView(generics.ListAPIView):
    """
    GET /api/documents/

    List documents accessible to the authenticated user.
    ADMIN sees all; others see only their department.
    """
    serializer_class = DocumentListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        departments = get_accessible_departments(self.request.user)
        return Document.objects.filter(department__in=departments)


class DocumentStatsView(APIView):
    """
    GET /api/documents/stats/

    Get document statistics and FAISS index info.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from ai.vector import get_vector_store

        departments = get_accessible_departments(request.user)
        documents = Document.objects.filter(department__in=departments)

        # Get FAISS index stats
        vector_store = get_vector_store()
        index_stats = vector_store.get_index_stats()

        # Filter to accessible departments
        filtered_stats = {
            dept: index_stats.get(dept, {'total_vectors': 0, 'total_chunks': 0})
            for dept in departments
        }

        return Response({
            'total_documents': documents.count(),
            'processed_documents': documents.filter(is_processed=True).count(),
            'departments': filtered_stats,
        })
