from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import DoctorSupportTicket

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
