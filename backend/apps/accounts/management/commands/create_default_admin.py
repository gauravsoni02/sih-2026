import os

from django.core.management.base import BaseCommand

from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Create a default admin user from ADMIN_USERNAME and ADMIN_PASSWORD env vars'

    def handle(self, *args, **options):
        username = os.environ.get('ADMIN_USERNAME', 'admin')
        password = os.environ.get('ADMIN_PASSWORD')

        if not password:
            self.stdout.write(self.style.WARNING('ADMIN_PASSWORD not set, skipping admin creation'))
        elif User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(f'Admin user "{username}" already exists'))
        else:
            User.objects.create_superuser(
                username=username,
                password=password,
                role=User.Role.ADMIN,
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user "{username}"'))

        self._create_demo_users()

    def _create_demo_users(self) -> None:
        """Seed one user per role when DEMO_USERS_PASSWORD is set.

        No default password: without the env var nothing is created, so a
        known-credential account can never appear in production by accident.
        """
        demo_password = os.environ.get('DEMO_USERS_PASSWORD')
        if not demo_password:
            return

        from apps.laboratory.models import Laboratory
        lab = Laboratory.objects.order_by('id').first()

        demo_users = [
            ('manager1', User.Role.LAB_MANAGER, 'Meera', 'Sharma'),
            ('engineer1', User.Role.ENGINEER, 'Arun', 'Patel'),
            ('viewer1', User.Role.VIEWER, 'Kavya', 'Nair'),
        ]
        for username, role, first, last in demo_users:
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'Demo user "{username}" already exists')
                continue
            User.objects.create_user(
                username=username,
                password=demo_password,
                role=role,
                first_name=first,
                last_name=last,
                laboratory=lab,
            )
            self.stdout.write(self.style.SUCCESS(
                f'Created demo user "{username}" ({role})'
            ))
