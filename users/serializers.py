"""
Serializers for user registration, login, and profile.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import User, Role


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
    )
    role = serializers.ChoiceField(choices=Role.choices, default=Role.HR)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'role')
        read_only_fields = ('id',)

    def create(self, validated_data):
        """Create a new user with a hashed password."""
        return User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            role=validated_data.get('role', Role.HR),
        )


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login (validates credentials)."""

    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs):
        """Authenticate the user."""
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError('Invalid credentials.')
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled.')

        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for reading user profile data."""

    class Meta:
        model = User
        fields = ('id', 'username', 'role', 'is_active', 'created_at')
        read_only_fields = fields


class AccessTokenCreateSerializer(serializers.Serializer):
    """Serializer for admin-issued one-time access token."""

    email = serializers.EmailField(required=False, allow_blank=False)
    assigned_role = serializers.ChoiceField(
        choices=[Role.ADMIN, Role.HR, Role.LEGAL, Role.FINANCE],
        default=Role.HR,
    )
    expires_in_hours = serializers.IntegerField(min_value=1, max_value=24 * 30, default=72)


class AccessTokenVerifySerializer(serializers.Serializer):
    """Serializer for validating and consuming a one-time access token."""

    email = serializers.EmailField()
    access_token = serializers.CharField(min_length=10, max_length=256)


class FirebaseLoginSerializer(serializers.Serializer):
    """Serializer for Firebase token exchange."""
    firebase_token = serializers.CharField(min_length=10)
    email = serializers.EmailField()
    uid = serializers.CharField(required=False, allow_blank=True)


class OTPVerifySerializer(serializers.Serializer):
    """Serializer for OTP verification."""
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=4, max_length=10)


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for requesting a password reset OTP."""
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password using an OTP."""
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(min_length=8, style={'input_type': 'password'})
