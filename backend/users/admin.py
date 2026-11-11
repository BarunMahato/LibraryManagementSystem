from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Library Credit Profile', {'fields': ('name', 'role', 'total_credits_spent')}),
    )
    readonly_fields = ('created_at', 'available_credits', 'total_credits_earned')
    list_display = ('id', 'username', 'name', 'role', 'available_credits', 'total_credits_spent', 'created_at')
    list_filter = ('role',)