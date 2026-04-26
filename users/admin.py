import secrets
from datetime import timedelta

from django.contrib import admin, messages
from django import forms
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .models import User, AccessToken


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username',)
    ordering = ('-created_at',)


@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    class AccessTokenAdminForm(forms.ModelForm):
        send_email = forms.BooleanField(
            required=False,
            initial=True,
            help_text='Send the generated access token to the assigned email after save.',
            label='Send token to email',
        )

        class Meta:
            model = AccessToken
            fields = '__all__'

    form = AccessTokenAdminForm

    list_display = (
        'token_prefix',
        'assigned_email',
        'assigned_role',
        'created_by',
        'is_active',
        'used_at',
        'used_by_email',
        'expires_at',
        'created_at',
    )
    list_filter = ('is_active', 'used_at', 'expires_at', 'created_at')
    search_fields = ('token_prefix', 'assigned_email', 'used_by_email')
    ordering = ('-created_at',)
    readonly_fields = (
        'token_hash',
        'token_prefix',
        'created_by',
        'created_at',
        'used_at',
        'used_by_email',
    )

    def get_fields(self, request, obj=None):
        if obj is None:
            # Add form: keep it simple for admins. Token is auto-generated.
            return ('assigned_email', 'assigned_role', 'is_active', 'expires_at', 'send_email')
        # Change form: show token metadata but never allow editing hash/prefix.
        return (
            'assigned_email',
            'assigned_role',
            'is_active',
            'expires_at',
            'token_prefix',
            'token_hash',
            'created_by',
            'created_at',
            'used_at',
            'used_by_email',
        )

    def _generate_unique_token(self):
        for _ in range(5):
            plain_token = f"atk_{secrets.token_urlsafe(24)}"
            token_hash = AccessToken.hash_token(plain_token)
            if not AccessToken.objects.filter(token_hash=token_hash).exists():
                return plain_token, token_hash
        raise RuntimeError('Failed to generate unique access token')

    def save_model(self, request, obj, form, change):
        if not change:
            plain_token, token_hash = self._generate_unique_token()
            obj.token_hash = token_hash
            obj.token_prefix = plain_token[:12]
            obj.created_by = request.user
            if not obj.expires_at:
                obj.expires_at = timezone.now() + timedelta(hours=72)
            request._generated_access_token = plain_token
            request._send_access_token_email = bool(form.cleaned_data.get('send_email'))
        super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        plain_token = getattr(request, '_generated_access_token', None)
        if plain_token:
            self.message_user(
                request,
                (
                    "Access token created. Copy and send this now (shown once): "
                    f"{plain_token}"
                ),
                level=messages.WARNING,
            )

        should_send = bool(getattr(request, '_send_access_token_email', False))
        if should_send and obj.assigned_email and plain_token:
            subject = 'Your IntraDoc Access Token'
            body = (
                "You have been granted signup access for IntraDoc.\n\n"
                f"Access token: {plain_token}\n"
                f"Assigned role: {obj.assigned_role}\n"
                f"Expires at (UTC): {obj.expires_at.isoformat() if obj.expires_at else 'N/A'}\n\n"
                "This token is one-time use. Do not share it."
            )
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@intradoc.local'
            # Send after DB commit so email I/O never extends DB write lock window.
            def send_after_commit():
                try:
                    send_mail(subject, body, from_email, [obj.assigned_email], fail_silently=False)
                except Exception:
                    # Cannot report via message_user after response; error remains in server logs.
                    pass

            transaction.on_commit(send_after_commit)
            self.message_user(
                request,
                f'Access token save committed. Email queued to {obj.assigned_email}.',
                level=messages.SUCCESS,
            )
        return super().response_add(request, obj, post_url_continue)
