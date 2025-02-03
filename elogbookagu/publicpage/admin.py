from django.contrib import admin
from .models import LogYear, LogYearSection, Department, Group, Student, Doctor, Staff, TrainingSite,CustomUser
from django.contrib.auth.admin import UserAdmin



# LogYear को एडमिन पैनल में दिखाने के लिए
@admin.register(LogYear)
class LogYearAdmin(admin.ModelAdmin):
    # Admin पैनल में कौन से फील्ड दिखेंगे
    list_display = ("year_name",)
    # सर्च के लिए कौन से फील्ड होंगे
    search_fields = ("year_name",)

# LogYearSection को एडमिन पैनल में दिखाने के लिए
@admin.register(LogYearSection)
class LogYearSectionAdmin(admin.ModelAdmin):
    list_display = ("year_section_name", "year_name")
    # फिल्टर ऑप्शन लॉग ईयर के आधार पर
    list_filter = ("year_name",)
    # सर्च ऑप्शन में year_section_name और year_name शामिल
    search_fields = ("year_section_name", "year_name")

# Department को एडमिन पैनल में दिखाने के लिए
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "log_year", "log_year_section")
    list_filter = ("log_year",)
    search_fields = ("name",)

# Group को एडमिन पैनल में दिखाने के लिए
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("group_name", "log_year", "log_year_section")
    list_filter = ("log_year",)
    search_fields = ("group_name",)

# Student को एडमिन पैनल में दिखाने के लिए
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("user", "group")
    list_filter = ("group",)
    # सर्च ऑप्शन यूज़रनेम के आधार पर
    search_fields = ("user__username",)

# Doctor को एडमिन पैनल में दिखाने के लिए
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    # डॉक्टर का यूज़रनेम और उसके डिपार्टमेंट्स दिखाना
    list_display = ('user', 'get_departments')
    # डिपार्टमेंट के नाम से फिल्टरिंग
    list_filter = ('departments__name',)

    def get_departments(self, obj):
        """
        डॉक्टर के सभी डिपार्टमेंट्स को एक स्ट्रिंग में बदल कर दिखाना
        """
        return ", ".join([department.name for department in obj.departments.all()])
    
    get_departments.short_description = 'Departments'  # कॉलम का नाम बदलना

# Staff को एडमिन पैनल में दिखाने के लिए
@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("user",)
    search_fields = ("user__username",)

# TrainingSite को एडमिन पैनल में दिखाने के लिए
@admin.register(TrainingSite)
class TrainingSiteAdmin(admin.ModelAdmin):
    list_display = ("name", "log_year")
    list_filter = ("log_year",)
    search_fields = ("name",)



# Custom User Admin for CustomUser model
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'is_staff', 'profile_photo')
    list_filter = ('role', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    
    # Add the fields to the form for user creation and change
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'profile_photo')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'profile_photo')}),
    )

# Register the CustomUser model with the custom admin
admin.site.register(CustomUser, CustomUserAdmin)