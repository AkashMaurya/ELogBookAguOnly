from django.contrib import admin
from .models import ActivityType, CoreDiaProSession

# ActivityType के लिए Admin
class ActivityTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'department')
    list_filter = ('department',)
    search_fields = ('name', 'department__name')
    ordering = ('name',)

# Activity के लिए Admin
class CoreDiaProSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'activity_type', 'department')
    list_filter = ('activity_type', 'department')
    search_fields = ('name', 'activity_type__name', 'department__name')
    ordering = ('name',)

# ActivityType के लिए Inline
class ActivityTypeInline(admin.TabularInline):
    model = ActivityType
    extra = 1

# Activity के लिए Inline
class ActivityInline(admin.TabularInline):
    model = CoreDiaProSession
    extra = 1



# मॉडल्स को रजिस्टर करें

admin.site.register(ActivityType, ActivityTypeAdmin)
admin.site.register(CoreDiaProSession, CoreDiaProSessionAdmin)