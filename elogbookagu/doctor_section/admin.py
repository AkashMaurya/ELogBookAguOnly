from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import DoctorSupportTicket, Notification

# Register your models here.

@admin.register(DoctorSupportTicket)
class DoctorSupportTicketAdmin(ImportExportModelAdmin):
    list_display = ('doctor', 'subject', 'date_created', 'status')
    list_filter = ('status',)
    search_fields = ('doctor__user__username', 'doctor__user__first_name', 'subject', 'description')
    readonly_fields = ('date_created', 'resolved_date')
    date_hierarchy = 'date_created'

    fieldsets = (
        ('Ticket Information', {
            'fields': ('doctor', 'subject', 'description')
        }),
        ('Status', {
            'fields': ('status', 'admin_comments', 'resolved_date')
        }),
        ('Timestamps', {
            'fields': ('date_created',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'created_at', 'is_read')
    list_filter = ('is_read',)
    search_fields = ('recipient__user__username', 'recipient__user__first_name', 'title', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Notification Information', {
            'fields': ('recipient', 'log_entry', 'title', 'message')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
