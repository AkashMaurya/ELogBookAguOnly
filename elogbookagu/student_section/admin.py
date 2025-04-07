from django.contrib import admin
from .models import StudentLogFormModel
from import_export.admin import ImportExportModelAdmin



@admin.register(StudentLogFormModel)
class StudentLogFormAdmin(ImportExportModelAdmin):
    list_display = ('student', 'date', 'department', 'activity_type', 'is_reviewed', 'get_status')
    list_filter = ('is_reviewed', 'department', 'log_year', 'log_year_section', 'group')
    search_fields = ('student__user__username', 'student__user__first_name', 'patient_id', 'description')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'date', 'patient_id')
        }),
        ('Academic Details', {
            'fields': ('log_year', 'log_year_section', 'group')
        }),
        ('Department & Supervision', {
            'fields': ('department', 'tutor', 'training_site')
        }),
        ('Activity Information', {
            'fields': ('activity_type', 'core_diagnosis', 'participation_type', 'description')
        }),
        ('Review Status', {
            'fields': ('is_reviewed', 'review_date', 'reviewer_comments')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
