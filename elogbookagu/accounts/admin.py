from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin

# Register your models here.
# Student को एडमिन पैनल में दिखाने के लिए
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("user", "group")
    list_filter = ("group",)
    # सर्च ऑप्शन यूज़रनेम के आधार पर
   


# Doctor को एडमिन पैनल में दिखाने के लिए
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    # डॉक्टर का यूज़रनेम और उसके डिपार्टमेंट्स दिखाना
    list_display = ("user", "get_departments")
    # डिपार्टमेंट के नाम से फिल्टरिंग
    list_filter = ("departments__name",)

    def get_departments(self, obj):
        """
        डॉक्टर के सभी डिपार्टमेंट्स को एक स्ट्रिंग में बदल कर दिखाना
        """
        return ", ".join([department.name for department in obj.departments.all()])

    get_departments.short_description = "Departments"  # कॉलम का नाम बदलना


# Staff को एडमिन पैनल में दिखाने के लिए
@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("user",)
    search_fields = ("user__username",)



# Custom User Admin for CustomUser model
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'role', 'is_staff', 'profile_photo',)
    list_filter = ('role', 'is_staff', 'is_superuser',)
    search_fields = ('username', 'email',)
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'role', 'profile_photo', 'is_active', 'is_staff', 'is_superuser')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {'fields': ('username', 'email', 'password1', 'password2', 'role', 'profile_photo')}),
    )

# Register the CustomUser model with the custom admin
admin.site.register(CustomUser, CustomUserAdmin)