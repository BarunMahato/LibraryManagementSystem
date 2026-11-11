from rest_framework import serializers
from .models import Book, BookCopy, BorrowLog


class BookCopySerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    home_shelf_code = serializers.CharField(source='book.home_shelf_code', read_only=True)
    current_location_display = serializers.CharField(read_only=True)

    class Meta:
        model = BookCopy
        fields = [
            'id',
            'barcode',
            'book',
            'book_title',
            'home_shelf_code',
            'status',
            'current_location_display',
        ]


class BookCatalogSerializer(serializers.ModelSerializer):
    under_desk_copies = serializers.SerializerMethodField()
    on_shelf_copies = serializers.SerializerMethodField()
    total_available = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author',
            'credit_cost',
            'home_shelf_code',
            'total_available',
            'under_desk_copies',
            'on_shelf_copies',
        ]

    def get_under_desk_copies(self, obj):
        copies = [c for c in obj.copies.all() if c.status == BookCopy.Status.UNDER_DESK]
        return BookCopySerializer(copies, many=True).data

    def get_on_shelf_copies(self, obj):
        copies = [c for c in obj.copies.all() if c.status == BookCopy.Status.ON_SHELF]
        return BookCopySerializer(copies, many=True).data

    def get_total_available(self, obj):
        return sum(
            1 for c in obj.copies.all()
            if c.status in (BookCopy.Status.UNDER_DESK, BookCopy.Status.ON_SHELF)
        )


class BorrowLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    barcode = serializers.CharField(source='copy.barcode', read_only=True)
    book_title = serializers.CharField(source='copy.book.title', read_only=True)

    class Meta:
        model = BorrowLog
        fields = [
            'id',
            'user',
            'user_name',
            'copy',
            'barcode',
            'book_title',
            'credits_charged',
            'borrowed_at',
            'returned_at',
        ]


class CheckoutRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    copy_barcode = serializers.CharField(max_length=64)


class ReturnRequestSerializer(serializers.Serializer):
    copy_barcode = serializers.CharField(max_length=64)


class ReshelveRequestSerializer(serializers.Serializer):
    copy_barcodes = serializers.ListField(
        child=serializers.CharField(max_length=64),
        required=False,
        allow_empty=True,
        help_text="Optional list of specific barcodes. If omitted, reshelves all UNDER_DESK copies.",
    )