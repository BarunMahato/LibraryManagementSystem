from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import User
from users.permissions import IsLibrarian, IsLibrarianOrReadOnly
from .models import Book, BookCopy, BorrowLog
from .serializers import (
    BookCatalogSerializer,
    BookCopySerializer,
    BorrowLogSerializer,
    CheckoutRequestSerializer,
    ReshelveRequestSerializer,
    ReturnRequestSerializer,
)


class BookListCreateAPIView(APIView):
    """GET: Search catalog with grouped UNDER_DESK & ON_SHELF copies. POST: Add new book title."""
    permission_classes = [IsLibrarianOrReadOnly]

    def get(self, request):
        books = Book.objects.prefetch_related('copies').all().order_by('title')
        search = request.query_params.get('q')
        if search:
            books = books.filter(Q(title__icontains=search) | Q(author__icontains=search))
        serializer = BookCatalogSerializer(books, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BookCatalogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookDetailAPIView(APIView):
    permission_classes = [IsLibrarianOrReadOnly]
    def get(self, request, pk):
        book = get_object_or_404(Book.objects.prefetch_related('copies'), pk=pk)
        serializer = BookCatalogSerializer(book)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BookCopyListCreateAPIView(APIView):
    """GET: List physical copies. POST: Register a new barcoded physical copy."""

    def get(self, request):
        copies = BookCopy.objects.select_related('book').all()
        serializer = BookCopySerializer(copies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BookCopySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckoutBookAPIView(APIView):
    """Workflow B: Atomic Checkout with PostgreSQL row-level locking (SELECT ... FOR UPDATE)."""

    def post(self, request):
        serializer = CheckoutRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data['user_id']
        copy_barcode = serializer.validated_data['copy_barcode'].strip()

        with transaction.atomic():
            try:
                user = User.objects.select_for_update().get(pk=user_id)
            except User.DoesNotExist:
                return Response(
                    {"code": "USER_NOT_FOUND", "message": f"Member ID #{user_id} does not exist."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            try:
                copy = (
                    BookCopy.objects.select_for_update()
                    .select_related('book')
                    .get(barcode=copy_barcode)
                )
            except BookCopy.DoesNotExist:
                return Response(
                    {"code": "COPY_NOT_FOUND", "message": f"Barcode '{copy_barcode}' not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if copy.status == BookCopy.Status.CHECKED_OUT:
                return Response(
                    {
                        "code": "COPY_ALREADY_CHECKED_OUT",
                        "message": f"Copy '{copy.barcode}' ({copy.book.title}) is already checked out.",
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            credit_cost = copy.book.credit_cost
            current_balance = user.available_credits

            if current_balance < credit_cost:
                deficit = credit_cost - current_balance
                unlock = user.next_credit_unlock_info
                return Response(
                    {
                        "code": "INSUFFICIENT_CREDITS",
                        "message": (
                            f"Insufficient credits: '{copy.book.title}' costs {credit_cost} credits, "
                            f"but {user.name or user.username} only has {current_balance} credits "
                            f"(needs {deficit} more). Next +5 credits unlock in "
                            f"{unlock['hours_remaining']}h {unlock['minutes_remaining']}m."
                        ),
                        "available_credits": current_balance,
                        "required_credits": credit_cost,
                        "deficit": deficit,
                        "next_credit_unlock": unlock,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.total_credits_spent = F('total_credits_spent') + credit_cost
            user.save(update_fields=['total_credits_spent'])
            user.refresh_from_db()

            copy.status = BookCopy.Status.CHECKED_OUT
            copy.save(update_fields=['status', 'updated_at'])

            borrow_log = BorrowLog.objects.create(
                user=user,
                copy=copy,
                credits_charged=credit_cost,
            )

        return Response(
            {
                "message": f"Issued '{copy.book.title}' ({copy.barcode}) to {user.name or user.username}.",
                "remaining_credits": user.available_credits,
                "borrow_log": BorrowLogSerializer(borrow_log).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ReturnBookAPIView(APIView):
    """Workflow A: 1-Click Return Triage -> sets returned_at = NOW() and status = UNDER_DESK."""

    def post(self, request):
        serializer = ReturnRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        copy_barcode = serializer.validated_data['copy_barcode'].strip()

        with transaction.atomic():
            try:
                copy = (
                    BookCopy.objects.select_for_update()
                    .select_related('book')
                    .get(barcode=copy_barcode)
                )
            except BookCopy.DoesNotExist:
                return Response(
                    {"code": "COPY_NOT_FOUND", "message": f"Barcode '{copy_barcode}' not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            if copy.status != BookCopy.Status.CHECKED_OUT:
                return Response(
                    {
                        "code": "COPY_NOT_CHECKED_OUT",
                        "message": f"Copy '{copy.barcode}' is currently {copy.get_status_display()} and cannot be returned.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            active_log = (
                BorrowLog.objects.select_for_update()
                .filter(copy=copy, returned_at__isnull=True)
                .first()
            )
            if active_log:
                active_log.returned_at = timezone.now()
                active_log.save(update_fields=['returned_at'])

            copy.status = BookCopy.Status.UNDER_DESK
            copy.save(update_fields=['status', 'updated_at'])

        return Response(
            {
                "message": f"'{copy.book.title}' ({copy.barcode}) returned and placed UNDER_DESK.",
                "copy": BookCopySerializer(copy).data,
            },
            status=status.HTTP_200_OK,
        )


class ReshelveDeskPileAPIView(APIView):
    """Workflow C: GET lists UNDER_DESK pile sorted by shelf code; POST marks them ON_SHELF."""

    def get(self, request):
        desk_copies = (
            BookCopy.objects.select_related('book')
            .filter(status=BookCopy.Status.UNDER_DESK)
            .order_by('book__home_shelf_code', 'barcode')
        )
        return Response(
            {
                "count": desk_copies.count(),
                "results": BookCopySerializer(desk_copies, many=True).data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = ReshelveRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        barcodes = serializer.validated_data.get('copy_barcodes')

        with transaction.atomic():
            qs = BookCopy.objects.select_for_update().filter(status=BookCopy.Status.UNDER_DESK)
            if barcodes:
                qs = qs.filter(barcode__in=barcodes)
            reshelved_count = qs.update(status=BookCopy.Status.ON_SHELF, updated_at=timezone.now())

        return Response(
            {
                "message": f"Reshelved {reshelved_count} copy(ies) from UNDER_DESK back to ON_SHELF.",
                "reshelved_count": reshelved_count,
            },
            status=status.HTTP_200_OK,
        )