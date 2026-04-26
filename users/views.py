"""
Views for user authentication and profile management.
"""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
import requests
import logging

logger = logging.getLogger(__name__)

from .models import AccessToken, EmailOTP, User, Role
from .permissions import IsAdmin
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    AccessTokenCreateSerializer,
    AccessTokenVerifySerializer,
    FirebaseLoginSerializer,
    OTPVerifySerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/

    Register a new user.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens for the newly registered user
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'message': 'User registered successfully.',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role,
                },
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    POST /api/auth/login/

    Authenticate user and return JWT tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'message': 'Login successful.',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role,
                },
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
            },
            status=status.HTTP_200_OK,
        )


class ProfileView(generics.RetrieveAPIView):
    """
    GET /api/auth/profile/

    Retrieve the authenticated user's profile.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class AccessTokenCreateView(APIView):
    """
    POST /api/auth/access-tokens/create/

    Admin-only endpoint to issue a one-time access token.
    """
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = AccessTokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assigned_email = serializer.validated_data.get('email')
        assigned_role = serializer.validated_data.get('assigned_role')
        expires_in_hours = serializer.validated_data['expires_in_hours']
        expires_at = timezone.now() + timedelta(hours=expires_in_hours)

        plain_token, token = AccessToken.issue_token(
            created_by=request.user,
            assigned_email=assigned_email,
            assigned_role=assigned_role,
            expires_at=expires_at,
        )

        return Response(
            {
                'message': 'Access token created successfully.',
                'token': plain_token,
                'token_id': token.id,
                'assigned_email': token.assigned_email,
                'assigned_role': token.assigned_role,
                'expires_at': token.expires_at,
                'one_time_use': True,
            },
            status=status.HTTP_201_CREATED,
        )


class AccessTokenVerifyView(APIView):
    """
    POST /api/auth/verify-token

    Validate and atomically consume one-time access token.
    """
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = AccessTokenVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].lower()
        access_token = serializer.validated_data['access_token']
        token_hash = AccessToken.hash_token(access_token)

        try:
            token = AccessToken.objects.select_for_update().get(
                token_hash=token_hash,
                is_active=True,
            )
        except AccessToken.DoesNotExist:
            return Response(
                {'valid': False, 'error': 'Invalid access token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token.used_at:
            return Response(
                {'valid': False, 'error': 'Access token already used.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token.is_expired:
            return Response(
                {'valid': False, 'error': 'Access token expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token.assigned_email and token.assigned_email != email:
            return Response(
                {'valid': False, 'error': 'Access token does not match this email.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate OTP record first, then send. On send failure, rollback to keep token reusable.
        otp_code, otp_record = EmailOTP.create_otp(email=email, purpose=EmailOTP.PURPOSE_SIGNUP)
        subject = 'IntraDoc Email Verification OTP'
        body = (
            "Use the OTP below to verify your email for IntraDoc signup.\n\n"
            f"OTP: {otp_code}\n"
            f"Expires at (UTC): {otp_record.expires_at.isoformat()}\n\n"
            "If you did not request this, ignore this email."
        )
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@intradoc.local'
        try:
            send_mail(subject, body, from_email, [email], fail_silently=False)
        except Exception as exc:
            transaction.set_rollback(True)
            return Response(
                {
                    'valid': False,
                    'error': f'Failed to send OTP email: {exc}',
                    'otp_sent': False,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        token.used_at = timezone.now()
        token.used_by_email = email
        token.save(update_fields=['used_at', 'used_by_email'])

        return Response(
            {
                'valid': True,
                'message': 'Access token verified.',
                'one_time_use': True,
                'assigned_role': token.assigned_role,
                'otp_sent': True,
            },
            status=status.HTTP_200_OK,
        )


class OTPVerifyView(APIView):
    """
    POST /api/auth/verify-otp

    Verify email OTP sent during signup gating.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'].lower()
        otp = serializer.validated_data['otp']

        otp_record = (
            EmailOTP.objects
            .filter(email=email, purpose=EmailOTP.PURPOSE_SIGNUP, verified_at__isnull=True)
            .order_by('-created_at')
            .first()
        )
        if not otp_record:
            return Response(
                {'verified': False, 'error': 'No OTP request found for this email.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if otp_record.is_expired:
            return Response(
                {'verified': False, 'error': 'OTP expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not otp_record.matches(otp):
            return Response(
                {'verified': False, 'error': 'Invalid OTP.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp_record.verified_at = timezone.now()
        otp_record.save(update_fields=['verified_at'])

        return Response(
            {'verified': True, 'message': 'OTP verified successfully.'},
            status=status.HTTP_200_OK,
        )


class FirebaseLoginView(APIView):
    """
    POST /api/auth/firebase-login

    Verify Firebase ID token via Google Identity Toolkit and
    exchange it for backend JWT tokens.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = FirebaseLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        firebase_token = serializer.validated_data['firebase_token']
        client_email = serializer.validated_data['email'].lower()

        firebase_api_key = getattr(settings, 'FIREBASE_API_KEY', '')
        if not firebase_api_key:
            return Response(
                {'error': 'FIREBASE_API_KEY is not configured on backend.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        verify_url = (
            f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={firebase_api_key}"
        )
        try:
            verify_resp = requests.post(
                verify_url,
                json={'idToken': firebase_token},
                timeout=10,
            )
            if verify_resp.status_code != 200:
                return Response(
                    {'error': 'Invalid Firebase token.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            payload = verify_resp.json()
            users = payload.get('users', [])
            if not users:
                return Response(
                    {'error': 'Invalid Firebase token payload.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            token_email = (users[0].get('email') or '').lower()
            if not token_email or token_email != client_email:
                return Response(
                    {'error': 'Email mismatch between Firebase token and request.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except requests.RequestException:
            return Response(
                {'error': 'Could not verify Firebase token at this time.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Require email OTP verification ONLY for new signups.
        # If the user already exists in our DB, they've already passed verification once.
        user_exists = User.objects.filter(username=client_email).exists()
        
        if not user_exists:
            latest_otp = (
                EmailOTP.objects
                .filter(email=client_email, purpose=EmailOTP.PURPOSE_SIGNUP)
                .order_by('-created_at')
                .first()
            )
            if not latest_otp or not latest_otp.verified_at:
                return Response(
                    {'error': 'Email OTP is not verified yet. New accounts must verify their email via the signup flow.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        role_from_token = (
            AccessToken.objects
            .filter(used_by_email=client_email, used_at__isnull=False, is_active=True)
            .order_by('-used_at')
            .values_list('assigned_role', flat=True)
            .first()
        ) or Role.HR

        user, created = User.objects.get_or_create(
            username=client_email,
            defaults={'role': role_from_token},
        )
        if created:
            user.set_unusable_password()
            user.save(update_fields=['password'])
        elif user.role != Role.ADMIN and role_from_token and user.role != role_from_token:
            user.role = role_from_token
            user.save(update_fields=['role'])

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'message': 'Firebase login exchange successful.',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role,
                },
            },
            status=status.HTTP_200_OK,
        )


class ForgotPasswordView(APIView):
    """
    POST /api/auth/forgot-password
    
    Request a password reset OTP.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].lower()
        logger.info(f"Password reset requested for email: {email}")

        # Check if user exists (username is the email)
        user_exists = User.objects.filter(username=email).exists()
        
        # TIGHT COUPLING: If not in Django, check if they exist in Firebase Auth
        if not user_exists:
            firebase_api_key = getattr(settings, 'FIREBASE_API_KEY', '')
            if firebase_api_key:
                try:
                    # use createAuthUri to check if email is registered in Firebase
                    resp = requests.post(
                        f"https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri?key={firebase_api_key}",
                        json={"identifier": email, "continueUri": "http://localhost"},
                        timeout=5
                    )
                    if resp.status_code == 200:
                        is_registered = resp.json().get('registered', False)
                        if is_registered:
                            logger.info(f"Syncing Firebase user to Django: {email}")
                            # Auto-create the user in Django to tightly couple the DBs
                            User.objects.create_user(username=email, password=None, role=Role.HR)
                            user_exists = True
                except Exception as e:
                    logger.error(f"Firebase sync check failed: {str(e)}")

        if not user_exists:
            logger.warning(f"Password reset requested for non-existent user: {email}")
            return Response(
                {'error': 'No account found with this email address in our system or Firebase.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate OTP
        otp_code, otp_record = EmailOTP.create_otp(
            email=email, 
            purpose=EmailOTP.PURPOSE_RESET_PASSWORD
        )

        # Send beautiful HTML email
        subject = 'Reset Your IntraDoc Password'
        html_content = f"""
        <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #1f2937; margin: 0; padding: 0;">
                <div style="max-width: 600px; margin: 20px auto; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                    <div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 40px 20px; text-align: center;">
                        <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.025em;">IntraDoc AI</h1>
                        <p style="color: #e0e7ff; margin-top: 8px; font-size: 16px;">Secure Document Intelligence</p>
                    </div>
                    <div style="padding: 40px 30px;">
                        <h2 style="color: #111827; margin-top: 0; font-size: 22px; font-weight: 700;">Password Reset Request</h2>
                        <p style="font-size: 16px; color: #4b5563;">We received a request to reset your password. Use the verification code below to proceed with the reset process:</p>
                        
                        <div style="background-color: #f9fafb; border: 2px dashed #d1d5db; padding: 30px; text-align: center; border-radius: 12px; margin: 30px 0;">
                            <span style="font-family: 'Courier New', Courier, monospace; font-size: 42px; font-weight: 800; letter-spacing: 10px; color: #4f46e5;">{otp_code}</span>
                        </div>
                        
                        <p style="font-size: 14px; color: #6b7280; background-color: #fff7ed; padding: 12px; border-left: 4px solid #f97316; border-radius: 4px;">
                            <strong>Security Note:</strong> This code will expire in <strong>10 minutes</strong>. If you did not request this password reset, please ignore this email and ensure your account is secure.
                        </p>
                        
                        <hr style="border: 0; border-top: 1px solid #f3f4f6; margin: 40px 0;" />
                        
                        <div style="text-align: center;">
                            <p style="font-size: 12px; color: #9ca3af; margin: 0;">
                                &copy; 2026 IntraDoc AI &bull; Advanced Agentic Coding Team
                            </p>
                            <p style="font-size: 12px; color: #9ca3af; margin-top: 4px;">
                                This is an automated security notification.
                            </p>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        text_content = f"Your IntraDoc password reset OTP is: {otp_code}. It expires in 10 minutes."
        
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@intradoc.local'
        msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
        msg.attach_alternative(html_content, "text/html")
        
        try:
            msg.send(fail_silently=False)
            logger.info(f"Password reset email sent successfully to {email}")
        except Exception as e:
            return Response(
                {'error': f'Failed to send password reset email: {str(e)}'}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return Response({'message': 'Password reset OTP sent successfully.'}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """
    POST /api/auth/reset-password
    
    Verify OTP and reset the user's password.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email'].lower()
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']
        
        otp_record = EmailOTP.objects.filter(
            email=email, 
            purpose=EmailOTP.PURPOSE_RESET_PASSWORD,
            verified_at__isnull=True
        ).order_by('-created_at').first()
        
        if not otp_record:
            return Response(
                {'error': 'No password reset request found for this email.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if otp_record.is_expired:
            return Response(
                {'error': 'OTP has expired. Please request a new one.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not otp_record.matches(otp):
            return Response(
                {'error': 'Invalid OTP.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify OTP
        otp_record.verified_at = timezone.now()
        otp_record.save(update_fields=['verified_at'])
        
        # Update User Password
        try:
            user = User.objects.get(username=email)
            user.set_password(new_password)
            user.save()
            return Response({'message': 'Password reset successfully. You can now login with your new password.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
