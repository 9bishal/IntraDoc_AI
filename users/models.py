"""
User model with role-based access control.

Roles:
    ADMIN    - Full access to all documents and queries.
    HR       - Access restricted to HR department documents.
    ACCOUNTS - Access restricted to Accounts department documents.
    LEGAL    - Access restricted to Legal department documents.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import hashlib
import secrets
from datetime import timedelta


class Role(models.TextChoices):
    """Enumeration of user roles."""
    ADMIN = 'ADMIN', 'Admin'
    HR = 'HR', 'HR'
    # Legacy role retained for backward compatibility with existing data.
    ACCOUNTS = 'ACCOUNTS', 'Accounts'
    LEGAL = 'LEGAL', 'Legal'
    FINANCE = 'FINANCE', 'Finance'


class UserManager(BaseUserManager):
    """Custom manager for the User model."""

    def create_user(self, username, password=None, role=Role.HR, **extra_fields):
        """Create and return a regular user with a hashed password."""
        if not username:
            raise ValueError('Users must have a username')

        user = self.model(username=username, role=role, **extra_fields)
        user.set_password(password)  # Uses bcrypt via PASSWORD_HASHERS
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        """Create and return a superuser with ADMIN role."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, password, role=Role.ADMIN, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with role-based access."""

    username = models.CharField(max_length=150, unique=True, db_index=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.HR,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_admin(self):
        """Check if the user has the ADMIN role."""
        return self.role == Role.ADMIN

    @property
    def department(self):
        """Return the department name for the user's role (lowercase)."""
        if self.role == Role.ADMIN:
            return 'all'
        if self.role in (Role.FINANCE, Role.ACCOUNTS):
            return 'accounts'
        return self.role.lower()


class AccessToken(models.Model):
    """
    One-time access token for gated signup.

    Security model:
        - Stores only SHA-256 hash of token value.
        - Token is consumed atomically on successful verification.
        - Consumed token cannot be reused.
    """

    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    token_prefix = models.CharField(max_length=12, db_index=True)
    assigned_email = models.EmailField(blank=True, null=True)
    assigned_role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.HR,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_access_tokens',
    )
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    used_at = models.DateTimeField(blank=True, null=True)
    used_by_email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'access_tokens'
        ordering = ['-created_at']

    def __str__(self):
        status = 'used' if self.used_at else 'active'
        return f"{self.token_prefix}... ({status})"

    @staticmethod
    def hash_token(token):
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    @classmethod
    def issue_token(cls, created_by=None, assigned_email=None, assigned_role=Role.HR, expires_at=None):
        """
        Create and persist a new one-time access token.

        Returns:
            tuple[str, AccessToken]: (plain_token, token_record)
        """
        for _ in range(5):
            plain_token = f"atk_{secrets.token_urlsafe(24)}"
            token_hash = cls.hash_token(plain_token)
            if not cls.objects.filter(token_hash=token_hash).exists():
                token = cls.objects.create(
                    token_hash=token_hash,
                    token_prefix=plain_token[:12],
                    assigned_email=(assigned_email or '').lower() or None,
                    assigned_role=assigned_role,
                    created_by=created_by,
                    expires_at=expires_at,
                )
                return plain_token, token
        raise RuntimeError('Failed to generate unique access token')

    @property
    def is_expired(self):
        return bool(self.expires_at and self.expires_at <= timezone.now())


class EmailOTP(models.Model):
    """
    OTP records for email verification flows.
    """

    PURPOSE_SIGNUP = 'signup'
    PURPOSE_RESET_PASSWORD = 'reset_password'
    PURPOSE_CHOICES = [
        (PURPOSE_SIGNUP, 'Signup'),
        (PURPOSE_RESET_PASSWORD, 'Reset Password'),
    ]

    email = models.EmailField(db_index=True)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default=PURPOSE_SIGNUP)
    otp_hash = models.CharField(max_length=64)
    expires_at = models.DateTimeField(db_index=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_otps'
        ordering = ['-created_at']

    @staticmethod
    def hash_code(code):
        return hashlib.sha256(code.encode('utf-8')).hexdigest()

    @classmethod
    def create_otp(cls, email, purpose=PURPOSE_SIGNUP, ttl_minutes=10):
        code = f"{secrets.randbelow(1000000):06d}"
        instance = cls.objects.create(
            email=email.lower(),
            purpose=purpose,
            otp_hash=cls.hash_code(code),
            expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
        )
        return code, instance

    def matches(self, code):
        return self.otp_hash == self.hash_code(code)

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()
