from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
# Change the import to use relative import
from .models import (
    LogYear, 
    LogYearSection, 
    Department, 
    Group, 
    TrainingSite, 
    ActivityType, 
    CoreDiaProSession
)



# Resource class for CoreDiaProSession (for import/export functionality)
class CoreDiaProSessionResource(resources.ModelResource):
    # ForeignKey fields mapped by name instead of ID
    activity_type = fields.Field(
        column_name='activity_type',
        attribute='activity_type',
        widget=ForeignKeyWidget(ActivityType, field='name')
    )
    department = fields.Field(
        column_name='department',
        attribute='department',
        widget=ForeignKeyWidget(Department, field='name')
    )

    class Meta:
        model = CoreDiaProSession
        fields = ("name", "activity_type", "department")
        import_id_fields = ("name",)  # Unique field for identifying records

    # Display names instead of IDs during export
    def dehydrate_activity_type(self, obj):
        return obj.activity_type.name if obj.activity_type else ''

    def dehydrate_department(self, obj):
        return obj.department.name if obj.department else ''


# Admin configuration for LogYear
@admin.register(LogYear)
class LogYearAdmin(admin.ModelAdmin):
    list_display = ("year_name",)
    search_fields = ("year_name",)
    ordering = ("year_name",)


# Admin configuration for LogYearSection
@admin.register(LogYearSection)
class LogYearSectionAdmin(admin.ModelAdmin):
    list_display = ("year_section_name", "year_name", "is_deleted")
    list_filter = ("year_name", "is_deleted")
    search_fields = ("year_section_name", "year_name__year_name")
    ordering = ("year_section_name",)


# Inline for ActivityType (to show in Department admin)
class ActivityTypeInline(admin.TabularInline):
    model = ActivityType
    extra = 1


# Admin configuration for Department
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "log_year", "log_year_section")
    list_filter = ("log_year", "log_year_section")
    search_fields = ("name", "log_year__year_name", "log_year_section__year_section_name")
    inlines = [ActivityTypeInline]  # Show ActivityType inline within Department
    ordering = ("name",)


# Admin configuration for Group
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("group_name", "log_year", "log_year_section")
    list_filter = ("log_year", "log_year_section")
    search_fields = ("group_name", "log_year__year_name", "log_year_section__year_section_name")
    ordering = ("group_name",)


# Admin configuration for TrainingSite
@admin.register(TrainingSite)
class TrainingSiteAdmin(admin.ModelAdmin):
    list_display = ("name", "log_year")
    list_filter = ("log_year",)
    search_fields = ("name", "log_year__year_name")
    ordering = ("name",)


# Inline for CoreDiaProSession (to show in ActivityType admin)
class CoreDiaProSessionInline(admin.TabularInline):
    model = CoreDiaProSession
    extra = 1


# Admin configuration for ActivityType
@admin.register(ActivityType)
class ActivityTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "department")
    list_filter = ("department",)
    search_fields = ("name", "department__name")
    inlines = [CoreDiaProSessionInline]  # Show CoreDiaProSession inline within ActivityType
    ordering = ("name",)


# Admin configuration for CoreDiaProSession with Import/Export
@admin.register(CoreDiaProSession)
class CoreDiaProSessionAdmin(ImportExportModelAdmin):
    resource_class = CoreDiaProSessionResource  # Enables import/export functionality using the defined resource
    list_display = ("name", "activity_type", "department")  # Columns shown in the list view
    list_filter = ("activity_type", "department")  # Filters shown in the sidebar
    search_fields = ("name", "activity_type__name", "department__name")  # Fields searchable in the search bar
    ordering = ("name",)  # Default ordering of records
