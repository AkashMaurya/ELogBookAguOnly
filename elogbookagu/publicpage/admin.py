from django.contrib import admin
from .models import LogYear,LogYearSection, Department, Group, Student, Doctor, Staff

@admin.register(LogYear)
class LogYearAdmin(admin.ModelAdmin):
    list_display = ('year_name',)
    search_fields = ('year_name',)

@admin.register(LogYearSection)
class LogYearSectionAdmin(admin.ModelAdmin):
    list_display = ('year_section_name', 'year_name',)
    list_filter = ('year_name',)
    search_fields = ('year_section_name', 'year_name',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'log_year','log_year_section')
    list_filter = ('log_year',)
    search_fields = ('name',)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('group_name', 'log_year', 'log_year_section',) 
    list_filter = ('log_year',)
    search_fields = ('group_name',)

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'group',)
    list_filter = ('group',)
    search_fields = ('user__username',)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'department',)
    list_filter = ('department',)
    search_fields = ('user__username',)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)
