from django.contrib import admin
from .models import Book, BookCopy, BorrowLog

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'credit_cost', 'home_shelf_code')
    search_fields = ('title', 'author', 'home_shelf_code')

@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ('id', 'barcode', 'book', 'status', 'current_location_display')
    list_filter = ('status',)
    search_fields = ('barcode', 'book__title')

@admin.register(BorrowLog)
class BorrowLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'copy', 'user', 'credits_charged', 'borrowed_at', 'returned_at')
    list_filter = ('returned_at',)