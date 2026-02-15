from django.contrib import admin
from .models import UserActivity, UserSession


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'ip_address', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'description', 'ip_address')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'activity_type', 'description', 'ip_address', 'user_agent', 'created_at')
    list_per_page = 50


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_key', 'ip_address', 'login_time', 'logout_time', 'is_active')
    list_filter = ('is_active', 'login_time', 'logout_time')
    search_fields = ('user__username', 'session_key', 'ip_address')
    ordering = ('-login_time',)
    readonly_fields = ('user', 'session_key', 'ip_address', 'user_agent', 'login_time')
    list_editable = ('is_active',)
