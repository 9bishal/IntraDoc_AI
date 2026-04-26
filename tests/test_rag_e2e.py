"""
End-to-End RAG Test Suite with Real Queries.

Tests the full pipeline: document upload → indexing → query → chat response

Run with:
    python manage.py test tests.test_rag_e2e -v 2
"""

import io
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User, Role
from documents.models import Document
from chat.models import ChatLog


# Use temporary directories for test isolation
TEST_MEDIA_ROOT = tempfile.mkdtemp()
TEST_FAISS_DIR = tempfile.mkdtemp()


def create_test_pdf(content="This is test content for the document."):
    """Create a minimal valid PDF file in memory with .pdf extension."""
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
    file_obj = io.BytesIO(pdf_content.encode('latin-1'))
    file_obj.name = 'test_document.pdf'  # Set filename for validation
    return file_obj


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT, FAISS_INDEX_DIR=TEST_FAISS_DIR)
class RAGEndToEndTests(TestCase):
    """End-to-end RAG pipeline tests with real queries."""

    def setUp(self):
        """Create test users and documents."""
        self.client = APIClient()
        
        # Create test users with different roles
        # Note: user.department is a property that returns role.lower()
        self.hr_user = User.objects.create_user(
            username='hr_employee',
            password='hrpass12345',
            role=Role.HR
        )
        
        self.admin_user = User.objects.create_user(
            username='admin_user',
            password='adminpass12345',
            role=Role.ADMIN
        )
        
        self.legal_user = User.objects.create_user(
            username='legal_user',
            password='legalpass12345',
            role=Role.LEGAL
        )
        
        self.accounts_user = User.objects.create_user(
            username='accounts_user',
            password='accountspass12345',
            role=Role.ACCOUNTS
        )

    def test_hr_document_upload_and_query(self):
        """Test: HR user uploads HR document and queries it."""
        self.client.force_authenticate(user=self.hr_user)
        
        # Upload HR document
        pdf_content = create_test_pdf(
            "The annual leave policy provides 20 days of paid leave per year. "
            "Employees must submit leave requests 30 days in advance. "
            "Medical leave is provided for up to 15 days with a doctor's certificate."
        )
        
        response = self.client.post(
            reverse('documents:upload'),
            {
                'file': pdf_content,
                'department': 'hr',
            },
            format='multipart',
        )
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Upload error: {response.json()}")
            print(f"User role: {self.hr_user.role}, Department: {self.hr_user.department}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        print(f"Upload response: {response.json()}")
        doc_id = response.json().get('id')
        
        # Query the document
        response = self.client.post(
            reverse('chat:chat'),
            {'query': 'What is the annual leave policy?'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify response
        self.assertIn('response', data)
        self.assertIsNotNone(data['response'])
        self.assertGreater(len(data['response']), 0)
        self.assertEqual(data['chunks_used'], 1)
        self.assertIn('hr', data['departments_searched'])
        
        # Verify chat was logged
        logs = ChatLog.objects.filter(user=self.hr_user)
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().query, 'What is the annual leave policy?')
        print(f"✅ HR Query Response: {data['response'][:200]}...")

    def test_legal_document_access_restriction(self):
        """Test: HR user cannot access legal documents."""
        self.client.force_authenticate(user=self.hr_user)
        
        # Create a legal document (as admin)
        from documents.services import process_document
        import tempfile
        pdf_content = create_test_pdf("Contract terms and conditions.")
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(pdf_content.getvalue())
            legal_doc = Document.objects.create(
                file=tmp.name,
                department='legal',
                uploaded_by=self.admin_user,
            )
        
        # HR user tries to query about legal document
        response = self.client.post(
            reverse('chat:chat'),
            {'query': 'What are the contract terms?'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should not find legal documents
        self.assertNotIn('legal', data['departments_searched'])
        print(f"✅ Access Control: HR user correctly blocked from legal docs")

    def test_accounts_document_query(self):
        """Test: Accounts user can query Accounts department documents."""
        self.client.force_authenticate(user=self.accounts_user)
        
        # Upload Accounts document
        pdf_content = create_test_pdf(
            "Budget allocation for Q1 2024: "
            "HR Department: $500,000, "
            "IT Department: $750,000, "
            "Finance Department: $300,000. "
            "All departments must submit expense reports by the 15th of each month."
        )
        
        response = self.client.post(
            reverse('documents:upload'),
            {
                'file': pdf_content,
                'department': 'accounts',
            },
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Query the document
        response = self.client.post(
            reverse('chat:chat'),
            {'query': 'What is the budget information?'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify response
        self.assertIn('response', data)
        self.assertGreater(len(data['response']), 0)
        self.assertIn('accounts', data['departments_searched'])
        print(f"✅ Accounts Query Response: {data['response'][:200]}...")

    def test_multi_document_query(self):
        """Test: Query across multiple documents returns best matches."""
        self.client.force_authenticate(user=self.hr_user)
        
        # Upload multiple HR documents
        docs_data = [
            ("Attendance Policy", "Employees must maintain 95% attendance. "
                                 "Tardiness is recorded after 5 minutes. "
                                 "Absenteeism requires medical certificate."),
            ("Performance Review", "Annual performance reviews are conducted in December. "
                                  "Ratings: Excellent, Good, Satisfactory, Needs Improvement. "
                                  "Ratings determine salary increments."),
            ("Recruitment Policy", "Hiring requires 3 rounds of interviews. "
                                  "Offer letters are valid for 30 days. "
                                  "Background verification is mandatory."),
        ]
        
        for title, content in docs_data:
            pdf_content = create_test_pdf(content)
            response = self.client.post(
                reverse('documents:upload'),
                {
                    'file': pdf_content,
                    'department': 'hr',
                },
                format='multipart',
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Query that should match multiple documents
        response = self.client.post(
            reverse('chat:chat'),
            {'query': 'Tell me about employee policies and procedures'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return relevant information from multiple documents
        self.assertIn('response', data)
        self.assertGreater(len(data['response']), 0)
        self.assertGreaterEqual(data['chunks_used'], 1)
        print(f"✅ Multi-Doc Query Response: {data['response'][:200]}...")

    def test_follow_up_query(self):
        """Test: Follow-up queries use conversation context."""
        self.client.force_authenticate(user=self.hr_user)
        
        # Upload document
        pdf_content = create_test_pdf(
            "Leave Policy: 20 days annual leave, 5 days casual leave, "
            "15 days medical leave. "
            "Sick leave requires doctor's certificate after 3 consecutive days."
        )
        
        response = self.client.post(
            reverse('documents:upload'),
            {
                'file': pdf_content,
                'department': 'hr',
            },
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # First query
        response1 = self.client.post(
            reverse('chat:chat'),
            {'query': 'How many days of annual leave do employees get?'},
            format='json',
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        first_response = response1.json()
        print(f"✅ First Query: {first_response['response'][:150]}...")
        
        # Follow-up query
        response2 = self.client.post(
            reverse('chat:chat'),
            {'query': 'What about medical leave?'},
            format='json',
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        second_response = response2.json()
        print(f"✅ Follow-up Query: {second_response['response'][:150]}...")
        
        # Both should be logged
        logs = ChatLog.objects.filter(user=self.hr_user).order_by('timestamp')
        self.assertEqual(logs.count(), 2)

    def test_empty_query_response(self):
        """Test: Query with no matching documents returns helpful message."""
        self.client.force_authenticate(user=self.hr_user)
        
        # Query with no documents uploaded
        response = self.client.post(
            reverse('chat:chat'),
            {'query': 'What is the vacation policy?'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should return helpful message
        self.assertIn('response', data)
        self.assertIn('found', data['response'].lower())
        print(f"✅ Empty Query Response: {data['response']}")

    def test_admin_cross_department_access(self):
        """Test: Admin user can access documents from all departments."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create documents in different departments
        departments = ['hr', 'legal', 'accounts']
        for dept in departments:
            pdf_content = create_test_pdf(f"This is a {dept} document.")
            response = self.client.post(
                reverse('documents:upload'),
                {
                    'file': pdf_content,
                    'department': dept,
                },
                format='multipart',
            )
            if response.status_code != status.HTTP_201_CREATED:
                print(f"Upload error for {dept}: {response.json()}")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Admin queries
        response = self.client.post(
            reverse('chat:chat'),
            {'query': 'What documents are available?'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should have access to multiple departments
        self.assertEqual(len(data['departments_searched']), 3)
        print(f"✅ Admin Access: Can access {data['departments_searched']}")

    def test_chat_history_retrieval(self):
        """Test: User can retrieve their chat history."""
        self.client.force_authenticate(user=self.hr_user)
        
        # Create some chat logs
        for i in range(3):
            ChatLog.objects.create(
                user=self.hr_user,
                query=f'Question {i+1}',
                response=f'Answer {i+1}',
                context_chunks=str([]),
            )
        
        # Retrieve history
        response = self.client.get(reverse('chat:history'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should have 3 entries
        self.assertEqual(len(data), 3)
        # API returns in reverse order (newest first)
        self.assertEqual(data[0]['query'], 'Question 3')
        print(f"✅ Chat History: Retrieved {len(data)} entries")

    def test_real_world_hr_queries(self):
        """Test: Real-world HR department queries."""
        self.client.force_authenticate(user=self.hr_user)
        
        # Upload comprehensive HR document
        hr_doc_content = """
        COMPANY EMPLOYEE HANDBOOK
        
        1. LEAVE POLICY
        Annual Leave: 20 days per calendar year
        Sick Leave: 10 days per year with medical certificate
        Casual Leave: 5 days per year
        Maternity Leave: 6 months (for female employees)
        Paternity Leave: 15 days (for male employees)
        
        2. SALARY STRUCTURE
        Base Salary: Depends on designation and experience
        House Rent Allowance: 20% of base salary
        Dearness Allowance: 10% of base salary
        Performance Bonus: Up to 3 months (annual)
        
        3. WORKING HOURS
        Monday to Friday: 9 AM to 6 PM (1 hour lunch break)
        Weekend: Saturday and Sunday (off)
        Flexible hours available for approved roles
        
        4. CODE OF CONDUCT
        Employees must maintain professional behavior
        Punctuality is mandatory
        Confidentiality of company data is crucial
        Harassment of any kind is strictly prohibited
        """
        
        pdf_content = create_test_pdf(hr_doc_content)
        response = self.client.post(
            reverse('documents:upload'),
            {
                'file': pdf_content,
                'department': 'hr',
            },
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test multiple realistic queries
        queries = [
            'How many days of annual leave do I get?',
            'What is the salary structure?',
            'What are the working hours?',
            'What is the maternity leave policy?',
            'Tell me about house rent allowance',
        ]
        
        for query in queries:
            response = self.client.post(
                reverse('chat:chat'),
                {'query': query},
                format='json',
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            data = response.json()
            self.assertGreater(len(data['response']), 0)
            print(f"✅ Query: '{query}' → Got response ({len(data['response'])} chars)")
        
        # Verify all queries are logged
        logs = ChatLog.objects.filter(user=self.hr_user)
        self.assertEqual(logs.count(), len(queries))
