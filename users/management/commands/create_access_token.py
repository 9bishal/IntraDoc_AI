"""
Management command to create one-time signup access tokens.

Usage examples:
    python manage.py create_access_token
    python manage.py create_access_token --email employee@company.com --hours 48
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import AccessToken, Role


class Command(BaseCommand):
    help = 'Create a one-time access token for signup gating'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, default='', help='Bind token to a specific email')
        parser.add_argument('--hours', type=int, default=72, help='Token validity in hours (default: 72)')
        parser.add_argument(
            '--role',
            type=str,
            default=Role.HR,
            choices=[Role.ADMIN, Role.HR, Role.LEGAL, Role.FINANCE],
            help='Assigned role for the user created from this token',
        )

    def handle(self, *args, **options):
        email = (options.get('email') or '').strip().lower() or None
        hours = int(options.get('hours') or 72)
        role = options.get('role') or Role.HR
        if hours < 1:
            raise ValueError('--hours must be >= 1')

        expires_at = timezone.now() + timedelta(hours=hours)
        token, record = AccessToken.issue_token(
            created_by=None,
            assigned_email=email,
            assigned_role=role,
            expires_at=expires_at,
        )

        self.stdout.write(self.style.SUCCESS('One-time access token created'))
        self.stdout.write(f'token: {token}')
        self.stdout.write(f'token_id: {record.id}')
        self.stdout.write(f'assigned_email: {record.assigned_email or "(none)"}')
        self.stdout.write(f'assigned_role: {record.assigned_role}')
        self.stdout.write(f'expires_at: {record.expires_at.isoformat()}')
