"""
Comprehensive test suite for the AI Role-Based Document Retrieval Backend.

Tests cover:
    - User registration and authentication (JWT)
    - Role-based access control (RBAC)
    - Document upload and processing
    - Chat API with RAG pipeline
    - Vector store operations

Usage:
    python manage.py test tests.test_api -v 2
"""

import io
import json
import tempfile
import os

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User, Role
from documents.models import Document
from chat.models import ChatLog
from users.permissions import get_accessible_departments, can_access_department


# Use a temporary directory for test media and FAISS indexes
TEST_MEDIA_ROOT = tempfile.mkdtemp()
TEST_FAISS_DIR = tempfile.mkdtemp()


def create_test_pdf(content="This is test content for the document."):
    """Create a minimal valid PDF file in memory."""
    pdf_content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {len(content) + 20} >>
stream
BT /F1 12 Tf 100 700 Td ({content}) Tj ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
0
%%EOF"""
    return io.BytesIO(pdf_content.encode('latin-1'))


class AuthenticationTests(TestCase):
    """Test user registration and JWT authentication."""

    def setUp(self):
        self.client = APIClient()

    def test_register_user(self):
        """Test user registration returns JWT tokens."""
        response = self.client.post(
            reverse('users:register'),
            {
                'username': 'testuser',
                'password': 'testpass1234',
                'role': 'HR',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('tokens', data)
        self.assertIn('access', data['tokens'])
        self.assertIn('refresh', data['tokens'])
        self.assertEqual(data['user']['username'], 'testuser')
        self.assertEqual(data['user']['role'], 'HR')

    def test_register_duplicate_username(self):
        """Test registration fails for duplicate username."""
        User.objects.create_user(username='existing', password='pass1234')
        response = self.client.post(
            reverse('users:register'),
            {
                'username': 'existing',
                'password': 'newpass1234',
                'role': 'HR',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """Test successful login returns JWT tokens."""
        User.objects.create_user(username='loginuser', password='loginpass1234')
        response = self.client.post(
            reverse('users:login'),
            {
                'username': 'loginuser',
                'password': 'loginpass1234',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('tokens', data)
        self.assertEqual(data['user']['username'], 'loginuser')

    def test_login_invalid_credentials(self):
        """Test login fails with wrong password."""
        User.objects.create_user(username='loginuser', password='correctpass')
        response = self.client.post(
            reverse('users:login'),
            {
                'username': 'loginuser',
                'password': 'wrongpass',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_authenticated(self):
        """Test that authenticated user can access their profile."""
        user = User.objects.create_user(
            username='profileuser', password='pass1234', role=Role.ADMIN
        )
        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['username'], 'profileuser')
        self.assertEqual(response.json()['role'], 'ADMIN')

    def test_profile_unauthenticated(self):
        """Test that unauthenticated request is rejected."""
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RBACTests(TestCase):
    """Test Role-Based Access Control logic."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', password='admin1234', role=Role.ADMIN
        )
        self.hr_user = User.objects.create_user(
            username='hr_user', password='hrpass1234', role=Role.HR
        )
        self.accounts_user = User.objects.create_user(
            username='accounts_user', password='accpass1234', role=Role.ACCOUNTS
        )
        self.legal_user = User.objects.create_user(
            username='legal_user', password='legalpass1234', role=Role.LEGAL
        )

    def test_admin_accessible_departments(self):
        """Admin should access all departments."""
        departments = get_accessible_departments(self.admin)
        self.assertEqual(sorted(departments), ['accounts', 'hr', 'legal'])

    def test_hr_accessible_departments(self):
        """HR user should only access HR department."""
        departments = get_accessible_departments(self.hr_user)
        self.assertEqual(departments, ['hr'])

    def test_accounts_accessible_departments(self):
        """Accounts user should only access Accounts department."""
        departments = get_accessible_departments(self.accounts_user)
        self.assertEqual(departments, ['accounts'])

    def test_admin_can_access_any_department(self):
        """Admin can access HR, Accounts, and Legal."""
        self.assertTrue(can_access_department(self.admin, 'hr'))
        self.assertTrue(can_access_department(self.admin, 'accounts'))
        self.assertTrue(can_access_department(self.admin, 'legal'))

    def test_hr_cannot_access_accounts(self):
        """HR user cannot access Accounts department."""
        self.assertFalse(can_access_department(self.hr_user, 'accounts'))

    def test_hr_can_access_hr(self):
        """HR user can access HR department."""
        self.assertTrue(can_access_department(self.hr_user, 'hr'))

    def test_accounts_cannot_access_legal(self):
        """Accounts user cannot access Legal department."""
        self.assertFalse(can_access_department(self.accounts_user, 'legal'))


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT, FAISS_INDEX_DIR=TEST_FAISS_DIR)
class DocumentTests(TestCase):
    """Test document upload and listing."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            username='admin', password='admin1234', role=Role.ADMIN
        )
        self.hr_user = User.objects.create_user(
            username='hr_user', password='hrpass1234', role=Role.HR
        )
        self.accounts_user = User.objects.create_user(
            username='accounts_user', password='accpass1234', role=Role.ACCOUNTS
        )

    def test_upload_document_to_own_department(self):
        """HR user can upload to HR department."""
        self.client.force_authenticate(user=self.hr_user)
        pdf_file = create_test_pdf("HR leave policy document content here")
        pdf_file.name = 'hr_policy.pdf'

        response = self.client.post(
            reverse('documents:upload'),
            {'file': pdf_file, 'department': 'hr'},
            format='multipart',
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_201_CREATED, status.HTTP_200_OK],
        )

    def test_upload_document_to_other_department_forbidden(self):
        """HR user cannot upload to Accounts department."""
        self.client.force_authenticate(user=self.hr_user)
        pdf_file = create_test_pdf("Accounts document")
        pdf_file.name = 'accounts_doc.pdf'

        response = self.client.post(
            reverse('documents:upload'),
            {'file': pdf_file, 'department': 'accounts'},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_upload_to_any_department(self):
        """Admin can upload to any department."""
        self.client.force_authenticate(user=self.admin)
        pdf_file = create_test_pdf("Legal contract document")
        pdf_file.name = 'legal_contract.pdf'

        response = self.client.post(
            reverse('documents:upload'),
            {'file': pdf_file, 'department': 'legal'},
            format='multipart',
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_201_CREATED, status.HTTP_200_OK],
        )

    def test_list_documents_rbac(self):
        """HR user should only see HR documents."""
        # Create documents in different departments
        Document.objects.create(
            file='test.pdf', department='hr',
            uploaded_by=self.admin, filename='hr_doc.pdf'
        )
        Document.objects.create(
            file='test2.pdf', department='accounts',
            uploaded_by=self.admin, filename='acc_doc.pdf'
        )

        self.client.force_authenticate(user=self.hr_user)
        response = self.client.get(reverse('documents:list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # HR user should only see HR documents
        data = response.json()
        for doc in data:
            self.assertEqual(doc['department'], 'hr')

    def test_admin_sees_all_documents(self):
        """Admin should see documents from all departments."""
        Document.objects.create(
            file='test.pdf', department='hr',
            uploaded_by=self.admin, filename='hr_doc.pdf'
        )
        Document.objects.create(
            file='test2.pdf', department='accounts',
            uploaded_by=self.admin, filename='acc_doc.pdf'
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse('documents:list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_upload_non_pdf_rejected(self):
        """Non-PDF files should be rejected."""
        self.client.force_authenticate(user=self.hr_user)
        txt_file = io.BytesIO(b"This is a text file")
        txt_file.name = 'document.txt'

        response = self.client.post(
            reverse('documents:upload'),
            {'file': txt_file, 'department': 'hr'},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class VectorStoreTests(TestCase):
    """Test FAISS vector store operations."""

    @override_settings(FAISS_INDEX_DIR=TEST_FAISS_DIR)
    def test_add_and_search_chunks(self):
        """Test adding chunks and searching them."""
        from ai.vector import VectorStore
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            with override_settings(FAISS_INDEX_DIR=tmpdir):
                vs = VectorStore()

                # Add HR chunks
                chunks = [
                    "The company leave policy allows 15 days annual leave.",
                    "Sick leave can be availed for up to 10 days per year.",
                    "Maternity leave is available for 6 months.",
                ]
                added = vs.add_chunks('hr', chunks, document_id=1)
                self.assertEqual(added, 3)

                # Search
                results = vs.search("leave policy", ['hr'], top_k=2)
                self.assertGreater(len(results), 0)
                self.assertEqual(results[0]['department'], 'hr')

    @override_settings(FAISS_INDEX_DIR=TEST_FAISS_DIR)
    def test_search_isolation(self):
        """Test that searches are isolated by department."""
        from ai.vector import VectorStore
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            with override_settings(FAISS_INDEX_DIR=tmpdir):
                vs = VectorStore()

                vs.add_chunks('hr', ["HR specific document about hiring"], document_id=1)
                vs.add_chunks('accounts', ["Accounts payable process"], document_id=2)

                # Search only HR
                results = vs.search("hiring", ['hr'], top_k=5)
                for r in results:
                    self.assertEqual(r['department'], 'hr')

                # Search only Accounts
                results = vs.search("payable", ['accounts'], top_k=5)
                for r in results:
                    self.assertEqual(r['department'], 'accounts')


class ChatAPITests(TestCase):
    """Test the chat API endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.hr_user = User.objects.create_user(
            username='hr_user', password='hrpass1234', role=Role.HR
        )

    def test_chat_requires_authentication(self):
        """Chat endpoint requires JWT authentication."""
        response = self.client.post(
            reverse('chat:chat'),
            {'query': 'What is the leave policy?'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_chat_empty_query_rejected(self):
        """Empty query should be rejected."""
        self.client.force_authenticate(user=self.hr_user)
        response = self.client.post(
            reverse('chat:chat'),
            {'query': ''},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(FAISS_INDEX_DIR=TEST_FAISS_DIR)
    def test_chat_no_documents(self):
        """Chat with no documents should return a helpful message."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with override_settings(FAISS_INDEX_DIR=tmpdir):
                self.client.force_authenticate(user=self.hr_user)
                response = self.client.post(
                    reverse('chat:chat'),
                    {'query': 'What is the leave policy?'},
                    format='json',
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                data = response.json()
                self.assertIn('response', data)

    def test_chat_creates_log(self):
        """Chat interaction should be logged."""
        self.client.force_authenticate(user=self.hr_user)
        self.client.post(
            reverse('chat:chat'),
            {'query': 'Test query for logging'},
            format='json',
        )
        logs = ChatLog.objects.filter(user=self.hr_user)
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().query, 'Test query for logging')

    def test_chat_history(self):
        """Chat history endpoint returns user's logs."""
        self.client.force_authenticate(user=self.hr_user)

        # Create some chat logs
        ChatLog.objects.create(
            user=self.hr_user,
            query='First question',
            response='First answer',
        )
        ChatLog.objects.create(
            user=self.hr_user,
            query='Second question',
            response='Second answer',
        )

        response = self.client.get(reverse('chat:history'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)


class DocumentProcessingTests(TestCase):
    """Test document text extraction and chunking."""

    def test_chunk_text(self):
        """Test text chunking produces correct number of chunks."""
        from documents.services import chunk_text

        text = "This is a test sentence. " * 100  # ~2500 characters
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertGreaterEqual(len(chunk), 20)

    def test_chunk_short_text(self):
        """Short text should produce a single chunk."""
        from documents.services import chunk_text

        text = "Short text here."
        chunks = chunk_text(text)
        self.assertEqual(len(chunks), 1)

    def test_chunk_empty_text(self):
        """Empty text should produce no chunks."""
        from documents.services import chunk_text

        chunks = chunk_text("")
        self.assertEqual(len(chunks), 0)


class HealthCheckTests(TestCase):
    """Test the health check endpoint."""

    def test_health_check_accessible(self):
        """Health check should be accessible without auth."""
        client = APIClient()
        response = client.get(reverse('health-check'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('services', data)
