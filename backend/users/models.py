from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        LIBRARIAN = 'LIBRARIAN', 'Librarian'
        MEMBER = 'MEMBER', 'Member'

    name = models.CharField(max_length=150)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total_credits_spent = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['role'],
                condition=models.Q(role='LIBRARIAN'),
                name='only_one_librarian_role',
            ),
        ]

    @property
    def total_credits_earned(self) -> int:
        elapsed_seconds = max(0.0, (timezone.now() - self.created_at).total_seconds())
        completed_days = int(elapsed_seconds // 86400)  # 86,400 seconds = 24 hours
        return 5 + (completed_days * 5)

    @property
    def available_credits(self) -> int:
        return self.total_credits_earned - self.total_credits_spent

    @property
    def next_credit_unlock_info(self) -> dict:
        now = timezone.now()
        elapsed_seconds = max(0.0, (now - self.created_at).total_seconds())
        completed_days = int(elapsed_seconds // 86400)
        next_unlock_at = self.created_at + timedelta(days=completed_days + 1)
        remaining_seconds = max(0, int((next_unlock_at - now).total_seconds()))
        hours, remainder = divmod(remaining_seconds, 3600)
        minutes = remainder // 60
        return {
            "next_unlock_at": next_unlock_at,
            "hours_remaining": hours,
            "minutes_remaining": minutes,
        }

    def __str__(self):
        return f"{self.name or self.username} ({self.role}) - {self.available_credits} cr"
