"""
Management command to seed the database with test users.

Usage:
    python manage.py seed_users
"""

from django.core.management.base import BaseCommand
from users.models import User, Role


class Command(BaseCommand):
    help = 'Create test users for each role (admin, hr_user, accounts_user, legal_user, finance_user)'

    def handle(self, *args, **options):
        test_users = [
            {'username': 'admin', 'password': 'admin1234', 'role': Role.ADMIN},
            {'username': 'hr_user', 'password': 'hrpass1234', 'role': Role.HR},
            {'username': 'accounts_user', 'password': 'accpass1234', 'role': Role.ACCOUNTS},
            {'username': 'legal_user', 'password': 'legalpass1234', 'role': Role.LEGAL},
            {'username': 'finance_user', 'password': 'finpass1234', 'role': Role.FINANCE},
        ]

        for user_data in test_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={'role': user_data['role']},
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created user: {user.username} (role={user.role})"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"User already exists: {user.username} (role={user.role})"
                    )
                )

        self.stdout.write(self.style.SUCCESS('\nTest users seeded successfully!'))
