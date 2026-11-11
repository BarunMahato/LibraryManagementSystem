from django.conf import settings
from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    author = models.CharField(max_length=255, db_index=True)
    credit_cost = models.PositiveIntegerField(default=5)
    home_shelf_code = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Format: Aisle-Rack-Shelf (e.g., B-04-S2)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.credit_cost} cr | {self.home_shelf_code})"


class BookCopy(models.Model):
    class Status(models.TextChoices):
        ON_SHELF = 'ON_SHELF', 'On Shelf'
        UNDER_DESK = 'UNDER_DESK', 'Under Desk'
        CHECKED_OUT = 'CHECKED_OUT', 'Checked Out'

    barcode = models.CharField(max_length=64, unique=True, db_index=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ON_SHELF,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Book Copies"

    @property
    def current_location_display(self) -> str:
        if self.status == self.Status.UNDER_DESK:
            return "Under Your Desk"
        if self.status == self.Status.ON_SHELF:
            return f"Shelf {self.book.home_shelf_code}"
        return "Checked Out"

    def __str__(self):
        return f"[{self.barcode}] {self.book.title} ({self.status})"


class BorrowLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='borrow_logs',
    )
    copy = models.ForeignKey(
        BookCopy,
        on_delete=models.CASCADE,
        related_name='borrow_logs',
    )
    credits_charged = models.PositiveIntegerField()
    borrowed_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ['-borrowed_at']
        constraints = [
            models.UniqueConstraint(
                fields=['copy'],
                condition=models.Q(returned_at__isnull=True),
                name='unique_active_borrow_per_copy',
            )
        ]

    def __str__(self):
        state = "Returned" if self.returned_at else "Active"
        return f"{self.copy.barcode} -> {self.user_id} [{state}]"