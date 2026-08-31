from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        LAB_MANAGER = 'lab_manager', 'Lab Manager'
        ENGINEER = 'engineer', 'Engineer'
        VIEWER = 'viewer', 'Viewer'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ENGINEER)
    laboratory = models.ForeignKey(
        'laboratory.Laboratory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
    )

    class Meta:
        db_table = 'accounts_user'
