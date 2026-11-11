from django.urls import path
from .views import (
    BookCopyListCreateAPIView,
    BookDetailAPIView,
    BookListCreateAPIView,
    CheckoutBookAPIView,
    ReshelveDeskPileAPIView,
    ReturnBookAPIView,
)

urlpatterns = [
    # Catalog & Physical Barcoded Copies
    path('books/', BookListCreateAPIView.as_view(), name='book-list-create'),
    path('books/<int:pk>/', BookDetailAPIView.as_view(), name='book-detail'),
    path('copies/', BookCopyListCreateAPIView.as_view(), name='copy-list-create'),

    # Core Transactional Workflows
    path('transactions/checkout/', CheckoutBookAPIView.as_view(), name='checkout-book'),
    path('transactions/return/', ReturnBookAPIView.as_view(), name='return-book'),
    path('transactions/reshelve/', ReshelveDeskPileAPIView.as_view(), name='reshelve-desk-pile'),
]